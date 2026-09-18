from __future__ import annotations

from dataclasses import asdict, dataclass

PERFORMANCE_BUDGET_SCHEMA_VERSION = "minimalizer-v2-performance-budget-v1"


@dataclass(frozen=True, slots=True)
class PerformanceBudget:
    case_count: int = 5
    repeats: int = 2
    confirmation_batches: int = 3
    max_analysis_side: int = 400
    web_workers: int = 1
    max_concurrent_jobs: int = 2
    mean_v2_seconds_max: float = 5.0
    max_case_v2_seconds_max: float = 5.5
    mean_case_ratio_max: float = 7.0
    max_case_ratio_max: float = 9.0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PerformanceMeasurement:
    mean_legacy_seconds: float
    mean_v2_seconds: float
    max_case_v2_seconds: float
    mean_case_ratio: float
    max_case_ratio: float
    case_count: int
    repeats: int
    analysis_max_side: int = 400
    web_workers: int = 1
    max_concurrent_jobs: int = 2


@dataclass(frozen=True, slots=True)
class PerformanceBudgetEvaluation:
    schema_version: str
    passed: bool
    checks: tuple[tuple[str, bool], ...]
    budget: PerformanceBudget
    measurement: PerformanceMeasurement

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "passed": self.passed,
            "checks": {name: passed for name, passed in self.checks},
            "budget": self.budget.to_dict(),
            "measurement": asdict(self.measurement),
        }


def evaluate_performance_budget(
    measurement: PerformanceMeasurement,
    budget: PerformanceBudget = PerformanceBudget(),
) -> PerformanceBudgetEvaluation:
    checks = (
        ("case_count", measurement.case_count == budget.case_count),
        ("repeats", measurement.repeats == budget.repeats),
        ("analysis_max_side", measurement.analysis_max_side <= budget.max_analysis_side),
        ("web_workers", measurement.web_workers <= budget.web_workers),
        ("max_concurrent_jobs", measurement.max_concurrent_jobs <= budget.max_concurrent_jobs),
        ("mean_v2_seconds", measurement.mean_v2_seconds <= budget.mean_v2_seconds_max),
        ("max_case_v2_seconds", measurement.max_case_v2_seconds <= budget.max_case_v2_seconds_max),
        ("mean_case_ratio", measurement.mean_case_ratio <= budget.mean_case_ratio_max),
        ("max_case_ratio", measurement.max_case_ratio <= budget.max_case_ratio_max),
    )
    return PerformanceBudgetEvaluation(
        schema_version=PERFORMANCE_BUDGET_SCHEMA_VERSION,
        passed=all(passed for _, passed in checks),
        checks=checks,
        budget=budget,
        measurement=measurement,
    )
