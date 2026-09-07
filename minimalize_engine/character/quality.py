from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

import numpy as np
import cv2

from ..models import Scene, Shape
from .models import CharacterStructure
from .part_types import CharacterPartType
from .heuristics import mask_bbox, mask_centroid
from .face_geometry import evaluate_face_geometry
from .hand_quality import evaluate_hand_quality


@dataclass
class CharacterQualityReport:
    score: float

    face_retention_score: float | None
    face_geometry_score: float | None
    face_boundary_score: float | None
    face_identity_score: float | None
    face_safety_score: float
    body_readability_score: float | None
    limb_separation_score: float | None
    prop_retention_score: float | None
    layout_score: float | None
    geometry_fidelity_score: float | None
    hand_quality_score: float | None

    face_applicable: bool
    face_geometry_applicable: bool
    face_boundary_applicable: bool
    face_identity_applicable: bool
    body_applicable: bool
    limb_separation_applicable: bool
    prop_applicable: bool
    layout_applicable: bool
    geometry_applicable: bool
    hand_applicable: bool

    expected_body_parts: int
    retained_body_parts: int
    expected_props: int
    retained_props: int

    face_shape_count: int
    body_shape_count: int
    prop_shape_count: int
    hand_shape_count: int

    retry_reasons: list[str]
    diagnostics: dict

    def to_dict(self) -> dict:
        return asdict(self)


def _shape_bounds(shape: Shape) -> tuple[float, float, float, float] | None:
    if shape.shape_type == "rectangle":
        if None in {shape.x, shape.y, shape.width, shape.height}:
            return None
        return (
            float(shape.x),
            float(shape.y),
            float(shape.x + shape.width),
            float(shape.y + shape.height),
        )
    if shape.shape_type in {"circle", "ellipse"}:
        if None in {shape.cx, shape.cy, shape.rx, shape.ry}:
            return None
        return (
            float(shape.cx - shape.rx),
            float(shape.cy - shape.ry),
            float(shape.cx + shape.rx),
            float(shape.cy + shape.ry),
        )
    if not shape.points:
        return None
    xs = [p[0] for p in shape.points]
    ys = [p[1] for p in shape.points]
    half = max(0.0, shape.stroke_width * 0.5)
    return (
        float(min(xs) - half),
        float(min(ys) - half),
        float(max(xs) + half),
        float(max(ys) + half),
    )


def _bbox_iou(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[2], b[2])
    y1 = min(a[3], b[3])
    inter = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    aa = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    bb = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = aa + bb - inter
    return 0.0 if union <= 1e-9 else float(inter / union)


def _bbox_center(
    bbox: tuple[float, float, float, float],
) -> tuple[float, float]:
    return (
        (bbox[0] + bbox[2]) / 2.0,
        (bbox[1] + bbox[3]) / 2.0,
    )


def _mean(values: Iterable[float], default: float = 1.0) -> float:
    vals = list(values)
    return float(sum(vals) / len(vals)) if vals else float(default)


def _weighted_mean(items: list[tuple[float, float]]) -> float:
    valid = [(float(score), float(weight)) for score, weight in items if weight > 0]
    if not valid:
        return 1.0
    total = sum(weight for _, weight in valid)
    return float(sum(score * weight for score, weight in valid) / max(total, 1e-9))


