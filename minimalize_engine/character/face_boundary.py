from __future__ import annotations

from dataclasses import asdict, dataclass, field

import cv2
import numpy as np

from .heuristics import mask_bbox


@dataclass(slots=True)
class FaceBoundaryGuardResult:
    face_mask: np.ndarray
    hair_mask: np.ndarray
    face_protect_mask: np.ndarray
    hair_restrict_mask: np.ndarray
    conflict_mask_before: np.ndarray
    conflict_mask_after: np.ndarray
    boundary_score_hint: float
    strategy: str
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self, *, include_masks: bool = False) -> dict:
        data = {
            "boundary_score_hint": self.boundary_score_hint,
            "strategy": self.strategy,
            "diagnostics": self.diagnostics,
            "enabled": True,
        }
        if include_masks:
            data.update(
                {
                    "face_mask": self.face_mask,
                    "hair_mask": self.hair_mask,
                    "face_protect_mask": self.face_protect_mask,
                    "hair_restrict_mask": self.hair_restrict_mask,
                    "conflict_mask_before": self.conflict_mask_before,
                    "conflict_mask_after": self.conflict_mask_after,
                }
            )
        return data


def _clamp01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _ellipse_kernel(radius: int) -> np.ndarray:
    radius = max(1, int(radius))
    size = radius * 2 + 1
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))


def _validation_point(
    validation: dict | None,
    key: str,
) -> tuple[float, float] | None:
    raw = (validation or {}).get(key)
    if raw is None:
        return None
    return float(raw[0]), float(raw[1])


def _zone_rect(
    shape: tuple[int, int],
    x0: int,
    y0: int,
    x1: int,
    y1: int,
) -> np.ndarray:
    h, w = shape[:2]
    x0 = max(0, min(w, x0))
    x1 = max(0, min(w, x1))
    y0 = max(0, min(h, y0))
    y1 = max(0, min(h, y1))
    out = np.zeros((h, w), dtype=np.uint8)
    if x1 > x0 and y1 > y0:
        out[y0:y1, x0:x1] = 255
    return out


def build_face_protect_mask(
    face_mask: np.ndarray,
    validation: dict | None = None,
    *,
    eye_protect_strength: float = 0.80,
    cheek_protect_strength: float = 0.72,
    chin_protect_strength: float = 0.85,
    forehead_allowance: float = 0.18,
) -> np.ndarray:
    """
    Build a thin protection halo around the readable part of the face.

    The upper forehead is deliberately less protected because bangs legitimately
    overlap it. Eyes, cheeks and chin are protected more aggressively.
    """
    face = (face_mask > 0).astype(np.uint8) * 255
    if np.count_nonzero(face) == 0:
        return face

    x, y, w, h = mask_bbox(face)
    base_radius = max(1, int(round(min(w, h) * 0.055)))
    halo = cv2.dilate(face, _ellipse_kernel(base_radius))

    protect = np.zeros_like(face)
    forehead_cut = y + int(round(h * np.clip(forehead_allowance, 0.08, 0.34)))

    # General lower-face protection.
    lower_zone = _zone_rect(face.shape, x - base_radius, forehead_cut, x + w + base_radius, y + h + base_radius)
    protect = cv2.bitwise_or(protect, cv2.bitwise_and(halo, lower_zone))

    def add_anchor(point: tuple[float, float] | None, strength: float, radius_scale: float) -> None:
        nonlocal protect
        if point is None:
            return
        strength = _clamp01(strength)
        radius = max(2, int(round(min(w, h) * radius_scale * (0.70 + 0.55 * strength))))
        anchor = np.zeros_like(face)
        cv2.circle(
            anchor,
            (int(round(point[0])), int(round(point[1]))),
            radius,
            255,
            thickness=-1,
        )
        protect = cv2.bitwise_or(protect, anchor)

    left_eye = _validation_point(validation, "left_eye")
    right_eye = _validation_point(validation, "right_eye")
    mouth = _validation_point(validation, "mouth")

    add_anchor(left_eye, eye_protect_strength, 0.15)
    add_anchor(right_eye, eye_protect_strength, 0.15)
    add_anchor(mouth, cheek_protect_strength, 0.13)

    # Cheek band protects the central face even if individual anchors are weak.
    cheek_top = y + int(round(h * 0.34))
    cheek_bottom = y + int(round(h * 0.80))
    cheek_zone = _zone_rect(
        face.shape,
        x - int(round(w * 0.08)),
        cheek_top,
        x + w + int(round(w * 0.08)),
        cheek_bottom,
    )
    cheek_halo = cv2.dilate(face, _ellipse_kernel(max(1, int(round(base_radius * (0.65 + cheek_protect_strength))))))
    protect = cv2.bitwise_or(protect, cv2.bitwise_and(cheek_halo, cheek_zone))

    # Chin gets a stronger lower halo so long side hair cannot cut into it.
    chin_top = y + int(round(h * 0.68))
    chin_zone = _zone_rect(
        face.shape,
        x - int(round(w * 0.06)),
        chin_top,
        x + w + int(round(w * 0.06)),
        y + h + base_radius * 2,
    )
    chin_halo = cv2.dilate(face, _ellipse_kernel(max(1, int(round(base_radius * (0.75 + chin_protect_strength))))))
    protect = cv2.bitwise_or(protect, cv2.bitwise_and(chin_halo, chin_zone))

    return protect


