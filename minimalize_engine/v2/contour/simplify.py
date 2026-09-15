from __future__ import annotations

from dataclasses import replace

import cv2
import numpy as np

from minimalize_engine.v2.contour.types import (
    BoundaryChain,
    BoundaryGraph,
    ContourSimplificationConfig,
    ContourSimplificationMetrics,
    ContourSimplificationResult,
    RegionContour,
)
from minimalize_engine.v2.contour.validation import (
    assemble_region_loops,
    candidate_chain_intersection_free,
    candidate_passes_guards,
    directional_limit_for_region,
    evaluate_region_candidate,
    rasterize_loops,
)
from minimalize_engine.v2.region_merge.types import RegionMergeResult, RegionSelection
from minimalize_engine.v2.types import ImageBundle, RegionId


def _micro_cleanup(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float32)
    if len(points) <= 2:
        return points.copy()
    kept = [points[0]]
    for index in range(1, len(points) - 1):
        a = kept[-1]
        b = points[index]
        c = points[index + 1]
        ab = b - a
        bc = c - b
        cross = float(ab[0] * bc[1] - ab[1] * bc[0])
        if abs(cross) <= 1e-6 and float(np.dot(ab, bc)) >= 0.0:
            continue
        kept.append(b)
    kept.append(points[-1])
    return np.asarray(kept, dtype=np.float32)


def _chain_length(points: np.ndarray) -> float:
    if len(points) < 2:
        return 0.0
    return float(np.linalg.norm(np.diff(points.astype(np.float64), axis=0), axis=1).sum())


def _simplify_open_chain(points: np.ndarray, epsilon: float) -> np.ndarray:
    cleaned = _micro_cleanup(points)
    if epsilon <= 0.0 or len(cleaned) <= 2:
        return cleaned
    approx = cv2.approxPolyDP(cleaned.reshape(-1, 1, 2), float(epsilon), False)
    candidate = approx.reshape(-1, 2).astype(np.float32, copy=False)
    if len(candidate) < 2:
        return cleaned
    candidate[0] = cleaned[0]
    candidate[-1] = cleaned[-1]
    return candidate


def _planar_line_candidate(
    points: np.ndarray,
    shape: tuple[int, int],
    config: ContourSimplificationConfig,
) -> np.ndarray:
    points = np.asarray(points, dtype=np.float32)
    if len(points) < config.planar_line_fit_min_points:
        return points
    height, width = shape
    diagonal = max(1.0, float(np.hypot(width, height)))
    min_span = diagonal * config.planar_line_fit_min_span_diagonal_ratio
    max_deviation = diagonal * config.planar_line_fit_max_deviation_diagonal_ratio
    output = [points[0]]
    start = 0
    while start < len(points) - 1:
        best = start + 1
        minimum_end = start + config.planar_line_fit_min_points - 1
        for end in range(len(points) - 1, minimum_end - 1, -1):
            span = points[start:end + 1].astype(np.float64, copy=False)
            chord_vector = span[-1] - span[0]
            chord = float(np.linalg.norm(chord_vector))
            if chord < min_span:
                continue
            arc = _chain_length(span)
            if arc <= 0.0 or chord / arc < config.planar_line_fit_min_efficiency:
                continue
            unit = chord_vector / chord
            relative = span - span[0]
            projection = relative @ unit
            if float(projection.min()) < -1e-6 or float(projection.max()) > chord + 1e-6:
                continue
            normal = np.asarray([-unit[1], unit[0]], dtype=np.float64)
            deviation = np.abs(relative @ normal)
            if float(deviation.max()) <= max_deviation:
                best = end
                break
        output.append(points[best])
        start = best
    return np.asarray(output, dtype=np.float32)


def _epsilon_for_chain(
    chain: BoundaryChain,
    preset: str,
    factor: float,
    config: ContourSimplificationConfig,
) -> float:
    if factor <= 0.0:
        return 0.0
    raw = _chain_length(chain.points) * config.epsilon_ratio_for(preset) * factor
    return float(np.clip(raw, config.epsilon_min_px, config.epsilon_max_px))


def _copy_graph_with_points(
    graph: BoundaryGraph,
    points_by_chain: dict[int, np.ndarray],
) -> BoundaryGraph:
    chains = {
        chain_id: replace(chain, points=points_by_chain[chain_id])
        for chain_id, chain in graph.chains.items()
    }
    return BoundaryGraph(
        vertices=dict(graph.vertices),
        chains=chains,
        region_chains={key: list(value) for key, value in graph.region_chains.items()},
    )


