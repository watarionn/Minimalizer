from __future__ import annotations
from dataclasses import dataclass
from .evaluation import ABMetrics,ABResult,Decision,evaluate_ab
from .combined_evidence import ObserverEvidence,CombinedEvidenceResult,compare_observer_evidence,observer_evidence_allows_adoption

@dataclass(frozen=True)
class CandidateGateResult:
    decision: Decision
    hard_gate: ABResult
    observer_gate: CombinedEvidenceResult
    reasons: tuple[str,...]

def evaluate_candidate(
    baseline_metrics: ABMetrics,
    candidate_metrics: ABMetrics,
    baseline_observers: ObserverEvidence,
    candidate_observers: ObserverEvidence,
) -> CandidateGateResult:
    # Raw cross-style spatial IoU is deliberately not promoted here. The existing
    # AB evaluator receives neutral observer-presence placeholders so its
    # identity/silhouette/objective/determinism contract remains authoritative.
    neutral_baseline=ABMetrics(
        objective=baseline_metrics.objective,identity_ratio=baseline_metrics.identity_ratio,
        silhouette_ratio=baseline_metrics.silhouette_ratio,regional_retention={},
        regional_spatial_iou={},deterministic=baseline_metrics.deterministic,runtime_ms=baseline_metrics.runtime_ms)
    neutral_candidate=ABMetrics(
        objective=candidate_metrics.objective,identity_ratio=candidate_metrics.identity_ratio,
        silhouette_ratio=candidate_metrics.silhouette_ratio,regional_retention={},
        regional_spatial_iou={},deterministic=candidate_metrics.deterministic,runtime_ms=candidate_metrics.runtime_ms)
    hard=evaluate_ab(neutral_baseline,neutral_candidate,critical_regions=())
    observers=compare_observer_evidence(baseline_observers,candidate_observers)
    reasons=list(hard.reasons)+list(observers.reasons)
    if hard.decision is Decision.REJECT:
        decision=Decision.REJECT
    elif hard.decision is Decision.HOLD:
        decision=Decision.HOLD
    elif not observer_evidence_allows_adoption(observers):
        decision=Decision.REJECT if (
            observers.dino.value=="REGRESSED" or observers.abstraction.value=="REGRESSED"
        ) else Decision.HOLD
    else:
        decision=Decision.ADOPT
    return CandidateGateResult(decision,hard,observers,tuple(reasons))
