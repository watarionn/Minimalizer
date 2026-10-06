from __future__ import annotations

import pytest

from minimalizer_zerobase.evaluation.expanded_regression_gate import (
    build_expanded_regression_gate,
)


def test_diagnostics_cannot_rescue_hard_failure():
    report = build_expanded_regression_gate(
        hard_gate={"pass_gate": False, "survival_pass": False, "forbidden_face_pass": True},
        semantic_retention_score=1.0,
        adaptive_complexity_ratio=1.0,
        component_survival_ratio=1.0,
        primitive_economy_ratio=1.0,
        teacher_coverage_ratio=1.0,
        teacher_primitive_disagreements=0,
    )
    assert report.pass_gate is False
    assert report.hard_gate_pass is False
    assert report.diagnostics_can_override_hard_fail is False


def test_bad_diagnostics_cannot_fail_passing_hard_gate():
    report = build_expanded_regression_gate(
        hard_gate={"pass_gate": True, "survival_pass": True, "forbidden_face_pass": True},
        semantic_retention_score=0.0,
        adaptive_complexity_ratio=0.0,
        component_survival_ratio=0.0,
        primitive_economy_ratio=0.0,
        teacher_coverage_ratio=0.0,
        teacher_primitive_disagreements=99,
    )
    assert report.pass_gate is True
    assert report.hard_gate["survival_pass"] is True
    assert report.hard_gate["forbidden_face_pass"] is True


def test_missing_diagnostics_stay_visible():
    report = build_expanded_regression_gate(hard_gate={"pass_gate": True})
    assert report.diagnostic_summary == {"available": 0, "unavailable": 6}
    assert all(x.status == "UNAVAILABLE" for x in report.diagnostics)


def test_gc001_sa9_teacher_diagnostic_is_not_a_gate():
    report = build_expanded_regression_gate(
        hard_gate={"pass_gate": True},
        teacher_coverage_ratio=0.25,
        teacher_primitive_disagreements=0,
    )
    by_name = {x.name: x for x in report.diagnostics}
    assert by_name["teacher_coverage"].value == 0.25
    assert by_name["teacher_primitive_disagreements"].value == 0
    assert report.pass_gate is True


@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_ratio_diagnostics_are_bounded(value):
    with pytest.raises(ValueError):
        build_expanded_regression_gate(
            hard_gate={"pass_gate": True},
            teacher_coverage_ratio=value,
        )


def test_hard_gate_contract_is_required():
    with pytest.raises(ValueError):
        build_expanded_regression_gate(hard_gate={})