def build_hair_restrict_mask(
    head_mask: np.ndarray,
    face_mask: np.ndarray,
    *,
    face_protect_mask: np.ndarray | None = None,
    forehead_allowance: float = 0.18,
) -> np.ndarray:
    face = (face_mask > 0).astype(np.uint8) * 255
    if np.count_nonzero(face) == 0:
        return np.zeros_like(face)

    x, y, w, h = mask_bbox(face)
    protect = (
        (face_protect_mask > 0).astype(np.uint8) * 255
        if face_protect_mask is not None
        else cv2.dilate(face, _ellipse_kernel(max(1, int(round(min(w, h) * 0.055)))))
    )

    # Bangs may enter the top forehead zone. Keep that area unrestricted while
    # preserving a strong guard around eyes, cheeks and chin.
    allow_bottom = y + int(round(h * np.clip(forehead_allowance + 0.10, 0.18, 0.42)))
    forehead_allow = _zone_rect(
        face.shape,
        x - int(round(w * 0.18)),
        max(0, y - int(round(h * 0.25))),
        x + w + int(round(w * 0.18)),
        allow_bottom,
    )
    restrict = cv2.bitwise_and(protect, cv2.bitwise_not(forehead_allow))

    # Keep restriction local to the head/face vicinity. Long hair farther down
    # remains legal as long as it does not enter the protected face halo.
    head_or_face = cv2.bitwise_or(
        cv2.dilate((head_mask > 0).astype(np.uint8) * 255, _ellipse_kernel(max(1, int(round(min(w, h) * 0.10))))),
        cv2.dilate(face, _ellipse_kernel(max(1, int(round(min(w, h) * 0.12))))),
    )
    return cv2.bitwise_and(restrict, head_or_face)


def detect_boundary_conflict_band(
    face_mask: np.ndarray,
    hair_mask: np.ndarray,
    *,
    restrict_mask: np.ndarray | None = None,
) -> np.ndarray:
    hair = (hair_mask > 0).astype(np.uint8) * 255
    if restrict_mask is not None:
        return cv2.bitwise_and(hair, (restrict_mask > 0).astype(np.uint8) * 255)

    face = (face_mask > 0).astype(np.uint8) * 255
    if np.count_nonzero(face) == 0:
        return np.zeros_like(face)
    x, y, w, h = mask_bbox(face)
    halo = cv2.dilate(face, _ellipse_kernel(max(1, int(round(min(w, h) * 0.06)))))
    return cv2.bitwise_and(hair, halo)


def separate_face_and_hair_by_priority(
    face_mask: np.ndarray,
    hair_mask: np.ndarray,
    face_protect_mask: np.ndarray,
    hair_restrict_mask: np.ndarray,
    *,
    guard_strength: float = 0.65,
) -> tuple[np.ndarray, np.ndarray]:
    face = (face_mask > 0).astype(np.uint8) * 255
    hair = (hair_mask > 0).astype(np.uint8) * 255
    strength = _clamp01(guard_strength)

    conflict = cv2.bitwise_and(hair, hair_restrict_mask)
    if np.count_nonzero(conflict) == 0:
        return face, hair

    # Stronger settings remove the whole conflict band. Softer settings retain
    # the outer edge, which helps preserve intentional side-hair contact.
    if strength >= 0.58:
        removal = conflict
    else:
        erode_radius = 1 if strength >= 0.35 else 2
        core = cv2.erode(conflict, _ellipse_kernel(erode_radius))
        removal = core

    guarded_hair = cv2.bitwise_and(hair, cv2.bitwise_not(removal))

    # Face itself is intentionally not expanded. Phase 10.2 already fitted the
    # face contour; this phase only prevents hair from erasing its readable edge.
    guarded_face = face.copy()
    return guarded_face, guarded_hair


