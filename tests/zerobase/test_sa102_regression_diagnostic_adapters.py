from __future__ import annotations

from dataclasses import replace

import pytest

from minimalizer_zerobase.evaluation.regression_diagnostic_adapters import (
    ComponentSurvivalEvidence,
    PrimitiveEconomyEvidence,
    adaptive_complexity_value,
    assemble_expanded_regression_gate,
    component_survival_value,
    primitive_economy_value,
    teacher_values,
)
from minimalizer_zerobase.semantic_abstraction.adaptive_primitive_budget import (
    AdaptivePrimitiveBudget,
)
from minimalizer_zerobase.semantic_abstraction.teacher_coverage_diagnostic import (
    TeacherCoverageDiagnostic,
)


def _teacher():
    return TeacherCoverageDiagnostic(
        total_roles=8,
        labeled_roles=2,
        unresolved_roles=6,
        coverage_ratio=0.25,
        decision_histogram={"REAUTHORED": 2},
        comparable_primitive_roles=0,
        primitive_disagreements=0,
        semantic_retention_observed_roles=0,
    )


def test_gc001_teacher_values_flow_into_envelope_without_gate_authority():
    report = assemble_expanded_regression_gate(
        hard_gate={"pass_gate": True, "survival_pass": True},
        teacher_diagnostic=_teacher(),
    )
    by_name = {x.name: x for x in report.diagnostics}
    assert by_name["teacher_coverage"].value == 0.25
    assert by_name["teacher_primitive_disagreements"].value == 0
    assert report.pass_gate is True
    assert report.diagnostics_can_override_hard_fail is False


def test_teacher_boundary_violation_fails_closed():
    with pytest.raises(ValueError):
        teacher_values(replace(_teacher(), production_input_allowed=True))


def test_adaptive_budget_maps_to_utilization_not_quality():
    budget = AdaptivePrimitiveBudget(
        global_cap=8,
        allocated_total=6,
        unallocated=2,
        entries=(),
    )
    assert adaptive_complexity_value(budget) == 0.75


def test_zero_adaptive_cap_is_unavailable():
    budget = AdaptivePrimitiveBudget(
        global_cap=0,
        allocated_total=0,
        unallocated=0,
        entries=(),
    )
    assert adaptive_complexity_value(budget) is None


def test_component_survival_is_explicit_evidence_ratio():
    assert component_survival_value(
        ComponentSurvivalEvidence(source_components=5, surviving_components=4)
    ) == 0.8
    with pytest.raises(ValueError):
        component_survival_value(
            ComponentSurvivalEvidence(source_components=4, surviving_components=5)
        )


def test_primitive_economy_reports_supported_share_of_emitted_primitives():
    assert primitive_economy_value(
        PrimitiveEconomyEvidence(supported_primitives=4, emitted_primitives=5)
    ) == 0.8
    assert primitive_economy_value(
        PrimitiveEconomyEvidence(supported_primitives=0, emitted_primitives=0)
    ) == 1.0


def test_missing_evidence_stays_unavailable():
    report = assemble_expanded_regression_gate(hard_gate={"pass_gate": False})
    assert report.pass_gate is False
    assert report.diagnostic_summary == {"available": 0, "unavailable": 6}
