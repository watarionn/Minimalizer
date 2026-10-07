"""Source-grounded contour proposals for existing face/hair masks.

Research-only: produces observations, never a renderable new primitive.
All proposals must pass the existing SA10 hard gates before adoption.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ContourProposal:
    owner: str
    points_xy: tuple[tuple[int, int], ...]
    source_iou: float
    vertices: int


def propose_existing_contour(
    owner: str,
    existing_mask: np.ndarray,
    source_part_mask: np.ndarray,
    *,
    vertex_budget: int = 16,
    min_iou: float = 0.90,
) -> ContourProposal | None:
    """Suggest a simplified contour without adding geometry or changing ownership.

    Fail closed for multi-component, holed, or disconnected masks. The returned
    contour is diagnostic, not permission to modify a VectorScene.
    """
    if owner not in {"face", "hair"}:
        raise ValueError("only existing face/hair owners are eligible")
    a = np.asarray(existing_mask).astype(bool)
    b = np.asarray(source_part_mask).astype(bool)
    if a.ndim != 2 or a.shape != b.shape or not a.any() or not b.any():
        return None
    if vertex_budget < 3:
        raise ValueError("vertex_budget must be >= 3")

    def topology(mask: np.ndarray) -> tuple[int, int]:
        contours, hierarchy = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )
        if hierarchy is None:
            return (0, 0)
        levels = hierarchy[0]
        return (
            sum(int(parent == -1) for parent in levels[:, 3]),
            sum(int(parent != -1) for parent in levels[:, 3]),
        )

    # No contour-only proposal can safely represent multiple islands or holes.
    if topology(a) != (1, 0) or topology(b) != (1, 0):
        return None
    contours, _ = cv2.findContours(
        b.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(contour, True)
    if perimeter <= 0:
        return None

    candidate = None
    for fraction in np.linspace(0.001, 0.12, 100):
        polygon = cv2.approxPolyDP(contour, float(fraction * perimeter), True)
        if 3 <= len(polygon) <= vertex_budget:
            candidate = polygon
            break
    if candidate is None:
        return None

    raster = np.zeros(b.shape, dtype=np.uint8)
    cv2.fillPoly(raster, [candidate], 1)
    raster_bool = raster.astype(bool)
    if topology(raster_bool) != (1, 0):
        return None
    union = np.count_nonzero(raster_bool | b)
    iou = float(np.count_nonzero(raster_bool & b) / union) if union else 0.0
    if iou < min_iou:
        return None
    points = tuple((int(p[0][0]), int(p[0][1])) for p in candidate)
    return ContourProposal(owner, points, iou, len(points))