def compute_face_boundary_score_hint(
    original_face_mask: np.ndarray,
    guarded_face_mask: np.ndarray,
    original_hair_mask: np.ndarray,
    guarded_hair_mask: np.ndarray,
    *,
    restrict_mask: np.ndarray,
    skin_mask: np.ndarray | None = None,
) -> float:
    restrict_area = max(1, int(np.count_nonzero(restrict_mask)))
    conflict_before = int(np.count_nonzero((original_hair_mask > 0) & (restrict_mask > 0)))
    conflict_after = int(np.count_nonzero((guarded_hair_mask > 0) & (restrict_mask > 0)))

    before_ratio = conflict_before / restrict_area
    after_ratio = conflict_after / restrict_area
    conflict_score = _clamp01(1.0 - after_ratio / 0.20)

    original_hair_area = max(1, int(np.count_nonzero(original_hair_mask)))
    removed_ratio = max(
        0.0,
        (np.count_nonzero(original_hair_mask) - np.count_nonzero(guarded_hair_mask))
        / original_hair_area,
    )
    edit_score = _clamp01(1.0 - removed_ratio / 0.18)

    face_retention = (
        np.count_nonzero((guarded_face_mask > 0) & (original_face_mask > 0))
        / max(1, np.count_nonzero(original_face_mask))
    )

    skin_score = 1.0
    if skin_mask is not None and np.count_nonzero(guarded_face_mask) > 0:
        skin_score = _clamp01(
            np.count_nonzero((guarded_face_mask > 0) & (skin_mask > 0))
            / max(1, np.count_nonzero(guarded_face_mask))
            / 0.72
        )

    # A large pre-conflict is useful diagnostic evidence even when the guard
    # fixes it. Penalize it lightly, not as strongly as residual conflict.
    pre_conflict_penalty = min(0.12, before_ratio * 0.30)
    score = (
        conflict_score * 0.45
        + edit_score * 0.20
        + float(face_retention) * 0.20
        + skin_score * 0.15
        - pre_conflict_penalty
    )
    return _clamp01(score)


def apply_face_boundary_guard(
    image_rgb: np.ndarray | None,
    *,
    face_mask: np.ndarray,
    hair_mask: np.ndarray,
    head_mask: np.ndarray,
    subject_mask: np.ndarray,
    skin_mask: np.ndarray | None = None,
    validation: dict | None = None,
    guard_strength: float = 0.65,
    eye_protect_strength: float = 0.80,
    cheek_protect_strength: float = 0.72,
    chin_protect_strength: float = 0.85,
    forehead_allowance: float = 0.18,
) -> FaceBoundaryGuardResult:
    face = (face_mask > 0).astype(np.uint8) * 255
    hair = (hair_mask > 0).astype(np.uint8) * 255

    if np.count_nonzero(face) == 0 or np.count_nonzero(hair) == 0:
        empty = np.zeros_like(face)
        return FaceBoundaryGuardResult(
            face_mask=face,
            hair_mask=hair,
            face_protect_mask=empty,
            hair_restrict_mask=empty,
            conflict_mask_before=empty,
            conflict_mask_after=empty,
            boundary_score_hint=1.0,
            strategy="no_overlap_candidates",
            diagnostics={
                "face_pixels": int(np.count_nonzero(face)),
                "hair_pixels": int(np.count_nonzero(hair)),
                "removed_hair_pixels": 0,
            },
        )

    protect = build_face_protect_mask(
        face,
        validation,
        eye_protect_strength=eye_protect_strength,
        cheek_protect_strength=cheek_protect_strength,
        chin_protect_strength=chin_protect_strength,
        forehead_allowance=forehead_allowance,
    )
    restrict = build_hair_restrict_mask(
        head_mask,
        face,
        face_protect_mask=protect,
        forehead_allowance=forehead_allowance,
    )
    before = detect_boundary_conflict_band(face, hair, restrict_mask=restrict)

    guarded_face, guarded_hair = separate_face_and_hair_by_priority(
        face,
        hair,
        protect,
        restrict,
        guard_strength=guard_strength,
    )

    # Do not normalize or clamp the whole hair mask here. The guard owns only
    # the local face-boundary conflict band; unrelated long-hair geometry must
    # remain byte-for-byte unchanged.

    after = detect_boundary_conflict_band(
        guarded_face,
        guarded_hair,
        restrict_mask=restrict,
    )
    score = compute_face_boundary_score_hint(
        face,
        guarded_face,
        hair,
        guarded_hair,
        restrict_mask=restrict,
        skin_mask=skin_mask,
    )

    before_pixels = int(np.count_nonzero(before))
    after_pixels = int(np.count_nonzero(after))
    removed = max(0, int(np.count_nonzero(hair)) - int(np.count_nonzero(guarded_hair)))
    strategy = "face_priority_guard" if before_pixels > 0 else "boundary_clear"

    return FaceBoundaryGuardResult(
        face_mask=guarded_face,
        hair_mask=guarded_hair,
        face_protect_mask=protect,
        hair_restrict_mask=restrict,
        conflict_mask_before=before,
        conflict_mask_after=after,
        boundary_score_hint=score,
        strategy=strategy,
        diagnostics={
            "face_pixels_before": int(np.count_nonzero(face)),
            "face_pixels_after": int(np.count_nonzero(guarded_face)),
            "hair_pixels_before": int(np.count_nonzero(hair)),
            "hair_pixels_after": int(np.count_nonzero(guarded_hair)),
            "removed_hair_pixels": removed,
            "conflict_pixels_before": before_pixels,
            "conflict_pixels_after": after_pixels,
            "restrict_pixels": int(np.count_nonzero(restrict)),
            "protect_pixels": int(np.count_nonzero(protect)),
            "guard_strength": float(guard_strength),
            "eye_protect_strength": float(eye_protect_strength),
            "cheek_protect_strength": float(cheek_protect_strength),
            "chin_protect_strength": float(chin_protect_strength),
            "forehead_allowance": float(forehead_allowance),
        },
    )


