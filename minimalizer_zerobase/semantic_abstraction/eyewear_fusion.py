from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import numpy as np

from .eyewear_structure import EyewearStructuralEvidence


@dataclass(frozen=True)
class EyewearObserverEvidence:
    observer_id: str
    mask: np.ndarray
    confidence: float
    role: str

    def __post_init__(self):
        if self.role not in {"region","feature_local"}:
            raise ValueError("unsupported eyewear observer role")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("observer confidence must be in [0,1]")


@dataclass(frozen=True)
class EyewearFusionResult:
    mask: np.ndarray
    confidence: float
    promoted: bool
    supporting_observers: tuple[str,...]
    reason: str

    def to_dict(self)->dict:
        y,x=np.where(self.mask)
        box=None if not len(x) else [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
        return {
            "promoted":self.promoted,
            "confidence":round(float(self.confidence),6),
            "supporting_observers":list(self.supporting_observers),
            "reason":self.reason,
            "bbox":box,
            "pixel_count":int(self.mask.sum()),
        }


def fuse_eyewear_evidence(
    structural: EyewearStructuralEvidence,
    observers: tuple[EyewearObserverEvidence,...],
    *,
    head_mask: np.ndarray,
    hair_mask: np.ndarray,
    face_mask: np.ndarray,
    minimum_independent_roles: int=2,
    minimum_confidence: float=.62,
)->EyewearFusionResult:
    """Fuse independent eyewear evidence. Evidence can promote a hypothesis, never semantic authority."""
    head=np.asarray(head_mask).astype(bool);hair=np.asarray(hair_mask).astype(bool);face=np.asarray(face_mask).astype(bool)
    shape=head.shape
    if hair.shape!=shape or face.shape!=shape:
        raise ValueError("authority mask shape mismatch")
    authority=head|hair
    empty=np.zeros(shape,bool)
    if not np.any(face) or not np.any(authority):
        return EyewearFusionResult(empty,0.0,False,(),"missing_authority")

    candidates=[]
    if structural.paired and structural.confidence>=.5 and np.any(structural.mask):
        candidates.append(("structural",structural.mask&authority,float(structural.confidence),"structural"))

    seen=set()
    for item in sorted(observers,key=lambda x:(x.role,x.observer_id)):
        mask=np.asarray(item.mask).astype(bool)
        if mask.shape!=shape:
            raise ValueError("observer mask shape mismatch")
        if item.observer_id in seen:
            continue
        seen.add(item.observer_id)
        clipped=mask&authority
        area=int(clipped.sum())
        if area<6:
            continue
        outside=int((mask&~authority).sum())/max(1,int(mask.sum()))
        if outside>.12:
            continue
        candidates.append((item.observer_id,clipped,float(item.confidence),item.role))

    roles={x[3] for x in candidates}
    if len(roles)<minimum_independent_roles:
        return EyewearFusionResult(empty,0.0,False,tuple(x[0] for x in candidates),"insufficient_independent_roles")

    # Require spatial agreement. A union is never authorized by confidence alone.
    support=np.zeros(shape,np.uint8)
    weighted=np.zeros(shape,np.float32)
    for _,mask,conf,_ in candidates:
        support+=mask.astype(np.uint8)
        weighted+=mask.astype(np.float32)*conf
    agreed=support>=minimum_independent_roles
    if int(agreed.sum())<6:
        return EyewearFusionResult(empty,0.0,False,tuple(x[0] for x in candidates),"no_spatial_agreement")

    conf=float(np.mean(weighted[agreed]/support[agreed]))
    ids=tuple(x[0] for x in candidates if np.any(x[1]&agreed))
    if conf<minimum_confidence:
        return EyewearFusionResult(agreed,conf,False,ids,"confidence_below_gate")

    # Never promote evidence whose agreed support is primarily deep inside the face.
    inside=float((agreed&face).sum())/max(1,int(agreed.sum()))
    if inside>.72:
        return EyewearFusionResult(agreed,conf,False,ids,"face_feature_risk")

    return EyewearFusionResult(agreed,conf,True,ids,"independent_spatial_agreement")
