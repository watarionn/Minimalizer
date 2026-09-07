from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math

import cv2
import numpy as np

from .face_rules import FaceFeatureLayout
from .models import CharacterPartCandidate, CharacterStructure
from .part_types import CharacterPartType


@dataclass(slots=True)
class FaceIdentitySignals:
    """Pre-budget signals describing which face cues are worth keeping.

    Phase 10.5-a does not change the rendered Shapes. It only measures how much
    identity/readability each candidate cue contributes so Phase 10.5-b can
    spend a small Shape budget deliberately instead of reserving every feature.
    """

    face_size_score: float
    eye_salience_score: float
    second_eye_salience_score: float
    mouth_salience_score: float
    fringe_relation_score: float
    contour_salience_score: float
    expression_salience_score: float

    primary_eye_side: str = "none"
    visibility_tier: str = "micro"
    face_render_scale: float = 0.0
    face_area_ratio: float = 0.0
    feature_density_score: float = 0.0
    abstraction_level: int = 4
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _clamp01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _face_render_bbox(
    face: CharacterPartCandidate,
    layout: FaceFeatureLayout | None = None,
) -> tuple[int, int, int, int]:
    contour = face.metadata.get("contour_fit") or {}
    raw = contour.get("face_ellipse_bbox")
    if raw and len(raw) == 4:
        return tuple(int(round(v)) for v in raw)
    if layout is not None:
        return tuple(int(round(v)) for v in layout.face_bbox)
    return face.bbox


def estimate_face_render_scale(
    structure: CharacterStructure,
    face: CharacterPartCandidate | None = None,
    layout: FaceFeatureLayout | None = None,
) -> float:
    """Return rendered face diameter relative to the short canvas side."""
    face = face or structure.first_part(CharacterPartType.FACE)
    if face is None:
        return 0.0
    _, _, fw, fh = _face_render_bbox(face, layout)
    canvas_h, canvas_w = structure.subject_mask.shape[:2]
    short_side = max(1.0, float(min(canvas_w, canvas_h)))
    # Geometric mean is stable for long/thin candidate boxes.
    diameter = math.sqrt(max(1.0, float(fw * fh)))
    return float(diameter / short_side)


def _visibility_score(render_scale: float) -> float:
    # Faces below ~5% of the short side are intentionally treated as micro.
    # At ~18% there is enough room for several independent identity marks.
    return _clamp01((render_scale - 0.045) / 0.135)


def _visibility_tier(render_scale: float) -> str:
    if render_scale < 0.070:
        return "micro"
    if render_scale < 0.115:
        return "small"
    if render_scale < 0.175:
        return "medium"
    return "large"


def _gray(image_rgb: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image_rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY)


def _local_feature_contrast(
    image_rgb: np.ndarray,
    point: tuple[float, float] | None,
    face_bbox: tuple[int, int, int, int],
    *,
    radius_ratio: float,
) -> float:
    if point is None:
        return 0.0

    gray = _gray(image_rgb)
    h, w = gray.shape[:2]
    fx, fy, fw, fh = face_bbox
    radius = max(1, int(round(min(fw, fh) * radius_ratio)))
    cx = int(round(point[0]))
    cy = int(round(point[1]))

    x0 = max(0, cx - radius)
    x1 = min(w, cx + radius + 1)
    y0 = max(0, cy - radius)
    y1 = min(h, cy + radius + 1)
    patch = gray[y0:y1, x0:x1]
    if patch.size < 3:
        return 0.0

    face_x0 = max(0, fx)
    face_x1 = min(w, fx + fw)
    face_y0 = max(0, fy)
    face_y1 = min(h, fy + fh)
    face_patch = gray[face_y0:face_y1, face_x0:face_x1]
    if face_patch.size < 6:
        return 0.0

    local_mean = float(np.mean(patch))
    local_std = float(np.std(patch))
    face_median = float(np.median(face_patch))
    mean_delta = abs(local_mean - face_median)

    # Anime eyes/mouths are usually identified by a dark/color edge. The local
    # standard deviation catches colored eyes that are not simply darker.
    return _clamp01(mean_delta / 62.0 * 0.58 + local_std / 58.0 * 0.42)


