from __future__ import annotations

import cv2
import numpy as np


def measure_long_line_support(
    image: np.ndarray,
    *,
    min_diagonal_ratio: float = 0.04,
    max_gap_diagonal_ratio: float = 0.007,
    hough_threshold: int = 25,
) -> tuple[float, float, int]:
    gray = cv2.cvtColor(np.asarray(image, dtype=np.uint8), cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 50, 120)
    edge_mask = edges > 0
    edge_count = int(edge_mask.sum())
    edge_density = edge_count / float(edge_mask.size) if edge_mask.size else 0.0
    height, width = edge_mask.shape
    diagonal = float(np.hypot(width, height))
    min_length = max(2, int(round(diagonal * min_diagonal_ratio)))
    max_gap = max(1, int(round(diagonal * max_gap_diagonal_ratio)))
    lines = cv2.HoughLinesP(
        edges, 1.0, np.pi / 180.0, hough_threshold,
        minLineLength=min_length, maxLineGap=max_gap,
    )
    if lines is None or edge_count == 0:
        return float(edge_density), 0.0, 0
    support = np.zeros_like(edges)
    for x1, y1, x2, y2 in lines[:, 0]:
        cv2.line(support, (int(x1), int(y1)), (int(x2), int(y2)), 255, 1, cv2.LINE_8)
    support = cv2.dilate(
        support, np.ones((3, 3), dtype=np.uint8), iterations=1
    ) > 0
    long_line_support = float(np.logical_and(edge_mask, support).sum() / edge_count)
    return float(edge_density), long_line_support, int(len(lines))


def measure_macro_facets(
    image: np.ndarray,
    *,
    rgb_quantization: int = 32,
    min_area_ratio: float = 0.001,
    large_area_ratio: float = 0.02,
    polygon_epsilon_ratio: float = 0.02,
) -> tuple[int, float, float]:
    rgb = np.asarray(image, dtype=np.uint8)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("macro-facet image must have shape (H, W, 3)")
    step = rgb_quantization
    quantized = np.clip(
        (rgb.astype(np.int16) + step // 2) // step * step, 0, 255
    ).astype(np.uint8)
    height, width = quantized.shape[:2]
    total = float(height * width)
    min_area = total * min_area_ratio
    large_area = total * large_area_ratio
    components: list[tuple[int, int]] = []
    for color in np.unique(quantized.reshape(-1, 3), axis=0):
        mask = np.all(quantized == color, axis=2).astype(np.uint8)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        for component_id in range(1, count):
            area = int(stats[component_id, cv2.CC_STAT_AREA])
            if area < min_area:
                continue
            component = (labels == component_id).astype(np.uint8)
            contours, _ = cv2.findContours(
                component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
            )
            if not contours:
                continue
            contour = max(contours, key=cv2.contourArea)
            perimeter = float(cv2.arcLength(contour, True))
            epsilon = polygon_epsilon_ratio * perimeter
            vertices = len(cv2.approxPolyDP(contour, epsilon, True))
            components.append((area, vertices))
    if not components:
        return 0, 0.0, 0.0
    areas = np.asarray([item[0] for item in components], dtype=np.float64)
    vertices = np.asarray([item[1] for item in components], dtype=np.float64)
    large_share = float(areas[areas >= large_area].sum() / total)
    mean_vertices = float(np.average(vertices, weights=areas))
    return len(components), large_share, mean_vertices
