from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

class Decision(str,Enum):
    ADOPT="ADOPT"; HOLD="HOLD"; REJECT="REJECT"

@dataclass(frozen=True)
class ABMetrics:
    objective: float | None
    identity_ratio: float | None
    silhouette_ratio: float | None
    regional_retention: Mapping[str,float] | None = None
    regional_spatial_iou: Mapping[str,float | None] | None = None
    deterministic: bool | None = None
    runtime_ms: float | None = None

@dataclass(frozen=True)
class ABResult:
    decision: Decision
    reasons: tuple[str,...]

def evaluate_ab(baseline: ABMetrics,candidate: ABMetrics,*,identity_floor=.985,silhouette_floor=.985,
                regional_floor=.94,spatial_iou_floor=.85,
                critical_regions=("subject","hair","clothes","object")) -> ABResult:
    reasons=[]
    required={"objective":candidate.objective,"identity_ratio":candidate.identity_ratio,
              "silhouette_ratio":candidate.silhouette_ratio,"deterministic":candidate.deterministic}
    missing=[k for k,v in required.items() if v is None]
    if missing: return ABResult(Decision.HOLD,(f"unavailable required metrics: {', '.join(missing)}",))
    if candidate.deterministic is not True: reasons.append("candidate is not deterministic")
    if candidate.identity_ratio < identity_floor: reasons.append("identity hard guard failed")
    if candidate.silhouette_ratio < silhouette_floor: reasons.append("silhouette hard guard failed")
    if candidate.regional_retention is not None:
        for label in critical_regions:
            if label in candidate.regional_retention and candidate.regional_retention[label] < regional_floor:
                reasons.append(f"{label} regional retention failed")
    if candidate.regional_spatial_iou is not None:
        for label in critical_regions:
            if label in candidate.regional_spatial_iou:
                value=candidate.regional_spatial_iou[label]
                if value is None or value < spatial_iou_floor:
                    reasons.append(f"{label} spatial IoU failed")
    if reasons: return ABResult(Decision.REJECT,tuple(reasons))
    if baseline.objective is None: return ABResult(Decision.HOLD,("baseline objective unavailable",))
    if candidate.objective >= baseline.objective:
        return ABResult(Decision.REJECT,("candidate objective did not improve",))
    if candidate.regional_retention is None:
        return ABResult(Decision.HOLD,("regional observer evidence unavailable",))
    if candidate.regional_spatial_iou is None:
        return ABResult(Decision.HOLD,("spatial regional evidence unavailable",))
    return ABResult(Decision.ADOPT,("objective improved with all hard guards available and passing",))
