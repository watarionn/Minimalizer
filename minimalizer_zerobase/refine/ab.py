from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from minimalizer_zerobase.refine.objective import LossBreakdown, AcceptancePolicy, accept_candidate

@dataclass(frozen=True)
class ABCase:
    case_id: str
    before: LossBreakdown
    after: LossBreakdown
    identity_ratio: float
    silhouette_ratio: float
    regional_guard: bool
    deterministic: bool
    runtime_ratio: float = 1.0

@dataclass(frozen=True)
class ABDecision:
    case_count: int
    accepted: int
    rejected: int
    improved: int
    regressed: int
    guard_failures: int
    deterministic: bool
    mean_objective_delta: float
    decision: str

def _dimension_regressed(row: ABCase) -> bool:
    # Composite gains may not hide regressions in identity-bearing soft dimensions.
    return (row.after.silhouette > row.before.silhouette
            or row.after.palette > row.before.palette
            or row.after.semantic > row.before.semantic
            or row.after.tiny_shape > row.before.tiny_shape
            or row.after.complexity > row.before.complexity
            or row.after.primitive_count > row.before.primitive_count)

def evaluate_ab(cases: Iterable[ABCase], *, policy: AcceptancePolicy = AcceptancePolicy()) -> ABDecision:
    rows=tuple(cases)
    if not rows:
        raise ValueError("A/B corpus is empty")
    accepted=improved=regressed=guard_failures=0
    deltas=[]
    for row in rows:
        delta=row.before.total-row.after.total
        deltas.append(delta)
        improved += int(delta > 0)
        dimension_regression=_dimension_regressed(row)
        regressed += int(delta < 0 or dimension_regression)
        guards = row.regional_guard and row.deterministic and not dimension_regression
        ok = guards and accept_candidate(before=row.before, after=row.after,
                                         identity_ratio=row.identity_ratio,
                                         silhouette_ratio=row.silhouette_ratio,
                                         policy=policy)
        accepted += int(ok)
        guard_failures += int(not guards or row.identity_ratio < policy.min_identity_ratio
                              or row.silhouette_ratio < policy.min_silhouette_ratio)
    deterministic=all(x.deterministic for x in rows)
    mean_delta=sum(deltas)/len(deltas)
    decision=("ADOPT" if deterministic and guard_failures == 0 and regressed == 0
              and accepted == len(rows) and mean_delta > 0 else "HOLD")
    return ABDecision(len(rows),accepted,len(rows)-accepted,improved,regressed,
                      guard_failures,deterministic,mean_delta,decision)
