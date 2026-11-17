"""Research-only conservative topology admission for frozen class32 sleeve proposals.

This *postproposal* source-only guard never invents source pixels or changes a
frozen owner. It removes uncertain sleeve additions at component collision
boundaries and any detached additions, so independently disconnected frozen
jacket/coat components cannot silently merge. No human labels are inputs.
It is not semantic correctness or release approval.
"""
from collections import deque
import numpy as np
from scipy import ndimage
from local_l02_guarded_sleeve_geodesic_shadow import propose_guarded_sleeve

class SleeveNoMergeHold(ValueError):
    pass


def _neighbors(connectivity):
    n = ((-1,0),(0,-1),(0,1),(1,0))
    if connectivity==8:
        n += ((-1,-1),(-1,1),(1,-1),(1,1))
    return n


def _cut_collisions(frozen, current, owner_id, connectivity):
    """Conservatively cut only *added* pixels, never frozen components."""
    st = ndimage.generate_binary_structure(2, 1 if connectivity==4 else 2)
    original = frozen==owner_id
    orig_labels, orig_n = ndimage.label(original,structure=st)
    if orig_n<=1:
        # Still remove orphan additions that cannot reach any frozen seed.
        labels,n=ndimage.label(current==owner_id,structure=st)
        seeded=np.unique(labels[original]);seeded=seeded[seeded>0]
        orphan=(current==owner_id)&(frozen==0)&~np.isin(labels,seeded)
        current[orphan]=0
        return int(orphan.sum())
    h,w=frozen.shape
    region=current==owner_id
    # Original owners are immutable and must be present in candidate.
    if np.any(original & ~region):raise SleeveNoMergeHold('FROZEN_OWNER_CHANGED')
    # Multi-source geodesic Voronoi labels within the proposal, with a fixed
    # deterministic queue order. This is only for cutting unsafe joins.
    comp=np.zeros((h,w),dtype=np.int32)
    distance=np.full((h,w),-1,dtype=np.int32)
    comp[original]=orig_labels[original]
    distance[original]=0
    q=deque(int(i) for i in np.flatnonzero(original))
    steps=_neighbors(connectivity)
    while q:
        idx=q.popleft();y,x=divmod(idx,w)
        for dy,dx in steps:
            yy=y+dy;xx=x+dx
            if yy<0 or xx<0 or yy>=h or xx>=w or not region[yy,xx]:continue
            if distance[yy,xx]==-1:
                distance[yy,xx]=distance[y,x]+1
                comp[yy,xx]=comp[y,x]
                q.append(yy*w+xx)
    # Remove all newly added pixels at a collision edge. This is intentionally
    # symmetric: arbitrary component ordering must not decide owner authority.
    boundary=np.zeros((h,w),dtype=bool)
    for dy,dx in steps:
        ys=slice(max(0,-dy),min(h,h-dy));xs=slice(max(0,-dx),min(w,w-dx))
        yt=slice(max(0,dy),min(h,h+dy));xt=slice(max(0,dx),min(w,w+dx))
        a=comp[ys,xs];b=comp[yt,xt]
        conflict=(a>0)&(b>0)&(a!=b)
        boundary[ys,xs]|=conflict
        boundary[yt,xt]|=conflict
    removed=boundary & (current==owner_id) & (frozen==0)
    current[removed]=0
    # Strip candidate fragments disconnected from their original owner.
    labels,n=ndimage.label(current==owner_id,structure=st)
    seeded=np.unique(labels[original]);seeded=seeded[seeded>0]
    orphan=(current==owner_id)&(frozen==0)&~np.isin(labels,seeded)
    current[orphan]=0
    return int(removed.sum()+orphan.sum())


def propose_sleeve_without_frozen_component_merges(*,class_ids,anime_classes,
                source_alpha,frozen_candidate,frozen_owner,connectivity=4):
    raw,meta=propose_guarded_sleeve(class_ids=class_ids,
        anime_classes=anime_classes,source_alpha=source_alpha,
        frozen_candidate=frozen_candidate,frozen_owner=frozen_owner,
        connectivity=connectivity)
    out=raw.copy()
    removed=0
    for conn in (4,8):
        for owner_id in (1,2):
            removed+=_cut_collisions(frozen_owner,out,owner_id,conn)
    # Validate component bijection, not just counts. A merge, split or island
    # would change the number or correspondence of original components.
    for conn in (4,8):
        st=ndimage.generate_binary_structure(2,1 if conn==4 else 2)
        for owner_id in (1,2):
            orig,n=ndimage.label(frozen_owner==owner_id,structure=st)
            new,m=ndimage.label(out==owner_id,structure=st)
            if n!=m:raise SleeveNoMergeHold('FROZEN_COMPONENT_MERGE_OR_NEW_ISLAND')
            pairs=np.unique(np.stack((orig[frozen_owner==owner_id],new[frozen_owner==owner_id]),axis=1),axis=0)
            if len(pairs)!=n or len(np.unique(pairs[:,0]))!=n or len(np.unique(pairs[:,1]))!=m:
                raise SleeveNoMergeHold('FROZEN_COMPONENT_IDENTITY_CHANGED')
    if np.any((out!=frozen_owner)&(frozen_owner!=0)) or np.any((out>0)&(source_alpha==0)):
        raise SleeveNoMergeHold('FROZEN_OR_ALPHA_VIOLATION')
    return out,{
        'schema':'minimalizer/local-l02/sleeve-no-frozen-component-merge-shadow/v1',
        'raw_added_pixels':int(np.count_nonzero((raw>0)&(frozen_owner==0))),
        'safe_added_pixels':int(np.count_nonzero((out>0)&(frozen_owner==0))),
        'removed_uncertain_additions':int(removed),
        'frozen_owner_modified_pixels':0,'source_pixels_generated':0,
        'unseen_character_quality_pass':False,'semantic_quality_pass':False,
        'quality':'FAIL','L02':'HOLD','L03':'NO_GO','Golden':'HOLD','production':'NO_GO',
        'upstream_guard':meta['schema'],
    }
