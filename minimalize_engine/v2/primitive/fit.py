from __future__ import annotations

from collections import Counter
from dataclasses import replace

import numpy as np

from minimalize_engine.v2.contour.types import ContourSimplificationResult, RegionContour
from minimalize_engine.v2.primitive.candidates import (
    generate_candidate_geometries,
    polygon_complexity,
    primitive_complexity,
    semantic_adjustment,
)
from minimalize_engine.v2.primitive.scoring import (
    candidate_objective,
    evaluate_geometry,
    metric_rejection_reasons,
    region_reference_points,
)
from minimalize_engine.v2.primitive.types import (
    PrimitiveCandidate,
    PrimitiveFitConfig,
    PrimitiveFittingMetrics,
    PrimitiveFittingResult,
    RegionPrimitive,
)
from minimalize_engine.v2.region_merge.types import RegionSelection
from minimalize_engine.v2.types import ImageBundle, RegionId

def _neighbor_ids(contour_result: ContourSimplificationResult, region_id: RegionId) -> frozenset[RegionId]:
    result: set[RegionId] = set()
    graph = contour_result.boundary_graph
    for ref in graph.region_chains[region_id]:
        chain = graph.chains[ref.chain_id]
        if len(chain.regions) != 2:
            continue
        other = chain.regions[0] if chain.regions[1] == region_id else chain.regions[1]
        result.add(other)
    return frozenset(result)


def _subject_region_stats(
    bundle: ImageBundle,
    selection: RegionSelection,
) -> dict[RegionId, tuple[float, float]]:
    if bundle.subject_prob is None:
        return {}
    stats: dict[RegionId, tuple[float, float]] = {}
    confidence = bundle.subject_confidence
    for region_id in sorted(selection.region_ids):
        mask = selection.labels == region_id
        ratio = float(np.mean(bundle.subject_prob[mask]))
        conf = 1.0 if confidence is None else float(np.mean(confidence[mask]))
        stats[region_id] = (ratio, conf)
    return stats


def _subject_guarded_neighbors(
    region_id: RegionId,
    neighbors: frozenset[RegionId],
    subject_stats: dict[RegionId, tuple[float, float]],
    config: PrimitiveFitConfig,
) -> frozenset[RegionId]:
    if region_id not in subject_stats:
        return frozenset()
    ratio, confidence = subject_stats[region_id]
    if confidence < config.subject_confidence_threshold:
        return frozenset()
    guarded: set[RegionId] = set()
    for other in neighbors:
        if other not in subject_stats:
            continue
        other_ratio, other_confidence = subject_stats[other]
        if other_confidence < config.subject_confidence_threshold:
            continue
        separated = (ratio >= 0.5) != (other_ratio >= 0.5)
        if separated and abs(ratio - other_ratio) >= config.subject_critical_contrast:
            guarded.add(other)
    return frozenset(guarded)


def _target_xy(selection: RegionSelection, region_id: RegionId) -> np.ndarray:
    ys, xs = np.nonzero(selection.labels == region_id)
    if len(xs) == 0:
        raise ValueError(f"selection region {region_id} is empty")
    return np.column_stack((xs.astype(np.float32) + 0.5, ys.astype(np.float32) + 0.5))


def _candidate_for_geometry(
    region_id: RegionId,
    contour: RegionContour,
    geometry,
    selection: RegionSelection,
    contour_result: ContourSimplificationResult,
    neighbors: frozenset[RegionId],
    guarded_neighbors: frozenset[RegionId],
    contact_xy: np.ndarray,
    protected_xy: np.ndarray,
    baseline_complexity: float,
    config: PrimitiveFitConfig,
) -> PrimitiveCandidate:
    complexity = (
        baseline_complexity
        if geometry.kind == "polygon"
        else primitive_complexity(geometry.kind, config)
    )
    metrics = evaluate_geometry(
        region_id,
        contour,
        geometry,
        selection,
        neighbor_ids=neighbors,
        critical_neighbor_ids=guarded_neighbors,
        contact_xy=contact_xy,
        protected_xy=protected_xy,
        baseline_complexity=baseline_complexity,
        candidate_complexity=complexity,
        config=config,
    )
    disabled, adjustment = semantic_adjustment(contour, geometry.kind, config)
    error, objective = candidate_objective(
        metrics, semantic_adjustment=adjustment, config=config
    )
    reasons = list(metric_rejection_reasons(metrics, kind=geometry.kind, config=config))
    if disabled:
        reasons.append("semantic_disabled")
    return PrimitiveCandidate(
        region_id=region_id,
        geometry=geometry,
        metrics=metrics,
        complexity=complexity,
        baseline_complexity=baseline_complexity,
        visual_error=error,
        objective=objective,
        eligible=not reasons,
        rejection_reasons=tuple(reasons),
    )