def _face_quality(
    scene: Scene,
    structure: CharacterStructure,
) -> tuple[float | None, float, dict]:
    details = scene.metadata.get("character", {}).get("details", {})
    face_details = details.get("face", {})
    validation = (
        structure.metadata.get("face_validation")
        or face_details.get("validation")
        or {}
    )

    accepted = bool(validation.get("accepted", False))
    face_shapes = [
        s for s in scene.shapes
        if s.character_part == "face"
    ]

    # Phase 8.5 contract: a rejected/unknown face must not be redrawn.
    if not accepted:
        safety = 1.0 if len(face_shapes) == 0 else 0.0
        return None, safety, {
            "accepted_source_face": False,
            "generated_face_shapes": len(face_shapes),
            "validation_confidence": float(validation.get("confidence", 0.0)),
            "validation_reasons": list(validation.get("reasons") or []),
            "skipped_from_retention_score": True,
        }

    layout = face_details.get("layout") or {}
    identity_plan = face_details.get("identity_plan") or {}
    identity_rendering = face_details.get("identity_rendering") or {}
    identity_plan_applied = bool(identity_rendering.get("enabled", False))

    if identity_plan_applied and identity_plan:
        expected_eye_count = (
            int(bool(identity_plan.get("include_primary_eye", False)))
            + int(bool(identity_plan.get("include_secondary_eye", False)))
        )
        expected_mouth = bool(identity_plan.get("include_mouth", False))
    else:
        expected_eye_count = int(validation.get("eye_count", 0))
        expected_mouth = validation.get("mouth") is not None

    generated_eye_count = sum(
        1 for s in face_shapes
        if s.source_role == "character_eye"
    )
    generated_mouth = any(
        s.source_role == "character_mouth"
        for s in face_shapes
    )
    base_present = any(
        s.source_role == "character_face_base"
        for s in face_shapes
    )

    base_score = 1.0 if base_present else 0.0

    if expected_eye_count <= 0:
        eye_score = 1.0
    else:
        eye_score = min(1.0, generated_eye_count / expected_eye_count)

    mouth_score = (
        1.0
        if not expected_mouth
        else (1.0 if generated_mouth else 0.0)
    )

    validation_conf = float(validation.get("confidence", 0.0))
    retention = float(np.clip(
        base_score * 0.45
        + eye_score * 0.40
        + mouth_score * 0.10
        + min(1.0, validation_conf) * 0.05,
        0.0,
        1.0,
    ))

    safety = 1.0
    return retention, safety, {
        "accepted_source_face": True,
        "generated_face_shapes": len(face_shapes),
        "base_present": base_present,
        "expected_eye_count": expected_eye_count,
        "generated_eye_count": generated_eye_count,
        "expected_mouth": expected_mouth,
        "generated_mouth": generated_mouth,
        "identity_plan_applied": identity_plan_applied,
        "identity_minimality_level": identity_plan.get("minimality_level") if identity_plan_applied else None,
        "identity_target_shape_count": identity_plan.get("target_shape_count") if identity_plan_applied else None,
        "validation_confidence": validation_conf,
        "layout_confidence": float(layout.get("confidence", 0.0)) if layout else 0.0,
        "skipped_from_retention_score": False,
    }


def _body_readability(
    scene: Scene,
    structure: CharacterStructure,
) -> tuple[float, int, int, dict]:
    body_types = [
        CharacterPartType.TORSO,
        CharacterPartType.LEFT_ARM,
        CharacterPartType.RIGHT_ARM,
        CharacterPartType.LEFT_LEG,
        CharacterPartType.RIGHT_LEG,
    ]
    expected = [
        t for t in body_types
        if structure.first_part(t) is not None
    ]

    retained = 0
    per_part = {}
    for part_type in expected:
        key = str(part_type)
        shapes = [
            s for s in scene.shapes
            if s.character_part == key
            and s.layer_name == "character_body_base"
        ]
        present = len(shapes) > 0
        if present:
            retained += 1

        # Dedicated body primitives should be readable big Shapes, not lines.
        readable_shapes = [
            s for s in shapes
            if s.shape_type in {"polygon", "rectangle", "ellipse", "circle"}
        ]
        confidence = max(
            [float(s.part_confidence) for s in readable_shapes] + [0.0]
        )
        per_part[key] = {
            "present": present,
            "shape_count": len(shapes),
            "readable_shape_count": len(readable_shapes),
            "max_confidence": confidence,
        }

    if not expected:
        return 1.0, 0, 0, {"per_part": per_part}

    presence_score = retained / len(expected)
    confidence_score = _mean(
        [
            min(
                1.0,
                per_part[str(t)]["max_confidence"] / 0.60
            )
            for t in expected
            if per_part[str(t)]["present"]
        ],
        default=0.0,
    )
    score = float(np.clip(
        presence_score * 0.82 + confidence_score * 0.18,
        0.0,
        1.0,
    ))
    return score, len(expected), retained, {
        "per_part": per_part,
        "presence_score": presence_score,
        "confidence_score": confidence_score,
    }


