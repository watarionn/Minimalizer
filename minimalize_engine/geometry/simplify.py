from __future__ import annotations

import cv2
import numpy as np


def _polygon_iou(contour: np.ndarray, polygon: np.ndarray, mask: np.ndarray) -> float:
    if polygon is None or len(polygon) < 3:
        return 0.0

    poly_mask = np.zeros(mask.shape[:2], dtype=np.uint8)
    cv2.fillPoly(poly_mask, [polygon.astype(np.int32)], 255)

    a = mask > 0
    b = poly_mask > 0
    union = np.count_nonzero(a | b)
    if union == 0:
        return 1.0
    return float(np.count_nonzero(a & b) / union)


def simplify_contour(
    contour: np.ndarray,
    epsilon_ratio: float,
    *,
    mask: np.ndarray | None = None,
    area_ratio: float = 0.0,
    major_iou_target: float = 0.86,
    medium_iou_target: float = 0.78,
    small_iou_target: float = 0.68,
    max_major_epsilon_ratio: float = 0.010,
) -> np.ndarray:
    """
    Adaptive approxPolyDP.

    Large composition-defining masses get a smaller epsilon and must retain
    high mask IoU. This prevents a complex waterfront/building silhouette from
    collapsing into a giant triangle.
    """
    if contour is None or len(contour) < 3:
        return contour

    perimeter = max(float(cv2.arcLength(contour, True)), 1.0)

    if area_ratio >= 0.08:
        target_iou = major_iou_target
        ratio = min(epsilon_ratio, max_major_epsilon_ratio)
        min_vertices = 8
    elif area_ratio >= 0.03:
        target_iou = medium_iou_target
        ratio = min(epsilon_ratio, max_major_epsilon_ratio * 1.5)
        min_vertices = 6
    else:
        target_iou = small_iou_target
        ratio = epsilon_ratio
        min_vertices = 3

    # Search from simple to detailed, halving epsilon until fidelity is enough.
    best = contour
    for factor in (1.0, 0.75, 0.50, 0.35, 0.25, 0.15):
        epsilon = max(0.35, perimeter * ratio * factor)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) < min_vertices:
            best = approx
            continue

        if mask is None:
            return approx

        iou = _polygon_iou(contour, approx, mask)
        best = approx
        if iou >= target_iou:
            return approx

    return best
