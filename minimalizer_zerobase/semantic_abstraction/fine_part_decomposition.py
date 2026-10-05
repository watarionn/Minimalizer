from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np

from .ir import (
    AbstractionPlan, AbstractionPolicy, GeometryConstraints, SemanticPart,
    StructuralRole, VisualRole,
)


FINE_IDENTITY_CATEGORIES = (
    "eyewear",
    "headwear",
    "hair_front",
    "hair_side",
    "collar",
    "tie_or_neckwear",
    "major_accessory",
)


@dataclass(frozen=True)
class FinePartProposal:
    category: str
    parent_part_id: str
    mask: np.ndarray
    confidence: float
    evidence_ref: str


def _bbox(mask: np.ndarray) -> tuple[float,float,float,float] | None:
    ys,xs=np.where(np.asarray(mask).astype(bool))
    if not xs.size:
        return None
    h,w=mask.shape
    return (float(xs.min())/w,float(ys.min())/h,float(xs.max()+1)/w,float(ys.max()+1)/h)


def _components(mask: np.ndarray, minimum: int) -> tuple[np.ndarray,...]:
    binary=np.asarray(mask).astype(np.uint8)
    count,labels,stats,_=cv2.connectedComponentsWithStats(binary,8)
    rows=[]
    for label in range(1,count):
        area=int(stats[label,cv2.CC_STAT_AREA])
        if area>=minimum:
            rows.append((area,label))
    rows.sort(key=lambda x:(-x[0],x[1]))
    return tuple(labels==label for _,label in rows)


def observe_fine_identity_parts(
    rgb: np.ndarray,
    coarse_masks: Mapping[str,np.ndarray],
) -> tuple[FinePartProposal,...]:
    """Deterministic observer proposals. These are evidence, never semantic authority."""
    image=np.asarray(rgb,dtype=np.uint8)
    h,w=image.shape[:2]
    required=("head","hair","face","major_clothing","accessory_or_held_object")
    if any(name not in coarse_masks for name in required):
        raise ValueError("fine part observer requires head/hair/face/clothing/accessory masks")
    head=np.asarray(coarse_masks["head"]).astype(bool)
    hair=np.asarray(coarse_masks["hair"]).astype(bool)
    face=np.asarray(coarse_masks["face"]).astype(bool)
    clothing=np.asarray(coarse_masks["major_clothing"]).astype(bool)
    accessory=np.asarray(coarse_masks["accessory_or_held_object"]).astype(bool)
    proposals=[]

    face_box=cv2.boundingRect(face.astype(np.uint8)) if np.any(face) else None
    gray=cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
    edges=cv2.Canny(gray,55,135)>0

    if face_box:
        fx,fy,fw,fh=face_box
        yy,xx=np.indices((h,w))
        upper_face=(yy>=max(0,fy-int(.55*fh)))&(yy<=fy+int(.30*fh))&(xx>=fx-int(.45*fw))&(xx<=fx+int(1.45*fw))
        authority=(head|hair)&~face&upper_face
        quant=(image//48).astype(np.int32)
        packed=(quant[:,:,0]<<16)|(quant[:,:,1]<<8)|quant[:,:,2]
        parent_pixels=image[(head|hair)&~face]
        parent_median=np.median(parent_pixels,axis=0).astype(float) if len(parent_pixels) else np.array([128,128,128],float)
        candidates=[]
        for key in np.unique(packed[authority]):
            for comp in _components((packed==key)&authority,max(5,int(authority.sum()*.002))):
                ys,xs=np.where(comp); area=len(xs)
                if not area: continue
                bw=xs.max()-xs.min()+1; bh=ys.max()-ys.min()+1
                ratio=area/max(1,int(authority.sum()))
                color=np.median(image[comp],axis=0).astype(float)
                contrast=float(np.linalg.norm(color-parent_median))
                edge_density=float(edges[comp].sum()/area)
                if bw < max(4,int(.12*fw)) or bh < 3 or ratio>.34 or contrast<38:
                    continue
                span=bw/max(fw,1)
                score=.42+min(.22,span*.18)+min(.18,contrast/500)+min(.12,edge_density*.4)
                candidates.append((score,area,comp))
        candidates.sort(key=lambda x:(-x[0],-x[1]))
        if candidates:
            combined=np.zeros((h,w),bool)
            for _,_,comp in candidates[:4]: combined|=comp
            ys,xs=np.where(combined)
            if xs.size and (xs.max()-xs.min()+1)>=max(8,int(.32*fw)):
                proposals.append(FinePartProposal("eyewear","head",combined,min(1.0,candidates[0][0]+.12),"observer:fine:upper-face-structure"))

        front_zone=(yy>=max(0,fy-int(.7*fh)))&(yy<=fy+int(.75*fh))&(xx>=fx-int(.25*fw))&(xx<=fx+int(1.25*fw))
        front=hair&front_zone
        if np.any(front):
            proposals.append(FinePartProposal("hair_front","hair",front,.82,"observer:fine:hair-front-zone"))
        side=hair&~front_zone
        if np.any(side):
            proposals.append(FinePartProposal("hair_side","hair",side,.78,"observer:fine:hair-side-zone"))

    if np.any(clothing):
        ys,xs=np.where(clothing); cy0,cy1=ys.min(),ys.max()+1; cx0,cx1=xs.min(),xs.max()+1
        ch=max(1,cy1-cy0); cw=max(1,cx1-cx0); yy,xx=np.indices((h,w))
        upper=clothing&(yy<=cy0+int(.42*ch))
        center=upper&(xx>=cx0+int(.25*cw))&(xx<=cx0+int(.75*cw))
        if np.any(center):
            values=gray[center]; threshold=float(np.median(values))
            contrast=center&(np.abs(gray.astype(float)-threshold)>=18)
            comps=_components(contrast,max(6,int(clothing.sum()*.006)))
            if comps:
                tie=max(comps,key=lambda m:int(m.sum()))
                proposals.append(FinePartProposal("tie_or_neckwear","major_clothing",tie,.72,"observer:fine:upper-center-clothing"))
        collar=upper&~center
        if np.any(collar):
            proposals.append(FinePartProposal("collar","major_clothing",collar,.62,"observer:fine:upper-clothing"))

    if np.any(accessory):
        proposals.append(FinePartProposal("major_accessory","accessory_or_held_object",accessory,.9,"observer:fine:coarse-accessory"))

    return tuple(proposals)


def validate_fine_part_proposal(
    proposal: FinePartProposal,
    parent_mask: np.ndarray,
    *,
    face_mask: np.ndarray | None = None,
) -> tuple[bool, str]:
    mask=np.asarray(proposal.mask).astype(bool)
    parent=np.asarray(parent_mask).astype(bool)
    if mask.shape != parent.shape:
        return False,"shape_mismatch"
    area=int(mask.sum()); parent_area=max(1,int(parent.sum()))
    if area < 6:
        return False,"too_small"
    outside=int((mask&~parent).sum())
    if outside/max(area,1) > .08:
        return False,"outside_parent"
    ratio=area/parent_area
    limits={
        "eyewear":(.002,.16),"headwear":(.01,.55),"hair_front":(.03,.80),"hair_side":(.03,.90),
        "collar":(.01,.45),"tie_or_neckwear":(.002,.30),"major_accessory":(.01,1.0),
    }
    lo,hi=limits.get(proposal.category,(.0,1.0))
    if not (lo <= ratio <= hi):
        return False,"parent_area_ratio"
    if proposal.category=="eyewear" and face_mask is not None and np.any(face_mask):
        face=np.asarray(face_mask).astype(bool)
        near=cv2.dilate(face.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15))).astype(bool)
        if int((mask&near).sum())/area < .08:
            return False,"not_near_face"
    return True,"ok"


