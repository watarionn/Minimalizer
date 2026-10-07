from __future__ import annotations

import copy

import pytest

from minimalizer_zerobase.evaluation.gc001_complete_regression_artifact import (
    build_complete_gc001_regression_artifact,
)


def _inputs():
    return {
        "hard_gate": {
            "version": "sa7.35-v2",
            "survival_pass": True,
            "required_signature_count": 16,
            "missing_count": 0,
            "missing_signatures": [],
            "forbidden_face_detail_ratio": 0.0,
            "forbidden_face_pass": True,
            "pass_gate": True,
        },
        "adaptive_budget": {
            "version": "sa7.43-v1",
            "global_cap": 5,
            "allocated_total": 4,
            "unallocated": 1,
        },
        "semantic_retention": {
            "version": "sa7.45-v1",
            "semantic_retention_score": 0.7298672763136121,
            "authoritative": False,
            "can_override_hard_fail": False,
        },
        "teacher_evaluation": {
            "authority": {
                "production_input_allowed": False,
                "production_output_changed": False,
            },
            "coverage_diagnostic": {
                "coverage_ratio": 0.25,
                "primitive_disagreements": 0,
            },
        },
        "component_economy": {
            "version": "sa10.4-v1",
            "authoritative": False,
            "source_components": 9,
            "represented_components": 4,
            "component_survival_ratio": 4 / 9,
            "emitted_primitives": 4,
            "source_supported_primitives": 4,
            "primitive_economy_ratio": 1.0,
        },
    }


def test_complete_gc001_has_all_six_diagnostics_available():
    artifact = build_complete_gc001_regression_artifact(**_inputs())
    diagnostics = {d["name"]: d for d in artifact["regression_gate"]["diagnostics"]}
    assert all(d["status"] == "AVAILABLE" for d in diagnostics.values())
    assert diagnostics["semantic_retention"]["value"] == pytest.approx(0.7298672763136121)
    assert diagnostics["adaptive_complexity"]["value"] == pytest.approx(0.8)
    assert diagnostics["component_survival"]["value"] == pytest.approx(4 / 9)
    assert diagnostics["primitive_economy"]["value"] == pytest.approx(1.0)
    assert diagnostics["teacher_coverage"]["value"] == pytest.approx(0.25)
    assert diagnostics["teacher_primitive_disagreements"]["value"] == 0


def test_complete_gc001_is_deterministic():
    values = _inputs()
    assert build_complete_gc001_regression_artifact(**values) == build_complete_gc001_regression_artifact(**values)


def test_diagnostics_cannot_rescue_hard_failure():
    values = copy.deepcopy(_inputs())
    values["hard_gate"]["pass_gate"] = False
    artifact = build_complete_gc001_regression_artifact(**values)
    assert artifact["regression_gate"]["pass_gate"] is False


def test_authoritative_component_evidence_fails_closed():
    values = copy.deepcopy(_inputs())
    values["component_economy"]["authoritative"] = True
    with pytest.raises(ValueError):
        build_complete_gc001_regression_artifact(**values)


def test_canonical_semantic_observer_bundle_uses_candidate():
    values = _inputs()
    report = values["semantic_retention"]
    values["semantic_retention"] = {
        "observer_contract": "sa7.45-v1",
        "production_output_changed": False,
        "baseline_stage": "SA7.43",
        "candidate_stage": "SA7.44",
        "baseline": {**report, "semantic_retention_score": 0.7290167936939369},
        "candidate": report,
        "delta": 0.0008504826196752413,
        "hard_gate_override_allowed": False,
    }
    artifact = build_complete_gc001_regression_artifact(**values)
    diagnostics = {d["name"]: d for d in artifact["regression_gate"]["diagnostics"]}
    assert diagnostics["semantic_retention"]["value"] == pytest.approx(0.7298672763136121)
