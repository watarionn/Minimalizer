from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from minimalizer_zerobase.semantic_abstraction.semantic_golden_teacher import (
    GoldenDecisionLabel,
    SemanticGoldenTeacherReport,
)


TEACHER_COVERAGE_DIAGNOSTIC_VERSION = "sa9.3-v1"


@dataclass(frozen=True)
class TeacherCoverageDiagnostic:
    total_roles: int
    labeled_roles: int
    unresolved_roles: int
    coverage_ratio: float
    decision_histogram: dict[str, int]
    comparable_primitive_roles: int
    primitive_disagreements: int
    semantic_retention_observed_roles: int
    authoritative: bool = False
    can_override_hard_fail: bool = False
    production_input_allowed: bool = False
    production_output_changed: bool = False
    version: str = TEACHER_COVERAGE_DIAGNOSTIC_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "total_roles": self.total_roles,
            "labeled_roles": self.labeled_roles,
            "unresolved_roles": self.unresolved_roles,
            "coverage_ratio": self.coverage_ratio,
            "decision_histogram": dict(self.decision_histogram),
            "comparable_primitive_roles": self.comparable_primitive_roles,
            "primitive_disagreements": self.primitive_disagreements,
            "semantic_retention_observed_roles": self.semantic_retention_observed_roles,
            "authoritative": False,
            "can_override_hard_fail": False,
            "production_input_allowed": False,
            "production_output_changed": False,
            "interpretation": {
                "coverage_is_quality_score": False,
                "coverage_is_gate": False,
                "disagreement_is_gate": False,
            },
        }


def build_teacher_coverage_diagnostic(
    report: SemanticGoldenTeacherReport,
) -> TeacherCoverageDiagnostic:
    """Summarize teacher evidence availability without creating authority."""
    if report.authoritative:
        raise ValueError("teacher report must remain non-authoritative")
    if report.production_input_allowed:
        raise ValueError("teacher report cannot be a production input")
    if report.production_output_changed:
        raise ValueError("teacher report must not change production output")

    total = len(report.roles)
    if total == 0:
        raise ValueError("teacher coverage requires at least one role")

    labeled = [row for row in report.roles if row.golden_decision is not None]
    histogram = Counter(row.golden_decision.value for row in labeled)

    comparable = [
        row for row in labeled if row.golden_advisor_agreement is not None
    ]
    disagreements = sum(
        row.golden_advisor_agreement is False for row in comparable
    )
    retention_observed = sum(
        row.semantic_retention is not None for row in report.roles
    )

    return TeacherCoverageDiagnostic(
        total_roles=total,
        labeled_roles=len(labeled),
        unresolved_roles=total - len(labeled),
        coverage_ratio=len(labeled) / total,
        decision_histogram={
            label.value: histogram.get(label.value, 0)
            for label in GoldenDecisionLabel
        },
        comparable_primitive_roles=len(comparable),
        primitive_disagreements=disagreements,
        semantic_retention_observed_roles=retention_observed,
    )
