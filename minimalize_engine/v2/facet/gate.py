from __future__ import annotations

import numpy as np

from minimalize_engine.v2.detail_budget.types import HIDE_OVERLAY, DetailBudgetResult
from minimalize_engine.v2.facet.render import apply_planar_facet_overlay, facet_overlay_mask
from minimalize_engine.v2.facet.types import (
    PlanarFacetCandidate,
    PlanarFacetGateConfig,
    PlanarFacetGateDecision,
    PlanarFacetOverlay,
    PlanarFacetRenderMetrics,
    PlanarFacetRenderPlan,
    PlanarFacetResult,
)
from minimalize_engine.v2.palette.sampling import ciede2000
from minimalize_engine.v2.palette.types import PaletteConsolidationResult
from minimalize_engine.v2.preprocessing import rgb_to_canonical_lab
from minimalize_engine.v2.primitive.scoring import rasterize_geometry
from minimalize_engine.v2.primitive.types import PrimitiveFittingResult
from minimalize_engine.v2.visual_metrics import measure_long_line_support, measure_macro_facets


def _render_base(
    shape: tuple[int, int],
    primitives: PrimitiveFittingResult,
    palette: PaletteConsolidationResult,
    detail_budget: DetailBudgetResult,
) -> np.ndarray:
    canvas = np.full((*shape, 3), 255, dtype=np.uint8)
    for region_id in sorted(primitives.primitives):
        if detail_budget.actions[region_id] == HIDE_OVERLAY:
            continue
        geometry = primitives.primitives[region_id].selected.geometry
        mask = rasterize_geometry(geometry, shape, origin=(0, 0), scale=2)
        palette_id = detail_budget.effective_palette_by_region[region_id]
        canvas[mask] = palette.entries[palette_id].rgb
    return canvas

def _overlay_from_candidate(candidate: PlanarFacetCandidate) -> PlanarFacetOverlay:
    return PlanarFacetOverlay(
        region_id=candidate.region_id,
        rgb=candidate.variant_rgb,
        line_a=candidate.line_a,
        line_b=candidate.line_b,
        line_c=candidate.line_c,
        variant_side=candidate.variant_side,
    )


def _macro(image: np.ndarray, config: PlanarFacetGateConfig) -> tuple[int, float, float]:
    return measure_macro_facets(
        image,
        rgb_quantization=config.macro_rgb_quantization,
        min_area_ratio=config.macro_min_area_ratio,
        large_area_ratio=config.macro_large_area_ratio,
        polygon_epsilon_ratio=config.macro_polygon_epsilon_ratio,
    )


def _line_support(image: np.ndarray, config: PlanarFacetGateConfig) -> float:
    return measure_long_line_support(
        image,
        min_diagonal_ratio=config.line_min_diagonal_ratio,
        max_gap_diagonal_ratio=config.line_max_gap_diagonal_ratio,
        hough_threshold=config.line_hough_threshold,
    )[1]

def _protected_relationship_ok(
    candidate: PlanarFacetCandidate,
    palette: PaletteConsolidationResult,
    detail_budget: DetailBudgetResult,
    config: PlanarFacetGateConfig,
) -> bool:
    variant_lab = rgb_to_canonical_lab(
        np.asarray([[candidate.variant_rgb]], dtype=np.uint8)
    )[0, 0]
    base_lab = palette.entries[candidate.base_palette_id].lab
    for relationship in palette.relationships:
        if relationship.protection < config.protected_relationship_threshold:
            continue
        if candidate.region_id not in {relationship.region_a, relationship.region_b}:
            continue
        other = (
            relationship.region_b
            if candidate.region_id == relationship.region_a
            else relationship.region_a
        )
        other_palette_id = detail_budget.effective_palette_by_region[other]
        other_lab = palette.entries[other_palette_id].lab
        base_delta = float(ciede2000(base_lab, other_lab))
        variant_delta = float(ciede2000(variant_lab, other_lab))
        if base_delta > 1.0e-12 and variant_delta < config.min_protected_contrast_ratio * base_delta:
            return False
        if abs(relationship.original_delta_l) >= config.significant_delta_l:
            assigned_delta_l = float(variant_lab[0] - other_lab[0])
            if candidate.region_id == relationship.region_b:
                assigned_delta_l = -assigned_delta_l
            if relationship.original_delta_l * assigned_delta_l < 0.0:
                return False
    return True


def _overlay_shape_reasons_from_mask(
    shape: tuple[int, int],
    mask: np.ndarray,
    config: PlanarFacetGateConfig,
) -> tuple[str, ...]:
    ys, xs = np.where(mask)
    if xs.size == 0:
        return ("empty_overlay",)
    width = int(xs.max() - xs.min() + 1)
    height = int(ys.max() - ys.min() + 1)
    diagonal = max(1.0, float(np.hypot(shape[1], shape[0])))
    short_ratio = min(width, height) / diagonal
    aspect_ratio = max(width, height) / max(1.0, min(width, height))
    reasons: list[str] = []
    if short_ratio < config.min_overlay_short_side_diagonal_ratio:
        reasons.append("overlay_too_thin")
    if aspect_ratio > config.max_overlay_aspect_ratio:
        reasons.append("overlay_too_elongated")
    return tuple(reasons)


