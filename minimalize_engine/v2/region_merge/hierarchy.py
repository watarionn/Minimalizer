from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import heapq

from minimalize_engine.v2.types import ImageBundle, RegionAnnotation, RegionId
from minimalize_engine.v2.region_merge.cost import (
    MergeEvaluation,
    RegionMergeConfig,
    evaluate_merge,
    is_safe_consolidation,
)
from minimalize_engine.v2.region_merge.graph import (
    apply_merge,
    build_initial_merge_tree,
    build_region_graph,
    edge_key,
    validate_graph,
    validate_merge_tree,
)
from minimalize_engine.v2.region_merge.segmentation import oversegment
from minimalize_engine.v2.region_merge.types import (
    RegionGraph,
    RegionMergeMetrics,
    RegionMergeResult,
    RegionMergeTree,
)


@dataclass(slots=True)
class _MergeMetricsCollector:
    initial_edge_count: int
    evaluation_count: int = 0
    blocked_evaluation_count: int = 0
    safe_candidate_count: int = 0
    barrier_counts: Counter[str] = field(default_factory=Counter)

    def record(self, evaluation: MergeEvaluation, *, safe_candidate: bool = False) -> None:
        self.evaluation_count += 1
        if not evaluation.allowed:
            self.blocked_evaluation_count += 1
            self.barrier_counts.update(evaluation.blocked_by)
        if safe_candidate:
            self.safe_candidate_count += 1

    def freeze(self, *, final_root_count: int) -> RegionMergeMetrics:
        return RegionMergeMetrics(
            initial_edge_count=self.initial_edge_count,
            evaluation_count=self.evaluation_count,
            blocked_evaluation_count=self.blocked_evaluation_count,
            safe_candidate_count=self.safe_candidate_count,
            final_root_count=final_root_count,
            barrier_counts=tuple(sorted(self.barrier_counts.items())),
        )


def _evaluate_active_edge(
    graph: RegionGraph,
    left_id: RegionId,
    right_id: RegionId,
    *,
    image_area: int,
    config: RegionMergeConfig,
    use_line_prior: bool = True,
) -> MergeEvaluation:
    key = edge_key(left_id, right_id)
    return evaluate_merge(
        graph.nodes[left_id],
        graph.nodes[right_id],
        graph.edges[key],
        image_area=image_area,
        config=config,
        use_line_prior=use_line_prior,
    )


def _push_safe_candidate(
    heap: list[tuple[float, int, int]],
    graph: RegionGraph,
    left_id: RegionId,
    right_id: RegionId,
    *,
    image_area: int,
    config: RegionMergeConfig,
    metrics: _MergeMetricsCollector,
) -> None:
    evaluation = _evaluate_active_edge(
        graph, left_id, right_id, image_area=image_area, config=config, use_line_prior=False
    )
    edge = graph.edges[edge_key(left_id, right_id)]
    safe = is_safe_consolidation(
        graph.nodes[left_id],
        graph.nodes[right_id],
        edge,
        evaluation,
        image_area=image_area,
        config=config,
    )
    metrics.record(evaluation, safe_candidate=safe)
    if safe:
        heapq.heappush(heap, (evaluation.total_cost, min(left_id, right_id), max(left_id, right_id)))


def run_safe_consolidation(
    graph: RegionGraph,
    tree: RegionMergeTree,
    *,
    image_area: int,
    config: RegionMergeConfig,
    metrics: _MergeMetricsCollector,
) -> int:
    heap: list[tuple[float, int, int]] = []
    for left_id, right_id in sorted(graph.edges):
        _push_safe_candidate(
            heap,
            graph,
            left_id,
            right_id,
            image_area=image_area,
            config=config,
            metrics=metrics,
        )
    merge_count = 0
    while heap:
        cost, left_id, right_id = heapq.heappop(heap)
        key = edge_key(left_id, right_id)
        if left_id not in graph.nodes or right_id not in graph.nodes or key not in graph.edges:
            continue
        evaluation = _evaluate_active_edge(
            graph, left_id, right_id, image_area=image_area, config=config, use_line_prior=False
        )
        edge = graph.edges[key]
        safe = is_safe_consolidation(
            graph.nodes[left_id], graph.nodes[right_id], edge, evaluation,
            image_area=image_area, config=config,
        )
        metrics.record(evaluation, safe_candidate=safe)
        if not safe:
            continue
        if abs(evaluation.total_cost - cost) > 1e-12:
            heapq.heappush(heap, (evaluation.total_cost, left_id, right_id))
            continue
        new_id = apply_merge(
            graph,
            tree,
            left_id,
            right_id,
            raw_merge_cost=evaluation.total_cost,
            stage="safe",
        )
        merge_count += 1
        for neighbor_id in sorted(graph.adjacency[new_id]):
            _push_safe_candidate(
                heap,
                graph,
                new_id,
                neighbor_id,
                image_area=image_area,
                config=config,
                metrics=metrics,
            )
    return merge_count


