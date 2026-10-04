from __future__ import annotations
from dataclasses import asdict, dataclass
import os
from typing import Any

DIFFMIN_ENV = "MINIMALIZER_DIFFMIN"
DIFFMIN_OFF = "off"
DIFFMIN_GUARDED = "guarded"

@dataclass(frozen=True)
class DiffMinEvidence:
    hard_guards_pass: bool
    silhouette_iou: float
    baseline_dino_score: float | None
    candidate_dino_score: float | None

@dataclass(frozen=True)
class DiffMinDecision:
    requested_mode: str
    apply_candidate: bool
    rollback_to_baseline: bool
    reason: str
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class GuardedDiffMinPolicy:
    min_silhouette_iou: float = .985
    require_dino_improvement: bool = True

class GuardedDiffMinSwitch:
    def __init__(self, requested_mode: str | None = None, policy: GuardedDiffMinPolicy | None = None):
        mode=(requested_mode or os.getenv(DIFFMIN_ENV,DIFFMIN_OFF)).strip().lower()
        if mode not in {DIFFMIN_OFF,DIFFMIN_GUARDED}:
            raise ValueError(f"unsupported DiffMin mode: {mode}")
        self.requested_mode=mode
        self.policy=policy or GuardedDiffMinPolicy()

    def decide(self,evidence:DiffMinEvidence)->DiffMinDecision:
        if self.requested_mode==DIFFMIN_OFF:
            return DiffMinDecision(self.requested_mode,False,True,"disabled-by-default")
        if not evidence.hard_guards_pass:
            return DiffMinDecision(self.requested_mode,False,True,"hard-guard-failed")
        if evidence.silhouette_iou < self.policy.min_silhouette_iou:
            return DiffMinDecision(self.requested_mode,False,True,"scene-silhouette-regressed")
        if evidence.baseline_dino_score is None or evidence.candidate_dino_score is None:
            return DiffMinDecision(self.requested_mode,False,True,"observer-evidence-missing")
        if self.policy.require_dino_improvement and evidence.candidate_dino_score <= evidence.baseline_dino_score:
            return DiffMinDecision(self.requested_mode,False,True,"observer-not-improved")
        return DiffMinDecision(self.requested_mode,True,False,"guarded-candidate-improved")

