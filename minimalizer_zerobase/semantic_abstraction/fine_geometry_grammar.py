from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np

from .evidence_adapter import build_semantic_abstraction_evidence
from .fine_part_decomposition import (
    FINE_IDENTITY_CATEGORIES,
    FinePartProposal,
    observe_fine_identity_parts,
    promote_fine_identity_parts,
)
from .policy import apply_importance_policy
from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.structure.graph import StructuralLayoutGraph


@dataclass(frozen=True)
class FineGeometryPrimitive:
    semantic_part: str
    family: str
    mask: np.ndarray
    rgb: tuple[int,int,int]
    priority: int


_MINIMUMS={"eyewear":2,"headwear":1,"hair_front":1,"hair_side":1,"collar":1,"tie_or_neckwear":1,"major_accessory":1}
_PRIORITY={"hair_side":10,"hair_front":20,"headwear":30,"collar":40,"tie_or_neckwear":50,"major_accessory":60,"eyewear":70}


def _components(mask:np.ndarray,limit:int)->tuple[np.ndarray,...]:
    binary=np.asarray(mask).astype(np.uint8)
    count,labels,stats,_=cv2.connectedComponentsWithStats(binary,8)
    rows=[]
    for label in range(1,count):
        area=int(stats[label,cv2.CC_STAT_AREA])
        if area>=3: rows.append((area,label))
    rows.sort(key=lambda row:(-row[0],row[1]))
    return tuple(labels==label for _,label in rows[:limit])


def _median(rgb:np.ndarray,mask:np.ndarray)->tuple[int,int,int]:
    pixels=np.asarray(rgb)[np.asarray(mask).astype(bool)]
    if not len(pixels): return (128,128,128)
    value=np.median(pixels,axis=0).astype(int)
    return tuple(int(x) for x in value[:3])


def _primitive_masks(category:str,mask:np.ndarray)->tuple[tuple[str,np.ndarray],...]:
    m=np.asarray(mask).astype(bool)
    if category=="eyewear":
        components=_components(m,3)
        if len(components)>=2:
            return tuple(("ellipse",x) for x in components[:3])
        ys,xs=np.where(m)
        if not xs.size: return ()
        mid=float(np.median(xs))
        left=m&(np.indices(m.shape)[1]<=mid)
        right=m&(np.indices(m.shape)[1]>mid)
        rows=tuple(("ellipse",x) for x in (left,right) if int(x.sum())>=3)
        return rows or (("convex_polygon",m),)
    if category in ("hair_front","hair_side","headwear","collar","tie_or_neckwear","major_accessory"):
        components=_components(m,3 if category in ("hair_front","hair_side","collar") else 2)
        return tuple(("convex_polygon",x) for x in components) or (("convex_polygon",m),)
    return ()


def reserve_fine_part_budget(categories:tuple[str,...],budget:int)->dict[str,int]:
    if budget<0: raise ValueError("budget must be non-negative")
    out={};remaining=int(budget)
    for category in sorted(set(categories),key=lambda c:(-_PRIORITY.get(c,0),c)):
        need=_MINIMUMS.get(category,0)
        if need and remaining>=need:
            out[category]=need;remaining-=need
    return out


def build_fine_geometry_primitives(
    rgb:np.ndarray,
    coarse_masks:Mapping[str,np.ndarray],
    graph:StructuralLayoutGraph,
    *,
    primitive_budget:int=10,
)->tuple[FineGeometryPrimitive,...]:
    normalized={name:np.asarray(coarse_masks[name]) if name in coarse_masks else np.zeros(rgb.shape[:2],dtype=np.uint8) for name in PART_NAMES}
    baseline=apply_importance_policy(build_semantic_abstraction_evidence(part_masks=normalized,graph=graph))
    proposals=observe_fine_identity_parts(rgb,normalized)
    parent_masks={
        "head":normalized["head"],"hair":normalized["hair"],
        "major_clothing":normalized["major_clothing"],
        "accessory_or_held_object":normalized["accessory_or_held_object"],
    }
    promoted=promote_fine_identity_parts(baseline,proposals,parent_masks=parent_masks,face_mask=normalized["face"])
    allowed={p.category for p in promoted.parts if p.category in FINE_IDENTITY_CATEGORIES}
    selected=tuple(p for p in proposals if p.category in allowed)
    reservations=reserve_fine_part_budget(tuple(p.category for p in selected),primitive_budget)
    rows=[]
    for proposal in sorted(selected,key=lambda p:(_PRIORITY.get(p.category,0),p.category)):
        cap=reservations.get(proposal.category,0)
        if cap<1: continue
        pieces=_primitive_masks(proposal.category,proposal.mask)[:cap]
        for family,mask in pieces:
            rows.append(FineGeometryPrimitive(
                semantic_part=proposal.category,family=family,mask=mask,
                rgb=_median(rgb,mask),priority=_PRIORITY.get(proposal.category,0),
            ))
    return tuple(rows)