def _push_hierarchy_candidate(
    heap: list[tuple[float, int, int]],
    graph: RegionGraph,
    left_id: RegionId,
    right_id: RegionId,
    *,
    image_area: int,
    config: RegionMergeConfig,
    metrics: _MergeMetricsCollector,
) -> None:
    evaluation = _evaluate_active_edge(
        graph, left_id, right_id, image_area=image_area, config=config
    )
    metrics.record(evaluation)
    if evaluation.allowed:
        heapq.heappush(
            heap,
            (evaluation.total_cost, min(left_id, right_id), max(left_id, right_id)),
        )


def run_hierarchical_merge(
    graph: RegionGraph,
    tree: RegionMergeTree,
    *,
    image_area: int,
    config: RegionMergeConfig,
    metrics: _MergeMetricsCollector,
) -> int:
    heap: list[tuple[float, int, int]] = []
    for left_id, right_id in sorted(graph.edges):
        _push_hierarchy_candidate(
            heap,
            graph,
            left_id,
            right_id,
            image_area=image_area,
            config=config,
            metrics=metrics,
        )

    merge_count = 0
    while heap:
        cost, left_id, right_id = heapq.heappop(heap)
        key = edge_key(left_id, right_id)
        if left_id not in graph.nodes or right_id not in graph.nodes or key not in graph.edges:
            continue
        evaluation = _evaluate_active_edge(
            graph, left_id, right_id, image_area=image_area, config=config
        )
        metrics.record(evaluation)
        if not evaluation.allowed:
            continue
        if abs(evaluation.total_cost - cost) > 1e-12:
            heapq.heappush(heap, (evaluation.total_cost, left_id, right_id))
            continue
        new_id = apply_merge(
            graph,
            tree,
            left_id,
            right_id,
            raw_merge_cost=evaluation.total_cost,
            stage="hierarchy",
        )
        merge_count += 1
        for neighbor_id in sorted(graph.adjacency[new_id]):
            _push_hierarchy_candidate(
                heap,
                graph,
                new_id,
                neighbor_id,
                image_area=image_area,
                config=config,
                metrics=metrics,
            )
    return merge_count


def run_region_merge_from_graph(
    graph: RegionGraph,
    *,
    config: RegionMergeConfig | None = None,
) -> RegionMergeResult:
    config = config or RegionMergeConfig()
    validate_graph(graph)
    initial_labels = graph.initial_labels.copy()
    initial_region_count = len(graph.nodes)
    tree = build_initial_merge_tree(graph)
    metrics = _MergeMetricsCollector(initial_edge_count=len(graph.edges))
    image_area = int(initial_labels.size)

    safe_merge_count = run_safe_consolidation(
        graph,
        tree,
        image_area=image_area,
        config=config,
        metrics=metrics,
    )
    hierarchy_merge_count = run_hierarchical_merge(
        graph,
        tree,
        image_area=image_area,
        config=config,
        metrics=metrics,
    )
    validate_graph(graph)
    validate_merge_tree(tree)
    frozen_metrics = metrics.freeze(final_root_count=len(tree.roots))
    return RegionMergeResult(
        initial_labels=initial_labels,
        tree=tree,
        initial_region_count=initial_region_count,
        safe_merge_count=safe_merge_count,
        hierarchy_merge_count=hierarchy_merge_count,
        metrics=frozen_metrics,
    )


def run_region_merge(
    bundle: ImageBundle,
    *,
    annotations: dict[RegionId, RegionAnnotation] | None = None,
    config: RegionMergeConfig | None = None,
) -> RegionMergeResult:
    config = config or RegionMergeConfig()
    segmentation = oversegment(
        bundle,
        iterations=config.slic_iterations,
        edge_coverage_threshold=config.edge_coverage_threshold,
        retry_scale=config.retry_scale,
        max_retry_target_factor=config.max_retry_target_factor,
        provider=config.slic_provider,
    )
    graph = build_region_graph(
        bundle,
        segmentation.labels,
        annotations=annotations,
        gradient_bins=config.gradient_bins,
    )
    return run_region_merge_from_graph(graph, config=config)