def promote_fine_identity_parts(\n    plan: AbstractionPlan,\n    proposals: tuple[FinePartProposal,...],\n    *,\n    parent_masks: Mapping[str,np.ndarray] | None=None,\n    face_mask: np.ndarray | None=None,\n    minimum_confidence: float=.60,\n) -> AbstractionPlan:
    """Promote observer evidence only under an existing non-suppressed semantic parent."""
    parents={p.id:p for p in plan.parts}
    additions=[]
    counts={}
    for proposal in proposals:
        if proposal.category not in FINE_IDENTITY_CATEGORIES:
            continue
        parent=parents.get(proposal.parent_part_id)
        if parent is None or parent.abstraction_policy is AbstractionPolicy.SUPPRESS:
            continue
        if proposal.confidence < minimum_confidence or not np.any(proposal.mask):\n            continue\n        if parent_masks is not None:\n            if proposal.parent_part_id not in parent_masks:\n                continue\n            valid,_reason=validate_fine_part_proposal(proposal,parent_masks[proposal.parent_part_id],face_mask=face_mask)\n            if not valid:\n                continue
        counts[proposal.category]=counts.get(proposal.category,0)+1
        suffix=counts[proposal.category]
        pid=proposal.category if suffix==1 else f"{proposal.category}:{suffix}"
        additions.append(SemanticPart(
            id=pid,category=proposal.category,parent=proposal.parent_part_id,
            bbox=_bbox(proposal.mask),confidence=proposal.confidence,
            structural_role=StructuralRole.ATTACHED,visual_role=VisualRole.IDENTITY_ACCENT,
            importance=max(.75,parent.importance),
            abstraction_policy=AbstractionPolicy.PRESERVE,
            geometry_constraints=GeometryConstraints(
                allowed_families=("convex_polygon","ellipse"),
                min_primitives=1,max_primitives=3,preserve_outer_contour=True,
            ),
            evidence_refs=(proposal.evidence_ref,),
        ))
    return AbstractionPlan(parts=tuple(plan.parts)+tuple(additions),schema_version=plan.schema_version)
