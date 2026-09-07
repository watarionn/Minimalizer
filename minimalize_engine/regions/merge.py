from __future__ import annotations
import cv2
import numpy as np
from ..models import Region
from ..palette.color_distance import delta_e76


def merge_similar_regions(
    regions: list[Region],
    image_shape,
    distance_ratio: float,
    color_delta_e: float,
) -> list[Region]:
    """
    Conservative v0.1 merge:
    only merge regions of similar color whose dilated masks touch.
    This keeps the algorithm deterministic and avoids semantic guesses.
    """
    if len(regions) < 2 or distance_ratio <= 0:
        return regions

    h, w = image_shape[:2]
    radius = max(1, int(round(min(h, w) * distance_ratio)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))

    remaining = regions[:]
    used = set()
    merged = []

    for i, a in enumerate(remaining):
        if a.id in used:
            continue
        mask = a.mask.copy()
        members = [a]
        dilated = cv2.dilate(mask, kernel)

        for b in remaining[i + 1:]:
            if b.id in used:
                continue
            if delta_e76(a.color_lab, b.color_lab) > color_delta_e:
                continue
            if np.any((dilated > 0) & (b.mask > 0)):
                mask = cv2.bitwise_or(mask, b.mask)
                members.append(b)
                used.add(b.id)

        if len(members) == 1:
            merged.append(a)
            continue

        ys, xs = np.nonzero(mask)
        area = int(len(xs))
        if area == 0:
            merged.append(a)
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        total_weight = sum(m.area for m in members)
        rgb = tuple(int(round(sum(m.color_rgb[k] * m.area for m in members) / total_weight)) for k in range(3))
        lab = tuple(float(sum(m.color_lab[k] * m.area for m in members) / total_weight) for k in range(3))
        new = Region(
            id=a.id,
            palette_id=a.palette_id,
            mask=mask,
            area=area,
            area_ratio=area / (h * w),
            color_rgb=rgb,
            color_lab=lab,
            bbox=(x0, y0, x1 - x0 + 1, y1 - y0 + 1),
            centroid=(float(xs.mean()), float(ys.mean())),
            importance_score=max(m.importance_score for m in members),
            is_accent=any(m.is_accent for m in members),
            touches_edge=any(m.touches_edge for m in members),
        )
        merged.append(new)
        used.add(a.id)

    return merged