def _limb_separation(
    scene: Scene,
    structure: CharacterStructure,
) -> tuple[float | None, dict]:
    pairs = [
        (CharacterPartType.LEFT_ARM, CharacterPartType.RIGHT_ARM, "arms"),
        (CharacterPartType.LEFT_LEG, CharacterPartType.RIGHT_LEG, "legs"),
    ]
    pair_scores = []
    diagnostics = {}

    for left_t, right_t, label in pairs:
        left_expected = structure.first_part(left_t) is not None
        right_expected = structure.first_part(right_t) is not None
        if not (left_expected and right_expected):
            diagnostics[label] = {
                "applicable": False,
                "reason": "both source limbs were not detected",
            }
            continue

        left_shapes = [
            s for s in scene.shapes
            if s.character_part == str(left_t)
            and s.layer_name == "character_body_base"
        ]
        right_shapes = [
            s for s in scene.shapes
            if s.character_part == str(right_t)
            and s.layer_name == "character_body_base"
        ]

        if not left_shapes or not right_shapes:
            pair_scores.append(0.0)
            diagnostics[label] = {
                "applicable": True,
                "score": 0.0,
                "reason": "one or both dedicated limb Shapes missing",
            }
            continue

        lb = _shape_bounds(left_shapes[0])
        rb = _shape_bounds(right_shapes[0])
        if lb is None or rb is None:
            pair_scores.append(0.0)
            diagnostics[label] = {
                "applicable": True,
                "score": 0.0,
                "reason": "limb bounds unavailable",
            }
            continue

        iou = _bbox_iou(lb, rb)
        lc = _bbox_center(lb)
        rc = _bbox_center(rb)
        # Crossing poses are legitimate, so side order is only a soft bonus.
        order_score = 1.0 if lc[0] <= rc[0] else 0.72
        overlap_score = float(np.clip(1.0 - iou / 0.46, 0.0, 1.0))
        score = float(np.clip(
            overlap_score * 0.82 + order_score * 0.18,
            0.0,
            1.0,
        ))
        pair_scores.append(score)
        diagnostics[label] = {
            "applicable": True,
            "score": score,
            "bbox_iou": iou,
            "left_center": list(lc),
            "right_center": list(rc),
            "order_score": order_score,
        }

    if not pair_scores:
        return None, diagnostics
    return _mean(pair_scores, default=0.0), diagnostics


def _prop_retention(
    scene: Scene,
    structure: CharacterStructure,
) -> tuple[float | None, int, int, dict]:
    descriptors = list(
        structure.metadata.get("prop_descriptors")
        or scene.metadata.get("character", {})
            .get("details", {})
            .get("props", {})
            .get("descriptors", [])
        or []
    )
    if not descriptors:
        return None, 0, 0, {
            "applicable": False,
            "descriptors": [],
        }

    prop_shapes = [
        s for s in scene.shapes
        if s.character_part == "prop"
    ]
    roles = {s.source_role for s in prop_shapes}

    role_expectations = {
        "staff_like": {"character_staff", "character_staff_head"},
        "sword_like": {"character_sword_blade", "character_sword_guard"},
        "microphone_like": {"character_microphone_body", "character_microphone_head"},
        "headphone_like": {"character_headphone_cup", "character_headphone_band"},
        "hat_like": {"character_hat", "character_hat_brim"},
        "bag_like": {"character_bag", "character_bag_handle"},
        "unknown": {"character_prop", "character_handheld_prop"},
    }

    retained = 0
    rows = []
    for descriptor in descriptors:
        ptype = descriptor.get("prop_type", "unknown")
        expected_roles = role_expectations.get(ptype, role_expectations["unknown"])
        present_roles = sorted(roles & expected_roles)
        present = len(present_roles) > 0
        if present:
            retained += 1
        rows.append({
            "prop_type": ptype,
            "confidence": float(descriptor.get("confidence", 0.0)),
            "expected_roles": sorted(expected_roles),
            "present_roles": present_roles,
            "retained": present,
        })

    score = retained / max(1, len(descriptors))
    return float(score), len(descriptors), retained, {
        "applicable": True,
        "descriptors": rows,
        "generated_prop_shapes": len(prop_shapes),
    }


