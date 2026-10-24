"""Research-only minimum frozen-owner path restoration after hue abstention.

Restore *only previously owned source pixels* when color abstention disconnects a
4-connected owner component. This is a structural hypothesis, not a proof that
restored paths are garments. No human labels, coordinates, image generation,
or new package dependency is used.
"""
from __future__ import annotations
from collections import deque
import numpy as np
from scipy import ndimage
from local_l02_hue_seed_contact_shadow import propose_hue_conflict_seed_contact_guard

class TopologyRepairHold(ValueError):
    pass


def _bridge_one_component(old_component, current, owner_id, blocked=None):
    """Connect one 4-neighbour fragment to the largest one via removed pixels."""
    st=ndimage.generate_binary_structure(2,1)
    labels,n=ndimage.label(current & old_component,structure=st)
    if n <= 1:
        return 0
    counts=np.bincount(labels.ravel(),minlength=n+1)
    counts[0]=0
    main=int(np.argmax(counts))
    if blocked is None:
        blocked=np.zeros_like(old_component,dtype=bool)
    if blocked.shape != old_component.shape or blocked.dtype != np.bool_:
        raise TopologyRepairHold('INVALID_BLOCKED_MASK')
    # A restored path may never pass through an abstained fragment that also
    # touches a competing owner. Such a path is not semantically established.
    available=old_component & ~blocked
    removed=available & ~current
    frontier=ndimage.binary_dilation(labels==main,structure=st) & removed
    h,w=current.shape
    visited=np.zeros((h,w),dtype=bool)
    predecessor=np.full((h,w),-1,dtype=np.int32)
    q=deque()
    for flat in np.flatnonzero(frontier):
        flat=int(flat);y,x=divmod(flat,w)
        visited[y,x]=True
        q.append(flat)
    end=-1
    while q:
        flat=q.popleft()
        y,x=divmod(flat,w)
        for yy,xx in ((y-1,x),(y,x-1),(y,x+1),(y+1,x)):
            if yy<0 or xx<0 or yy>=h or xx>=w or not available[yy,xx]:
                continue
            other=int(labels[yy,xx])
            if other and other!=main:
                end=flat
                break
            if removed[yy,xx] and not visited[yy,xx]:
                visited[yy,xx]=True
                predecessor[yy,xx]=flat
                q.append(yy*w+xx)
        if end>=0:
            break
    if end<0:
        raise TopologyRepairHold('NO_FROZEN_OWNER_PATH')
    restored=0
    while end>=0:
        y,x=divmod(end,w)
        if not current[y,x]:
            current[y,x]=True
            restored+=1
        end=int(predecessor[y,x])
    return restored


def propose_hue_topology_repair_shadow(source_rgba, class_ids, frozen_owner):
    provisional,meta=propose_hue_conflict_seed_contact_guard(
        source_rgba,class_ids,frozen_owner
    )
    out=provisional.copy()
    st=ndimage.generate_binary_structure(2,1)
    bridges=0
    pixels=0
    for owner_id in (1,2):
        original=frozen_owner==owner_id
        original_ids,n=ndimage.label(original,structure=st)
        # Cache the independent competing-owner contact mask once per owner.
        competing=(frozen_owner!=0)&(frozen_owner!=owner_id)
        touching=ndimage.binary_dilation(competing,structure=np.ones((3,3),dtype=np.uint8))
        for i in range(1,n+1):
            old_comp=original_ids==i
            current=out==owner_id
            if not np.any(current & old_comp):
                raise TopologyRepairHold('ORIGINAL_OWNER_COMPONENT_ERASED')
            # A complete removed 8-connected fragment touching a competing
            # frozen owner is ambiguous; keep every pixel in it abstained.
            removed=old_comp & (out!=owner_id)
            if not np.any(removed):
                continue
            removed_ids,removed_n=ndimage.label(removed,structure=np.ones((3,3),dtype=np.uint8))
            blocked_ids=np.unique(removed_ids[removed & touching])
            blocked_ids=blocked_ids[blocked_ids>0]
            blocked_lookup=np.zeros(removed_n+1,dtype=bool)
            blocked_lookup[blocked_ids]=True
            blocked=blocked_lookup[removed_ids]
            # Never reconnect two distinct original components or invent pixels.
            while True:
                new_count=ndimage.label(current & old_comp,structure=st)[1]
                if new_count<=1:
                    break
                delta=_bridge_one_component(old_comp,current,owner_id,blocked=blocked)
                if delta<=0:
                    raise TopologyRepairHold('NO_REPAIR_PROGRESS')
                pixels+=delta
                bridges+=1
            out[old_comp & current]=owner_id
        if ndimage.label(out==owner_id,structure=st)[1]!=n:
            raise TopologyRepairHold('OWNER_TOPOLOGY_NOT_RESTORED')
    if np.any((out!=0)&(out!=frozen_owner)):
        raise TopologyRepairHold('OWNER_PROMOTION')
    if np.any((out>0)&(source_rgba[:,:,3]==0)):
        raise TopologyRepairHold('SOURCE_ALPHA')
    return out, {
        **meta,
        'schema':'minimalizer/l02/hue-topology-repair-shadow/v1',
        'topology_bridges_restored':int(bridges),
        'topology_original_owner_pixels_restored':int(pixels),
        'final_abstained_pixels':int(np.count_nonzero(out!=frozen_owner)),
        'owner_promotions':0,
        'semantic_quality_pass':False,
        'release_authorized':False,
    }
