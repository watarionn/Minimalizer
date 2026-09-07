from __future__ import annotations

import colorsys
import cv2
import numpy as np

from ..models import Region


def _saturation(rgb) -> float:
    r, g, b = (v / 255.0 for v in rgb)
    _, s, _ = colorsys.rgb_to_hsv(r, g, b)
    return float(s)


def choose_background_region(regions: list[Region]) -> Region | None:
    """
    Primary background is usually the largest region touching the actual canvas edge.
    This correctly identifies a white/cream photo frame when one is present.
    """
    edge = [r for r in regions if r.touches_edge]
    if not edge:
        return max(regions, key=lambda r: r.area, default=None)
    return max(edge, key=lambda r: r.area)


def choose_background_like_region_ids(
    regions: list[Region],
    image_shape,
    primary: Region | None,
) -> set[int]:
    """
    Return regions that behave like backdrop rather than foreground objects.

    v0.1.1 specifically recognizes one broad upper low-saturation mass adjacent
    to the primary frame/background. This handles sky without requiring AI.
    """
    ids: set[int] = set()
    if primary is not None:
        ids.add(primary.id)

    if not regions:
        return ids

    h, w = image_shape[:2]

    # Suppress thin frame/ring artifacts. Their external contour can span almost
    # the whole canvas even though the actual colored pixels occupy only a thin
    # outline. Filling that contour would otherwise create a giant false polygon.
    for r in regions:
        x, y, bw, bh = r.bbox
        if bw / w < 0.84 or bh / h < 0.84:
            continue
        if r.area_ratio > 0.10:
            continue

        contours, _ = cv2.findContours(
            r.mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        if not contours:
            continue
        outer = max(contours, key=cv2.contourArea)
        outer_area = max(float(cv2.contourArea(outer)), 1.0)
        occupancy_inside_outer = r.area / outer_area

        if occupancy_inside_outer < 0.22:
            ids.add(r.id)

    primary_mask = primary.mask if primary is not None else None

    best = None
    best_score = -1.0

    for r in regions:
        if primary is not None and r.id == primary.id:
            continue
        x, y, bw, bh = r.bbox

        if r.area_ratio < 0.12:
            continue
        if bw / w < 0.62:
            continue
        if y / h > 0.18:
            continue
        if r.centroid[1] / h > 0.42:
            continue
        if _saturation(r.color_rgb) > 0.24:
            continue

        adjacency = False
        if primary_mask is not None:
            kernel = np.ones((7, 7), np.uint8)
            dilated = cv2.dilate((primary_mask > 0).astype(np.uint8), kernel, iterations=1)
            adjacency = bool(np.any((dilated > 0) & (r.mask > 0)))

        near_top = y <= max(16, int(h * 0.04))
        if not (adjacency or near_top):
            continue

        score = r.area_ratio + 0.15 * (bw / w) - 0.10 * _saturation(r.color_rgb)
        if score > best_score:
            best = r
            best_score = score

    if best is not None:
        ids.add(best.id)

    return ids


def resolve_background(mode: str, source_region: Region | None, custom_color):
    if mode == "transparent":
        return None
    if mode == "white":
        return (255, 255, 255)
    if mode == "custom":
        return tuple(custom_color)
    if source_region is not None:
        return source_region.color_rgb
    return tuple(custom_color)
