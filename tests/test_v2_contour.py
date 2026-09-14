from __future__ import annotations

import numpy as np
import pytest

from minimalize_engine.v2.contour import (
    BoundaryChain, BoundaryGraph, BoundaryVertex, OrientedChainRef,
    ContourSimplificationConfig,
    build_boundary_graph,
    simplify_region_contours,
)
from minimalize_engine.v2.contour.validation import (
    candidate_chain_intersection_free,
    directional_limit_for_region,
    loops_have_self_intersection,
)
from minimalize_engine.v2.preprocessing import build_image_bundle
from minimalize_engine.v2.region_merge.graph import (
    build_initial_merge_tree,
    build_region_graph_from_arrays,
)
from minimalize_engine.v2.region_merge.types import (
    HierarchyCut,
    RegionMergeMetrics,
    RegionMergeResult,
    RegionSelection,
)
from minimalize_engine.v2.types import CharacteristicSupport, RegionAnnotation


def _result_and_selection(
    labels: np.ndarray,
    *,
    preset: str = "detailed",
    annotations: dict[int, RegionAnnotation] | None = None,
):
    height, width = labels.shape
    image = np.zeros((height, width, 3), dtype=np.uint8)
    bundle = build_image_bundle(image, analysis_max_side=max(height, width))
    graph = build_region_graph_from_arrays(
        labels,
        bundle.analysis_lab,
        bundle.edge_raw,
        bundle.edge_structural,
        annotations=annotations,
    )
    tree = build_initial_merge_tree(graph)
    region_ids = frozenset(int(value) for value in np.unique(labels))
    metrics = RegionMergeMetrics(
        initial_edge_count=len(graph.edges),
        evaluation_count=0,
        blocked_evaluation_count=0,
        safe_candidate_count=0,
        final_root_count=len(region_ids),
    )
    result = RegionMergeResult(
        initial_labels=labels,
        tree=tree,
        initial_region_count=len(region_ids),
        safe_merge_count=0,
        hierarchy_merge_count=0,
        metrics=metrics,
    )
    cut = HierarchyCut(
        preset=preset,
        selected_ids=region_ids,
        region_count=len(region_ids),
        visual_loss=0.0,
        normalized_visual_loss=0.0,
        objective=0.0,
        max_selected_hierarchy_height=0.0,
    )
    selection = RegionSelection(
        preset=preset,
        cut=cut,
        labels=labels,
        region_ids=region_ids,
    )
    return bundle, result, selection


def test_boundary_graph_reuses_one_shared_chain_for_both_regions():
    labels = np.array(
        [[0, 0, 0, 1, 1, 1]] * 4,
        dtype=np.int32,
    )
    bundle, result, selection = _result_and_selection(labels)
    graph = build_boundary_graph(
        bundle, result, selection, config=ContourSimplificationConfig()
    )
    shared = [chain for chain in graph.chains.values() if chain.regions == (0, 1)]
    assert len(shared) == 1
    chain_id = shared[0].id
    refs0 = [ref for ref in graph.region_chains[0] if ref.chain_id == chain_id]
    refs1 = [ref for ref in graph.region_chains[1] if ref.chain_id == chain_id]
    assert len(refs0) == len(refs1) == 1
    assert refs0[0].reversed is not refs1[0].reversed


def test_contour_simplification_reduces_grid_vertices_without_region_loss():
    labels = np.array(
        [[0, 0, 0, 1, 1, 1]] * 4,
        dtype=np.int32,
    )
    bundle, result, selection = _result_and_selection(labels)
    output = simplify_region_contours(
        bundle, result, selection, config=ContourSimplificationConfig()
    )
    assert set(output.contours) == {0, 1}
    assert output.metrics.simplified_vertex_count < output.metrics.original_vertex_count
    assert output.metrics.min_region_iou == pytest.approx(1.0)
    assert output.metrics.max_area_change == pytest.approx(0.0)
    assert all(contour.area_px == 12 for contour in output.contours.values())


def test_characteristic_conflict_protects_shared_boundary_chain():
    labels = np.array([[0, 0, 1, 1]] * 3, dtype=np.int32)
    annotations = {
        0: RegionAnnotation(
            characteristic_supports=(CharacteristicSupport(1, 6.0, 0.95),)
        ),
        1: RegionAnnotation(
            characteristic_supports=(CharacteristicSupport(2, 6.0, 0.95),)
        ),
    }
    bundle, result, selection = _result_and_selection(labels, annotations=annotations)
    graph = build_boundary_graph(
        bundle, result, selection, config=ContourSimplificationConfig()
    )
    shared = next(chain for chain in graph.chains.values() if chain.regions == (0, 1))
    assert shared.protected is True
    assert "characteristic_boundary" in shared.protection_reasons


def test_face_directional_limit_is_stricter_than_generic_limit():
    labels = np.array([[0, 0], [0, 0]], dtype=np.int32)
    annotations = {
        0: RegionAnnotation(semantic_tag="face", semantic_confidence=0.95)
    }
    _, result, _ = _result_and_selection(labels, annotations=annotations)
    config = ContourSimplificationConfig(max_directional_loss=0.20)
    limit = directional_limit_for_region(result, 0, labels.size, config)
    assert limit == pytest.approx(0.20 * 0.65)


def test_self_intersection_guard_detects_bow_tie_polygon():
    loop = np.asarray(
        [[0.0, 0.0], [4.0, 4.0], [0.0, 4.0], [4.0, 0.0]],
        dtype=np.float32,
    )
    assert loops_have_self_intersection((loop,)) is True


def test_hole_topology_survives_simplification():
    labels = np.zeros((9, 9), dtype=np.int32)
    labels[2:7, 2:7] = 1
    labels[3:6, 3:6] = 0
    bundle, result, selection = _result_and_selection(labels)
    output = simplify_region_contours(
        bundle, result, selection, config=ContourSimplificationConfig()
    )
    assert set(output.contours) == {0, 1}
    assert output.metrics.min_region_iou >= 0.90
    assert len(output.contours[1].loops) == 2


def test_incremental_intersection_guard_distinguishes_touch_from_overlap():
    vertices = {
        0: BoundaryVertex(0, 0.0, 0.0),
        1: BoundaryVertex(1, 4.0, 4.0),
    }
    chains = {
        0: BoundaryChain(0, 0, 1, np.array([[0, 0], [4, 0], [4, 4]], np.float32), (0,)),
        1: BoundaryChain(1, 1, 0, np.array([[4, 4], [0, 4], [0, 0]], np.float32), (0,)),
    }
    graph = BoundaryGraph(
        vertices=vertices,
        chains=chains,
        region_chains={0: [OrientedChainRef(0, False), OrientedChainRef(1, False)]},
    )
    safe = {0: chains[0].points.copy(), 1: chains[1].points.copy()}
    assert candidate_chain_intersection_free(graph, 0, 0, safe) is True

    overlap = dict(safe)
    overlap[0] = np.array([[0, 0], [0, 4], [4, 4]], dtype=np.float32)
    assert candidate_chain_intersection_free(graph, 0, 0, overlap) is False
