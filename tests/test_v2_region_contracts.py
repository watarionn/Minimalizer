import numpy as np
import pytest

from minimalize_engine.v2.types import (
    CharacteristicSupport,
    ImageBundle,
    RegionAnnotation,
)
from minimalize_engine.v2.region_merge.graph import (
    apply_merge,
    build_initial_merge_tree,
    build_region_graph,
    validate_graph,
    validate_merge_tree,
)
from minimalize_engine.v2.region_merge.types import MergeTreeNode, RegionEdge


def _graph_fixture():
    labels = np.array([[0, 0, 1], [0, 2, 1], [2, 2, 1]], dtype=np.int32)
    lab = np.zeros((3, 3, 3), dtype=np.float32)
    lab[labels == 0] = (10, 1, 2)
    lab[labels == 1] = (40, 4, 5)
    lab[labels == 2] = (70, 7, 8)
    raw = np.zeros((3, 3), dtype=np.float32)
    structural = np.zeros((3, 3), dtype=np.float32)
    return build_region_graph(labels, lab, raw, structural)


def test_image_bundle_enforces_analysis_shape_and_core_dtypes():
    source = np.zeros((4, 6, 3), dtype=np.uint8)
    rgb = np.zeros((2, 3, 3), dtype=np.uint8)
    lab = np.zeros((2, 3, 3), dtype=np.float32)
    edge = np.zeros((2, 3), dtype=np.float32)
    bundle = ImageBundle(source, rgb, rgb.copy(), lab, lab.copy(), edge, edge.copy(), scale_x=2.0, scale_y=2.0)
    assert bundle.analysis_rgb.shape == (2, 3, 3)
    with pytest.raises(ValueError):
        ImageBundle(source, rgb, rgb.copy(), lab.astype(np.float64), lab.copy(), edge, edge.copy())
    with pytest.raises(ValueError):
        ImageBundle(source, rgb, np.zeros((2, 4, 3), dtype=np.uint8), lab, lab.copy(), edge, edge.copy())


def test_characteristic_support_and_annotation_reject_invalid_contracts():
    with pytest.raises(ValueError):
        CharacteristicSupport(anchor_id=0, support_mass=-1.0, confidence=0.5)
    with pytest.raises(ValueError):
        CharacteristicSupport(anchor_id=0, support_mass=1.0, confidence=1.1)
    support = CharacteristicSupport(anchor_id=2, support_mass=3.0, confidence=0.8)
    with pytest.raises(ValueError):
        RegionAnnotation(characteristic_supports=(support, support))
    with pytest.raises(ValueError):
        RegionAnnotation(semantic_tag=None, semantic_confidence=0.5)


def test_region_edge_rejects_invalid_histograms_and_alpha_fraction():
    with pytest.raises(ValueError):
        RegionEdge(0, 1, 2.0, np.array([1, -1]), np.array([0, 0]), 0.0)
    with pytest.raises(ValueError):
        RegionEdge(0, 1, 2.0, np.array([1, 1]), np.array([2, 1]), 0.0)
    with pytest.raises(ValueError):
        RegionEdge(0, 1, 2.0, np.array([1, 1]), np.array([1, 1]), 1.01)


def test_apply_merge_rejects_invalid_metadata_without_mutating_graph():
    graph = _graph_fixture()
    tree = build_initial_merge_tree(graph)
    before_nodes = set(graph.nodes)
    before_roots = set(tree.roots)
    with pytest.raises(ValueError):
        apply_merge(graph, tree, 0, 1, raw_merge_cost=float('nan'), stage='safe')
    with pytest.raises(ValueError):
        apply_merge(graph, tree, 0, 1, raw_merge_cost=-0.1, stage='safe')
    with pytest.raises(ValueError):
        apply_merge(graph, tree, 0, 1, raw_merge_cost=0.1, stage='')
    assert set(graph.nodes) == before_nodes
    assert tree.roots == before_roots


def test_merge_tree_validation_accepts_forest_and_checks_monotonic_structure():
    graph = _graph_fixture()
    tree = build_initial_merge_tree(graph)
    validate_merge_tree(tree)
    merged = apply_merge(graph, tree, 0, 1, raw_merge_cost=0.3, stage='safe')
    validate_graph(graph)
    validate_merge_tree(tree)
    assert tree.roots == {2, merged}
    root = apply_merge(graph, tree, 2, merged, raw_merge_cost=0.1, stage='hierarchy')
    validate_merge_tree(tree)
    node = tree.nodes[root]
    tree.nodes[root] = MergeTreeNode(
        region_id=node.region_id,
        left_id=node.left_id,
        right_id=node.right_id,
        raw_merge_cost=node.raw_merge_cost,
        hierarchy_height=0.2,
        stage=node.stage,
        stats=node.stats,
    )
    with pytest.raises(ValueError, match='monotonic'):
        validate_merge_tree(tree)
