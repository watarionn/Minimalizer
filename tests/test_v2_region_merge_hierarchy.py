import numpy as np

from minimalize_engine.v2.region_merge.cost import RegionMergeConfig
from minimalize_engine.v2.region_merge.graph import build_region_graph_from_arrays, validate_merge_tree
from minimalize_engine.v2.preprocessing import build_image_bundle
from minimalize_engine.v2.region_merge.hierarchy import run_region_merge, run_region_merge_from_graph


def _chain_graph(*, alpha=None):
    labels = np.array([[0, 1, 2]], dtype=np.int32)
    lab = np.zeros((1, 3, 3), dtype=np.float32)
    lab[0, 0] = (20, 0, 0)
    lab[0, 1] = (22, 0, 0)
    lab[0, 2] = (80, 0, 0)
    edge = np.zeros((1, 3), dtype=np.float32)
    return build_region_graph_from_arrays(labels, lab, edge, edge, alpha=alpha)


def test_hierarchy_merges_connected_graph_to_one_root_without_barriers():
    result = run_region_merge_from_graph(_chain_graph(), config=RegionMergeConfig())
    validate_merge_tree(result.tree)
    assert result.initial_region_count == 3
    assert result.safe_merge_count == 0
    assert result.hierarchy_merge_count == 2
    assert len(result.tree.roots) == 1
    assert result.initial_labels.flags.writeable is False


def test_alpha_barrier_leaves_a_forest():
    alpha = np.array([[0.0, 0.0, 1.0]], dtype=np.float32)
    result = run_region_merge_from_graph(_chain_graph(alpha=alpha), config=RegionMergeConfig())
    validate_merge_tree(result.tree)
    assert result.hierarchy_merge_count == 1
    assert len(result.tree.roots) == 2
    assert dict(result.metrics.barrier_counts)["alpha"] >= 1


def test_safe_consolidation_absorbs_only_obvious_tiny_fragment():
    labels = np.ones((40, 40), dtype=np.int32)
    labels[20, 20] = 0
    lab = np.zeros((40, 40, 3), dtype=np.float32)
    lab[:] = (50, 0, 0)
    edge = np.zeros((40, 40), dtype=np.float32)
    graph = build_region_graph_from_arrays(labels, lab, edge, edge)
    result = run_region_merge_from_graph(graph, config=RegionMergeConfig())
    validate_merge_tree(result.tree)
    assert result.safe_merge_count == 1
    assert result.hierarchy_merge_count == 0
    merged_id = result.tree.merge_sequence[0]
    assert result.tree.nodes[merged_id].stage == "safe"


def test_region_merge_is_deterministic_for_same_graph_and_config():
    first = run_region_merge_from_graph(_chain_graph(), config=RegionMergeConfig())
    second = run_region_merge_from_graph(_chain_graph(), config=RegionMergeConfig())
    assert first.tree.merge_sequence == second.tree.merge_sequence
    assert [first.tree.nodes[node].raw_merge_cost for node in first.tree.merge_sequence] == [
        second.tree.nodes[node].raw_merge_cost for node in second.tree.merge_sequence
    ]


def test_public_run_region_merge_builds_shared_hierarchy_end_to_end():
    image = np.zeros((32, 48, 3), dtype=np.uint8)
    image[:, :24] = (210, 60, 50)
    image[:, 24:] = (55, 80, 210)
    bundle = build_image_bundle(image, analysis_max_side=48)
    config = RegionMergeConfig(edge_coverage_threshold=0.0)
    result = run_region_merge(bundle, config=config)
    validate_merge_tree(result.tree)
    assert result.initial_region_count > 1
    assert result.safe_merge_count + result.hierarchy_merge_count == len(result.tree.merge_sequence)
    assert result.metrics.final_root_count == len(result.tree.roots)
    assert result.initial_labels.dtype == np.int32
    assert result.initial_labels.flags.writeable is False


def test_safe_consolidation_is_line_neutral():
    labels = np.ones((40, 40), dtype=np.int32)
    labels[20, 20] = 0
    lab = np.zeros((40, 40, 3), dtype=np.float32)
    lab[:] = (50, 0, 0)
    structural = np.zeros((40, 40), dtype=np.float32)
    structural[20, 20] = 0.05
    no_line = np.zeros((40, 40), dtype=np.float32)
    full_line = np.ones((40, 40), dtype=np.float32)
    config = RegionMergeConfig(line_prior_strength=1.0)

    baseline = run_region_merge_from_graph(
        build_region_graph_from_arrays(labels, lab, structural, structural, line_support=no_line),
        config=config,
    )
    guided = run_region_merge_from_graph(
        build_region_graph_from_arrays(labels, lab, structural, structural, line_support=full_line),
        config=config,
    )

    assert baseline.safe_merge_count == guided.safe_merge_count == 1
    baseline_safe = [baseline.tree.nodes[i].raw_merge_cost for i in baseline.tree.merge_sequence if baseline.tree.nodes[i].stage == "safe"]
    guided_safe = [guided.tree.nodes[i].raw_merge_cost for i in guided.tree.merge_sequence if guided.tree.nodes[i].stage == "safe"]
    assert guided_safe == baseline_safe
