from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .models import Shape
from .subject_segmentation import SubjectSegmentation


@dataclass(frozen=True)
class MacroSubjectGuardResult:
    enabled: bool
    reason: str
    shapes: tuple[Shape, ...] = ()
    subject_bbox: tuple[int, int, int, int] | None = None
    subject_area_ratio: float = 0.0
    subject_coverage_ratio: float = 0.0
    outside_subject_ratio: float = 0.0
    head_anchor_count: int = 0
    torso_anchor_count: int = 0
    arm_anchor_count: int = 0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "shape_count": len(self.shapes),
            "subject_bbox": list(self.subject_bbox) if self.subject_bbox is not None else None,
            "subject_area_ratio": round(float(self.subject_area_ratio), 6),
            "subject_coverage_ratio": round(float(self.subject_coverage_ratio), 6),
            "outside_subject_ratio": round(float(self.outside_subject_ratio), 6),
            "head_anchor_count": self.head_anchor_count,
            "torso_anchor_count": self.torso_anchor_count,
            "arm_anchor_count": self.arm_anchor_count,
        }


def _dominant_source_color(
    pixels: np.ndarray,
    background: tuple[int, int, int] | None,
) -> tuple[int, int, int]:
    if pixels.size == 0:
        return (128, 128, 128)
    pixels = pixels.reshape(-1, 3).astype(np.uint8, copy=False)
    bins = (pixels // 24).astype(np.int16)
    keys, inverse, counts = np.unique(bins, axis=0, return_inverse=True, return_counts=True)
    background_array = np.asarray(background or (255, 255, 255), dtype=np.float32)
    ranked: list[tuple[float, tuple[int, int, int]]] = []
    total = max(int(len(pixels)), 1)
    for index, _key in enumerate(keys):
        selected = pixels[inverse == index]
        color_array = np.median(selected, axis=0).astype(np.float32)
        distance = float(np.linalg.norm(color_array - background_array))
        fraction = float(counts[index]) / float(total)
        score = fraction + min(distance / 255.0, 1.0) * 0.08
        ranked.append((score, tuple(int(v) for v in np.round(color_array))))
    return max(ranked, key=lambda item: item[0])[1]


def _bounded_rect(
    bbox: tuple[int, int, int, int],
    width: int,
    height: int,
    x0_ratio: float,
    y0_ratio: float,
    x1_ratio: float,
    y1_ratio: float,
) -> tuple[int, int, int, int]:
    sx0, sy0, sx1, sy1 = bbox
    sw = max(sx1 - sx0, 1)
    sh = max(sy1 - sy0, 1)
    x0 = max(0, min(width, int(round(sx0 + sw * x0_ratio))))
    x1 = max(0, min(width, int(round(sx0 + sw * x1_ratio))))
    y0 = max(0, min(height, int(round(sy0 + sh * y0_ratio))))
    y1 = max(0, min(height, int(round(sy0 + sh * y1_ratio))))
    return x0, y0, x1, y1


def _simplified_component_polygon(
    subject_mask: np.ndarray,
    rect: tuple[int, int, int, int],
    *,
    min_pixels: int,
    max_vertices: int = 8,
    max_outside_ratio: float = 0.24,
) -> tuple[np.ndarray | None, np.ndarray | None, float]:
    height, width = subject_mask.shape
    x0, y0, x1, y1 = rect
    if x1 <= x0 or y1 <= y0:
        return None, None, 1.0
    zone = np.zeros_like(subject_mask, dtype=np.uint8)
    zone[y0:y1, x0:x1] = subject_mask[y0:y1, x0:x1]
    zone = cv2.morphologyEx(zone, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(zone, 8)
    if count <= 1:
        return None, None, 1.0
    candidates = [
        (int(stats[index, cv2.CC_STAT_AREA]), index)
        for index in range(1, count)
        if int(stats[index, cv2.CC_STAT_AREA]) >= min_pixels
    ]
    if not candidates:
        return None, None, 1.0
    _area, index = max(candidates)
    component = (labels == index).astype(np.uint8)
    contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None, 1.0
    contour = max(contours, key=cv2.contourArea)
    perimeter = float(cv2.arcLength(contour, True))
    if perimeter <= 1e-6:
        return None, None, 1.0
    polygon = None
    for epsilon_ratio in (0.045, 0.055, 0.070, 0.090, 0.120):
        candidate = cv2.approxPolyDP(contour, max(1.0, perimeter * epsilon_ratio), True).reshape(-1, 2)
        if 3 <= len(candidate) <= max_vertices:
            polygon = candidate
            break
    if polygon is None:
        hull = cv2.convexHull(contour).reshape(-1, 2)
        if len(hull) < 3:
            return None, None, 1.0
        polygon = hull if len(hull) <= max_vertices else cv2.approxPolyDP(
            hull.reshape(-1, 1, 2), max(1.0, perimeter * 0.10), True
        ).reshape(-1, 2)
    if len(polygon) < 3:
        return None, None, 1.0
    polygon_mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillPoly(polygon_mask, [np.round(polygon).astype(np.int32)], 1)
    polygon_pixels = max(int(polygon_mask.sum()), 1)
    outside_ratio = int((polygon_mask & (1 - subject_mask)).sum()) / polygon_pixels
    if outside_ratio > max_outside_ratio:
        return None, None, outside_ratio
    return polygon.astype(np.float32), component, outside_ratio


def build_macro_subject_guard(
    segmentation: SubjectSegmentation,
    width: int,
    height: int,
) -> MacroSubjectGuardResult:
    """Build a few coarse subject anchors without inventing fine anatomy.

    This guard is intentionally conservative and only consumes the deterministic
    AI-free subject candidate that already exists in Minimalizer. It preserves a
    head/hair mass, a torso mass, and optional side/arm masses before later
    aggressive poster cleanup can collapse the person into background slabs.
    """
    if segmentation.rgba is None or segmentation.mask is None:
        return MacroSubjectGuardResult(False, "subject_candidate_missing")
    if segmentation.reason not in {"accepted", "confidence_gate"}:
        return MacroSubjectGuardResult(False, "subject_candidate_reason_gate")
    if float(segmentation.border_dominant_fraction) < 0.30:
        return MacroSubjectGuardResult(False, "background_evidence_gate")
    if float(segmentation.center_fill_ratio) < 0.35:
        return MacroSubjectGuardResult(False, "center_fill_gate")
    if float(segmentation.border_leak_ratio) > 0.56:
        return MacroSubjectGuardResult(False, "border_leak_gate")
    if not segmentation.enabled and float(segmentation.confidence) < 0.42:
        return MacroSubjectGuardResult(False, "confidence_gate")

    width = max(int(width), 1)
    height = max(int(height), 1)
    rgb = cv2.resize(segmentation.rgba[:, :, :3], (width, height), interpolation=cv2.INTER_AREA)
    mask = cv2.resize(
        segmentation.mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST
    )
    mask = (mask > 0).astype(np.uint8)
    ys, xs = np.where(mask > 0)
    if xs.size < 64:
        return MacroSubjectGuardResult(False, "subject_too_small")
    subject_area_ratio = float(mask.mean())
    if not 0.18 <= subject_area_ratio <= 0.82:
        return MacroSubjectGuardResult(False, "subject_area_gate", subject_area_ratio=subject_area_ratio)

    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    canvas_area = max(float(width * height), 1.0)
    min_pixels = max(8, int(round(canvas_area * 0.0045)))
    zone_specs = (
        ("head", "head", 947000, 0.18, 0.00, 0.82, 0.46, 0.20),
        ("torso", "torso", 947001, 0.20, 0.32, 0.80, 1.00, 0.18),
        ("left_arm", "left_arm", 947002, 0.00, 0.08, 0.40, 0.88, 0.28),
        ("right_arm", "right_arm", 947003, 0.60, 0.08, 1.00, 0.88, 0.28),
    )
    anchors: list[Shape] = []
    anchor_masks: list[np.ndarray] = []
    outside_weighted = 0.0
    outside_pixels = 0
    for zone_name, character_part, shape_id, x0r, y0r, x1r, y1r, outside_limit in zone_specs:
        rect = _bounded_rect(bbox, width, height, x0r, y0r, x1r, y1r)
        polygon, component, outside_ratio = _simplified_component_polygon(
            mask,
            rect,
            min_pixels=min_pixels,
            max_vertices=8,
            max_outside_ratio=outside_limit,
        )
        if polygon is None or component is None:
            continue
        color = _dominant_source_color(rgb[component > 0], segmentation.background_rgb)
        anchor = Shape(
            id=shape_id,
            shape_type="polygon",
            fill_color=color,
            points=[(float(x), float(y)) for x, y in polygon],
            z_index=39800 + len(anchors),
            importance=1.0,
            source_role=f"phase15_macro_{zone_name}_anchor",
            layer_name="foreground",
            semantic_type=f"character_{zone_name}_macro_anchor",
            character_part=character_part,
            part_confidence=max(0.70, min(0.98, float(segmentation.confidence) + 0.20)),
            side_hint="left" if zone_name == "left_arm" else "right" if zone_name == "right_arm" else "unknown",
        )
        anchors.append(anchor)
        polygon_mask = np.zeros_like(mask, dtype=np.uint8)
        cv2.fillPoly(polygon_mask, [np.round(polygon).astype(np.int32)], 1)
        anchor_masks.append(polygon_mask)
        pixels = int(polygon_mask.sum())
        outside_weighted += outside_ratio * pixels
        outside_pixels += pixels

    head_count = sum(shape.character_part == "head" for shape in anchors)
    torso_count = sum(shape.character_part == "torso" for shape in anchors)
    arm_count = sum(shape.character_part in {"left_arm", "right_arm"} for shape in anchors)
    if head_count < 1 or torso_count < 1:
        return MacroSubjectGuardResult(
            False,
            "required_macro_anchor_missing",
            subject_bbox=bbox,
            subject_area_ratio=subject_area_ratio,
            head_anchor_count=head_count,
            torso_anchor_count=torso_count,
            arm_anchor_count=arm_count,
        )

    combined = np.zeros_like(mask, dtype=np.uint8)
    for anchor_mask in anchor_masks:
        combined |= anchor_mask
    subject_pixels = max(int(mask.sum()), 1)
    coverage_ratio = int((combined & mask).sum()) / subject_pixels
    outside_ratio = outside_weighted / max(outside_pixels, 1)
    if coverage_ratio < 0.28:
        return MacroSubjectGuardResult(
            False,
            "macro_coverage_gate",
            subject_bbox=bbox,
            subject_area_ratio=subject_area_ratio,
            subject_coverage_ratio=coverage_ratio,
            outside_subject_ratio=outside_ratio,
            head_anchor_count=head_count,
            torso_anchor_count=torso_count,
            arm_anchor_count=arm_count,
        )

    return MacroSubjectGuardResult(
        True,
        "macro_subject_anchors",
        shapes=tuple(anchors),
        subject_bbox=bbox,
        subject_area_ratio=subject_area_ratio,
        subject_coverage_ratio=coverage_ratio,
        outside_subject_ratio=outside_ratio,
        head_anchor_count=head_count,
        torso_anchor_count=torso_count,
        arm_anchor_count=arm_count,
    )
