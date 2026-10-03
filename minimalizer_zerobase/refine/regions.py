from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Protocol

@dataclass(frozen=True)
class RegionObservation:
    label: str
    coverage: float
    confidence: float = 1.0
    def __post_init__(self):
        if not self.label: raise ValueError("region label is required")
        if not 0.0 <= self.coverage <= 1.0: raise ValueError("coverage must be in [0, 1]")
        if not 0.0 <= self.confidence <= 1.0: raise ValueError("confidence must be in [0, 1]")

class RegionObserver(Protocol):
    """Observation-only segmentation boundary. It has no pixel/Scene mutation API."""
    name: str
    def observe(self, image: object) -> tuple[RegionObservation, ...]: ...

@dataclass(frozen=True)
class RegionGuardPolicy:
    min_confidence: float = 0.5
    min_retention: float = 0.94
    critical_labels: tuple[str, ...] = ("subject", "hair", "clothes", "object")

def regional_retention(reference: tuple[RegionObservation, ...], candidate: tuple[RegionObservation, ...],
                       *, policy: RegionGuardPolicy = RegionGuardPolicy()) -> dict[str, float]:
    ref={r.label:r for r in reference if r.confidence >= policy.min_confidence}
    cand={r.label:r for r in candidate if r.confidence >= policy.min_confidence}
    result={}
    for label,r in ref.items():
        if label not in cand: result[label]=0.0; continue
        result[label]=max(0.0,min(1.0,cand[label].coverage/max(r.coverage,1e-9)))
    return result

def regional_guard_passes(retention: Mapping[str,float], *, policy: RegionGuardPolicy = RegionGuardPolicy()) -> bool:
    return all(retention.get(label,0.0) >= policy.min_retention
               for label in policy.critical_labels if label in retention)

def weighted_regional_loss(losses: Mapping[str,float], weights: Mapping[str,float]) -> float:
    active=[(float(losses[k]),float(w)) for k,w in weights.items() if k in losses and w > 0]
    if not active: return 0.0
    return sum(loss*w for loss,w in active)/sum(w for _,w in active)
