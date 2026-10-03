from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
import numpy as np

@dataclass(frozen=True)
class OwnershipRetention:
    per_part_iou: Mapping[str,float]
    minimum_iou: float
    passed: bool
    reasons: tuple[str,...]

def mask_iou(reference: np.ndarray,candidate: np.ndarray)->float:
    a=np.asarray(reference,dtype=bool); b=np.asarray(candidate,dtype=bool)
    if a.shape!=b.shape: raise ValueError("ownership mask shape mismatch")
    union=np.logical_or(a,b).sum()
    return 1.0 if union==0 else float(np.logical_and(a,b).sum()/union)

def evaluate_ownership_retention(reference: Mapping[str,np.ndarray],candidate: Mapping[str,np.ndarray],*,minimum_iou:float=.985,critical_parts:tuple[str,...]=("hair","face","major_clothing","left_arm","right_arm","lower_body"))->OwnershipRetention:
    scores={}; reasons=[]
    for part in critical_parts:
        if part not in reference or part not in candidate:
            reasons.append(f"{part} ownership mask unavailable")
            continue
        score=mask_iou(reference[part],candidate[part]); scores[part]=score
        if score<minimum_iou: reasons.append(f"{part} ownership IoU {score:.6f} below {minimum_iou:.6f}")
    minimum=min(scores.values()) if scores else 0.0
    return OwnershipRetention(scores,minimum,not reasons,tuple(reasons))

def union_masks(masks) -> np.ndarray:
    items=[np.asarray(m,dtype=bool) for m in masks]
    if not items: raise ValueError("ownership union requires at least one mask")
    shape=items[0].shape
    if any(m.shape!=shape for m in items): raise ValueError("ownership union shape mismatch")
    out=np.zeros(shape,dtype=bool)
    for m in items: out|=m
    return out
