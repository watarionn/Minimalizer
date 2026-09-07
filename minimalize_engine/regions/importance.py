from __future__ import annotations
import cv2
import numpy as np
from ..models import Region, PaletteColor
from ..palette.color_distance import delta_e76


def _saturation(rgb) -> float:
    r, g, b = [x / 255.0 for x in rgb]
    mx, mn = max(r, g, b), min(r, g, b)
    return 0.0 if mx == 0 else (mx - mn) / mx


def _structure_score(region: Region) -> float:
    contours, _ = cv2.findContours(region.mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0
    c = max(contours, key=cv2.contourArea)
    area = max(float(cv2.contourArea(c)), 1.0)
    peri = max(float(cv2.arcLength(c, True)), 1.0)
    circularity = min(1.0, 4.0 * np.pi * area / (peri * peri))
    x, y, w, h = region.bbox
    elongation = max(w, h) / max(1.0, min(w, h))
    elong_score = min(1.0, (elongation - 1.0) / 5.0)
    return max(circularity, elong_score * 0.7)


def calculate_importance(
    regions: list[Region],
    palette: list[PaletteColor],
    weights,
    preserve_accents: bool,
    min_region_area_ratio: float,
    accent_repeat_min: int,
) -> list[Region]:
    if not regions:
        return regions

    palette_by_id = {p.id: p for p in palette}
    max_area = max(r.area_ratio for r in regions)

    # Global dominant palette color gives a stable, cheap contrast reference.
    dominant = max(palette, key=lambda p: p.ratio)

    by_palette: dict[int, list[Region]] = {}
    for r in regions:
        by_palette.setdefault(r.palette_id, []).append(r)

    for r in regions:
        r.area_score = min(1.0, r.area_ratio / max(max_area, min_region_area_ratio))
        r.contrast_score = min(1.0, delta_e76(r.color_lab, dominant.lab) / 90.0)
        p = palette_by_id[r.palette_id]
        r.rarity_score = min(1.0, max(0.0, (0.25 - p.ratio) / 0.25))
        r.structure_score = _structure_score(r)

        r.importance_score = (
            r.area_score * weights.area
            + r.contrast_score * weights.contrast
            + r.rarity_score * weights.rarity
            + r.structure_score * weights.structure
        )

    if preserve_accents:
        # Accent rescue v0.1:
        # saturated/rare colors repeated at least N times as small-to-medium components.
        for palette_id, group in by_palette.items():
            if len(group) < accent_repeat_min:
                continue
            p = palette_by_id[palette_id]
            sat = _saturation(p.rgb)
            if sat < 0.45 or p.ratio > 0.20:
                continue
            sizes = np.array([r.area for r in group], dtype=np.float32)
            med = float(np.median(sizes))
            if med <= 0:
                continue
            similar = [r for r in group if 0.25 * med <= r.area <= 4.0 * med]
            if len(similar) >= accent_repeat_min:
                for r in similar:
                    r.is_accent = True
                    r.importance_score = max(r.importance_score, 0.55)

    return regions
