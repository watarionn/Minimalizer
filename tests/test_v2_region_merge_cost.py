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
    geometry_cost,
    pose_relation_cost,
)
from minimalize_engine.v2.region_merge.graph import (
    build_region_graph_from_arrays,
    merge_region_stats,
)


def _two_region_graph(
    *,
    lab_left=(50, 0, 0),
    lab_right=(50, 0, 0),
    subject=None,
    confidence=None,
    alpha=None,
    line_support=None,
    structural_edge=None,
    raw_edge=None,
    annotations=None,
):
    labels = np.array([[0, 1]], dtype=np.int32)
    lab = np.zeros((1, 2, 3), dtype=np.float32)
    lab[0, 0] = lab_left
    lab[0, 1] = lab_right
    edge = np.zeros((1, 2), dtype=np.float32)
    structural_edge = edge if structural_edge is None else structural_edge
    raw_edge = edge if raw_edge is None else raw_edge
    return build_region_graph_from_arrays(
        labels, lab, raw_edge, structural_edge,
        subject_prob=subject,
        subject_confidence=confidence,
        alpha=alpha,
        line_support=line_support,
        annotations=annotations,
    )


def test_region_merge_config_is_json_serializable():
    payload = json.loads(json.dumps(asdict(RegionMergeConfig())))
    assert payload["color_tau"] == 25.0
    assert payload["safe_area_ratio"] == pytest.approx(0.0008)
    assert payload["pose_relation_weight"] == pytest.approx(0.0)
    assert payload["line_prior_strength"] == pytest.approx(0.0)


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


def test_line_prior_requires_structural_consensus():
    line_support = np.ones((1, 2), dtype=np.float32)
    graph = _two_region_graph(line_support=line_support)
    edge = graph.edges[(0, 1)]

    assert edge.line_support_mean == pytest.approx(1.0)
    assert boundary_cost(edge, line_prior_strength=0.0) == pytest.approx(0.0)
    assert boundary_cost(edge, line_prior_strength=0.55) == pytest.approx(0.0)


def test_line_prior_amplifies_structural_boundary_monotonically_and_bounded():
    line_support = np.ones((1, 2), dtype=np.float32)
    structural = np.full((1, 2), 0.4, dtype=np.float32)
    graph = _two_region_graph(line_support=line_support, structural_edge=structural)
    edge = graph.edges[(0, 1)]
    base = boundary_cost(edge, line_prior_strength=0.0)
    weak = boundary_cost(edge, line_prior_strength=0.25)
    strong = boundary_cost(edge, line_prior_strength=0.55)

    assert base > 0.0
    assert base <= weak <= strong <= 1.0
    assert strong == pytest.approx(base + 0.55 * edge.line_support_mean * base * (1.0 - base))


def test_raw_only_boundary_gets_no_line_bonus():
    line_support = np.ones((1, 2), dtype=np.float32)
    raw = np.ones((1, 2), dtype=np.float32)
    graph = _two_region_graph(line_support=line_support, raw_edge=raw)
    edge = graph.edges[(0, 1)]
    assert boundary_cost(edge, line_prior_strength=0.55) == pytest.approx(
        boundary_cost(edge, line_prior_strength=0.0)
    )


def test_pose_relation_cost_only_protects_distinct_known_structures():
    distinct = {
        0: RegionAnnotation(structure_tag="torso", structure_confidence=0.8),
        1: RegionAnnotation(structure_tag="left_upper_arm", structure_confidence=0.6),
    }
    same = {
        0: RegionAnnotation(structure_tag="torso", structure_confidence=0.8),
        1: RegionAnnotation(structure_tag="torso", structure_confidence=0.6),
    }

    distinct_graph = _two_region_graph(annotations=distinct)
    same_graph = _two_region_graph(annotations=same)

    assert pose_relation_cost(
        distinct_graph.nodes[0], distinct_graph.nodes[1]
    ) == pytest.approx(0.6)
    assert pose_relation_cost(
        same_graph.nodes[0], same_graph.nodes[1]
    ) == pytest.approx(0.0)


def test_geometry_cost_matches_full_merged_stats_reference():
    graph = _two_region_graph(lab_left=(30, 4, -2), lab_right=(55, -3, 6))
    left, right = graph.nodes[0], graph.nodes[1]
    edge = graph.edges[(0, 1)]
    candidate = merge_region_stats(
        left,
        right,
        new_region_id=2,
        shared_boundary_px=edge.shared_boundary_px,
    )
    base_hull = max(1e-12, left.hull_area + right.hull_area)
    inflation = max(0.0, candidate.hull_area - base_hull) / base_hull
    expected = float(np.clip(1.0 - math.exp(-inflation / 0.25), 0.0, 1.0))
    assert geometry_cost(left, right, edge, tau=0.25) == expected


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


def test_soft_priors_raise_cost_only_when_explicitly_enabled():
    annotations = {
        0: RegionAnnotation(structure_tag="torso", structure_confidence=0.8),
        1: RegionAnnotation(structure_tag="left_upper_arm", structure_confidence=0.8),
    }
    line_support = np.ones((1, 2), dtype=np.float32)
    structural = np.full((1, 2), 0.4, dtype=np.float32)
    graph = _two_region_graph(
        annotations=annotations,
        line_support=line_support,
        structural_edge=structural,
    )
    left, right = graph.nodes[0], graph.nodes[1]
    edge = graph.edges[(0, 1)]

    baseline = evaluate_merge(
        left,
        right,
        edge,
        image_area=2,
        config=RegionMergeConfig(major_mass_weight=0.0, accent_weight=0.0),
    )
    guided = evaluate_merge(
        left,
        right,
        edge,
        image_area=2,
        config=RegionMergeConfig(
            major_mass_weight=0.0,
            accent_weight=0.0,
            pose_relation_weight=0.06,
            line_prior_strength=0.55,
        ),
    )

    assert baseline.allowed is True
    assert guided.allowed is True
    assert baseline.soft_protection == pytest.approx(0.0)
    assert guided.soft_protection == pytest.approx(0.048)
    assert baseline.boundary_cost > 0.0
    assert guided.boundary_cost > baseline.boundary_cost
    assert guided.total_cost > baseline.total_cost
    assert guided.blocked_by == ()


def test_region_merge_config_rejects_invalid_prior_weights():
    with pytest.raises(ValueError, match="color_weight"):
        RegionMergeConfig(color_weight=-0.01)
    with pytest.raises(ValueError, match="pose_relation_weight"):
        RegionMergeConfig(pose_relation_weight=1.01)
    with pytest.raises(ValueError, match="line_prior_strength"):
        RegionMergeConfig(line_prior_strength=-0.01)