def fit_region_primitives(
    bundle: ImageBundle,
    selection: RegionSelection,
    contour_result: ContourSimplificationResult,
    *,
    config: PrimitiveFitConfig,
) -> PrimitiveFittingResult:
    expected = set(selection.region_ids)
    if selection.labels.shape != bundle.analysis_rgb.shape[:2]:
        raise ValueError("selection labels must match analysis resolution")
    if set(contour_result.contours) != expected:
        raise ValueError("contour result regions must match selection")
    if set(contour_result.boundary_graph.region_chains) != expected:
        raise ValueError("BoundaryGraph regions must match selection")

    subject_stats = _subject_region_stats(bundle, selection)
    primitives: dict[RegionId, RegionPrimitive] = {}
    graph = contour_result.boundary_graph

    for region_id in sorted(selection.region_ids):
        contour = contour_result.contours[region_id]
        neighbors = _neighbor_ids(contour_result, region_id)
        contact_xy, protected_xy, protected_neighbors = region_reference_points(
            graph, region_id
        )
        subject_neighbors = _subject_guarded_neighbors(
            region_id, neighbors, subject_stats, config
        )
        guarded_neighbors = frozenset(protected_neighbors | subject_neighbors)
        target_xy = _target_xy(selection, region_id)
        baseline_complexity = polygon_complexity(contour, config)
        geometries = generate_candidate_geometries(contour, target_xy, config)
        candidates = [
            _candidate_for_geometry(
                region_id,
                contour,
                geometry,
                selection,
                contour_result,
                neighbors,
                guarded_neighbors,
                contact_xy,
                protected_xy,
                baseline_complexity,
                config,
            )
            for geometry in geometries
        ]
        baseline = next(
            item for item in candidates if item.geometry.kind == "polygon"
        )
        finalized: list[PrimitiveCandidate] = []
        for candidate in candidates:
            if (
                candidate.geometry.kind != "polygon"
                and candidate.eligible
                and candidate.objective > baseline.objective - config.adoption_margin
            ):
                candidate = replace(
                    candidate,
                    eligible=False,
                    rejection_reasons=("adoption_margin",),
                )
            finalized.append(candidate)

        eligible = [item for item in finalized if item.eligible]
        if not eligible:
            raise ValueError(f"region {region_id} has no eligible primitive")
        selected = min(
            eligible,
            key=lambda item: (
                item.objective,
                item.visual_error,
                item.complexity,
                item.geometry.kind,
            ),
        )
        primitives[region_id] = RegionPrimitive(
            region_id=region_id,
            selected=selected,
            candidates=tuple(finalized),
        )

    counts = Counter(
        item.selected.geometry.kind for item in primitives.values()
    )
    selected_items = [item.selected for item in primitives.values()]
    guarded_name = "critical_" + "neighbor_leakage"
    metrics = PrimitiveFittingMetrics(
        region_count=len(primitives),
        converted_region_count=sum(item.converted for item in primitives.values()),
        primitive_counts=tuple(sorted(counts.items())),
        mean_iou=float(np.mean([item.metrics.iou for item in selected_items])),
        worst_critical_neighbor_leakage=float(
            max(float(getattr(item.metrics, guarded_name)) for item in selected_items)
        ),
        mean_complexity_gain=float(
            np.mean([item.metrics.complexity_gain for item in selected_items])
        ),
    )
    return PrimitiveFittingResult(primitives=primitives, metrics=metrics)