def _overlay_shape_reasons(
    shape: tuple[int, int],
    geometry,
    overlay: PlanarFacetOverlay,
    config: PlanarFacetGateConfig,
) -> tuple[str, ...]:
    mask = facet_overlay_mask(shape, geometry, overlay)
    return _overlay_shape_reasons_from_mask(shape, mask, config)


def build_facet_render_plan(
    shape: tuple[int, int],
    primitives: PrimitiveFittingResult,
    palette: PaletteConsolidationResult,
    detail_budget: DetailBudgetResult,
    facet_result: PlanarFacetResult,
    *,
    preset: str,
    config: PlanarFacetGateConfig,
) -> PlanarFacetRenderPlan:
    base_image = _render_base(shape, primitives, palette, detail_budget)
    baseline_macro = _macro(base_image, config)
    baseline_line = _line_support(base_image, config)
    if not config.enabled_for(preset):
        decisions = {
            region_id: PlanarFacetGateDecision(
                region_id=region_id,
                accepted=False,
                reasons=("gate_disabled",),
                facet_count_delta=0,
                large_share_delta=0.0,
                mean_vertices_delta=0.0,
                long_line_delta=0.0,
            )
            for region_id in facet_result.candidates
        }
        metrics = PlanarFacetRenderMetrics(
            candidate_count=len(decisions), accepted_count=0, accepted_area_ratio=0.0,
            baseline_facet_count=baseline_macro[0], final_facet_count=baseline_macro[0],
            baseline_large_share=baseline_macro[1], final_large_share=baseline_macro[1],
            baseline_mean_vertices=baseline_macro[2], final_mean_vertices=baseline_macro[2],
            baseline_long_line_support=baseline_line, final_long_line_support=baseline_line,
        )
        return PlanarFacetRenderPlan({}, decisions, metrics)
    current_image = base_image
    current_macro = baseline_macro
    current_line = baseline_line
    overlays: dict[int, PlanarFacetOverlay] = {}
    decisions: dict[int, PlanarFacetGateDecision] = {}
    ordered = sorted(
        facet_result.candidates.values(),
        key=lambda item: (-item.source_gradient_range, -item.overlay_area_ratio, item.region_id),
    )
    for candidate in ordered:
        overlay = _overlay_from_candidate(candidate)
        geometry = primitives.primitives[candidate.region_id].selected.geometry
        overlay_mask = facet_overlay_mask(shape, geometry, overlay)
        preliminary: list[str] = []
        if not _protected_relationship_ok(candidate, palette, detail_budget, config):
            preliminary.append("protected_relationship")
        preliminary.extend(_overlay_shape_reasons_from_mask(shape, overlay_mask, config))
        if preliminary:
            decisions[candidate.region_id] = PlanarFacetGateDecision(
                region_id=candidate.region_id,
                accepted=False,
                reasons=tuple(preliminary),
                facet_count_delta=0,
                large_share_delta=0.0,
                mean_vertices_delta=0.0,
                long_line_delta=0.0,
            )
            continue
        trial_image = apply_planar_facet_overlay(
            current_image, geometry, overlay, mask=overlay_mask
        )
        trial_macro = _macro(trial_image, config)
        trial_line = _line_support(trial_image, config)
        count_delta = trial_macro[0] - current_macro[0]
        large_delta = trial_macro[1] - current_macro[1]
        vertices_delta = trial_macro[2] - current_macro[2]
        line_delta = trial_line - current_line
        reasons: list[str] = []
        if trial_macro[0] < current_macro[0]:
            reasons.append("facet_count_regression")
        if large_delta > config.max_large_share_increase:
            reasons.append("large_share_regression")
        if vertices_delta > config.max_mean_vertices_increase:
            reasons.append("vertex_complexity_regression")
        macro_gain = (
            count_delta > 0
            or large_delta < -config.min_large_share_gain
            or vertices_delta < -config.min_mean_vertices_gain
        )
        if not macro_gain:
            reasons.append("no_macro_gain")
        if trial_line < baseline_line - config.max_long_line_loss:
            reasons.append("long_line_loss")
        accepted = not reasons
        decisions[candidate.region_id] = PlanarFacetGateDecision(
            region_id=candidate.region_id,
            accepted=accepted,
            reasons=tuple(reasons),
            facet_count_delta=int(count_delta),
            large_share_delta=float(large_delta),
            mean_vertices_delta=float(vertices_delta),
            long_line_delta=float(line_delta),
        )
        if accepted:
            overlays[candidate.region_id] = overlay
            current_image = trial_image
            current_macro = trial_macro
            current_line = trial_line

    accepted_area = float(sum(
        facet_result.candidates[region_id].overlay_area_ratio
        for region_id in overlays
    ))
    metrics = PlanarFacetRenderMetrics(
        candidate_count=len(facet_result.candidates),
        accepted_count=len(overlays),
        accepted_area_ratio=accepted_area,
        baseline_facet_count=baseline_macro[0],
        final_facet_count=current_macro[0],
        baseline_large_share=baseline_macro[1],
        final_large_share=current_macro[1],
        baseline_mean_vertices=baseline_macro[2],
        final_mean_vertices=current_macro[2],
        baseline_long_line_support=baseline_line,
        final_long_line_support=current_line,
    )
    return PlanarFacetRenderPlan(overlays, decisions, metrics)
