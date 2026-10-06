from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from minimalizer_zerobase.evaluation.expanded_regression_gate import (
    ExpandedRegressionGateReport,
    build_expanded_regression_gate,
)
from minimalizer_zerobase.semantic_abstraction.adaptive_primitive_budget import (
    AdaptivePrimitiveBudget,
)
from minimalizer_zerobase.semantic_abstraction.semantic_retention_observer import (
    SemanticRetentionReport,
)
from minimalizer_zerobase.semantic_abstraction.teacher_coverage_diagnostic import (
    TeacherCoverageDiagnostic,
)

SA10_DIAGNOSTIC_ADAPTER_VERSION = "sa10.2-v1"


@dataclass(frozen=True)
class ComponentSurvivalEvidence:
    source_components: int
    surviving_components: int
    authoritative: bool = False


@dataclass(frozen=True)
class PrimitiveEconomyEvidence:
    supported_primitives: int
    emitted_primitives: int
    authoritative: bool = False


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator < 0 or numerator < 0:
        raise ValueError("diagnostic counts must be non-negative")
    if numerator > denominator:
        raise ValueError("diagnostic numerator cannot exceed denominator")
    if denominator == 0:
        return None
    return numerator / denominator


def semantic_retention_value(report: SemanticRetentionReport | None) -> float | None:
    if report is None:
        return None
    if report.authoritative or report.can_override_hard_fail:
        raise ValueError("semantic retention observer must remain non-authoritative")
    return report.semantic_retention_score


def adaptive_complexity_value(budget: AdaptivePrimitiveBudget | None) -> float | None:
    if budget is None or budget.global_cap == 0:
        return None
    return budget.allocated_total / budget.global_cap


def component_survival_value(
    evidence: ComponentSurvivalEvidence | None,
) -> float | None:
    if evidence is None:
        return None
    if evidence.authoritative:
        raise ValueError("component survival evidence is diagnostic-only")
    return _ratio(evidence.surviving_components, evidence.source_components)


def primitive_economy_value(
    evidence: PrimitiveEconomyEvidence | None,
) -> float | None:
    if evidence is None:
        return None
    if evidence.authoritative:
        raise ValueError("primitive economy evidence is diagnostic-only")
    if evidence.emitted_primitives == 0:
        return 1.0 if evidence.supported_primitives == 0 else None
    if evidence.supported_primitives > evidence.emitted_primitives:
        raise ValueError("supported primitives cannot exceed emitted primitives")
    return evidence.supported_primitives / evidence.emitted_primitives


def teacher_values(
    diagnostic: TeacherCoverageDiagnostic | None,
) -> tuple[float | None, int | None]:
    if diagnostic is None:
        return None, None
    if (
        diagnostic.authoritative
        or diagnostic.can_override_hard_fail
        or diagnostic.production_input_allowed
        or diagnostic.production_output_changed
    ):
        raise ValueError("teacher diagnostic crossed evaluation-only boundary")
    return diagnostic.coverage_ratio, diagnostic.primitive_disagreements


def assemble_expanded_regression_gate(
    *,
    hard_gate: Mapping[str, Any],
    semantic_retention: SemanticRetentionReport | None = None,
    adaptive_budget: AdaptivePrimitiveBudget | None = None,
    component_survival: ComponentSurvivalEvidence | None = None,
    primitive_economy: PrimitiveEconomyEvidence | None = None,
    teacher_diagnostic: TeacherCoverageDiagnostic | None = None,
) -> ExpandedRegressionGateReport:
    teacher_coverage, teacher_disagreements = teacher_values(teacher_diagnostic)
    return build_expanded_regression_gate(
        hard_gate=hard_gate,
        semantic_retention_score=semantic_retention_value(semantic_retention),
        adaptive_complexity_ratio=adaptive_complexity_value(adaptive_budget),
        component_survival_ratio=component_survival_value(component_survival),
        primitive_economy_ratio=primitive_economy_value(primitive_economy),
        teacher_coverage_ratio=teacher_coverage,
        teacher_primitive_disagreements=teacher_disagreements,
    )
