from __future__ import annotations
from dataclasses import dataclass
from .evaluation import ABMetrics,ABResult,Decision,evaluate_ab
from .combined_evidence import ObserverEvidence,CombinedEvidenceResult,compare_observer_evidence,EvidenceTrend
from .semantic_ownership import OwnershipRetention

@dataclass(frozen=True)
class CandidateGateResult:
    decision: Decision
    hard_gate: ABResult
    observer_gate: CombinedEvidenceResult
    ownership_gate: OwnershipRetention | None
    reasons: tuple[str,...]

def evaluate_candidate(
    baseline_metrics: ABMetrics,
    candidate_metrics: ABMetrics,
    baseline_observers: ObserverEvidence,
    candidate_observers: ObserverEvidence,
    *,
    ownership: OwnershipRetention | None = None,
) -> CandidateGateResult:
    neutral_baseline=ABMetrics(objective=baseline_metrics.objective,identity_ratio=baseline_metrics.identity_ratio,silhouette_ratio=baseline_metrics.silhouette_ratio,regional_retention={},regional_spatial_iou={},deterministic=baseline_metrics.deterministic,runtime_ms=baseline_metrics.runtime_ms)
    neutral_candidate=ABMetrics(objective=candidate_metrics.objective,identity_ratio=candidate_metrics.identity_ratio,silhouette_ratio=candidate_metrics.silhouette_ratio,regional_retention={},regional_spatial_iou={},deterministic=candidate_metrics.deterministic,runtime_ms=candidate_metrics.runtime_ms)
    hard=evaluate_ab(neutral_baseline,neutral_candidate,critical_regions=())
    observers=compare_observer_evidence(baseline_observers,candidate_observers)
    reasons=list(hard.reasons)
    if ownership is None: reasons.append("renderer semantic ownership evidence unavailable")
    else: reasons.extend(ownership.reasons)
    # Grounded-SAM abstraction is diagnostic only. Record its reasons but do not veto.
    reasons.extend(observers.reasons)
    if hard.decision is Decision.REJECT:
        decision=Decision.REJECT
    elif hard.decision is Decision.HOLD or ownership is None:
        decision=Decision.HOLD
    elif not ownership.passed:
        decision=Decision.REJECT
    elif observers.dino is EvidenceTrend.REGRESSED:
        decision=Decision.REJECT
    elif observers.dino is EvidenceTrend.UNAVAILABLE:
        decision=Decision.HOLD
    else:
        decision=Decision.ADOPT
    return CandidateGateResult(decision,hard,observers,ownership,tuple(reasons))
