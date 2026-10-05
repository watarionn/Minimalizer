from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
import numpy as np

PROTOTYPE_BANK_VERSION="sa7.11-v1"

@dataclass(frozen=True)
class PrototypeEntry:
    source_sha256:str
    vector:np.ndarray
    role:str="positive"

def build_prototype_bank(entries:tuple[PrototypeEntry,...])->dict:
    if not entries: raise ValueError("prototype bank requires non-target references")
    dim=None;serial=[]
    for e in sorted(entries,key=lambda x:(x.role,x.source_sha256)):
        if e.role not in {"positive","negative"}:raise ValueError("unsupported prototype role")
        if len(e.source_sha256)!=64:raise ValueError("source hash required")
        v=np.asarray(e.vector,dtype=np.float32).reshape(-1)
        if not np.isfinite(v).all() or not np.linalg.norm(v)>0:raise ValueError("invalid prototype vector")
        dim=dim or len(v)
        if len(v)!=dim:raise ValueError("prototype dimension mismatch")
        v=v/np.linalg.norm(v)
        serial.append({"source_sha256":e.source_sha256,"role":e.role,"vector":[round(float(x),8) for x in v]})
    payload={"version":PROTOTYPE_BANK_VERSION,"entries":serial}
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    payload["bank_sha256"]=hashlib.sha256(canonical).hexdigest()
    return payload

def positive_centroid(bank:dict)->np.ndarray:
    vals=[np.asarray(e["vector"],np.float32) for e in bank["entries"] if e["role"]=="positive"]
    if not vals:raise ValueError("positive prototype required")
    v=np.mean(vals,axis=0);return v/max(float(np.linalg.norm(v)),1e-8)
