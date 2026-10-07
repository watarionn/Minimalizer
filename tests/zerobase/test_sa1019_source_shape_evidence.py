import numpy as np

from minimalizer_zerobase.evaluation.source_shape_evidence import (
    evaluate_source_shape_evidence, generate_vtracer_candidate,
    vtracer_backend_status, rasterize_source_bound_svg,
    evaluate_source_bound_candidate,
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


def test_sa1026_vtracer_requires_authorized_semantic_mask_and_is_explicit_noop():
    source = np.zeros((16, 16), np.uint8)
    source[4:12, 4:12] = 1
    result = generate_vtracer_candidate(source, source.copy())
    assert result["candidate_authority"] is False
    assert result["visible_output_changed"] is False
    assert result["status"] in {"unavailable", "no-op", "fallback_noop"}
    assert "source_mask_sha256" in result


def test_sa1026_vtracer_rejects_semantic_pixels_outside_immutable_source():
    source = np.zeros((8, 8), np.uint8)
    authorized = np.zeros_like(source)
    authorized[0, 0] = 1
    result = generate_vtracer_candidate(source, authorized)
    assert result == {
        **result,
        "status": "no-op",
        "reason": "authorized_mask_outside_immutable_source",
    }


def test_sa1026_backend_status_isolated_without_parent_import():
    status = vtracer_backend_status()
    assert status["isolated"] is True
    assert status["license_boundary"] == "MIT OR Apache-2.0"


def test_sa1026_worker_nonzero_is_fallback_noop(monkeypatch):
    import subprocess
    from minimalizer_zerobase.refine import vtracer_subprocess
    class Completed:
        returncode = 17
        stderr = "native crash"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Completed())
    result = vtracer_subprocess.run_vtracer_isolated(np.ones((4, 4), np.uint8))
    assert result["status"] == "fallback_noop"
    assert result["reason"] == "nonzero"
    assert result["isolated"] is True


def test_sa1026_tiny_synthetic_svg_subset_is_deterministic_and_source_bound():
    svg = '<svg width="32" height="32"><path fill="#fff" transform="translate(2 1)" d="M 2 2 L 20 2 C 25 2 25 20 20 20 L 2 20 Z"/></svg>'
    first = rasterize_source_bound_svg(svg, (32, 32))
    second = rasterize_source_bound_svg(svg, (32, 32))
    assert np.array_equal(first, second)
    source = np.zeros((32, 32), np.uint8); source[3:22, 4:28] = 1
    report = evaluate_source_bound_candidate(source, first)
    assert report["iou"] > 0
    assert report["candidate_components"] == 1
    assert report["authority"] is False


def test_sa1026_svg_rejects_non_boundary_transform():
    with __import__('pytest').raises(ValueError, match="unsupported transform"):
        rasterize_source_bound_svg('<svg><path fill="red" transform="scale(2)" d="M0 0 L2 0 L2 2 Z"/></svg>', (8, 8))
