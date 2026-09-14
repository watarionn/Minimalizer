from dataclasses import asdict
import json
import math

import numpy as np
import pytest

from minimalize_engine.v2.types import CharacteristicSupport, RegionAnnotation
from minimalize_engine.v2.region_merge.cost import (
    RegionMergeConfig,
    boundary_cost,
    color_cost,
    evaluate_merge,
)
from minimalize_engine.v2.region_merge.graph import build_region_graph_from_arrays


def _two_region_graph(*, lab_left=(50, 0, 0), lab_right=(50, 0, 0), subject=None, confidence=None, alpha=None, annotations=None):
    labels = np.array([[0, 1]], dtype=np.int32)
    lab = np.zeros((1, 2, 3), dtype=np.float32)
    lab[0, 0] = lab_left
    lab[0, 1] = lab_right
    edge = np.zeros((1, 2), dtype=np.float32)
    return build_region_graph_from_arrays(
        labels, lab, edge, edge,
        subject_prob=subject,
        subject_confidence=confidence,
        alpha=alpha,
        annotations=annotations,
    )


def test_region_merge_config_is_json_serializable():
    payload = json.loads(json.dumps(asdict(RegionMergeConfig())))
    assert payload["color_tau"] == 25.0
    assert payload["safe_area_ratio"] == pytest.approx(0.0008)


def test_color_cost_matches_ward_formula():
    graph = _two_region_graph(lab_left=(10, 0, 0), lab_right=(20, 0, 0))
    left, right = graph.nodes[0], graph.nodes[1]
    expected_ec = ((1 * 1 / 2) * 100.0) / 2.0
    expected = 1.0 - math.exp(-expected_ec / 25.0)
    assert color_cost(left, right, tau=25.0) == pytest.approx(expected)


def test_boundary_cost_uses_structural_and_raw_quantiles():
    graph = _two_region_graph()
    edge = graph.edges[(0, 1)]
    assert boundary_cost(edge) == pytest.approx(0.0)


def test_subject_background_hard_barrier():
    subject = np.array([[1.0, 0.0]], dtype=np.float32)
    confidence = np.ones((1, 2), dtype=np.float32)
    graph = _two_region_graph(subject=subject, confidence=confidence)
    evaluation = evaluate_merge(
        graph.nodes[0], graph.nodes[1], graph.edges[(0, 1)],
        image_area=2, config=RegionMergeConfig(),
    )
    assert evaluation.allowed is False
    assert evaluation.total_cost == math.inf
    assert "subject_background" in evaluation.blocked_by


def test_alpha_hard_barrier():
    alpha = np.array([[0.0, 1.0]], dtype=np.float32)
    graph = _two_region_graph(alpha=alpha)
    evaluation = evaluate_merge(
        graph.nodes[0], graph.nodes[1], graph.edges[(0, 1)],
        image_area=2, config=RegionMergeConfig(),
    )
    assert evaluation.allowed is False
    assert "alpha" in evaluation.blocked_by


def test_characteristic_anchor_hard_barrier():
    annotations = {
        0: RegionAnnotation(characteristic_supports=(CharacteristicSupport(1, 1.0, 1.0),)),
        1: RegionAnnotation(characteristic_supports=(CharacteristicSupport(2, 1.0, 1.0),)),
    }
    graph = _two_region_graph(
        lab_left=(20, 0, 0), lab_right=(60, 0, 0), annotations=annotations
    )
    evaluation = evaluate_merge(
        graph.nodes[0], graph.nodes[1], graph.edges[(0, 1)],
        image_area=2, config=RegionMergeConfig(),
    )
    assert evaluation.allowed is False
    assert "characteristic_anchor" in evaluation.blocked_by


def test_semantic_hard_pair_barrier():
    annotations = {
        0: RegionAnnotation(semantic_tag="face", semantic_confidence=0.95),
        1: RegionAnnotation(semantic_tag="background", semantic_confidence=0.95),
    }
    graph = _two_region_graph(annotations=annotations)
    config = RegionMergeConfig(semantic_hard_pairs=(("face", "background"),))
    evaluation = evaluate_merge(
        graph.nodes[0], graph.nodes[1], graph.edges[(0, 1)],
        image_area=2, config=config,
    )
    assert evaluation.allowed is False
    assert "semantic" in evaluation.blocked_by


def test_strong_edge_alone_is_not_a_hard_barrier():
    labels = np.array([[0, 1]], dtype=np.int32)
    lab = np.full((1, 2, 3), (50, 0, 0), dtype=np.float32)
    edge_map = np.ones((1, 2), dtype=np.float32)
    graph = build_region_graph_from_arrays(labels, lab, edge_map, edge_map)
    evaluation = evaluate_merge(
        graph.nodes[0], graph.nodes[1], graph.edges[(0, 1)],
        image_area=2, config=RegionMergeConfig(),
    )
    assert evaluation.allowed is True
    assert evaluation.boundary_cost > 0.95
    assert evaluation.blocked_by == ()


def test_region_merge_config_rejects_negative_weights():
    with pytest.raises(ValueError, match="color_weight"):
        RegionMergeConfig(color_weight=-0.01)
