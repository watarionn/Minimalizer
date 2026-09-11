from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .models import Shape
from .subject_plane_cleanup import (
    absorb_small_label_fragments,
    component_priority,
    is_macro_anchor,
    safe_simplify_polygon,
)


@dataclass(frozen=True)
class SubjectPlaneResult:
    enabled: bool
    reason: str
    shapes: tuple[Shape, ...] = ()
    color_count: int = 0
    plane_count: int = 0
    vertex_count: int = 0
    contrast_adjusted_colors: int = 0
    gesture_plane_count: int = 0
    bridge_kernel_size: int = 1
    subject_coverage_ratio: float = 0.0
    outside_subject_ratio: float = 0.0
    absorbed_fragment_count: int = 0
    absorbed_fragment_pixels: int = 0
    protected_fragment_count: int = 0
    suppressed_plane_count: int = 0
    adaptive_refinement_count: int = 0
    macro_anchor_count: int = 0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "color_count": self.color_count,
            "plane_count": self.plane_count,
            "vertex_count": self.vertex_count,
            "contrast_adjusted_colors": self.contrast_adjusted_colors,
            "gesture_plane_count": self.gesture_plane_count,
            "bridge_kernel_size": self.bridge_kernel_size,
            "subject_coverage_ratio": self.subject_coverage_ratio,
            "outside_subject_ratio": self.outside_subject_ratio,
            "absorbed_fragment_count": self.absorbed_fragment_count,
            "absorbed_fragment_pixels": self.absorbed_fragment_pixels,
            "protected_fragment_count": self.protected_fragment_count,
            "suppressed_plane_count": self.suppressed_plane_count,
            "adaptive_refinement_count": self.adaptive_refinement_count,
            "macro_anchor_count": self.macro_anchor_count,
        }


