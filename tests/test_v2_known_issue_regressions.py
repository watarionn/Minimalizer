from __future__ import annotations

import math

import numpy as np

from minimalize_engine.v2.regression import RegressionConfig, run_regression_case
from minimalize_engine.v2.region_merge.cost import RegionMergeConfig, evaluate_merge
from minimalize_engine.v2.region_merge.graph import build_region_graph_from_arrays
from minimalize_engine.v2.types import CharacteristicSupport, RegionAnnotation


def _two_region_graph(*, annotations=None, subject=None, confidence=None):
    labels = np.asarray([[0, 1]], dtype=np.int32)
    lab = np.asarray([[[55.0, 8.0, 12.0], [56.0, 9.0, 13.0]]], dtype=np.float32)
    edge = np.zeros((1, 2), dtype=np.float32)
    return build_region_graph_from_arrays(
        labels,
        lab,
        edge,
        edge,
        annotations=annotations,
        subject_prob=subject,
        subject_confidence=confidence,
    )


def _evaluate(graph, config=None):
    return evaluate_merge(
        graph.nodes[0], graph.nodes[1], graph.edges[(0, 1)],
        image_area=2, config=config or RegionMergeConfig(),
    )


def test_known_issue_face_right_gouge_keeps_contour_iou_guard():
    image = np.full((64, 64, 3), (240, 150, 190), dtype=np.uint8)
    image[14:52, 18:46] = (245, 220, 205)
    image[24:38, 46:53] = (245, 220, 205)
    result = run_regression_case(
        image,
        regression_config=RegressionConfig(artifact_level="none", main_preset="minimal"),
        code_revision="known-issue-test",
    )
    assert result.metrics.contour_iou >= 0.90
    assert not result.invariant_failures


def test_known_issue_thin_rectangle_noise_does_not_survive_minimal_cut():
    image = np.full((64, 64, 3), 240, dtype=np.uint8)
    image[12:52, 18:46] = (220, 80, 120)
    image[8:56, 5:6] = (20, 20, 20)
    result = run_regression_case(
        image,
        regression_config=RegressionConfig(artifact_level="none", main_preset="minimal"),
        code_revision="known-issue-test",
    )
    assert result.metrics.thin_region_ratio == 0.0
    assert not result.invariant_failures


def test_known_issue_characteristic_accent_loss_hits_hard_barrier():
    annotations = {
        0: RegionAnnotation(characteristic_supports=(CharacteristicSupport(1, 1.0, 0.98),)),
        1: RegionAnnotation(characteristic_supports=(CharacteristicSupport(2, 1.0, 0.98),)),
    }
    evaluation = _evaluate(_two_region_graph(annotations=annotations))
    assert evaluation.allowed is False
    assert evaluation.total_cost == math.inf
    assert "characteristic_anchor" in evaluation.blocked_by


def test_known_issue_hair_skin_color_collapse_respects_semantic_hard_pair():
    annotations = {
        0: RegionAnnotation(semantic_tag="face", semantic_confidence=0.97),
        1: RegionAnnotation(semantic_tag="hair", semantic_confidence=0.97),
    }
    config = RegionMergeConfig(semantic_hard_pairs=(("face", "hair"),))
    evaluation = _evaluate(_two_region_graph(annotations=annotations), config)
    assert evaluation.allowed is False
    assert "semantic" in evaluation.blocked_by


def test_known_issue_subject_background_leakage_hits_hard_barrier():
    subject = np.asarray([[0.98, 0.02]], dtype=np.float32)
    confidence = np.asarray([[0.98, 0.98]], dtype=np.float32)
    evaluation = _evaluate(
        _two_region_graph(subject=subject, confidence=confidence)
    )
    assert evaluation.allowed is False
    assert evaluation.total_cost == math.inf
    assert "subject_background" in evaluation.blocked_by
