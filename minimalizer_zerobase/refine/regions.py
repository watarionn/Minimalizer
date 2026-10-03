from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Protocol

@dataclass(frozen=True)
class RegionObservation:
    label: str
    coverage: float
    confidence: float = 1.0
    spatial_mask: tuple[tuple[bool, ...], ...] | None = None
    def __post_init__(self):
        if not self.label: raise ValueError("region label is required")
        if not 0.0 <= self.coverage <= 1.0: raise ValueError("coverage must be in [0, 1]")
        if not 0.0 <= self.confidence <= 1.0: raise ValueError("confidence must be in [0, 1]")
        if self.spatial_mask is not None:
            if not self.spatial_mask or not self.spatial_mask[0]: raise ValueError("spatial_mask must be non-empty")
            width=len(self.spatial_mask[0])
            if any(len(row) != width for row in self.spatial_mask): raise ValueError("spatial_mask must be rectangular")

class RegionObserver(Protocol):
    """Observation-only segmentation boundary. It has no pixel/Scene mutation API."""
    name: str
    def observe(self, image: object) -> tuple[RegionObservation, ...]: ...

@dataclass(frozen=True)
class RegionGuardPolicy:
    min_confidence: float = 0.5
    min_retention: float = 0.94
    min_spatial_iou: float = 0.85
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

def spatial_iou(reference: RegionObservation, candidate: RegionObservation) -> float | None:
    a,b=reference.spatial_mask,candidate.spatial_mask
    if a is None or b is None: return None
    if len(a) != len(b) or len(a[0]) != len(b[0]): raise ValueError("spatial masks must share dimensions")
    intersection=union=0
    for ar,br in zip(a,b):
        for av,bv in zip(ar,br):
            intersection += bool(av and bv)
            union += bool(av or bv)
    return 1.0 if union == 0 else intersection/union

def regional_spatial_iou(reference: tuple[RegionObservation, ...], candidate: tuple[RegionObservation, ...],
                         *, policy: RegionGuardPolicy = RegionGuardPolicy()) -> dict[str, float | None]:
    ref={r.label:r for r in reference if r.confidence >= policy.min_confidence}
    cand={r.label:r for r in candidate if r.confidence >= policy.min_confidence}
    return {label: (0.0 if label not in cand else spatial_iou(r,cand[label])) for label,r in ref.items()}

def regional_guard_passes(retention: Mapping[str,float], *, spatial: Mapping[str,float | None] | None = None,
                          policy: RegionGuardPolicy = RegionGuardPolicy()) -> bool:
    for label in policy.critical_labels:
        if label in retention and retention.get(label,0.0) < policy.min_retention: return False
        if spatial is not None and label in spatial:
            value=spatial[label]
            if value is None or value < policy.min_spatial_iou: return False
    return True

def weighted_regional_loss(losses: Mapping[str,float], weights: Mapping[str,float]) -> float:
    active=[(float(losses[k]),float(w)) for k,w in weights.items() if k in losses and w > 0]
    if not active: return 0.0
    return sum(loss*w for loss,w in active)/sum(w for _,w in active)