def _weighted_quantized_candidates(
    pixels: np.ndarray,
    *,
    step: int = 24,
) -> tuple[np.ndarray, np.ndarray]:
    quantized = (pixels.astype(np.int16) // max(int(step), 1)).astype(np.int16)
    keys, inverse, counts = np.unique(
        quantized,
        axis=0,
        return_inverse=True,
        return_counts=True,
    )
    sums = np.zeros((len(keys), 3), dtype=np.float64)
    for channel in range(3):
        sums[:, channel] = np.bincount(
            inverse,
            weights=pixels[:, channel],
            minlength=len(keys),
        )
    means = sums / np.maximum(counts[:, None], 1)
    order = np.argsort(-counts, kind="stable")
    return means[order], counts[order]


def _deterministic_centers(pixels: np.ndarray, color_count: int) -> np.ndarray:
    candidates, counts = _weighted_quantized_candidates(pixels)
    count = min(max(int(color_count), 1), len(candidates))
    if count <= 0:
        return np.empty((0, 3), dtype=np.float64)

    selected = [candidates[0]]
    while len(selected) < count:
        selected_array = np.vstack(selected)
        distances = np.min(
            np.sum((candidates[:, None, :] - selected_array[None, :, :]) ** 2, axis=2),
            axis=1,
        )
        scores = distances * np.sqrt(counts.astype(np.float64))
        selected.append(candidates[int(np.argmax(scores))])

    centers = np.vstack(selected).astype(np.float64)
    for _ in range(12):
        distances = np.sum((pixels[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        labels = np.argmin(distances, axis=1)
        updated = np.vstack([
            pixels[labels == index].mean(axis=0) if np.any(labels == index) else centers[index]
            for index in range(len(centers))
        ])
        if float(np.max(np.abs(updated - centers))) < 0.1:
            centers = updated
            break
        centers = updated
    return np.clip(np.round(centers), 0, 255).astype(np.uint8)


def _contrast_adjusted(
    color: np.ndarray,
    background: tuple[int, int, int],
) -> tuple[np.ndarray, bool]:
    color_f = color.astype(np.float64)
    background_f = np.asarray(background, dtype=np.float64)
    if float(np.linalg.norm(color_f - background_f)) >= 70.0:
        return color.astype(np.uint8), False
    darker = np.clip(np.round(color_f * 0.68), 0, 255)
    lighter = np.clip(np.round(color_f + (255.0 - color_f) * 0.32), 0, 255)
    dark_distance = float(np.linalg.norm(darker - background_f))
    light_distance = float(np.linalg.norm(lighter - background_f))
    adjusted = darker if dark_distance >= light_distance else lighter
    return adjusted.astype(np.uint8), True


def _component_source_tone_override(
    display_color: np.ndarray,
    local_color: np.ndarray,
) -> tuple[np.ndarray, bool]:
    local = np.asarray(local_color, dtype=np.uint8)
    ycc = cv2.cvtColor(local.reshape(1, 1, 3), cv2.COLOR_RGB2YCrCb)[0, 0]
    yy, cr, cb = (int(v) for v in ycc)
    chroma = int(local.max()) - int(local.min())
    skin_like = 78 <= yy and 132 <= cr <= 194 and 68 <= cb <= 154
    if yy >= 205 and chroma <= 36 and not skin_like:
        return local, True
    return np.asarray(display_color, dtype=np.uint8), False


def _identity_component_bonus(
    local_color: np.ndarray, area: int, canvas_area: float,
    centroid: np.ndarray, width: int, height: int,
) -> float:
    local = np.asarray(local_color, dtype=np.uint8)
    yy, cr, cb = (int(v) for v in cv2.cvtColor(local.reshape(1, 1, 3), cv2.COLOR_RGB2YCrCb)[0, 0])
    chroma = int(local.max()) - int(local.min())
    skin_like = 78 <= yy and 132 <= cr <= 194 and 68 <= cb <= 154
    area_ratio = float(area) / max(float(canvas_area), 1.0)
    bonus = 0.0
    if yy >= 205 and chroma <= 36 and not skin_like and area_ratio >= 0.0040:
        bonus += 0.018
    cx, cy = (float(v) for v in centroid)
    central = 0.20 <= cx / max(float(width), 1.0) <= 0.80
    lower_head = cy / max(float(height), 1.0) >= 0.48
    if yy >= 185 and chroma <= 70 and central and lower_head and area_ratio >= 0.0060:
        bonus += 0.016
    return bonus



def _is_upper_gesture_representative(
    area: int, stats: np.ndarray, centroid: np.ndarray, local_color: np.ndarray,
    width: int, height: int, canvas_area: float,
) -> bool:
    area_ratio = float(area) / max(float(canvas_area), 1.0)
    _x, _y, bw, bh, _a = [float(v) for v in stats]
    cx, cy = (float(v) for v in centroid)
    nx, ny = cx / max(float(width), 1.0), cy / max(float(height), 1.0)
    extent = max(bw / max(float(width), 1.0), bh / max(float(height), 1.0))
    color = np.asarray(local_color, dtype=np.float32)
    luma = float(0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2])
    return (
        0.010 <= area_ratio <= 0.050 and ny <= 0.42 and
        (nx <= 0.30 or nx >= 0.70) and extent >= 0.18 and luma >= 175.0
    )

def _component_is_gesture_plane(
    color: np.ndarray,
    stats: np.ndarray,
    centroid: np.ndarray,
    width: int,
    height: int,
) -> bool:
    box_x, box_y, box_width, box_height, area = [float(value) for value in stats]
    center_x, center_y = [float(value) for value in centroid]
    canvas_area = max(float(width * height), 1.0)
    area_ratio = area / canvas_area
    luma = float(0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2])
    chroma = float(np.max(color) - np.min(color))
    side_position = center_x / max(float(width), 1.0)
    return (
        0.008 <= area_ratio <= 0.050
        and box_height / max(float(height), 1.0) >= 0.20
        and center_y / max(float(height), 1.0) <= 0.62
        and (side_position <= 0.40 or side_position >= 0.60)
        and luma <= 105.0
        and chroma <= 45.0
        and box_width >= 3.0
        and box_x > 0.0
        and box_y > 0.0
        and box_x + box_width < float(width)
        and box_y + box_height < float(height)
    )


def build_subject_color_planes(
    rgba: np.ndarray,
    width: int,
    height: int,
    background_rgb: tuple[int, int, int] | None,
    *,
    max_colors: int = 6,
    min_component_area_ratio: float = 0.0015,
    max_components_per_color: int = 4,
    max_total_planes: int = 17,
    fragment_area_ratio: float = 0.0030,
    simplify_epsilon_ratio: float = 0.036,
    bridge_radius_ratio: float = 0.0045,
    preserve_light_component_tones: bool = False,
    preserve_color_representatives: bool = False,
    preserve_upper_gesture_representatives: bool = False,
) -> SubjectPlaneResult:
    if rgba.ndim != 3 or rgba.shape[2] < 4:
        return SubjectPlaneResult(False, "rgba_required")
    width = max(int(width), 1)
    height = max(int(height), 1)
    background = tuple(int(v) for v in (background_rgb or (255, 255, 255)))

    rgb = cv2.resize(rgba[:, :, :3], (width, height), interpolation=cv2.INTER_AREA)
    alpha = cv2.resize(rgba[:, :, 3], (width, height), interpolation=cv2.INTER_NEAREST)
    mask = alpha >= 128
    pixels = rgb[mask].reshape(-1, 3).astype(np.float64)
    if len(pixels) < 64:
        return SubjectPlaneResult(False, "subject_too_small")

    centers = _deterministic_centers(pixels, min(max(int(max_colors), 1), 8))
    if len(centers) < 2:
        return SubjectPlaneResult(False, "insufficient_colors")
    distances = np.sum(
        (pixels[:, None, :] - centers[None, :, :].astype(np.float64)) ** 2,
        axis=2,
    )
    pixel_labels = np.argmin(distances, axis=1)
    label_image = np.full((height, width), -1, dtype=np.int16)
    label_image[mask] = pixel_labels.astype(np.int16)

    display_centers = centers.copy()
    adjusted_count = 0
    for index, color in enumerate(display_centers):
        adjusted, changed = _contrast_adjusted(color, background)
        display_centers[index] = adjusted
        adjusted_count += int(changed)
    canvas_area = max(float(width * height), 1.0)
    min_area = max(8, int(round(canvas_area * float(min_component_area_ratio))))
    bridge_radius = max(1, int(round(min(width, height) * float(bridge_radius_ratio))))
    bridge_kernel_size = 2 * bridge_radius + 1
    bridge_kernel = np.ones((bridge_kernel_size, bridge_kernel_size), dtype=np.uint8)
    subject_mask = mask.astype(np.uint8)
    label_image, absorbed_fragment_count, absorbed_fragment_pixels, protected_fragment_count = (
        absorb_small_label_fragments(
            label_image,
            centers,
            subject_mask,
            fragment_area_ratio=fragment_area_ratio,
        )
    )
    entries: list[tuple[int, int, np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []
    adaptive_refinement_count = 0
    for color_index in range(len(centers)):
        color_mask = (label_image == color_index).astype(np.uint8)
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, bridge_kernel)
        color_mask &= subject_mask
        count, labels, stats, centroids = cv2.connectedComponentsWithStats(color_mask, 8)
        components: list[tuple[int, int]] = []
        for component_index in range(1, count):
            area = int(stats[component_index, cv2.CC_STAT_AREA])
            if area >= min_area:
                components.append((area, component_index))
        for area, component_index in sorted(components, reverse=True)[:max_components_per_color]:
            component_mask = (labels == component_index).astype(np.uint8)
            contours, _ = cv2.findContours(
                component_mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            if not contours:
                continue
            contour = max(contours, key=cv2.contourArea)
            polygon, refinement_steps = safe_simplify_polygon(
                contour, component_mask, subject_mask, simplify_epsilon_ratio
            )
            if polygon is None or len(polygon) < 3:
                continue
            adaptive_refinement_count += int(refinement_steps > 0)
            local_color = np.median(rgb[component_mask > 0], axis=0).astype(np.uint8)
            entries.append((area, color_index, polygon, stats[component_index], centroids[component_index], local_color))

    if not entries:
        return SubjectPlaneResult(False, "no_planes")
    raw_component_count = len(entries)
    if raw_component_count > max(int(max_total_planes), 1):
        def entry_priority(item):
            return (
                _component_is_gesture_plane(centers[item[1]], item[3], item[4], width, height),
                component_priority(item[0], centers[item[1]], item[3], item[4], width, height)
                + (
                    _identity_component_bonus(
                        item[5], item[0], canvas_area, item[4], width, height
                    )
                    if preserve_light_component_tones else 0.0
                ),
                item[0],
            )
        prioritized = sorted(entries, key=entry_priority, reverse=True)
        budget = max(int(max_total_planes), 1)
        selected_prefix = []
        if preserve_upper_gesture_representatives:
            for side in ("left", "right"):
                side_candidates = []
                for item in prioritized:
                    nx = float(item[4][0]) / max(float(width), 1.0)
                    if side == "left" and nx > 0.30:
                        continue
                    if side == "right" and nx < 0.70:
                        continue
                    if _is_upper_gesture_representative(item[0], item[3], item[4], item[5], width, height, canvas_area):
                        side_candidates.append(item)
                if side_candidates:
                    selected_prefix.append(max(side_candidates, key=entry_priority))
        if preserve_color_representatives:
            representatives = []
            for color_index in range(len(centers)):
                center = centers[color_index]
                if int(center.max()) - int(center.min()) < 35:
                    continue
                candidates = [
                    item for item in prioritized
                    if item[1] == color_index and item[0] / canvas_area >= 0.0055
                ]
                if candidates:
                    representatives.append(candidates[0])
            representatives = sorted(representatives, key=entry_priority, reverse=True)[:budget]
            seed = []
            seen = set()
            for item in selected_prefix + representatives:
                if id(item) not in seen and len(seed) < budget:
                    seed.append(item); seen.add(id(item))
            entries = seed + [item for item in prioritized if id(item) not in seen][: max(0, budget - len(seed))]
        elif selected_prefix:
            seen = {id(item) for item in selected_prefix}
            entries = selected_prefix + [item for item in prioritized if id(item) not in seen][: max(0, budget - len(selected_prefix))]
        else:
            entries = prioritized[:budget]
    suppressed_plane_count = raw_component_count - len(entries)
    macro_anchor_count = sum(
        int(is_macro_anchor(item[0], item[3], item[4], width, height))
        for item in entries
    )
    entries.sort(key=lambda item: item[0], reverse=True)
    shapes: list[Shape] = []
    gesture_count = 0
    for index, (area, color_index, polygon, component_stats, centroid, local_color) in enumerate(entries):
        gesture = _component_is_gesture_plane(
            centers[color_index],
            component_stats,
            centroid,
            width,
            height,
        )
        center_x = float(centroid[0]) / max(float(width), 1.0)
        side_hint = "left" if center_x <= 0.40 else "right" if center_x >= 0.60 else "unknown"
        upper_gesture = bool(
            preserve_upper_gesture_representatives
            and _is_upper_gesture_representative(
                area, component_stats, centroid, local_color, width, height, canvas_area
            )
        )
        semantic_type = (
            "phase16_upper_gesture_plane" if upper_gesture
            else "phase10_gesture_plane" if gesture else "subject_mass"
        )
        source_role = (
            "phase16_upper_gesture_plane" if upper_gesture
            else "phase10_gesture_plane" if gesture else "phase10_subject_plane"
        )
        importance = 0.995 if upper_gesture else 0.985 if gesture else min(0.97, 0.55 + 2.5 * area / canvas_area)
        if gesture:
            gesture_count += 1
        fill_color = display_centers[color_index]
        if preserve_light_component_tones:
            fill_color, _ = _component_source_tone_override(fill_color, local_color)
        shapes.append(Shape(
            id=930000 + index,
            shape_type="polygon",
            fill_color=tuple(int(value) for value in fill_color),
            points=[(float(x), float(y)) for x, y in polygon],
            z_index=(31040 + index) if upper_gesture else (30000 + index),
            importance=importance,
            source_role=source_role,
            layer_name="foreground",
            semantic_type=semantic_type,
            character_part=(f"{side_hint}_arm" if upper_gesture and side_hint in {"left", "right"} else "unknown"),
            part_confidence=0.82 if upper_gesture else 0.0,
            side_hint=side_hint,
        ))

    plane_mask = np.zeros((height, width), dtype=np.uint8)
    for shape in shapes:
        if len(shape.points) < 3:
            continue
        points = np.round(np.asarray(shape.points, dtype=np.float32)).astype(np.int32)
        cv2.fillPoly(plane_mask, [points], 1)
    subject_pixels = max(int(subject_mask.sum()), 1)
    plane_pixels = max(int(plane_mask.sum()), 1)
    subject_coverage = int((plane_mask & subject_mask).sum()) / subject_pixels
    outside_subject = int((plane_mask & (1 - subject_mask)).sum()) / plane_pixels

    return SubjectPlaneResult(
        True,
        "accepted",
        shapes=tuple(shapes),
        color_count=len(centers),
        plane_count=len(shapes),
        vertex_count=sum(len(shape.points) for shape in shapes),
        contrast_adjusted_colors=adjusted_count,
        gesture_plane_count=gesture_count,
        bridge_kernel_size=bridge_kernel_size,
        subject_coverage_ratio=round(float(subject_coverage), 6),
        outside_subject_ratio=round(float(outside_subject), 6),
        absorbed_fragment_count=absorbed_fragment_count,
        absorbed_fragment_pixels=absorbed_fragment_pixels,
        protected_fragment_count=protected_fragment_count,
        suppressed_plane_count=suppressed_plane_count,
        adaptive_refinement_count=adaptive_refinement_count,
        macro_anchor_count=macro_anchor_count,
    )
