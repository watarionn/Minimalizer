from __future__ import annotations

from minimalizer_zerobase.evaluation.gc001_regression_assembly import (
    build_gc001_regression_artifact,
)


def _inputs():
    return dict(
        hard_gate={
            "version": "sa7.35-v2",
            "survival_pass": True,
            "required_signature_count": 16,
            "missing_count": 0,
            "forbidden_face_detail_ratio": 0.0,
            "forbidden_face_pass": True,
            "pass_gate": True,
        },
        adaptive_budget={
            "version": "sa7.43-v1",
            "global_cap": 5,
            "allocated_total": 4,
            "unallocated": 1,
        },
        semantic_retention={
            "version": "sa7.45-v1",
            "observer": "dinov3",
            "semantic_retention_score": 0.729867,
            "authoritative": False,
            "can_override_hard_fail": False,
        },
        teacher_evaluation={
            "authority": {
                "production_input_allowed": False,
                "production_output_changed": False,
            },
            "coverage_diagnostic": {
                "coverage_ratio": 0.25,
                "primitive_disagreements": 0,
            },
        },
    )


def test_gc001_assembly_uses_only_available_evidence():
    artifact = build_gc001_regression_artifact(**_inputs())
    report = artifact["regression_gate"]
    by_name = {x["name"]: x for x in report["diagnostics"]}
    assert report["pass_gate"] is True
    assert by_name["semantic_retention"]["value"] == 0.729867
    assert by_name["adaptive_complexity"]["value"] == 0.8
    assert by_name["teacher_coverage"]["value"] == 0.25
    assert by_name["component_survival"]["status"] == "UNAVAILABLE"
    assert by_name["primitive_economy"]["status"] == "UNAVAILABLE"


def test_gc001_assembly_is_deterministic():
    assert build_gc001_regression_artifact(**_inputs()) == build_gc001_regression_artifact(**_inputs())


def test_hard_failure_cannot_be_rescued_by_diagnostics():
    values = _inputs()
    values["hard_gate"] = {**values["hard_gate"], "pass_gate": False}
    artifact = build_gc001_regression_artifact(**values)
    assert artifact["regression_gate"]["pass_gate"] is False
