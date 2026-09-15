from __future__ import annotations

import cv2
import numpy as np

from minimalize_engine.v2.detail_budget.types import HIDE_OVERLAY, DetailBudgetResult
from minimalize_engine.v2.facet.types import (
    PlanarFacetCandidate,
    PlanarFacetConfig,
    PlanarFacetMetrics,
    PlanarFacetResult,
)
from minimalize_engine.v2.palette.sampling import ciede2000
from minimalize_engine.v2.palette.types import PaletteConsolidationResult
from minimalize_engine.v2.primitive.scoring import rasterize_geometry
from minimalize_engine.v2.primitive.types import PrimitiveFittingResult
from minimalize_engine.v2.region_merge.types import RegionSelection
from minimalize_engine.v2.types import ImageBundle


def fit_luminance_split(
    lab_l: np.ndarray,
    mask: np.ndarray,
    *,
    min_samples: int = 40,
) -> tuple[float, float, float, float, float, float, float] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) < min_samples:
        return None
    height, width = mask.shape
    xn = xs.astype(np.float64) / max(width - 1, 1) - 0.5
    yn = ys.astype(np.float64) / max(height - 1, 1) - 0.5
    design = np.column_stack([xn, yn, np.ones(len(xs), dtype=np.float64)])
    values = np.asarray(lab_l[ys, xs], dtype=np.float64)
    coefficients, *_ = np.linalg.lstsq(design, values, rcond=None)
    predicted = design @ coefficients
    variation = float(np.percentile(predicted, 90) - np.percentile(predicted, 10))
    threshold = float(np.median(predicted))
    positive = predicted >= threshold
    if not np.any(positive) or np.all(positive):
        return None
    positive_fraction = float(np.mean(positive))
    negative_mean = float(np.mean(values[~positive]))
    positive_mean = float(np.mean(values[positive]))
    a, b, c0 = (float(v) for v in coefficients)
    norm = float(np.hypot(a, b))
    if norm <= 1.0e-12:
        return None
    return a / norm, b / norm, (c0 - threshold) / norm, variation, negative_mean, positive_mean, positive_fraction


def _variant_rgb(
    base: tuple[int, int, int],
    sample: tuple[int, int, int],
    alpha: float,
) -> tuple[int, int, int]:
    base_rgb = np.asarray(base, dtype=np.float64)
    sample_rgb = np.asarray(sample, dtype=np.float64)
    mixed = (1.0 - alpha) * base_rgb + alpha * sample_rgb
    return tuple(int(v) for v in np.rint(np.clip(mixed, 0.0, 255.0)))


def build_planar_facets(
    bundle: ImageBundle,
    selection: RegionSelection,
    primitives: PrimitiveFittingResult,
    palette: PaletteConsolidationResult,
    detail_budget: DetailBudgetResult,
    *,
    preset: str,
    config: PlanarFacetConfig,
) -> PlanarFacetResult:
    if not config.enabled_for(preset):
        return PlanarFacetResult({}, PlanarFacetMetrics(0, 0.0, 0.0))
    height, width = selection.labels.shape
    yy, xx = np.indices((height, width), dtype=np.float64)
    xn = xx / max(width - 1, 1) - 0.5
    yn = yy / max(height - 1, 1) - 0.5
    total = float(height * width)
    candidates: dict[int, PlanarFacetCandidate] = {}
    for region_id in sorted(selection.region_ids):
        if detail_budget.actions[region_id] == HIDE_OVERLAY:
            continue
        info = detail_budget.shape_info[region_id]
        if info.area_ratio < config.min_region_area_ratio:
            continue
        sample = palette.region_samples[region_id]
        if sample.semantic_tag in set(config.critical_semantic_tags):
            continue
        split = fit_luminance_split(
            bundle.analysis_lab[:, :, 0],
            selection.labels == region_id,
            min_samples=config.min_sample_pixels,
        )
        if split is None:
            continue
        a, b, c, variation, negative_mean, positive_mean, positive_fraction = split
        if min(positive_fraction, 1.0 - positive_fraction) < config.min_source_half_ratio:
            continue
        if variation < config.min_gradient_range:
            continue
        palette_id = detail_budget.effective_palette_by_region[region_id]
        base_entry = palette.entries[palette_id]
        base_l = float(base_entry.lab[0])
        variant_side = 1 if abs(positive_mean - base_l) >= abs(negative_mean - base_l) else -1
        plane = a * xn + b * yn + c
        half = plane >= 0.0 if variant_side > 0 else plane < 0.0
        geometry = primitives.primitives[region_id].selected.geometry
        primitive_mask = rasterize_geometry(
            geometry, (height, width), origin=(0, 0), scale=2
        )
        overlay = primitive_mask & half
        primitive_area = int(primitive_mask.sum())
        overlay_area = int(overlay.sum())
        if primitive_area <= 0:
            continue
        half_ratio = overlay_area / float(primitive_area)
        if not config.min_overlay_half_ratio <= half_ratio <= 1.0 - config.min_overlay_half_ratio:
            continue
        variant_rgb = _variant_rgb(base_entry.rgb, sample.rgb, config.blend_alpha)
        rgb_delta = float(np.linalg.norm(
            np.asarray(variant_rgb, dtype=np.float64)
            - np.asarray(base_entry.rgb, dtype=np.float64)
        ))
        if rgb_delta < config.min_rgb_delta:
            continue
        source_delta_e = float(ciede2000(sample.lab, base_entry.lab))
        candidates[region_id] = PlanarFacetCandidate(
            region_id=region_id,
            base_palette_id=palette_id,
            variant_rgb=variant_rgb,
            line_a=a,
            line_b=b,
            line_c=c,
            variant_side=variant_side,
            overlay_area_ratio=overlay_area / total,
            source_gradient_range=variation,
            source_delta_e=source_delta_e,
        )
    gradients = [item.source_gradient_range for item in candidates.values()]
    metrics = PlanarFacetMetrics(
        candidate_count=len(candidates),
        candidate_area_ratio=float(sum(item.overlay_area_ratio for item in candidates.values())),
        mean_gradient_range=float(np.mean(gradients)) if gradients else 0.0,
    )
    return PlanarFacetResult(candidates, metrics)