def _shape_to_mask(scene: Scene, shape: Shape) -> np.ndarray:
    mask = np.zeros((scene.height, scene.width), dtype=np.uint8)
    if shape.shape_type == "polygon" and len(shape.points) >= 3:
        pts = np.asarray(shape.points, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
    elif shape.shape_type == "rectangle" and None not in {shape.x, shape.y, shape.width, shape.height}:
        x0 = int(round(shape.x))
        y0 = int(round(shape.y))
        x1 = int(round(shape.x + shape.width))
        y1 = int(round(shape.y + shape.height))
        cv2.rectangle(mask, (x0, y0), (x1, y1), 255, thickness=-1)
    elif shape.shape_type == "circle" and None not in {shape.cx, shape.cy, shape.rx}:
        cv2.circle(mask, (int(round(shape.cx)), int(round(shape.cy))), int(round(shape.rx)), 255, thickness=-1)
    elif shape.shape_type == "ellipse" and None not in {shape.cx, shape.cy, shape.rx, shape.ry}:
        cv2.ellipse(mask, (int(round(shape.cx)), int(round(shape.cy))), (int(round(shape.rx)), int(round(shape.ry))), 0.0, 0.0, 360.0, 255, thickness=-1)
    elif shape.shape_type == "line" and len(shape.points) >= 2:
        pts = np.asarray(shape.points, dtype=np.int32)
        width = max(1, int(round(shape.stroke_width or 1.0)))
        cv2.polylines(mask, [pts], False, 255, thickness=width)
    return mask


def _shape_union_mask(scene: Scene, shapes: list[Shape]) -> np.ndarray:
    union = np.zeros((scene.height, scene.width), dtype=np.uint8)
    for shape in shapes:
        union = cv2.bitwise_or(union, _shape_to_mask(scene, shape))
    return union


def _geometry_component_score(
    source_mask: np.ndarray,
    generated_mask: np.ndarray,
) -> dict:
    source = (source_mask > 0).astype(np.uint8)
    generated = (generated_mask > 0).astype(np.uint8)
    if np.count_nonzero(source) == 0 or np.count_nonzero(generated) == 0:
        return {
            "score": 0.0,
            "mask_iou": 0.0,
            "bbox_iou": 0.0,
            "center_score": 0.0,
            "area_score": 0.0,
            "source_area": int(np.count_nonzero(source)),
            "generated_area": int(np.count_nonzero(generated)),
        }

    inter = int(np.count_nonzero((source > 0) & (generated > 0)))
    union = int(np.count_nonzero((source > 0) | (generated > 0)))
    mask_iou = inter / max(union, 1)

    sb = mask_bbox(source * 255)
    gb = mask_bbox(generated * 255)
    bbox_iou = _bbox_iou(
        (sb[0], sb[1], sb[0] + sb[2], sb[1] + sb[3]),
        (gb[0], gb[1], gb[0] + gb[2], gb[1] + gb[3]),
    )
    sc = mask_centroid(source * 255)
    gc = mask_centroid(generated * 255)
    dx = sc[0] - gc[0]
    dy = sc[1] - gc[1]
    diag = max(1.0, np.hypot(sb[2], sb[3]))
    center_score = float(np.clip(1.0 - np.hypot(dx, dy) / (diag * 0.42), 0.0, 1.0))
    source_area = int(np.count_nonzero(source))
    generated_area = int(np.count_nonzero(generated))
    area_ratio = generated_area / max(source_area, 1)
    area_score = float(np.clip(1.0 - abs(np.log(max(area_ratio, 1e-6))) / np.log(2.4), 0.0, 1.0))
    score = float(np.clip(mask_iou * 0.46 + bbox_iou * 0.22 + center_score * 0.18 + area_score * 0.14, 0.0, 1.0))
    return {
        "score": score,
        "mask_iou": float(mask_iou),
        "bbox_iou": float(bbox_iou),
        "center_score": center_score,
        "area_score": area_score,
        "source_area": source_area,
        "generated_area": generated_area,
        "source_bbox": list(sb),
        "generated_bbox": list(gb),
        "source_center": [float(sc[0]), float(sc[1])],
        "generated_center": [float(gc[0]), float(gc[1])],
    }


def _part_geometry_shapes(scene: Scene, part_key: str) -> list[Shape]:
    if part_key == "face":
        base = [s for s in scene.shapes if s.character_part == "face" and s.source_role == "character_face_base"]
        return base or [s for s in scene.shapes if s.character_part == "face"]
    if part_key == "hair":
        base = [s for s in scene.shapes if s.character_part == "hair" and s.source_role == "character_hair_base"]
        return base or [s for s in scene.shapes if s.character_part == "hair"]
    return [
        s for s in scene.shapes
        if s.character_part == part_key and s.layer_name == "character_body_base"
    ]


def _geometry_fidelity(
    scene: Scene,
    structure: CharacterStructure,
) -> tuple[float | None, dict]:
    plan = [
        (CharacterPartType.FACE, 1.30),
        (CharacterPartType.HAIR, 1.05),
        (CharacterPartType.TORSO, 1.00),
        (CharacterPartType.LEFT_ARM, 0.92),
        (CharacterPartType.RIGHT_ARM, 0.92),
        (CharacterPartType.LEFT_LEG, 0.96),
        (CharacterPartType.RIGHT_LEG, 0.96),
    ]
    items: list[tuple[float, float]] = []
    details = {}
    for part_type, weight in plan:
        part = structure.first_part(part_type)
        if part is None:
            details[str(part_type)] = {"applicable": False, "reason": "source part missing"}
            continue
        shapes = _part_geometry_shapes(scene, str(part_type))
        if not shapes:
            items.append((0.0, weight))
            details[str(part_type)] = {"applicable": True, "score": 0.0, "reason": "generated shapes missing"}
            continue
        union = _shape_union_mask(scene, shapes)
        metrics = _geometry_component_score(part.mask, union)
        items.append((float(metrics["score"]), weight))
        details[str(part_type)] = {"applicable": True, **metrics, "shape_count": len(shapes)}

    if not items:
        return None, {"applicable": False, "parts": details}
    return _weighted_mean(items), {
        "applicable": True,
        "parts": details,
        "part_count": len(items),
    }


def _layout_quality(scene: Scene) -> tuple[float, dict]:
    layout = (
        scene.metadata.get("character", {})
        .get("layout", {})
    )
    if not layout.get("enabled", False):
        return 0.72, {
            "enabled": False,
            "score_is_fallback": True,
        }

    metrics = layout.get("metrics") or {}
    center_error = float(metrics.get("center_error", 0.0))
    top_error = float(metrics.get("top_error", 0.0))
    bottom_error = float(metrics.get("bottom_error", 0.0))
    clipped = bool(metrics.get("clipped", False))
    left_margin = float(metrics.get("left_margin_ratio", 0.0))
    right_margin = float(metrics.get("right_margin_ratio", 0.0))

    center_score = float(np.clip(1.0 - center_error / 0.055, 0.0, 1.0))
    top_score = float(np.clip(1.0 - top_error / 0.035, 0.0, 1.0))
    bottom_score = float(np.clip(1.0 - bottom_error / 0.035, 0.0, 1.0))

    min_margin = min(left_margin, right_margin)
    margin_score = float(np.clip(min_margin / 0.028, 0.0, 1.0))

    score = (
        center_score * 0.34
        + top_score * 0.24
        + bottom_score * 0.24
        + margin_score * 0.18
    )
    if clipped:
        score *= 0.20

    return float(np.clip(score, 0.0, 1.0)), {
        "enabled": True,
        "center_score": center_score,
        "top_score": top_score,
        "bottom_score": bottom_score,
        "margin_score": margin_score,
        "clipped": clipped,
        "center_error": center_error,
        "top_error": top_error,
        "bottom_error": bottom_error,
        "left_margin_ratio": left_margin,
        "right_margin_ratio": right_margin,
    }


def _face_boundary_quality(
    structure: CharacterStructure,
    *,
    enabled: bool,
) -> tuple[float | None, dict]:
    metadata = structure.metadata.get("face_boundary") or {}
    if not enabled:
        return None, {
            "applicable": False,
            "disabled_by_config": True,
            "reason": "face boundary guard disabled",
        }
    if not metadata.get("enabled", False):
        return None, {
            "applicable": False,
            "disabled_by_config": False,
            "reason": "validated face/hair boundary unavailable",
            **metadata,
        }
    raw = metadata.get("boundary_score_hint")
    if raw is None:
        return None, {
            "applicable": False,
            "reason": "boundary score unavailable",
            **metadata,
        }
    score = float(np.clip(raw, 0.0, 1.0))
    return score, {
        "applicable": True,
        **metadata,
    }


def evaluate_character_scene(
    scene: Scene,
    structure: CharacterStructure,
    *,
    enable_body_primitives: bool = True,
    enable_face_rules: bool = True,
    enable_face_geometry_quality: bool = True,
    enable_face_boundary_guard: bool = True,
    enable_prop_rules: bool = True,
    enable_hand_quality: bool = True,
    enable_character_layout: bool = True,
    min_score: float = 0.76,
    min_face_retention: float = 0.72,
    min_face_geometry: float = 0.72,
    min_face_boundary: float = 0.72,
    min_face_identity: float = 0.72,
    face_geometry_area_ratio_tolerance: float = 0.30,
    face_geometry_center_tolerance: float = 0.18,
    face_geometry_aspect_tolerance: float = 0.28,
    face_geometry_eye_span_tolerance: float = 0.30,
    face_geometry_mouth_offset_tolerance: float = 0.26,
    canvas_padding: float = 0.05,
    min_body_readability: float = 0.80,
    min_limb_separation: float = 0.62,
    min_prop_retention: float = 0.72,
    min_hand_score: float = 0.72,
    min_hand_retention: float = 0.72,
    min_hand_geometry: float = 0.72,
    min_hand_holding_contact: float = 0.45,
    min_layout_score: float = 0.72,
    min_geometry_fidelity: float = 0.40,
) -> CharacterQualityReport:
    face_score, face_safety, face_diag = _face_quality(scene, structure)
    if not enable_face_rules:
        face_score = None
        face_diag = {**face_diag, "disabled_by_config": True}

    face_geometry_metrics = None
    if enable_face_rules and enable_face_geometry_quality:
        face_geometry_metrics = evaluate_face_geometry(
            scene,
            structure,
            min_score=min_face_geometry,
            area_ratio_tolerance=face_geometry_area_ratio_tolerance,
            center_tolerance=face_geometry_center_tolerance,
            aspect_tolerance=face_geometry_aspect_tolerance,
            eye_span_tolerance=face_geometry_eye_span_tolerance,
            mouth_offset_tolerance=face_geometry_mouth_offset_tolerance,
            canvas_padding=canvas_padding,
        )
    face_geometry_score = (
        face_geometry_metrics.score
        if face_geometry_metrics is not None
        else None
    )
    face_geometry_diag = (
        face_geometry_metrics.to_dict()
        if face_geometry_metrics is not None
        else {
            "applicable": False,
            "disabled_by_config": not enable_face_geometry_quality,
            "reason": (
                "face geometry quality disabled"
                if not enable_face_geometry_quality
                else "validated source face unavailable"
            ),
        }
    )

    face_boundary_score, face_boundary_diag = _face_boundary_quality(
        structure,
        enabled=enable_face_boundary_guard,
    )

    face_details = scene.metadata.get("character", {}).get("details", {}).get("face", {})
    face_identity_diag = face_details.get("identity_validation")
    face_identity_score = (
        float(face_identity_diag.get("score"))
        if isinstance(face_identity_diag, dict) and face_identity_diag.get("score") is not None
        else None
    )

    raw_body_score, expected_body, retained_body, body_diag = _body_readability(
        scene,
        structure,
    )
    body_score = raw_body_score if enable_body_primitives else None
    if not enable_body_primitives:
        body_diag = {**body_diag, "disabled_by_config": True}

    limb_score, limb_diag = _limb_separation(scene, structure)
    if not enable_body_primitives:
        limb_score = None
        limb_diag = {**limb_diag, "disabled_by_config": True}

    prop_score, expected_props, retained_props, prop_diag = _prop_retention(
        scene,
        structure,
    )
    if not enable_prop_rules:
        prop_score = None
        prop_diag = {**prop_diag, "disabled_by_config": True}

    hand_report = evaluate_hand_quality(
        scene,
        min_score=min_hand_score,
        min_retention=min_hand_retention,
        min_geometry=min_hand_geometry,
        min_holding_contact=min_hand_holding_contact,
    )
    hand_score = hand_report.score if (enable_hand_quality and hand_report.applicable) else None
    hand_diag = hand_report.to_dict()
    if not enable_hand_quality:
        hand_diag = {**hand_diag, "disabled_by_config": True}

    raw_layout_score, layout_diag = _layout_quality(scene)
    layout_score = raw_layout_score if enable_character_layout else None
    if not enable_character_layout:
        layout_diag = {**layout_diag, "disabled_by_config": True}

    geometry_score, geometry_diag = _geometry_fidelity(scene, structure)

    weighted: list[tuple[float, float]] = [
        (face_safety, 0.07),
    ]
    if body_score is not None:
        weighted.append((body_score, 0.20))
    if layout_score is not None:
        weighted.append((layout_score, 0.16))
    if face_score is not None:
        weighted.append((face_score, 0.16))
    if face_geometry_score is not None:
        weighted.append((face_geometry_score, 0.15))
    if face_boundary_score is not None:
        weighted.append((face_boundary_score, 0.06))
    if face_identity_score is not None:
        weighted.append((face_identity_score, 0.08))
    if limb_score is not None:
        weighted.append((limb_score, 0.10))
    if prop_score is not None:
        weighted.append((prop_score, 0.07))
    if hand_score is not None:
        weighted.append((hand_score, 0.08))
    if geometry_score is not None:
        weighted.append((geometry_score, 0.09))

    score = _weighted_mean(weighted)

    reasons = []
    if face_safety < 0.99:
        reasons.append("false_face_generated")
    if face_score is not None and face_score < min_face_retention:
        reasons.append("face_retention_low")
    if (
        face_geometry_score is not None
        and face_geometry_score < min_face_geometry
    ):
        reasons.append("face_geometry_low")
    if (
        face_boundary_score is not None
        and face_boundary_score < min_face_boundary
    ):
        reasons.append("face_boundary_low")
    if (
        face_identity_score is not None
        and face_identity_score < min_face_identity
    ):
        reasons.append("face_identity_loss_low")
    if body_score is not None and body_score < min_body_readability:
        reasons.append("body_readability_low")
    if limb_score is not None and limb_score < min_limb_separation:
        reasons.append("limb_separation_low")
    if prop_score is not None and prop_score < min_prop_retention:
        reasons.append("prop_retention_low")
    if hand_score is not None:
        reasons.extend([r for r in hand_report.retry_reasons if r not in reasons])
    if layout_score is not None and layout_score < min_layout_score:
        reasons.append("layout_low")
    if geometry_score is not None and geometry_score < min_geometry_fidelity:
        reasons.append("geometry_fidelity_low")
    if score < min_score:
        reasons.append("character_quality_low")

    face_shape_count = sum(
        1 for s in scene.shapes
        if s.character_part == "face"
    )
    body_shape_count = sum(
        1 for s in scene.shapes
        if s.layer_name == "character_body_base"
    )
    prop_shape_count = sum(
        1 for s in scene.shapes
        if s.character_part == "prop"
    )
    hand_shape_count = sum(
        1 for s in scene.shapes
        if s.character_part == "hand" or s.semantic_type.startswith("character_hand_")
    )

    return CharacterQualityReport(
        score=float(np.clip(score, 0.0, 1.0)),
        face_retention_score=face_score,
        face_geometry_score=face_geometry_score,
        face_boundary_score=face_boundary_score,
        face_identity_score=face_identity_score,
        face_safety_score=face_safety,
        body_readability_score=body_score,
        limb_separation_score=limb_score,
        prop_retention_score=prop_score,
        layout_score=layout_score,
        geometry_fidelity_score=geometry_score,
        hand_quality_score=hand_score,
        face_applicable=face_score is not None,
        face_geometry_applicable=face_geometry_score is not None,
        face_boundary_applicable=face_boundary_score is not None,
        face_identity_applicable=face_identity_score is not None,
        body_applicable=body_score is not None,
        limb_separation_applicable=limb_score is not None,
        prop_applicable=prop_score is not None,
        layout_applicable=layout_score is not None,
        geometry_applicable=geometry_score is not None,
        hand_applicable=hand_score is not None,
        expected_body_parts=expected_body,
        retained_body_parts=retained_body,
        expected_props=expected_props,
        retained_props=retained_props,
        face_shape_count=face_shape_count,
        body_shape_count=body_shape_count,
        prop_shape_count=prop_shape_count,
        hand_shape_count=hand_shape_count,
        retry_reasons=reasons,
        diagnostics={
            "face": face_diag,
            "face_geometry": face_geometry_diag,
            "face_boundary": face_boundary_diag,
            "face_identity": face_identity_diag or {"applicable": False},
            "body": body_diag,
            "limbs": limb_diag,
            "props": prop_diag,
            "hands": hand_diag,
            "layout": layout_diag,
            "thresholds": {
                "score": min_score,
                "face_retention": min_face_retention,
                "face_geometry": min_face_geometry,
                "face_boundary": min_face_boundary,
                "face_identity": min_face_identity,
                "body_readability": min_body_readability,
                "limb_separation": min_limb_separation,
                "prop_retention": min_prop_retention,
                "hand_quality": min_hand_score,
                "hand_retention": min_hand_retention,
                "hand_geometry": min_hand_geometry,
                "layout": min_layout_score,
                "geometry_fidelity": min_geometry_fidelity,
            },
            "geometry": geometry_diag,
        },
    )


def character_retry_needed(
    report: CharacterQualityReport | dict,
) -> bool:
    if isinstance(report, CharacterQualityReport):
        reasons = report.retry_reasons
    else:
        reasons = list(report.get("retry_reasons") or [])
    return len(reasons) > 0


def character_selection_score(
    character_quality: CharacterQualityReport | dict | None,
    generic_quality: dict | None,
) -> float:
    generic = float((generic_quality or {}).get("score", 0.0))
    if character_quality is None:
        return generic
    if isinstance(character_quality, CharacterQualityReport):
        char = character_quality.score
        face_safety = character_quality.face_safety_score
    else:
        char = float(character_quality.get("score", 0.0))
        face_safety = float(character_quality.get("face_safety_score", 1.0))

    retry_reasons = []
    if isinstance(character_quality, CharacterQualityReport):
        retry_reasons = list(character_quality.retry_reasons)
    else:
        retry_reasons = list(character_quality.get("retry_reasons") or [])

    # A false face is a hard semantic failure and must never win merely because
    # generic edge similarity looks good. Also slightly prefer candidates that
    # resolve more character-specific retry reasons.
    safety_penalty = 0.25 if face_safety < 0.99 else 0.0
    reason_penalty = 0.04 * len(retry_reasons)
    return float(np.clip(char * 0.84 + generic * 0.16 - safety_penalty - reason_penalty, 0.0, 1.0))
