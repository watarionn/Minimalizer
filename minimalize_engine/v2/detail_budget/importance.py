from __future__ import annotations

import math
from collections import Counter
from typing import Mapping

import numpy as np

from minimalize_engine.v2.contour.types import ContourSimplificationResult, RegionContour
from minimalize_engine.v2.detail_budget.types import DetailBudgetConfig, DetailShapeInfo
from minimalize_engine.v2.palette.sampling import ciede2000
from minimalize_engine.v2.palette.types import PaletteConsolidationResult
from minimalize_engine.v2.primitive.types import PrimitiveFittingResult
from minimalize_engine.v2.region_merge.types import RegionSelection
from minimalize_engine.v2.types import ImageBundle, RegionId


def _chain_length(points: np.ndarray) -> float:
    if len(points) < 2:
        return 0.0
    delta = np.diff(points.astype(np.float64), axis=0)
    return float(np.sum(np.linalg.norm(delta, axis=1)))


def _neighbors(contour_result: ContourSimplificationResult, region_id: RegionId) -> tuple[RegionId, ...]:
    result: set[RegionId] = set()
    graph = contour_result.boundary_graph
    for ref in graph.region_chains[region_id]:
        chain = graph.chains[ref.chain_id]
        if len(chain.regions) != 2:
            continue
        other = chain.regions[0] if chain.regions[1] == region_id else chain.regions[1]
        result.add(other)
    return tuple(sorted(result))


def _boundary_scores(
    contour_result: ContourSimplificationResult,
    region_id: RegionId,
) -> tuple[float, float]:
    graph = contour_result.boundary_graph
    total = 0.0
    exterior = 0.0
    protected = 0.0
    for ref in graph.region_chains[region_id]:
        chain = graph.chains[ref.chain_id]
        length = _chain_length(chain.points)
        total += length
        if len(chain.regions) == 1:
            exterior += length
        if chain.protected:
            protected += length
    if total <= 0.0:
        return 0.0, 0.0
    return exterior / total, protected / total


def _pose_score(contour: RegionContour, config: DetailBudgetConfig) -> float:
    points = np.vstack(contour.loops).astype(np.float64)
    extent = np.maximum(np.ptp(points, axis=0), 1e-6)
    elongation = float(np.max(extent) / np.min(extent))
    score = (elongation - 1.0) / (config.pose_full_elongation - 1.0)
    score = float(np.clip(score, 0.0, 1.0))
    if contour.semantic_tag is not None:
        tag = contour.semantic_tag.casefold()
        if any(token in tag for token in ("limb", "arm", "leg")):
            score = max(score, contour.semantic_confidence)
    return score


def _contrast_score(
    region_id: RegionId,
    neighbors: tuple[RegionId, ...],
    palette_result: PaletteConsolidationResult,
    config: DetailBudgetConfig,
) -> float:
    if not neighbors:
        return 0.0
    source = palette_result.region_samples[region_id].lab
    maximum = max(
        float(ciede2000(source, palette_result.region_samples[other].lab))
        for other in neighbors
    )
    return float(np.clip(maximum / config.contrast_scale_delta_e, 0.0, 1.0))


def _critical_semantic(contour: RegionContour, config: DetailBudgetConfig) -> bool:
    if contour.semantic_tag is None:
        return False
    if contour.semantic_confidence < config.semantic_protection_confidence:
        return False
    tag = contour.semantic_tag.casefold()
    return any(token in tag for token in config.critical_semantic_tags)


def analyze_shape_importance(
    bundle: ImageBundle,
    selection: RegionSelection,
    contour_result: ContourSimplificationResult,
    primitive_result: PrimitiveFittingResult,
    palette_result: PaletteConsolidationResult,
    *,
    config: DetailBudgetConfig,
) -> Mapping[RegionId, DetailShapeInfo]:
    region_ids = set(selection.region_ids)
    if selection.labels.shape != bundle.analysis_rgb.shape[:2]:
        raise ValueError("selection labels must match analysis resolution")
    if set(contour_result.contours) != region_ids:
        raise ValueError("contour result regions must match selection")
    if set(primitive_result.primitives) != region_ids:
        raise ValueError("primitive result regions must match selection")
    if set(palette_result.region_to_palette) != region_ids:
        raise ValueError("palette assignments must match selection")

    anchor_counts = Counter(
        anchor_id
        for sample in palette_result.region_samples.values()
        for anchor_id in sample.anchor_ids
    )
    total_pixels = float(selection.labels.size)
    result: dict[RegionId, DetailShapeInfo] = {}

    for region_id in sorted(selection.region_ids):
        contour = contour_result.contours[region_id]
        sample = palette_result.region_samples[region_id]
        neighbors = _neighbors(contour_result, region_id)
        area_ratio = sample.pixel_count / total_pixels
        area_score = math.sqrt(
            min(area_ratio / max(config.structural_mass_area_ratio, 1e-9), 1.0)
        )
        silhouette_fraction, protected_fraction = _boundary_scores(
            contour_result, region_id
        )
        mass_score = min(
            area_ratio / max(config.structural_mass_area_ratio, 1e-9), 1.0
        )
        structural_score = float(
            np.clip(max(mass_score, silhouette_fraction, protected_fraction), 0.0, 1.0)
        )
        characteristic_score = 1.0 if sample.anchor_ids else 0.0
        contrast_score = _contrast_score(
            region_id, neighbors, palette_result, config
        )
        semantic_score = (
            sample.semantic_confidence if sample.semantic_tag is not None else 0.0
        )
        pose_score = _pose_score(contour, config)
        importance = (
            config.area_weight * area_score
            + config.structural_weight * structural_score
            + config.characteristic_weight * characteristic_score
            + config.contrast_weight * contrast_score
            + config.semantic_weight * semantic_score
            + config.pose_weight * pose_score
        )
        importance = float(np.clip(importance, 0.0, 1.0))

        reasons: list[str] = []
        if area_ratio >= config.structural_mass_area_ratio:
            reasons.append("structural_mass")
        if silhouette_fraction >= config.silhouette_protection_ratio:
            reasons.append("silhouette_contributor")
        if pose_score >= config.pose_protection_threshold:
            reasons.append("pose_structure")
        if _critical_semantic(contour, config):
            reasons.append("critical_semantic")
        if any(anchor_counts[anchor_id] <= 1 for anchor_id in sample.anchor_ids):
            reasons.append("last_characteristic_support")

        result[region_id] = DetailShapeInfo(
            region_id=region_id,
            palette_id=palette_result.region_to_palette[region_id],
            area_ratio=float(np.clip(area_ratio, 0.0, 1.0)),
            area_score=area_score,
            structural_score=structural_score,
            characteristic_score=characteristic_score,
            contrast_score=contrast_score,
            semantic_score=semantic_score,
            pose_score=pose_score,
            importance=importance,
            neighbor_ids=neighbors,
            anchor_ids=sample.anchor_ids,
            protected=bool(reasons),
            protection_reasons=tuple(reasons),
        )
    return result
