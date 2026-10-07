"""Shared deterministic material-topology normalization and evidence."""

from __future__ import annotations

import cv2
import numpy as np

TINY_COMPONENT_AREA_RATIO = 0.00015
TINY_COMPONENT_AREA_MINIMUM = 8


def tiny_component_area_threshold(subject_area: int | float) -> int:
    return max(TINY_COMPONENT_AREA_MINIMUM, int(round(float(subject_area) * TINY_COMPONENT_AREA_RATIO)))

def canonical_material_mask(mask: np.ndarray, *, tiny_component_area_threshold: int | None = None) -> np.ndarray:
    """Remove owner-local segmentation specks and pinholes only.

    Components and enclosed holes smaller than the canonical Phase14 threshold
    are segmentation noise. Border-connected background is never a hole.
    """
    binary = (np.asarray(mask) > 0).astype(np.uint8)
    if binary.ndim != 2:
        raise ValueError("material masks must be 2D")
    cutoff = (tiny_component_area_threshold if tiny_component_area_threshold is not None
              else globals()["tiny_component_area_threshold"](int(binary.sum())))
    if cutoff < 1:
        raise ValueError("tiny_component_area_threshold must be positive")
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    cleaned = np.zeros_like(binary)
    for label in range(1, count):
        if int(stats[label, cv2.CC_STAT_AREA]) >= cutoff:
            cleaned[labels == label] = 1

    padded = cv2.copyMakeBorder(cleaned, 1, 1, 1, 1, cv2.BORDER_CONSTANT)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(1 - padded, 8)
    for label in range(1, count):
        x, y, width, height, area = stats[label]
        enclosed = (
            x > 0 and y > 0
            and x + width < padded.shape[1]
            and y + height < padded.shape[0]
        )
        if enclosed and int(area) < cutoff:
            cleaned[labels[1:-1, 1:-1] == label] = 1
    return cleaned.astype(bool)


def mask_topology(mask: np.ndarray) -> dict[str, int]:
    """Return deterministic 8-connected component/hole/Euler evidence."""
    binary = (np.asarray(mask) > 0).astype(np.uint8)
    components, _, _, _ = cv2.connectedComponentsWithStats(binary, 8)
    padded = cv2.copyMakeBorder(binary, 1, 1, 1, 1, cv2.BORDER_CONSTANT)
    background, _, _, _ = cv2.connectedComponentsWithStats(1 - padded, 8)
    component_count = max(0, int(components) - 1)
    hole_count = max(0, int(background) - 1)
    return {
        "components": component_count,
        "holes": hole_count,
        "euler_characteristic": component_count - hole_count,
    }