def _original_masks(selection: RegionSelection) -> dict[RegionId, np.ndarray]:
    return {
        region_id: (selection.labels == region_id)
        for region_id in sorted(selection.region_ids)
    }



def _mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise ValueError("region mask is empty")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1

def _assert_boundary_graph_round_trip(
    graph: BoundaryGraph,
    selection: RegionSelection,
    config: ContourSimplificationConfig,
) -> None:
    shape = selection.labels.shape
    for region_id in sorted(selection.region_ids):
        loops = assemble_region_loops(graph, region_id)
        mask = rasterize_loops(loops, shape, scale=config.raster_scale)
        expected = selection.labels == region_id
        if not np.array_equal(mask, expected):
            mismatch = int(np.count_nonzero(mask != expected))
            raise ValueError(
                f"BoundaryGraph round-trip mismatch for region {region_id}: {mismatch} pixels"
            )


def _candidate_valid_for_regions(
    graph: BoundaryGraph,
    merge_result: RegionMergeResult,
    selection: RegionSelection,
    original_masks: dict[RegionId, np.ndarray],
    points_by_chain: dict[int, np.ndarray],
    chain_id: int,
    region_ids: tuple[RegionId, ...],
    config: ContourSimplificationConfig,
) -> bool:
    total_pixels = int(selection.labels.size)
    for region_id in region_ids:
        if not candidate_chain_intersection_free(graph, region_id, chain_id, points_by_chain):
            return False
        loops = assemble_region_loops(graph, region_id, points_by_chain)
        original_full = original_masks[region_id]
        x0, y0, x1, y1 = _mask_bbox(original_full)
        original_local = original_full[y0:y1, x0:x1]
        candidate_mask = rasterize_loops(
            loops, (y1 - y0, x1 - x0),
            scale=config.raster_scale, origin=(x0, y0),
        )
        directional_limit = directional_limit_for_region(
            merge_result, region_id, total_pixels, config
        )
        metrics = evaluate_region_candidate(
            original_local, candidate_mask, loops,
            directional_limit=directional_limit,
            config=config,
            check_self_intersection=False,
        )
        if not candidate_passes_guards(
            metrics, directional_limit=directional_limit, config=config
        ):
            return False
    return True


def _contour_from_final_graph(
    graph: BoundaryGraph,
    merge_result: RegionMergeResult,
    selection: RegionSelection,
    region_id: RegionId,
    config: ContourSimplificationConfig,
) -> tuple[RegionContour, np.ndarray]:
    loops = assemble_region_loops(graph, region_id)
    mask = rasterize_loops(loops, selection.labels.shape, scale=config.raster_scale)
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise ValueError(f"final contour removed region {region_id}")
    stats = merge_result.tree.nodes[region_id].stats
    contour = RegionContour(
        region_id=region_id,
        loops=tuple(loop.astype(np.float32, copy=False) for loop in loops),
        area_px=int(len(xs)),
        centroid=(float(np.mean(xs + 0.5)), float(np.mean(ys + 0.5))),
        semantic_tag=stats.semantic_tag,
        semantic_confidence=stats.semantic_confidence,
    )
    return contour, mask