def _feature_salience(
    image_rgb: np.ndarray,
    feature: tuple[float, float, float] | None,
    face_bbox: tuple[int, int, int, int],
    *,
    visibility: float,
    radius_ratio: float,
) -> float:
    if feature is None:
        return 0.0
    confidence = _clamp01(float(feature[2]))
    contrast = _local_feature_contrast(
        image_rgb,
        (float(feature[0]), float(feature[1])),
        face_bbox,
        radius_ratio=radius_ratio,
    )
    # At tiny render sizes even a good detector should not force another Shape.
    size_gate = 0.28 + 0.72 * visibility
    return _clamp01((confidence * 0.62 + contrast * 0.38) * size_gate)


def score_eye_salience(
    image_rgb: np.ndarray,
    face: CharacterPartCandidate,
    layout: FaceFeatureLayout,
    *,
    visibility: float | None = None,
    structure: CharacterStructure | None = None,
) -> tuple[float, float, str, dict]:
    if visibility is None:
        if structure is None:
            visibility = 1.0
        else:
            visibility = _visibility_score(
                estimate_face_render_scale(structure, face, layout)
            )

    bbox = _face_render_bbox(face, layout)
    rows = []
    for side, eye in [
        ("left", layout.left_eye),
        ("right", layout.right_eye),
    ]:
        score = _feature_salience(
            image_rgb,
            eye,
            bbox,
            visibility=visibility,
            radius_ratio=0.085,
        )
        rows.append((side, score, eye))

    rows.sort(key=lambda row: row[1], reverse=True)
    primary_side = rows[0][0] if rows and rows[0][1] > 0.0 else "none"
    primary = rows[0][1] if rows else 0.0
    secondary = rows[1][1] if len(rows) > 1 else 0.0
    return (
        float(primary),
        float(secondary),
        primary_side,
        {
            "left_eye_salience": next(r[1] for r in rows if r[0] == "left"),
            "right_eye_salience": next(r[1] for r in rows if r[0] == "right"),
            "left_eye_detected": layout.left_eye is not None,
            "right_eye_detected": layout.right_eye is not None,
        },
    )


def score_mouth_salience(
    image_rgb: np.ndarray,
    face: CharacterPartCandidate,
    layout: FaceFeatureLayout,
    *,
    visibility: float,
) -> tuple[float, dict]:
    bbox = _face_render_bbox(face, layout)
    base = _feature_salience(
        image_rgb,
        layout.mouth,
        bbox,
        visibility=visibility,
        radius_ratio=0.070,
    )
    if layout.mouth is None:
        return 0.0, {
            "mouth_detected": False,
            "mouth_confidence": 0.0,
            "mouth_contrast": 0.0,
        }

    contrast = _local_feature_contrast(
        image_rgb,
        (layout.mouth[0], layout.mouth[1]),
        bbox,
        radius_ratio=0.070,
    )
    # Mouth is more disposable than an eye in a minimal abstraction. A detected
    # mouth needs stronger evidence before it becomes identity-significant.
    salience = _clamp01(base * 0.88)
    return salience, {
        "mouth_detected": True,
        "mouth_confidence": float(layout.mouth[2]),
        "mouth_contrast": contrast,
    }


def score_fringe_relation(
    structure: CharacterStructure,
    face: CharacterPartCandidate,
) -> tuple[float, dict]:
    hair = structure.first_part(CharacterPartType.HAIR)
    if hair is None:
        return 0.0, {
            "hair_detected": False,
            "boundary_conflict_pixels": 0,
            "near_face_hair_ratio": 0.0,
        }

    face_mask = (face.mask > 0).astype(np.uint8) * 255
    hair_mask = (hair.mask > 0).astype(np.uint8) * 255
    fx, fy, fw, fh = _face_render_bbox(face)
    radius = max(1, int(round(min(fw, fh) * 0.12)))
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (radius * 2 + 1, radius * 2 + 1),
    )
    halo = cv2.dilate(face_mask, kernel)
    near_hair = cv2.bitwise_and(hair_mask, halo)
    face_area = max(1, int(np.count_nonzero(face_mask)))
    near_ratio = int(np.count_nonzero(near_hair)) / face_area

    boundary = face.metadata.get("boundary_guard") or {}
    diag = boundary.get("diagnostics") or {}
    conflict_before = int(diag.get("conflict_pixels_before", 0) or 0)
    conflict_ratio = conflict_before / face_area

    # Side/bang contact can be an identity cue even after the guard has correctly
    # removed illegal overlap. Use pre-guard conflict only as a modest boost.
    score = _clamp01(
        min(1.0, near_ratio / 0.34) * 0.76
        + min(1.0, conflict_ratio / 0.08) * 0.24
    )
    return score, {
        "hair_detected": True,
        "near_face_hair_pixels": int(np.count_nonzero(near_hair)),
        "near_face_hair_ratio": float(near_ratio),
        "boundary_conflict_pixels": conflict_before,
        "boundary_conflict_ratio": float(conflict_ratio),
        "boundary_strategy": boundary.get("strategy", "unknown"),
    }


