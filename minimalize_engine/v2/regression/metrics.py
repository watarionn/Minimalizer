from __future__ import annotations

from typing import Mapping

import numpy as np

from minimalize_engine.v2.palette.sampling import ciede2000
from minimalize_engine.v2.pipeline import MinimalizerV2Result, PipelineConfig
from minimalize_engine.v2.regression.types import RegressionConfig, RegressionMetrics


def _micro_region_ratio(result: MinimalizerV2Result, preset: str, threshold: float) -> float:
    selected = result.presets[preset].selection.region_ids
    total = float(result.region_merge.initial_labels.size)
    count = sum(
        result.region_merge.tree.nodes[region_id].stats.pixel_count / total <= threshold
        for region_id in selected
    )
    return count / float(len(selected)) if selected else 0.0


def _thin_region_ratio(result: MinimalizerV2Result, preset: str, threshold: float) -> float:
    selected = result.presets[preset].selection.region_ids
    thin = 0
    for region_id in selected:
        x0, y0, x1, y1 = result.region_merge.tree.nodes[region_id].stats.bbox
        width = max(x1 - x0, 1)
        height = max(y1 - y0, 1)
        ratio = min(width, height) / float(max(width, height))
        thin += ratio <= threshold
    return thin / float(len(selected)) if selected else 0.0


def _anchor_recall(
    result: MinimalizerV2Result,
    preset: str,
    config: PipelineConfig,
) -> float | None:
    characteristic = result.characteristic
    if characteristic is None:
        return None
    expected = {
        anchor.id for anchor in characteristic.anchors
        if anchor.confidence >= config.palette.anchor_confidence_threshold
    }
    if not expected:
        return 1.0
    palette = result.presets[preset].palette
    retained = {
        anchor_id
        for entry in palette.entries.values()
        for anchor_id in entry.anchor_ids
    }
    return len(expected & retained) / float(len(expected))
def _contrast_metrics(result: MinimalizerV2Result, preset: str) -> tuple[float, int]:
    palette = result.presets[preset].palette
    ratios: list[float] = []
    flips = 0
    for relationship in palette.relationships:
        palette_a = palette.region_to_palette[relationship.region_a]
        palette_b = palette.region_to_palette[relationship.region_b]
        entry_a = palette.entries[palette_a]
        entry_b = palette.entries[palette_b]
        assigned_delta_e = float(ciede2000(entry_a.lab, entry_b.lab))
        if relationship.original_delta_e > 1.0e-12:
            ratios.append(min(1.0, assigned_delta_e / relationship.original_delta_e))
        assigned_delta_l = float(entry_a.lab[0] - entry_b.lab[0])
        if abs(relationship.original_delta_l) > 1.0e-12:
            flips += relationship.original_delta_l * assigned_delta_l < 0.0
    retention = float(np.mean(ratios)) if ratios else 1.0
    return retention, int(flips)


def compute_regression_metrics(
    result: MinimalizerV2Result,
    *,
    preset: str,
    pipeline_config: PipelineConfig,
    regression_config: RegressionConfig,
    phase_timings: Mapping[str, float],
    runtime_seconds: float,
) -> RegressionMetrics:
    pipeline = result.presets[preset]
    selected = pipeline.selection.region_ids
    selected_primitives = [
        pipeline.primitives.primitives[region_id].selected
        for region_id in sorted(selected)
    ]
    primitive_count = max(len(selected_primitives), 1)
    converted = sum(item.geometry.kind != "polygon" for item in selected_primitives)
    polygon = sum(item.geometry.kind == "polygon" for item in selected_primitives)
    neighbor_leakage = max(
        (item.metrics.neighbor_leakage for item in selected_primitives),
        default=0.0,
    )
    critical_leakage = max(
        (item.metrics.critical_neighbor_leakage for item in selected_primitives),
        default=0.0,
    )
    contrast_retention, lightness_flips = _contrast_metrics(result, preset)
    return RegressionMetrics(
        initial_region_count=result.region_merge.initial_region_count,
        selected_region_count=len(selected),
        micro_region_ratio=_micro_region_ratio(
            result, preset, regression_config.micro_region_area_ratio
        ),
        thin_region_ratio=_thin_region_ratio(
            result, preset, regression_config.thin_region_ratio_threshold
        ),
        vertex_count=pipeline.contour.metrics.simplified_vertex_count,
        contour_iou=pipeline.contour.metrics.min_region_iou,
        max_directional_loss=pipeline.contour.metrics.max_directional_loss,
        primitive_conversion_rate=converted / float(primitive_count),
        polygon_fallback_rate=polygon / float(primitive_count),
        neighbor_leakage=float(neighbor_leakage),
        palette_count=pipeline.palette.metrics.palette_count,
        characteristic_anchor_recall=_anchor_recall(
            result, preset, pipeline_config
        ),
        contrast_retention=contrast_retention,
        lightness_flip_count=lightness_flips,
        visual_group_count=pipeline.detail_budget.metrics.visual_group_count,
        total_complexity=float(sum(item.complexity for item in selected_primitives)),
        subject_background_leakage=(
            float(critical_leakage)
            if result.bundle.subject_prob is not None
            else None
        ),
        runtime_seconds=float(runtime_seconds),
        phase_timings=dict(phase_timings),
    )
