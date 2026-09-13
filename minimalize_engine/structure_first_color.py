from __future__ import annotations

import cv2
import numpy as np

from .models import Shape
from .structure_first import StructureFirstResult


_PART_MAX_COLORS = {
    "body": 1,
    "hair": 2,
    "left_arm": 2,
    "right_arm": 2,
    "torso": 2,
    "face": 1,
}

_PART_Z = {
    "body": 30300,
    "hair": 30400,
    "left_arm": 30500,
    "right_arm": 30510,
    "torso": 30600,
    "face": 30700,
}


def _polygon(mask: np.ndarray, max_points: int = 10) -> list[tuple[float, float]] | None:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    perimeter = float(cv2.arcLength(contour, True))
    chosen = None
    for ratio in (0.018, 0.026, 0.036, 0.050, 0.070):
        approx = cv2.approxPolyDP(contour, max(1.5, perimeter * ratio), True).reshape(-1, 2)
        chosen = approx
        if 3 <= len(approx) <= max_points:
            break
    if chosen is None or len(chosen) < 3:
        return None
    return [(float(x), float(y)) for x, y in chosen]


def _largest_component(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if count <= 1:
        return mask.astype(np.uint8)
    index = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    return (labels == index).astype(np.uint8)


def _median_color(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    pixels = rgb[mask > 0]
    if len(pixels) == 0:
        return 160, 160, 160
    color = np.median(pixels, axis=0).astype(np.uint8)
    return tuple(int(value) for value in color)


def _cluster_masks(rgb: np.ndarray, part_mask: np.ndarray, max_colors: int) -> list[np.ndarray]:
    ys, xs = np.where(part_mask > 0)
    if len(xs) < 48 or max_colors <= 1:
        return [part_mask.astype(np.uint8)]

    pixels = rgb[ys, xs].astype(np.uint8)
    lab_pixels = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    spread = float(np.mean(np.std(lab_pixels, axis=0)))
    if spread < 7.0:
        return [part_mask.astype(np.uint8)]

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.8)
    _compactness, labels, _centers = cv2.kmeans(
        lab_pixels,
        max_colors,
        None,
        criteria,
        3,
        cv2.KMEANS_PP_CENTERS,
    )
    labels = labels.ravel()
    masks: list[np.ndarray] = []
    min_area = max(20, int(part_mask.sum() * 0.14))
    for label in range(max_colors):
        cluster = np.zeros_like(part_mask, dtype=np.uint8)
        selected = labels == label
        cluster[ys[selected], xs[selected]] = 1
        cluster = _largest_component(cluster)
        if int(cluster.sum()) >= min_area:
            masks.append(cluster)
    return masks or [part_mask.astype(np.uint8)]


def build_structure_first_color_shapes(
    rgb: np.ndarray,
    structure: StructureFirstResult,
    *,
    start_id: int = 961000,
) -> tuple[Shape, ...]:
    if not structure.enabled:
        return ()

    shapes: list[Shape] = []
    shape_id = start_id
    for part in ("body", "hair", "left_arm", "right_arm", "torso", "face"):
        part_mask = structure.masks.get(part)
        if part_mask is None or int(part_mask.sum()) < 24:
            continue
        clusters = _cluster_masks(rgb, part_mask, _PART_MAX_COLORS[part])
        clusters = sorted(clusters, key=lambda item: int(item.sum()), reverse=True)
        if part == "body" and structure.masks.get("torso") is not None:
            base_color_mask = structure.masks["torso"]
        else:
            base_color_mask = clusters[0]
        base_points = _polygon(part_mask, max_points=8 if part == "face" else 10)
        if base_points is None:
            continue
        side_hint = "left" if part == "left_arm" else "right" if part == "right_arm" else "unknown"
        shapes.append(
            Shape(
                id=shape_id,
                shape_type="polygon",
                fill_color=_median_color(rgb, base_color_mask),
                points=base_points,
                z_index=_PART_Z[part],
                importance=0.995,
                source_role=f"phase17_structure_color_{part}_base",
                layer_name="foreground",
                semantic_type=f"character_{part}",
                character_part=part,
                part_confidence=0.90,
                side_hint=side_hint,
            )
        )
        shape_id += 1

        if len(clusters) < 2 or part == "face":
            continue
        accent = clusters[1]
        accent_ratio = float(accent.sum()) / max(float(part_mask.sum()), 1.0)
        if not 0.14 <= accent_ratio <= 0.55:
            continue
        base_rgb = np.asarray(_median_color(rgb, base_color_mask), dtype=np.uint8).reshape(1, 1, 3)
        accent_rgb = np.asarray(_median_color(rgb, accent), dtype=np.uint8).reshape(1, 1, 3)
        base_lab = cv2.cvtColor(base_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
        accent_lab = cv2.cvtColor(accent_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
        if float(np.linalg.norm(base_lab - accent_lab)) < 14.0:
            continue
        accent_points = _polygon(accent, max_points=8)
        if accent_points is None:
            continue
        shapes.append(
            Shape(
                id=shape_id,
                shape_type="polygon",
                fill_color=_median_color(rgb, accent),
                points=accent_points,
                z_index=_PART_Z[part] + 1,
                importance=0.94,
                source_role=f"phase17_structure_color_{part}_accent",
                layer_name="foreground",
                semantic_type=f"character_{part}",
                character_part=part,
                part_confidence=0.82,
                side_hint=side_hint,
            )
        )
        shape_id += 1
    return tuple(shapes)
