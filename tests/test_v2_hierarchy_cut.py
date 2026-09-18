import numpy as np
import pytest

from minimalize_engine.v2.region_merge.cost import RegionMergeConfig
from minimalize_engine.v2.region_merge.cut import (
    build_cut_family,
    cumulative_visual_loss,
    materialize_region_selection,
    validate_cut_family,
)
from minimalize_engine.v2.region_merge.graph import (
    apply_merge,
    build_initial_merge_tree,
    build_region_graph_from_arrays,
)
from minimalize_engine.v2.region_merge.hierarchy import run_region_merge_from_graph
from minimalize_engine.v2.region_merge.types import (
    CutPolicy,
    RegionMergeMetrics,
    RegionMergeResult,
)


def _two_leaf_result(raw_cost: float = 0.25) -> RegionMergeResult:
    labels = np.array([[0, 1]], dtype=np.int32)
    lab = np.zeros((1, 2, 3), dtype=np.float32)
    edge = np.zeros((1, 2), dtype=np.float32)
    graph = build_region_graph_from_arrays(labels, lab, edge, edge)
    tree = build_initial_merge_tree(graph)
    apply_merge(graph, tree, 0, 1, raw_merge_cost=raw_cost, stage="hierarchy")
    metrics = RegionMergeMetrics(
        initial_edge_count=1,
        evaluation_count=0,
        blocked_evaluation_count=0,
        safe_candidate_count=0,
        final_root_count=1,
    )
    return RegionMergeResult(
        initial_labels=labels,
        tree=tree,
        initial_region_count=2,
        safe_merge_count=0,
        hierarchy_merge_count=1,
        metrics=metrics,
    )


def _stripe_result(count: int = 8) -> RegionMergeResult:
    labels = np.arange(count, dtype=np.int32)[None, :]
    lab = np.zeros((1, count, 3), dtype=np.float32)
    edge = np.zeros((1, count), dtype=np.float32)
    graph = build_region_graph_from_arrays(labels, lab, edge, edge)
    return run_region_merge_from_graph(graph, config=RegionMergeConfig())

def test_cumulative_visual_loss_matches_merge_formula():
    result = _two_leaf_result(raw_cost=0.25)
    policy = CutPolicy(1, 1, 1.0, 0.0)
    losses = cumulative_visual_loss(
        result.tree, total_pixels=result.initial_labels.size, policy=policy
    )
    root_id = next(iter(result.tree.roots))
    assert losses[0] == 0.0
    assert losses[1] == 0.0
    assert losses[root_id] == pytest.approx(0.25)


def test_height_guard_overrides_region_target():
    result = _two_leaf_result(raw_cost=0.90)
    policies = {
        "detailed": CutPolicy(1, 1, 0.50, 10.0, target_weight=10.0),
        "balanced": CutPolicy(1, 1, 0.60, 10.0, target_weight=10.0),
        "minimal": CutPolicy(1, 1, 0.70, 10.0, target_weight=10.0),
        "ultra_minimal": CutPolicy(1, 1, 0.80, 10.0, target_weight=10.0),
    }
    family = build_cut_family(result, policies=policies)
    assert [family.detailed.region_count, family.balanced.region_count,
            family.minimal.region_count, family.ultra_minimal.region_count] == [2, 2, 2, 2]

def test_nested_cut_family_and_materialization_are_deterministic():
    result = _stripe_result(8)
    policies = {
        "detailed": CutPolicy(4, 4, 1.35, 1.0, target_weight=10.0),
        "balanced": CutPolicy(3, 3, 1.35, 1.0, target_weight=10.0),
        "minimal": CutPolicy(2, 2, 1.35, 1.0, target_weight=10.0),
        "ultra_minimal": CutPolicy(1, 1, 1.35, 1.0, target_weight=10.0),
    }
    first = build_cut_family(result, policies=policies)
    second = build_cut_family(result, policies=policies)
    validate_cut_family(result, first)
    assert [first.detailed.region_count, first.balanced.region_count,
            first.minimal.region_count, first.ultra_minimal.region_count] == [4, 3, 2, 1]
    assert first == second

    cuts = (first.detailed, first.balanced, first.minimal, first.ultra_minimal)
    selections = [materialize_region_selection(result, cut) for cut in cuts]
    assert [len(np.unique(item.labels)) for item in selections] == [4, 3, 2, 1]
    assert all(item.labels.flags.writeable is False for item in selections)
    for finer, coarser in zip(selections, selections[1:]):
        for region_id in finer.region_ids:
            mask = finer.labels == region_id
            assert np.unique(coarser.labels[mask]).size == 1

def test_cut_policy_mapping_is_explicit_and_ordered():
    result = _stripe_result(4)
    with pytest.raises(ValueError, match="missing cut policies"):
        build_cut_family(result, policies={})
    bad = {
        "detailed": CutPolicy(2, 3, 0.40, 1.0),
        "balanced": CutPolicy(3, 3, 0.55, 1.0),
        "minimal": CutPolicy(1, 2, 0.70, 1.0),
        "ultra_minimal": CutPolicy(1, 1, 0.85, 1.0),
    }
    with pytest.raises(ValueError, match="target_min"):
        build_cut_family(result, policies=bad)

def test_hard_barrier_forest_cannot_be_coarsened_to_target_one():
    labels = np.array([[0, 1]], dtype=np.int32)
    lab = np.zeros((1, 2, 3), dtype=np.float32)
    edge = np.zeros((1, 2), dtype=np.float32)
    alpha = np.array([[0.0, 1.0]], dtype=np.float32)
    graph = build_region_graph_from_arrays(labels, lab, edge, edge, alpha=alpha)
    result = run_region_merge_from_graph(graph, config=RegionMergeConfig())
    assert len(result.tree.roots) == 2
    policies = {
        name: CutPolicy(1, 1, height, 10.0, target_weight=10.0)
        for name, height in zip(
            ("detailed", "balanced", "minimal", "ultra_minimal"),
            (0.40, 0.55, 0.70, 0.85),
        )
    }
    family = build_cut_family(result, policies=policies)
    assert [family.detailed.region_count, family.balanced.region_count,
            family.minimal.region_count, family.ultra_minimal.region_count] == [2, 2, 2, 2]
