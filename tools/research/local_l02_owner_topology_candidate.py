"""H04 local L02 *research only*. Graph-constrained interpretation of TWO-source garment observations.

The original signed immutable Phase4 owners are never written; inherited v2
shadow owners are inputs; signed H04 user polygons NEVER enter `resolve_owners`.
Staged owner candidates need independent cross-person evaluation and human signoff.
"""
from __future__ import annotations
import dataclasses
import numpy as np
import cv2
import heapq
import hashlib
import io
from PIL import Image

PROTECTED=('face','neck','left_arm','right_arm','lower_body','accessory_or_held_object')
PARENT='head'
LEAVES=('hair','face','neck','torso','left_arm','right_arm','lower_body','major_clothing','accessory_or_held_object','unknown')
PARTS=('head',)+LEAVES
class Hold(ValueError):pass

@dataclasses.dataclass(frozen=True)
class CandidateReport:
    source_pixels:int
    eligible_pixels:int
    retained_agreement_pixels:int
    rejected_islands_pixels:int
    hair_demotion_unknown_pixels:int
    torso_demotion_unknown_pixels:int
    transferred_hair_pixels:int
    transferred_torso_pixels:int
    transferred_unknown_pixels:int
    inherited_components:dict
    repaired_components:dict
    leaf_overlap_pixels:int
    signed_union_xor_pixels:int
    protected_xor_pixels:int
    parent_head_xor_pixels:int
    neck_torso_gap_old:float
    neck_torso_gap_new:float
    reserved_original_torso_bridge_pixels:int
    status:str='RESEARCH_CANDIDATE_NOT_GOLDEN'
    def as_dict(self):return dataclasses.asdict(self)

def count_components(mask):
    return cv2.connectedComponents(mask.astype('uint8'),connectivity=8)[0]-1

def validate_shapes(src,owners,evidence):
    if src.dtype!=np.uint8 or src.ndim!=3 or src.shape[2]!=4:raise Hold('source RGBA uint8 required')
    if set(owners)!=set(PARTS):raise Hold('11-part owner keyset mismatch')
    alpha=src[:,:,3]>0
    if evidence.shape!=alpha.shape or evidence.dtype!=bool:raise Hold('binary source-scale observation required')
    if any(x.shape!=alpha.shape or x.dtype!=bool for x in owners.values()):raise Hold('mask size/dtype mismatch')
    if any(np.any(x&~alpha) for x in owners.values()):raise Hold('part claims transparent source pixels')
    if np.any(evidence&~alpha):raise Hold('unsupported observation pixels')
    leafs=sum(owners[x].astype(np.uint8) for x in LEAVES)
    if (leafs>1).any():raise Hold('inherited exclusive leaves overlap')
    return alpha

def connected_core(observation,union,*,absolute_min_area=1000,relative_min_area=.025):
    if not (100<=absolute_min_area<=100000) or not (0<relative_min_area<.20):raise Hold('untrusted island gate')
    if not np.any(observation):raise Hold('empty observer consensus')
    n,labels,stats,_=cv2.connectedComponentsWithStats(observation.astype('uint8'),connectivity=8)
    threshold=max(absolute_min_area,int(round(observation.sum()*relative_min_area)))
    keep_ids=[i for i in range(1,n) if stats[i,cv2.CC_STAT_AREA]>=threshold]
    if not keep_ids:raise Hold('no large source-supported consensus component')
    core=np.isin(labels,keep_ids)
    if np.any(core&~union):raise Hold('component core lacks signed owner union')
    return core

