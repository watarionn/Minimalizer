from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Sequence
import numpy as np

EYEWEAR_OBSERVER_VERSION="sa7.9-v1"
EYEWEAR_PROMPT="glasses. goggles. sunglasses. eyewear."
EYEWEAR_LABELS=("glasses","goggles","sunglasses","eyewear")
DETECTION_THRESHOLD=.20
TEXT_THRESHOLD=.20
MIN_MASK_PIXELS=6
MAX_HEAD_AUTHORITY_RATIO=.70

@dataclass(frozen=True)
class EyewearDetection:
    label:str
    score:float
    sam_iou:float
    mask:np.ndarray

def canonical_eyewear_label(text:str)->str|None:
    v=str(text).casefold()
    for x in EYEWEAR_LABELS:
        if x in v:return x
    return None

def frozen_eyewear_records(
    detections:Sequence[EyewearDetection],*,head_hair_authority:np.ndarray,model_id:str
)->list[dict[str,Any]]:
    authority=np.asarray(head_hair_authority).astype(bool)
    out=[]
    for i,d in enumerate(detections):
        label=canonical_eyewear_label(d.label)
        if label is None or d.score<DETECTION_THRESHOLD:continue
        mask=np.asarray(d.mask).astype(bool)
        if mask.shape!=authority.shape:raise ValueError("eyewear mask shape mismatch")
        clipped=mask&authority
        n=int(clipped.sum())
        if n<MIN_MASK_PIXELS:continue
        ratio=n/max(1,int(authority.sum()))
        if ratio>MAX_HEAD_AUTHORITY_RATIO:continue
        conf=float(np.clip(d.score,0,1)*np.clip(d.sam_iou,0,1))
        ys,xs=np.where(clipped)
        out.append({
            "evidence_id":f"eyewear-v1-{label}-{i}",
            "semantic_label":label,
            "confidence":conf,
            "observer_role":"region",
            "geometry":{"bbox":[int(xs.min()),int(ys.min()),int(xs.max()-xs.min()+1),int(ys.max()-ys.min()+1)]},
            "provenance":{"producer":"sa7.9-eyewear-grounded-sam","model_id":model_id,"observer_version":EYEWEAR_OBSERVER_VERSION},
        })
    return out
