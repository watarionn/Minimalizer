from __future__ import annotations

import colorsys

from ..models import Region


def _brightness(rgb) -> float:
    r, g, b = (v / 255.0 for v in rgb)
    return float(0.299 * r + 0.587 * g + 0.114 * b)


def _saturation(rgb) -> float:
    r, g, b = (v / 255.0 for v in rgb)
    _, s, _ = colorsys.rgb_to_hsv(r, g, b)
    return float(s)


def assign_region_roles(regions: list[Region], image_shape, subject_mode: bool = False) -> list[Region]:
    h, w = image_shape[:2]

    for r in regions:
        x, y, bw, bh = r.bbox
        cx, cy = r.centroid
        aspect = bw / max(1.0, bh)
        inv_aspect = bh / max(1.0, bw)
        sat = _saturation(r.color_rgb)
        bright = _brightness(r.color_rgb)

        if subject_mode:
            if r.is_accent and r.area_ratio <= 0.0035 and sat >= 0.30:
                r.role = "accent"
            elif inv_aspect >= 2.2 and r.area_ratio <= 0.010:
                r.role = "vertical"
            elif r.area_ratio >= 0.0015:
                r.role = "structure"
            else:
                r.role = "misc"
            continue

        # Geometry gets first say. Repeated warm/dark fragments in architecture
        # must not all become accents just because they share a palette color.
        if inv_aspect >= 2.0 and r.area_ratio <= 0.008 and cy / h < 0.92:
            r.role = "vertical"
            continue

        if (
            0.44 <= cy / h <= 0.78
            and 1.4 <= aspect <= 8.0
            and 0.012 <= bw / w <= 0.28
            and bh / h <= 0.18
            and 0.0007 <= r.area_ratio <= 0.020
            and not r.touches_edge
        ):
            r.role = "boat"
            continue

        if cy / h > 0.58 and aspect >= 1.6 and bh / h <= 0.22:
            r.role = "water"
            continue

        if cy / h < 0.80 and r.area_ratio >= 0.0010 and bh / h >= 0.055:
            r.role = "structure"
            continue

        if (
            cy / h > 0.56
            and r.area_ratio <= 0.007
            and inv_aspect >= 1.15
            and not r.touches_edge
        ):
            r.role = "reflection"
            continue

        # Accent is deliberately late and small. This preserves lantern/window
        # rhythm without turning every orange building fragment into decoration.
        if (
            r.is_accent
            and r.area_ratio <= 0.0035
            and max(bw / w, bh / h) <= 0.16
            and sat >= 0.35
        ):
            r.role = "accent"
            continue

        if cy / h > 0.60 and r.area_ratio <= 0.0035 and bright < 0.34 and sat < 0.85:
            r.role = "reflection"
            continue

        r.role = "misc"

    return regions


def filter_reflection_noise(regions: list[Region], target_keep: int = 4) -> list[Region]:
    reflections = [r for r in regions if r.role == "reflection"]
    others = [r for r in regions if r.role != "reflection"]

    reflections.sort(key=lambda r: (r.importance_score, r.area_ratio), reverse=True)
    kept = []
    for r in reflections[:target_keep]:
        if r.importance_score >= 0.48 or r.area_ratio >= 0.0025:
            kept.append(r)

    return others + kept
