from __future__ import annotations

import cv2
import numpy as np


def _component_chroma(color: np.ndarray) -> float:
    return float(np.max(color) - np.min(color))


def _protected_fragment(
    color: np.ndarray,
    stats: np.ndarray,
    width: int,
    height: int,
    canvas_area: float,
) -> bool:
    _, _, box_width, box_height, area = [float(value) for value in stats]
    area_ratio = area / max(canvas_area, 1.0)
    extent = max(
        box_width / max(float(width), 1.0),
        box_height / max(float(height), 1.0),
    )
    if _component_chroma(color) >= 70.0 and area_ratio >= 0.0015:
        return True
    return extent >= 0.18 and area_ratio >= 0.0012


def absorb_small_label_fragments(
    label_image: np.ndarray,
    centers: np.ndarray,
    subject_mask: np.ndarray,
    *,
    fragment_area_ratio: float = 0.0030,
    max_color_distance: float = 95.0,
) -> tuple[np.ndarray, int, int, int]:
    height, width = label_image.shape[:2]
    canvas_area = max(float(width * height), 1.0)
    max_area = max(8, int(round(canvas_area * float(fragment_area_ratio))))
    kernel = np.ones((5, 5), dtype=np.uint8)
    original = label_image.copy()
    out = label_image.copy()
    candidates: list[tuple[int, int, np.ndarray]] = []
    protected_count = 0

    for color_index in range(len(centers)):
        color_mask = (original == color_index).astype(np.uint8)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(color_mask, 8)
        for component_index in range(1, count):
            area = int(stats[component_index, cv2.CC_STAT_AREA])
            if area >= max_area:
                continue
            if _protected_fragment(centers[color_index], stats[component_index], width, height, canvas_area):
                protected_count += 1
                continue
            component = (labels == component_index).astype(np.uint8)
            candidates.append((area, color_index, component))

    absorbed_count = 0
    absorbed_pixels = 0
    for area, color_index, component in sorted(candidates, key=lambda item: item[0]):
        ring = cv2.dilate(component, kernel, iterations=1)
        ring = (ring > 0) & (component == 0) & (subject_mask > 0)
        neighbors = original[ring]
        neighbors = neighbors[(neighbors >= 0) & (neighbors != color_index)]
        if neighbors.size == 0:
            continue
        labels, counts = np.unique(neighbors, return_counts=True)
        best_label = None
        best_score = -1.0
        for neighbor_label, contact in zip(labels, counts):
            distance = float(np.linalg.norm(
                centers[color_index].astype(np.float64)
                - centers[int(neighbor_label)].astype(np.float64)
            ))
            if distance > max_color_distance:
                continue
            score = float(contact) / (1.0 + distance / 40.0)
            if score > best_score:
                best_score = score
                best_label = int(neighbor_label)
        if best_label is None:
            continue
        out[component > 0] = best_label
        absorbed_count += 1
        absorbed_pixels += int(area)

    return out, absorbed_count, absorbed_pixels, protected_count


def safe_simplify_polygon(
    contour: np.ndarray,
    component_mask: np.ndarray,
    subject_mask: np.ndarray,
    requested_ratio: float,
) -> tuple[np.ndarray | None, int]:
    perimeter = float(cv2.arcLength(contour, True))
    if perimeter <= 0.0:
        return None, 0
    component_pixels = max(int(component_mask.sum()), 1)
    scales = (1.0, 0.80, 0.62, 0.48, 0.36, 0.26)
    best_polygon: np.ndarray | None = None
    best_score = -1.0
    best_attempt = 0

    for attempt, scale in enumerate(scales):
        epsilon = max(1.0, float(requested_ratio) * scale * perimeter)
        polygon = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
        if len(polygon) < 3:
            continue
        polygon_mask = np.zeros_like(component_mask, dtype=np.uint8)
        cv2.fillPoly(polygon_mask, [polygon.astype(np.int32)], 1)
        polygon_pixels = max(int(polygon_mask.sum()), 1)
        intersection = int((polygon_mask & component_mask).sum())
        union = max(polygon_pixels + component_pixels - intersection, 1)
        precision = intersection / polygon_pixels
        recall = intersection / component_pixels
        iou = intersection / union
        outside = int((polygon_mask & (1 - subject_mask)).sum()) / polygon_pixels
        score = iou - 0.55 * outside
        if score > best_score:
            best_polygon = polygon
            best_score = score
            best_attempt = attempt
        if precision >= 0.68 and recall >= 0.68 and iou >= 0.50 and outside <= 0.035:
            return polygon, attempt

    fallback = cv2.approxPolyDP(contour, max(1.0, 0.008 * perimeter), True).reshape(-1, 2)
    if len(fallback) >= 3:
        return fallback, len(scales)
    return best_polygon, best_attempt


def component_priority(
    area: int,
    color: np.ndarray,
    stats: np.ndarray,
    centroid: np.ndarray,
    width: int,
    height: int,
) -> float:
    canvas_area = max(float(width * height), 1.0)
    _, _, box_width, box_height, _ = [float(value) for value in stats]
    center_x, center_y = [float(value) for value in centroid]
    area_ratio = float(area) / canvas_area
    priority = area_ratio
    if _component_chroma(color) >= 70.0 and area_ratio >= 0.0020:
        priority += 0.018
    central = 0.20 <= center_x / max(float(width), 1.0) <= 0.80
    upper_body = center_y / max(float(height), 1.0) <= 0.82
    if central and upper_body and area_ratio >= 0.0035:
        priority += 0.010
    extent = max(
        box_width / max(float(width), 1.0),
        box_height / max(float(height), 1.0),
    )
    if extent >= 0.20 and area_ratio >= 0.0020:
        priority += 0.008
    return priority


def is_macro_anchor(
    area: int,
    stats: np.ndarray,
    centroid: np.ndarray,
    width: int,
    height: int,
) -> bool:
    canvas_area = max(float(width * height), 1.0)
    _, _, box_width, box_height, _ = [float(value) for value in stats]
    center_x, center_y = [float(value) for value in centroid]
    area_ratio = float(area) / canvas_area
    if area_ratio >= 0.010:
        return True
    central = 0.22 <= center_x / max(float(width), 1.0) <= 0.78
    upper_body = center_y / max(float(height), 1.0) <= 0.82
    extent = max(box_width / max(float(width), 1.0), box_height / max(float(height), 1.0))
    return (central and upper_body and area_ratio >= 0.0035) or (extent >= 0.20 and area_ratio >= 0.0020)
