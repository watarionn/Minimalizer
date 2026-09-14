import numpy as np
import pytest

from minimalize_engine.v2.region_merge.graph import (
    apply_merge,
    build_initial_merge_tree,
    build_region_graph,
    build_region_stats,
    merge_region_edges,
    merge_region_stats,
    validate_graph,
)
from minimalize_engine.v2.region_merge.types import RegionEdge


def _fixture():
    labels = np.array(
        [
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [2, 2, 1, 1],
            [2, 2, 2, 2],
        ],
        dtype=np.int32,
    )
    lab = np.zeros((4, 4, 3), dtype=np.float32)
    lab[labels == 0] = (10, 1, 2)
    lab[labels == 1] = (40, 4, 5)
    lab[labels == 2] = (70, 7, 8)
    raw = np.zeros((4, 4), dtype=np.float32)
    structural = np.zeros((4, 4), dtype=np.float32)
    raw[:, 1:3] = 0.8
    structural[:, 1:3] = 0.5
    return labels, lab, raw, structural


def test_region_stats_generation_uses_pixel_centers_and_exclusive_bbox():
    labels, lab, _, _ = _fixture()
    stats = build_region_stats(labels, lab)
    assert stats[0].pixel_count == 4
    assert stats[0].bbox == (0, 0, 2, 2)
    assert stats[0].centroid == pytest.approx((1.0, 1.0))
    assert stats[0].mean_lab == pytest.approx(np.array([10.0, 1.0, 2.0]))
    assert stats[0].lab_sse == pytest.approx(0.0)
    assert stats[0].perimeter_px == pytest.approx(8.0)
    assert stats[0].hull_area == pytest.approx(4.0)


def test_rag_construction_is_symmetric_and_builds_histograms():
    labels, lab, raw, structural = _fixture()
    graph = build_region_graph(labels, lab, raw, structural)
    validate_graph(graph)
    assert graph.adjacency[0] == {1, 2}
    assert graph.adjacency[1] == {0, 2}
    assert graph.adjacency[2] == {0, 1}
    assert set(graph.edges) == {(0, 1), (0, 2), (1, 2)}
    edge = graph.edges[(0, 1)]
    assert edge.shared_boundary_px == pytest.approx(2.0)
    assert int(edge.raw_gradient_hist.sum()) == 2
    assert int(edge.structural_gradient_hist.sum()) == 2
    assert edge.raw_gradient_hist.shape == (32,)


def test_merge_region_stats_preserves_additive_statistics_and_perimeter():
    labels, lab, raw, structural = _fixture()
    graph = build_region_graph(labels, lab, raw, structural)
    merged = merge_region_stats(
        graph.nodes[0],
        graph.nodes[1],
        new_region_id=3,
        shared_boundary_px=graph.edges[(0, 1)].shared_boundary_px,
    )
    assert merged.id == 3
    assert merged.pixel_count == 10
    assert merged.sum_lab == pytest.approx(
        graph.nodes[0].sum_lab + graph.nodes[1].sum_lab
    )
    assert merged.perimeter_px == pytest.approx(
        graph.nodes[0].perimeter_px + graph.nodes[1].perimeter_px - 4.0
    )


def test_merge_region_edges_adds_histograms_and_boundary_weighted_alpha():
    a = RegionEdge(0, 2, 2.0, np.array([1, 1]), np.array([0, 2]), 0.25)
    b = RegionEdge(1, 2, 3.0, np.array([2, 1]), np.array([1, 2]), 0.75)
    merged = merge_region_edges([a, b], new_region_id=3, neighbor_id=2)
    assert (merged.a, merged.b) == (2, 3)
    assert merged.shared_boundary_px == pytest.approx(5.0)
    assert merged.raw_gradient_hist.tolist() == [3, 2]
    assert merged.structural_gradient_hist.tolist() == [1, 4]
    assert merged.alpha_boundary_fraction == pytest.approx(0.55)


def test_apply_merge_uses_monotonic_ids_keeps_labels_immutable_and_updates_tree():
    labels, lab, raw, structural = _fixture()
    graph = build_region_graph(labels, lab, raw, structural)
    tree = build_initial_merge_tree(graph)
    initial_copy = graph.initial_labels.copy()

    first = apply_merge(graph, tree, 0, 1, raw_merge_cost=0.2, stage="safe")
    validate_graph(graph)
    assert first == 3
    assert graph.next_region_id == 4
    assert tree.nodes[first].hierarchy_height == pytest.approx(0.2)
    assert tree.roots == {2, 3}
    assert np.array_equal(graph.initial_labels, initial_copy)
    assert graph.initial_labels.flags.writeable is False
    with pytest.raises(ValueError):
        graph.initial_labels[0, 0] = 9

    second = apply_merge(
        graph,
        tree,
        2,
        3,
        raw_merge_cost=0.1,
        stage="hierarchy",
    )
    validate_graph(graph)
    assert second == 4
    assert graph.next_region_id == 5
    assert tree.nodes[second].hierarchy_height == pytest.approx(0.2)
    assert tree.roots == {4}
    assert tree.merge_sequence == [3, 4]
