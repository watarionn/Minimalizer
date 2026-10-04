from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class SceneEvidence:
    silhouette_iou:float
    dino_score:float
@dataclass(frozen=True)
class SceneRollbackPolicy:
    min_silhouette_iou:float=.985
    max_dino_drop:float=.01
def accept_scene_step(baseline:SceneEvidence,candidate:SceneEvidence,policy:SceneRollbackPolicy=SceneRollbackPolicy())->bool:
    return candidate.silhouette_iou>=policy.min_silhouette_iou and candidate.dino_score>=baseline.dino_score-policy.max_dino_drop