def render_face_boundary_overlay(
    image_rgb: np.ndarray,
    result: FaceBoundaryGuardResult,
) -> np.ndarray:
    out = image_rgb.copy()

    # Blend diagnostic masks instead of painting them opaque so facial details
    # remain visible in debug output.
    overlays = [
        (result.face_protect_mask, np.asarray([70, 220, 120], dtype=np.float32), 0.18),
        (result.hair_restrict_mask, np.asarray([255, 190, 70], dtype=np.float32), 0.16),
        (result.conflict_mask_before, np.asarray([255, 80, 90], dtype=np.float32), 0.46),
        (result.conflict_mask_after, np.asarray([180, 70, 255], dtype=np.float32), 0.54),
    ]
    work = out.astype(np.float32)
    for mask, color, alpha in overlays:
        idx = mask > 0
        if np.any(idx):
            work[idx] = work[idx] * (1.0 - alpha) + color * alpha
    out = np.clip(work, 0, 255).astype(np.uint8)

    face_contours, _ = cv2.findContours(
        (result.face_mask > 0).astype(np.uint8) * 255,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    hair_contours, _ = cv2.findContours(
        (result.hair_mask > 0).astype(np.uint8) * 255,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    cv2.drawContours(out, face_contours, -1, (70, 255, 130), 1, cv2.LINE_AA)
    cv2.drawContours(out, hair_contours, -1, (210, 100, 255), 1, cv2.LINE_AA)

    cv2.putText(
        out,
        f"face_boundary {result.boundary_score_hint:.3f}",
        (8, 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.38,
        (30, 30, 30),
        1,
        cv2.LINE_AA,
    )
    return out


def render_face_boundary_structure_overlay(
    image_rgb: np.ndarray,
    structure,
) -> np.ndarray:
    """Render the final guarded face/hair boundary from CharacterStructure."""
    from .part_types import CharacterPartType

    face = structure.first_part(CharacterPartType.FACE)
    hair = structure.first_part(CharacterPartType.HAIR)
    if face is None or hair is None:
        return image_rgb.copy()

    validation = structure.metadata.get("face_validation") or {}
    md = structure.metadata.get("face_boundary") or {}
    diagnostics = md.get("diagnostics") or {}
    protect = build_face_protect_mask(
        face.mask,
        validation,
        eye_protect_strength=float(diagnostics.get("eye_protect_strength", 0.80)),
        cheek_protect_strength=float(diagnostics.get("cheek_protect_strength", 0.72)),
        chin_protect_strength=float(diagnostics.get("chin_protect_strength", 0.85)),
        forehead_allowance=float(diagnostics.get("forehead_allowance", 0.18)),
    )
    head = structure.first_part(CharacterPartType.HEAD)
    head_mask = head.mask if head is not None else face.mask
    restrict = build_hair_restrict_mask(
        head_mask,
        face.mask,
        face_protect_mask=protect,
        forehead_allowance=float(diagnostics.get("forehead_allowance", 0.18)),
    )
    after = detect_boundary_conflict_band(
        face.mask,
        hair.mask,
        restrict_mask=restrict,
    )
    empty = np.zeros_like(face.mask)
    result = FaceBoundaryGuardResult(
        face_mask=face.mask,
        hair_mask=hair.mask,
        face_protect_mask=protect,
        hair_restrict_mask=restrict,
        conflict_mask_before=empty,
        conflict_mask_after=after,
        boundary_score_hint=float(md.get("boundary_score_hint") or 0.0),
        strategy=str(md.get("strategy") or "unknown"),
        diagnostics=diagnostics,
    )
    return render_face_boundary_overlay(image_rgb, result)
