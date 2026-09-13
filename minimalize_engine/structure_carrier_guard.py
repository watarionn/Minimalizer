from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .models import Shape
from .structure_geometry import simplify_mask_polygon


@dataclass
class CarrierGuardResult:
    enabled: bool
    reason: str
    patches: tuple[Shape, ...] = ()
    exposure_ratio: float = 0.0
    fallback_count: int = 0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "exposure_ratio": round(float(self.exposure_ratio), 6),
            "fallback_count": int(self.fallback_count),
        }

def _rasterize(shapes: tuple[Shape, ...], shape: tuple[int, int]) -> np.ndarray:
    covered = np.zeros(shape, dtype=np.uint8)
    for item in shapes:
        if not item.points:
            continue
        points = np.asarray(item.points, dtype=np.int32)
        if len(points) >= 3:
            cv2.fillPoly(covered, [points], 1)
    return covered


def _median_color(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    pixels = rgb[mask > 0]
    if len(pixels) == 0:
        return 160, 160, 160
    return tuple(int(value) for value in np.median(pixels, axis=0).astype(np.uint8))


def _shape_mask(item: Shape, shape: tuple[int, int]) -> np.ndarray:
    result = np.zeros(shape, dtype=np.uint8)
    if item.points:
        points = np.asarray(item.points, dtype=np.int32)
        if len(points) >= 3:
            cv2.fillPoly(result, [points], 1)
    return result


def _adjacent_color(component: np.ndarray, shapes: tuple[Shape, ...]) -> tuple[int, int, int] | None:
    ring = cv2.dilate(component, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) & (1 - component)
    best_color = None
    best_touch = 0
    for item in shapes:
        shape_mask = _shape_mask(item, component.shape)
        touch = int(np.count_nonzero(ring & shape_mask))
        if touch > best_touch:
            best_touch = touch
            best_color = item.fill_color
    return best_color


def _component_masks(mask: np.ndarray) -> list[np.ndarray]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    components: list[tuple[int, np.ndarray]] = []
    for index in range(1, count):
        area = int(stats[index, cv2.CC_STAT_AREA])
        components.append((area, (labels == index).astype(np.uint8)))
    components.sort(key=lambda item: item[0], reverse=True)
    return [component for _area, component in components]

def build_carrier_guard(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    structural_shapes: tuple[Shape, ...],
    *,
    start_id: int = 964000,
    max_patches: int = 6,
    max_exposure_ratio: float = 0.30,
) -> CarrierGuardResult:
    subject = (subject_mask > 0).astype(np.uint8)
    subject_area = max(int(subject.sum()), 1)
    covered = _rasterize(structural_shapes, subject.shape)
    covered = cv2.dilate(
        covered,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
    )
    uncovered = subject & (1 - covered)
    exposure_ratio = float(uncovered.sum()) / subject_area
    if exposure_ratio > max_exposure_ratio:
        return CarrierGuardResult(False, "carrier_exposure_gate", exposure_ratio=exposure_ratio)

    min_component = max(12, int(round(subject_area * 0.003)))
    patches: list[Shape] = []
    shape_id = start_id
    for component in _component_masks(uncovered):
        area = int(component.sum())
        if area < min_component:
            continue
        points = simplify_mask_polygon(component, max_points=14, min_iou=0.86)
        if points is None:
            continue
        inherited_color = _adjacent_color(component, structural_shapes)
        patches.append(
            Shape(
                id=shape_id,
                shape_type="polygon",
                fill_color=inherited_color or _median_color(rgb, component),
                points=points,
                z_index=30200,
                importance=0.90,
                source_role="phase17_carrier_patch",
                layer_name="foreground",
                semantic_type="character_carrier_patch",
                character_part="body",
                part_confidence=0.72,
            )
        )
        shape_id += 1
        if len(patches) >= max_patches:
            break

    return CarrierGuardResult(
        True,
        "ok",
        tuple(patches),
        exposure_ratio=exposure_ratio,
        fallback_count=len(patches),
    )
