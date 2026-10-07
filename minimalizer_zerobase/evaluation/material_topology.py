"""Shared deterministic material-topology normalization and evidence."""

from __future__ import annotations

import cv2
import numpy as np


def canonical_material_mask(mask: np.ndarray) -> np.ndarray:
    """Remove owner-local segmentation specks and pinholes only.

    Components and enclosed holes at or above 0.1% of the owner's foreground
    area (with a 2-pixel floor) remain material topology.  Border-connected
    background is never treated as a hole.
    """
    binary = (np.asarray(mask) > 0).astype(np.uint8)
    if binary.ndim != 2:
        raise ValueError("material masks must be 2D")
    cutoff = max(2, int(round(int(binary.sum()) * 0.001)))
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