def prune_detached_to_unknown(new_owner,old_owner):
    """Keep each inherited component's largest surviving fragment, ABSTAIN on detached islands.

    Detached fragments are deliberately not auto-called jacket; ownership becomes unknown.
    Never connect two fragments by painting/growing new mask pixels.
    """
    count,orig_labels,stats,_=cv2.connectedComponentsWithStats(old_owner.astype('uint8'),8)
    out=np.zeros_like(old_owner)
    for label_id in range(1,count):
        survivor=new_owner&(orig_labels==label_id)
        n,ids,frag_stats,_=cv2.connectedComponentsWithStats(survivor.astype('uint8'),8)
        if n<=1:raise Hold('entire inherited semantic component was removed')
        largest=1+int(np.argmax(frag_stats[1:,cv2.CC_STAT_AREA]))
        out|=(ids==largest)&survivor
    demoted=new_owner&~out
    if count_components(out)!=count_components(old_owner):raise Hold('topology not preserved')
    return out,demoted

def neck_torso_gap(neck,torso):
    if not (np.any(neck) and np.any(torso)):raise Hold('missing neck/torso source support')
    distance=cv2.distanceTransform((~neck).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    return float(np.min(distance[torso]))

def preserve_neck_torso_bridge(owners,core,*,max_attachment_fraction=.06):
    """Keep a minimum original-TORSO path from source-backed neck contact to the surviving shirt.

    This is STRUCTURAL support only, not proof of garment semantics. No pixels
    outside inherited torso may be connected, or any mask augmented by painting.
    """
    neck=owners['neck'];torso=owners['torso']
    if neck.shape!=torso.shape or not neck.any() or not torso.any():raise Hold('source neck or torso absent')
    h,w=torso.shape
    limit=max(6.,min(h,w)*max_attachment_fraction)
    near=cv2.distanceTransform((~neck).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    contact_distance=float(np.min(near[torso]))
    if contact_distance>limit:raise Hold('inherited neck-torso too distant; no manufactured attachment')
    survivor=torso&~core
    n,comp,stats,_=cv2.connectedComponentsWithStats(survivor.astype(np.uint8),8)
    if n<=1:raise Hold('no remaining torso shirt candidate')
    main=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
    target=(comp==main)
    # If the surviving main shirt already supports neck attachment, no bridge needed.
    if float(np.min(near[target]))<=limit:return np.zeros_like(torso)
    # Choose one original torso contact closest to the signed original neck; ties sorted deterministically.
    seeds=np.flatnonzero(torso & (near==contact_distance))
    if not len(seeds):raise Hold('no source-anchored neck contact')
    start=int(seeds[0])
    costs=np.full(torso.shape,np.inf,np.float64)
    prev=np.full(torso.size,-1,np.int64)
    costs.ravel()[start]=0.
    queue=[(0.,start)]
    neigh=[(-1,0,1.),(0,-1,1.),(0,1,1.),(1,0,1.),(-1,-1,1.41421356),(-1,1,1.41421356),(1,-1,1.41421356),(1,1,1.41421356)]
    found=-1
    while queue:
        cost,idx=heapq.heappop(queue)
        if cost>costs.ravel()[idx]+1e-6:continue
        y,x=divmod(idx,w)
        if target[y,x]:found=idx;break
        for dy,dx,step in neigh:
            yn,xn=y+dy,x+dx
            if not (0<=yn<h and 0<=xn<w) or not torso[yn,xn]:continue
            j=yn*w+xn
            new_cost=cost+step*(9. if core[yn,xn] else 1.)
            if new_cost<costs.ravel()[j]-1e-6:
                costs.ravel()[j]=new_cost;prev[j]=idx;heapq.heappush(queue,(new_cost,j))
    if found<0:raise Hold('original source torso has no path from neck to surviving shirt')
    path=np.zeros_like(torso,np.uint8);pos=found
    while pos>=0:
        y,x=divmod(pos,w);path[y,x]=1
        pos=int(prev[pos])
    # Dilate the source-backed path slightly for robust raster contact, but only INSIDE ORIGINAL TORSO.
    kept=(cv2.dilate(path,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))>0)&torso
    if float(np.min(near[kept]))>limit:raise Hold('reserved path is not attached to source neck')
    return kept

def verify_signed_source(src,source_bytes,expected_sha256):
    if not isinstance(source_bytes,bytes) or not isinstance(expected_sha256,str) or len(expected_sha256)!=64:
        raise Hold('signed immutable source bytes and SHA-256 required')
    if hashlib.sha256(source_bytes).hexdigest()!=expected_sha256:
        raise Hold('signed original source hash mismatch')
    try:
        decoded=np.asarray(Image.open(io.BytesIO(source_bytes)).convert('RGBA'),dtype=np.uint8)
    except Exception as exc:
        raise Hold('invalid signed original image encoding') from exc
    if src.shape!=decoded.shape or src.dtype!=decoded.dtype or not np.array_equal(src,decoded):
        raise Hold('decoded source pixels do not match authenticated immutable image')
    return True

def resolve_owners(src,owners,observation,*,source_bytes:bytes,expected_sha256:str):
    verify_signed_source(src,source_bytes,expected_sha256)
    original={k:v.copy() for k,v in owners.items()}
    alpha=validate_shapes(src,original,observation)
    old_union=np.logical_or.reduce([original[k] for k in PARTS])
    protected=np.logical_or.reduce([original[k] for k in PROTECTED])
    if np.any(observation&protected):raise Hold('observation illegally proposes protected pixels')
    if np.any(observation&~old_union):raise Hold('observer consensus beyond signed foreground union')
    core=connected_core(observation,old_union)
    bridge=preserve_neck_torso_bridge(original,core)
    core &= ~bridge
    new={k:v.copy() for k,v in original.items()}
    moved_hair=core&new['hair']
    moved_torso=core&new['torso']
    moved_unknown=core&new['unknown']
    new['hair'] &= ~core
    new['torso'] &= ~core
    new['unknown'] &= ~core
    new['major_clothing'] |= core
    new['hair'],demote_hair=prune_detached_to_unknown(new['hair'],original['hair'])
    new['torso'],demote_torso=prune_detached_to_unknown(new['torso'],original['torso'])
    new['unknown']|=(demote_hair|demote_torso)
    new_union=np.logical_or.reduce([new[k] for k in PARTS])
    if not np.array_equal(new_union,old_union):raise Hold('signed foreground union was changed')
    if not np.array_equal(new['head'],original['head']):raise Hold('head parent overwritten')
    if any(not np.array_equal(new[k],original[k]) for k in PROTECTED):raise Hold('protected anatomical mask modified')
    count_leaves=sum(new[k].astype(np.uint8) for k in LEAVES)
    if np.any(count_leaves>1):raise Hold('exclusive leaf ownership overlap')
    report=CandidateReport(
        source_pixels=int(alpha.sum()),eligible_pixels=int(old_union.sum()),
        retained_agreement_pixels=int(core.sum()),
        rejected_islands_pixels=int((observation&~core).sum()),
        hair_demotion_unknown_pixels=int(demote_hair.sum()),
        torso_demotion_unknown_pixels=int(demote_torso.sum()),
        transferred_hair_pixels=int(moved_hair.sum()),
        transferred_torso_pixels=int(moved_torso.sum()),
        transferred_unknown_pixels=int(moved_unknown.sum()),
        inherited_components={k:count_components(original[k]) for k in PARTS},
        repaired_components={k:count_components(new[k]) for k in PARTS},
        leaf_overlap_pixels=int((count_leaves>1).sum()),
        signed_union_xor_pixels=int(np.logical_xor(new_union,old_union).sum()),
        protected_xor_pixels=sum(int(np.logical_xor(original[k],new[k]).sum()) for k in PROTECTED),
        parent_head_xor_pixels=int(np.logical_xor(original['head'],new['head']).sum()),
        neck_torso_gap_old=neck_torso_gap(original['neck'],original['torso']),
        neck_torso_gap_new=neck_torso_gap(new['neck'],new['torso']),
        reserved_original_torso_bridge_pixels=int(bridge.sum())
    )
    if report.neck_torso_gap_new>max(6.,min(alpha.shape)*.06):
        raise Hold('neck-to-torso structural relation missing after proposed repair')
    if any(report.inherited_components[k]!=report.repaired_components[k] for k in ('head','hair','torso')):
        raise Hold('H04 required topology differs')
    return new,core,report
