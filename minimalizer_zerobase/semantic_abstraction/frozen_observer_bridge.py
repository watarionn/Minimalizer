from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Mapping
import numpy as np
from .eyewear_fusion import EyewearObserverEvidence


@dataclass(frozen=True)
class FrozenObserverArtifact:
    observer_id:str
    role:str
    semantic_label:str
    confidence:float
    mask:np.ndarray
    producer:str
    model_id:str
    source_sha256:str|None=None


def _mask_from_record(record:Mapping[str,Any],shape:tuple[int,int])->np.ndarray|None:
    raw=record.get("mask")
    if raw is not None:
        arr=np.asarray(raw)
        if arr.shape!=shape: raise ValueError("artifact mask shape mismatch")
        return arr.astype(bool)
    geom=record.get("geometry") or {}
    bbox=geom.get("bbox")
    if isinstance(bbox,(list,tuple)) and len(bbox)==4:
        x,y,w,h=(int(v) for v in bbox)
        if w<=0 or h<=0 or x<0 or y<0 or x+w>shape[1] or y+h>shape[0]: return None
        out=np.zeros(shape,bool);out[y:y+h,x:x+w]=1;return out
    return None


def bind_frozen_eyewear_artifact(record:Mapping[str,Any],*,shape:tuple[int,int])->FrozenObserverArtifact|None:
    """Bind untouched frozen observer records. Aggregate summaries cannot be reconstructed."""
    label=str(record.get("semantic_label") or record.get("label") or "").strip().lower()
    aliases={"eyewear","glasses","goggles","sunglasses"}
    if label not in aliases: return None
    provenance=record.get("provenance")
    if not isinstance(provenance,Mapping): return None
    producer=str(provenance.get("producer") or "").strip()
    model=str(provenance.get("model_id") or "").strip()
    if not producer or not model: return None
    confidence=float(record.get("confidence",0.0))
    if not 0.0<=confidence<=1.0: return None
    role=str(record.get("observer_role") or record.get("role") or "region")
    if role not in {"region","feature_local"}: return None
    mask=_mask_from_record(record,shape)
    if mask is None or int(mask.sum())<6: return None
    oid=str(record.get("evidence_id") or record.get("observer_id") or f"{producer}:{label}")
    return FrozenObserverArtifact(oid,role,label,confidence,mask,producer,model,record.get("source_sha256"))


def to_fusion_evidence(artifact:FrozenObserverArtifact)->EyewearObserverEvidence:
    return EyewearObserverEvidence(artifact.observer_id,artifact.mask,artifact.confidence,artifact.role)


def bind_frozen_records(records:list[Mapping[str,Any]],*,shape:tuple[int,int])->tuple[FrozenObserverArtifact,...]:
    out=[]
    for record in records:
        item=bind_frozen_eyewear_artifact(record,shape=shape)
        if item is not None: out.append(item)
    return tuple(sorted(out,key=lambda x:(x.role,x.observer_id)))
