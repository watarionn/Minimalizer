from __future__ import annotations

import cv2
import numpy as np


def _polygon_mask(shape: tuple[int, int], points: np.ndarray) -> np.ndarray:
    canvas = np.zeros(shape, dtype=np.uint8)
    if len(points) >= 3:
        cv2.fillPoly(canvas, [points.astype(np.int32)], 1)
    return canvas


def polygon_iou(mask: np.ndarray, points: np.ndarray) -> float:
    original = (mask > 0).astype(np.uint8)
    rendered = _polygon_mask(original.shape, points)
    union = int(np.logical_or(original > 0, rendered > 0).sum())
    if union == 0:
        return 0.0
    intersection = int(np.logical_and(original > 0, rendered > 0).sum())
    return intersection / float(union)


def simplify_mask_polygon(
    mask: np.ndarray,
    *,
    max_points: int = 28,
    min_iou: float = 0.90,
) -> list[tuple[float, float]] | None:
    contours, _ = cv2.findContours((mask > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    perimeter = float(cv2.arcLength(contour, True))
    if perimeter <= 0:
        return None
    best = None
    best_iou = -1.0
    for ratio in (0.004, 0.006, 0.008, 0.011, 0.015, 0.020, 0.028, 0.038, 0.052):
        approx = cv2.approxPolyDP(contour, max(1.0, perimeter * ratio), True).reshape(-1, 2)
        if len(approx) < 3:
            continue
        iou = polygon_iou(mask, approx)
        if len(approx) <= max_points and iou >= min_iou:
            best = approx
        if len(approx) <= max_points and iou > best_iou:
            best_iou = iou
            if best is None:
                best = approx

    if best is None:
        hull = cv2.convexHull(contour).reshape(-1, 2)
        if len(hull) < 3:
            return None
        best = hull
    return [(float(x), float(y)) for x, y in best]