def score_contour_salience(
    structure: CharacterStructure,
    face: CharacterPartCandidate,
    layout: FaceFeatureLayout | None = None,
) -> tuple[float, dict]:
    bbox = _face_render_bbox(face, layout)
    _, _, fw, fh = bbox
    aspect = fw / max(float(fh), 1.0)
    generic_aspect = 0.82
    aspect_distinctness = _clamp01(abs(math.log(max(aspect, 1e-6) / generic_aspect)) / 0.42)

    head = structure.first_part(CharacterPartType.HEAD)
    face_head_ratio = 0.0
    if head is not None:
        face_head_ratio = face.area / max(float(head.area), 1.0)
    mass_distinctness = _clamp01(abs(face_head_ratio - 0.34) / 0.30)

    contour = face.metadata.get("contour_fit") or {}
    fit_confidence = _clamp01(float(contour.get("confidence", face.confidence) or 0.0))
    score = _clamp01(
        fit_confidence * 0.45
        + aspect_distinctness * 0.32
        + mass_distinctness * 0.23
    )
    return score, {
        "aspect_ratio": float(aspect),
        "aspect_distinctness": aspect_distinctness,
        "face_head_area_ratio": float(face_head_ratio),
        "mass_distinctness": mass_distinctness,
        "contour_fit_confidence": fit_confidence,
    }


def _expression_salience(
    layout: FaceFeatureLayout,
    *,
    primary_eye: float,
    secondary_eye: float,
    mouth: float,
) -> tuple[float, dict]:
    wink = layout.wink_side in {"left", "right"}
    asymmetry = abs(primary_eye - secondary_eye)
    wink_bonus = 0.90 if wink else 0.0
    score = max(
        mouth,
        _clamp01(asymmetry * 1.15),
        wink_bonus,
    )
    return float(score), {
        "wink_side": layout.wink_side,
        "eye_salience_asymmetry": float(asymmetry),
        "wink_bonus": float(wink_bonus),
    }


def analyze_face_identity_signals(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    face: CharacterPartCandidate,
    layout: FaceFeatureLayout,
    *,
    abstraction_level: int = 4,
) -> FaceIdentitySignals:
    render_scale = estimate_face_render_scale(structure, face, layout)
    visibility = _visibility_score(render_scale)
    tier = _visibility_tier(render_scale)

    primary_eye, second_eye, primary_side, eye_diag = score_eye_salience(
        image_rgb,
        face,
        layout,
        visibility=visibility,
        structure=structure,
    )
    mouth, mouth_diag = score_mouth_salience(
        image_rgb,
        face,
        layout,
        visibility=visibility,
    )
    fringe, fringe_diag = score_fringe_relation(structure, face)
    contour, contour_diag = score_contour_salience(structure, face, layout)
    expression, expression_diag = _expression_salience(
        layout,
        primary_eye=primary_eye,
        secondary_eye=second_eye,
        mouth=mouth,
    )

    canvas_area = max(1, int(structure.subject_mask.size))
    face_area_ratio = face.area / float(canvas_area)

    present = [primary_eye, second_eye, mouth, fringe]
    useful = [score for score in present if score >= 0.34]
    # Density describes how many independent cues are worth spending Shape slots
    # on. It is diagnostic in 10.5-a and becomes a budget input in 10.5-b.
    density = _clamp01(len(useful) / 4.0 * 0.72 + np.mean(present) * 0.28)

    return FaceIdentitySignals(
        face_size_score=visibility,
        eye_salience_score=primary_eye,
        second_eye_salience_score=second_eye,
        mouth_salience_score=mouth,
        fringe_relation_score=fringe,
        contour_salience_score=contour,
        expression_salience_score=expression,
        primary_eye_side=primary_side,
        visibility_tier=tier,
        face_render_scale=float(render_scale),
        face_area_ratio=float(face_area_ratio),
        feature_density_score=float(density),
        abstraction_level=int(abstraction_level),
        diagnostics={
            "eye": eye_diag,
            "mouth": mouth_diag,
            "fringe": fringe_diag,
            "contour": contour_diag,
            "expression": expression_diag,
            "useful_signal_count": len(useful),
            "useful_signal_threshold": 0.34,
            "phase": "10.5-a",
            "rendering_changed": False,
        },
    )
