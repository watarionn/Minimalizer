from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class EvidenceTrend(str, Enum):
    IMPROVED="IMPROVED"
    STABLE="STABLE"
    REGRESSED="REGRESSED"
    UNAVAILABLE="UNAVAILABLE"


@dataclass(frozen=True)
class ObserverEvidence:
    dino_score: float | None = None
    abstraction_scores: Mapping[str,float] | None = None


@dataclass(frozen=True)
class CombinedEvidenceResult:
    dino: EvidenceTrend
    abstraction: EvidenceTrend
    reasons: tuple[str,...]


def _trend(before: float | None, after: float | None, tolerance: float) -> EvidenceTrend:
    if before is None or after is None:
        return EvidenceTrend.UNAVAILABLE
    delta=after-before
    if delta > tolerance:
        return EvidenceTrend.IMPROVED
    if delta < -tolerance:
        return EvidenceTrend.REGRESSED
    return EvidenceTrend.STABLE


def compare_observer_evidence(
    baseline: ObserverEvidence,
    candidate: ObserverEvidence,
    *,
    dino_tolerance: float = 0.01,
    abstraction_tolerance: float = 0.02,
    critical_regions: tuple[str,...] = ("hair","face-skin","limb","accessory"),
) -> CombinedEvidenceResult:
    dino=_trend(baseline.dino_score,candidate.dino_score,dino_tolerance)
    reasons=[]
    if baseline.abstraction_scores is None or candidate.abstraction_scores is None:
        abstraction=EvidenceTrend.UNAVAILABLE
    else:
        trends=[]
        for label in critical_regions:
            before=baseline.abstraction_scores.get(label)
            after=candidate.abstraction_scores.get(label)
            trend=_trend(before,after,abstraction_tolerance)
            trends.append(trend)
            if trend is EvidenceTrend.REGRESSED:
                reasons.append(f"{label} abstraction evidence regressed")
        if EvidenceTrend.REGRESSED in trends:
            abstraction=EvidenceTrend.REGRESSED
        elif EvidenceTrend.IMPROVED in trends:
            abstraction=EvidenceTrend.IMPROVED
        elif trends and all(t is EvidenceTrend.STABLE for t in trends):
            abstraction=EvidenceTrend.STABLE
        else:
            abstraction=EvidenceTrend.UNAVAILABLE
    if dino is EvidenceTrend.REGRESSED:
        reasons.append("DINO spatial evidence regressed")
    if dino is EvidenceTrend.UNAVAILABLE:
        reasons.append("DINO spatial evidence unavailable")
    if abstraction is EvidenceTrend.UNAVAILABLE:
        reasons.append("abstraction spatial evidence unavailable")
    return CombinedEvidenceResult(dino,abstraction,tuple(reasons))


def observer_evidence_allows_adoption(result: CombinedEvidenceResult) -> bool:
    """Observers can veto or hold, but cannot override identity/silhouette hard guards."""
    if result.dino in (EvidenceTrend.REGRESSED,EvidenceTrend.UNAVAILABLE):
        return False
    if result.abstraction is EvidenceTrend.REGRESSED:
        return False
    return True
