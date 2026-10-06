from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

SA10_REGRESSION_GATE_VERSION = "sa10-v1"


@dataclass(frozen=True)
class DiagnosticMetric:
    name: str
    status: str
    value: float | int | None
    detail: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ExpandedRegressionGateReport:
    version: str
    hard_gate_pass: bool
    hard_gate: Mapping[str, Any]
    diagnostics: tuple[DiagnosticMetric, ...]
    diagnostic_summary: Mapping[str, int]
    pass_gate: bool
    authoritative: bool = True
    diagnostics_can_override_hard_fail: bool = False

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "hard_gate": dict(self.hard_gate),
            "diagnostics": [x.to_dict() for x in self.diagnostics],
            "diagnostic_summary": dict(self.diagnostic_summary),
        }


def _metric(name: str, value: float | int | None, detail: str) -> DiagnosticMetric:
    return DiagnosticMetric(
        name=name,
        status="AVAILABLE" if value is not None else "UNAVAILABLE",
        value=value,
        detail=detail,
    )


def build_expanded_regression_gate(
    *,
    hard_gate: Mapping[str, Any],
    semantic_retention_score: float | None = None,
    adaptive_complexity_ratio: float | None = None,
    component_survival_ratio: float | None = None,
    primitive_economy_ratio: float | None = None,
    teacher_coverage_ratio: float | None = None,
    teacher_primitive_disagreements: int | None = None,
) -> ExpandedRegressionGateReport:
    """Wrap canonical hard-gate evidence with non-authoritative diagnostics.

    Diagnostics are intentionally unable to rescue or fail the canonical hard
    gate. Cross-case calibration is required before any diagnostic promotion.
    """
    if "pass_gate" not in hard_gate:
        raise ValueError("hard_gate must expose pass_gate")
    hard_pass = bool(hard_gate["pass_gate"])
    ratios = {
        "semantic_retention": semantic_retention_score,
        "adaptive_complexity": adaptive_complexity_ratio,
        "component_survival": component_survival_ratio,
        "primitive_economy": primitive_economy_ratio,
        "teacher_coverage": teacher_coverage_ratio,
    }
    for name, value in ratios.items():
        if value is not None and not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"{name} must be within [0, 1]")
    if teacher_primitive_disagreements is not None and teacher_primitive_disagreements < 0:
        raise ValueError("teacher_primitive_disagreements must be non-negative")

    diagnostics = (
        _metric("semantic_retention", semantic_retention_score, "CLIPasso/CLIPascene-inspired observer evidence"),
        _metric("adaptive_complexity", adaptive_complexity_ratio, "AdaVec-inspired budget utilization diagnostic"),
        _metric("component_survival", component_survival_ratio, "source-supported component survival diagnostic"),
        _metric("primitive_economy", primitive_economy_ratio, "Primitive/Geometrize-inspired economy diagnostic"),
        _metric("teacher_coverage", teacher_coverage_ratio, "SA9 evaluation-only teacher coverage"),
        _metric("teacher_primitive_disagreements", teacher_primitive_disagreements, "SA9 evaluation-only primitive-role disagreement count"),
    )
    available = sum(x.status == "AVAILABLE" for x in diagnostics)
    return ExpandedRegressionGateReport(
        version=SA10_REGRESSION_GATE_VERSION,
        hard_gate_pass=hard_pass,
        hard_gate=dict(hard_gate),
        diagnostics=diagnostics,
        diagnostic_summary={"available": available, "unavailable": len(diagnostics) - available},
        pass_gate=hard_pass,
    )
