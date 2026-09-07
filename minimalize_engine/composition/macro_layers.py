from __future__ import annotations

import cv2
import numpy as np

from ..models import Region, Shape
from .skeleton import CompositionSkeleton


def _blend(a, b, strength: float):
    strength = max(0.0, min(1.0, float(strength)))
    return tuple(int(round(a[i] * strength + b[i] * (1.0 - strength))) for i in range(3))


def _weighted_color(regions: list[Region], fallback):
    if not regions:
        return fallback
    total = sum(max(r.area, 1) for r in regions)
    return tuple(
        int(round(sum(r.color_rgb[k] * max(r.area, 1) for r in regions) / total))
        for k in range(3)
    )


def _skyline_components(
    regions: list[Region],
    h: int,
    w: int,
    skeleton: CompositionSkeleton | None = None,
    *,
    clip_corridor: bool = True,
):
    mask = np.zeros((h, w), dtype=np.uint8)
    for r in regions:
        mask = cv2.bitwise_or(mask, (r.mask > 0).astype(np.uint8))
    if not np.any(mask):
        return []

    # Reserve a detected negative-space corridor. This is intentionally applied
    # only to the macro skyline, not detail shapes.
    if skeleton is not None and skeleton.active and clip_corridor:
        margin = max(2, int(round(w * 0.012)))
        x0 = max(0, int(round(skeleton.corridor_x0)) - margin)
        x1 = min(w, int(round(skeleton.corridor_x1)) + margin)
        y1 = min(h, int(round(max(skeleton.horizon_y + h * 0.08, h * 0.62))))
        mask[:y1, x0:x1] = 0

    kx = max(3, int(round(w * 0.026)) | 1)
    ky = max(3, int(round(h * 0.010)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kx, ky))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Re-cut the corridor after closing so the morphology cannot bridge it.
    if skeleton is not None and skeleton.active and clip_corridor:
        margin = max(2, int(round(w * 0.010)))
        x0 = max(0, int(round(skeleton.corridor_x0)) - margin)
        x1 = min(w, int(round(skeleton.corridor_x1)) + margin)
        y1 = min(h, int(round(max(skeleton.horizon_y + h * 0.08, h * 0.62))))
        closed[:y1, x0:x1] = 0

    n, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    comps = []
    for cid in range(1, n):
        area = int(stats[cid, cv2.CC_STAT_AREA])
        bw = int(stats[cid, cv2.CC_STAT_WIDTH])
        if area < h * w * 0.004 or bw < w * 0.08:
            continue
        comps.append(labels == cid)
    comps.sort(key=lambda c: int(c.sum()), reverse=True)
    return comps[:4]


def _envelope_polygon(comp: np.ndarray, h: int, w: int):
    ys, xs = np.nonzero(comp)
    if len(xs) == 0:
        return []
    x0, x1 = int(xs.min()), int(xs.max())
    baseline = min(int(np.percentile(ys, 92)), int(h * 0.70))
    step = max(5, int(round(w / 90)))

    samples = []
    for x in range(x0, x1 + 1, step):
        xa = max(x0, x - step // 2)
        xb = min(x1 + 1, x + step // 2 + 1)
        yy, xx = np.nonzero(comp[:, xa:xb])
        if len(yy):
            samples.append((float(x), float(np.percentile(yy, 8))))

    if len(samples) < 3:
        return []

    top_values = [y for _, y in samples]
    if (x1 - x0) / max(w, 1) > 0.55 and float(np.median(top_values)) < h * 0.18:
        return []

    smooth = []
    for i, (x, y) in enumerate(samples):
        lo = max(0, i - 1)
        hi = min(len(samples), i + 2)
        vals = sorted(samples[j][1] for j in range(lo, hi))
        smooth.append((x, float(vals[len(vals)//2])))

    return smooth + [(float(x1), float(baseline)), (float(x0), float(baseline))]


def _water_base_points(
    h: int,
    w: int,
    top_y: int,
    skeleton: CompositionSkeleton | None,
    water_corridor: bool,
):
    if skeleton is None or not skeleton.active or not water_corridor:
        return [
            (0.0, float(top_y)),
            (float(w), float(top_y)),
            (float(w), float(h)),
            (0.0, float(h)),
        ]

    # Treat the detected center opening as a perspective channel. It widens
    # toward the bottom but keeps generous side margins.
    top_left = float(np.clip(skeleton.corridor_x0, w * 0.18, w * 0.62))
    top_right = float(np.clip(skeleton.corridor_x1, w * 0.38, w * 0.82))
    if top_right <= top_left:
        top_left, top_right = w * 0.44, w * 0.56

    spread = max(w * 0.13, (top_right - top_left) * 1.10)
    bottom_left = float(max(w * 0.08, top_left - spread))
    bottom_right = float(min(w * 0.92, top_right + spread))

    return [
        (top_left, float(top_y)),
        (top_right, float(top_y)),
        (bottom_right, float(h)),
        (bottom_left, float(h)),
    ]


def build_macro_layer_shapes(
    regions: list[Region],
    image_shape,
    background,
    *,
    start_id: int = 900000,
    water_strength: float = 0.38,
    skyline_strength: float = 0.72,
    skeleton: CompositionSkeleton | None = None,
    clip_skyline: bool = True,
    water_corridor: bool = True,
) -> list[Shape]:
    h, w = image_shape[:2]
    bg = background if background is not None else (245, 242, 233)
    out: list[Shape] = []
    sid = start_id

    water_regions = [
        r for r in regions
        if r.composition_layer == "water" or r.role in {"water", "reflection"}
    ]
    boats = [r for r in regions if r.role == "boat"]
    lower = water_regions + boats
    if lower:
        if skeleton is not None and skeleton.active:
            top_y = int(round(skeleton.horizon_y))
        else:
            top_candidates = [r.bbox[1] for r in lower]
            top_y = int(np.percentile(top_candidates, 35)) if top_candidates else int(h * 0.60)
        top_y = max(int(h * 0.50), min(int(h * 0.70), top_y))

        water_color = _weighted_color(water_regions, _weighted_color(boats, bg))
        fill = _blend(water_color, bg, water_strength)
        out.append(
            Shape(
                id=sid,
                shape_type="polygon",
                fill_color=fill,
                points=_water_base_points(h, w, top_y, skeleton, water_corridor),
                z_index=5,
                source_role="water_base",
                layer_name="water_base",
                importance=1.0,
            )
        )
        sid += 1

    skyline_regions = [
        r for r in regions
        if r.composition_layer in {"skyline", "midground"} and r.role == "structure"
    ]
    if skyline_regions:
        darkish = sorted(skyline_regions, key=lambda r: sum(r.color_rgb) / 3.0)
        dark_subset = darkish[:max(1, len(darkish)//2)]
        skyline_color = _weighted_color(dark_subset, _weighted_color(skyline_regions, bg))
        fill = _blend(skyline_color, bg, skyline_strength)
        for comp in _skyline_components(
            skyline_regions,
            h,
            w,
            skeleton,
            clip_corridor=clip_skyline,
        ):
            pts = _envelope_polygon(comp, h, w)
            if len(pts) < 5:
                continue
            out.append(
                Shape(
                    id=sid,
                    shape_type="polygon",
                    fill_color=fill,
                    points=pts,
                    z_index=10,
                    source_role="skyline_base",
                    layer_name="skyline_base",
                    importance=1.0,
                )
            )
            sid += 1

    return out