def _summarize_final_metrics(
    original_graph: BoundaryGraph,
    final_graph: BoundaryGraph,
    merge_result: RegionMergeResult,
    selection: RegionSelection,
    original_masks: dict[RegionId, np.ndarray],
    contours: dict[RegionId, RegionContour],
    final_masks: dict[RegionId, np.ndarray],
    config: ContourSimplificationConfig,
    *,
    fallback_chain_count: int,
    rejected_candidate_count: int,
) -> ContourSimplificationMetrics:
    original_vertices = sum(chain.original_point_count for chain in original_graph.chains.values())
    final_vertices = sum(len(chain.points) for chain in final_graph.chains.values())
    ious: list[float] = []
    area_changes: list[float] = []
    centroid_shifts: list[float] = []
    directional_losses: list[float] = []
    total_pixels = int(selection.labels.size)
    for region_id in sorted(selection.region_ids):
        directional_limit = directional_limit_for_region(
            merge_result, region_id, total_pixels, config
        )
        metrics = evaluate_region_candidate(
            original_masks[region_id], final_masks[region_id], contours[region_id].loops,
            directional_limit=directional_limit, config=config,
            check_self_intersection=False,
        )
        if not candidate_passes_guards(
            metrics, directional_limit=directional_limit, config=config
        ):
            raise ValueError(f"final contour failed guards for region {region_id}")
        ious.append(metrics.iou)
        area_changes.append(metrics.area_change)
        centroid_shifts.append(metrics.centroid_shift_ratio)
        directional_losses.append(metrics.directional_loss)
    return ContourSimplificationMetrics(
        original_vertex_count=original_vertices,
        simplified_vertex_count=final_vertices,
        protected_chain_count=sum(1 for chain in final_graph.chains.values() if chain.protected),
        fallback_chain_count=fallback_chain_count,
        rejected_candidate_count=rejected_candidate_count,
        min_region_iou=min(ious, default=1.0),
        max_area_change=max(area_changes, default=0.0),
        max_centroid_shift_ratio=max(centroid_shifts, default=0.0),
        max_directional_loss=max(directional_losses, default=0.0),
    )


def simplify_boundary_graph(
    graph: BoundaryGraph,
    merge_result: RegionMergeResult,
    selection: RegionSelection,
    *,
    config: ContourSimplificationConfig,
) -> ContourSimplificationResult:
    _assert_boundary_graph_round_trip(graph, selection, config)
    original_masks = _original_masks(selection)
    points_by_chain = {
        chain_id: chain.points.copy()
        for chain_id, chain in graph.chains.items()
    }
    fallback_chain_count = 0
    rejected_candidate_count = 0

    for chain_id in sorted(graph.chains):
        chain = graph.chains[chain_id]
        if chain.protected or len(chain.points) <= 2:
            continue
        accepted = chain.points
        simplified = False
        for factor in config.candidate_factors:
            epsilon = _epsilon_for_chain(chain, selection.preset, factor, config)
            candidate = _simplify_open_chain(chain.points, epsilon)
            if factor > 0.0 and len(candidate) >= len(chain.points):
                continue
            points_by_chain[chain_id] = candidate
            if factor == 0.0 or _candidate_valid_for_regions(
                graph, merge_result, selection, original_masks,
                points_by_chain, chain_id, chain.regions, config,
            ):
                accepted = candidate
                simplified = factor > 0.0 and len(candidate) < len(chain.points)
                break
            rejected_candidate_count += 1
        if config.planar_line_fit_enabled_for(selection.preset) and len(accepted) >= config.planar_line_fit_min_points:
            planar = _planar_line_candidate(accepted, selection.labels.shape, config)
            if len(planar) < len(accepted):
                points_by_chain[chain_id] = planar
                if _candidate_valid_for_regions(
                    graph, merge_result, selection, original_masks,
                    points_by_chain, chain_id, chain.regions, config,
                ):
                    accepted = planar
                    simplified = True
        points_by_chain[chain_id] = accepted
        if not simplified and len(chain.points) > 2:
            fallback_chain_count += 1

    final_graph = _copy_graph_with_points(graph, points_by_chain)
    contours: dict[RegionId, RegionContour] = {}
    final_masks: dict[RegionId, np.ndarray] = {}
    for region_id in sorted(selection.region_ids):
        contour, mask = _contour_from_final_graph(
            final_graph, merge_result, selection, region_id, config
        )
        contours[region_id] = contour
        final_masks[region_id] = mask

    metrics = _summarize_final_metrics(
        graph, final_graph, merge_result, selection,
        original_masks, contours, final_masks, config,
        fallback_chain_count=fallback_chain_count,
        rejected_candidate_count=rejected_candidate_count,
    )
    return ContourSimplificationResult(
        boundary_graph=final_graph,
        contours=contours,
        metrics=metrics,
    )


def simplify_region_contours(
    bundle: ImageBundle,
    merge_result: RegionMergeResult,
    selection: RegionSelection,
    *,
    config: ContourSimplificationConfig,
) -> ContourSimplificationResult:
    from minimalize_engine.v2.contour.boundary_graph import build_boundary_graph

    graph = build_boundary_graph(
        bundle, merge_result, selection, config=config
    )
    return simplify_boundary_graph(
        graph, merge_result, selection, config=config
    )
