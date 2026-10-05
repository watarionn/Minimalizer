from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class HoldoutScore:
    source_sha256:str
    role:str
    score:float

@dataclass(frozen=True)
class GeneralizationReport:
    positive_min:float
    negative_max:float
    margin:float
    passed:bool
    positive_count:int
    negative_count:int

def evaluate_contrastive_holdouts(scores:tuple[HoldoutScore,...],*,minimum_margin:float=.05,minimum_per_role:int=2)->GeneralizationReport:
    pos=[float(x.score) for x in scores if x.role=="positive"]
    neg=[float(x.score) for x in scores if x.role=="negative"]
    if len(pos)<minimum_per_role or len(neg)<minimum_per_role:
        raise ValueError("insufficient multi-holdout coverage")
    if any(len(x.source_sha256)!=64 for x in scores):
        raise ValueError("source hash required")
    pmin=min(pos);nmax=max(neg);margin=pmin-nmax
    return GeneralizationReport(pmin,nmax,margin,margin>=minimum_margin,len(pos),len(neg))
