import numpy as np

from minimalizer_zerobase.evaluation.source_shape_evidence import (
    evaluate_source_shape_evidence, vtracer_backend_status,
)


def test_sa1019_identical_synthetic_shape_matches_exactly():
    source = np.zeros((64, 64), np.uint8)
    source[12:52, 20:44] = 1
    report = evaluate_source_shape_evidence(source, source.copy())
    assert report["available"] is True
    assert report["match_shapes_i1"] == 0.0
    assert report["authority"]["shape_matching"] is False


def test_sa1019_shape_evidence_is_not_a_structural_override():
    source = np.zeros((64, 64), np.uint8)
    source[12:52, 20:44] = 1
    candidate = np.zeros_like(source)
    candidate[10:54, 18:46] = 1
    report = evaluate_source_shape_evidence(source, candidate)
    assert report["authority"]["source_anatomy"] is True
    assert report["authority"]["shape_matching"] is False


def test_vtracer_is_optional_and_license_bounded():
    status = vtracer_backend_status()
    assert status["optional"] is True
    assert status["license_boundary"] == "MIT OR Apache-2.0"
