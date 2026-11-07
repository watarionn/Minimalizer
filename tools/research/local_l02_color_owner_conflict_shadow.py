"""Source-only research veto for large owner color modes unsupported by an independent observer.

Never uses human annotations, hard-coded image coordinates or postscore labels.
Only removes already assigned owner pixels; all unknown pixels remain unknown.
A proposal must preserve every original owner component's 4/8 connectivity identity.
No known-case quality or unseen generalization is implied.
"""
import numpy as np
import cv2
from scipy.spatial import cKDTree
from local_l02_hue_extended_owner_shadow import _assert_component_identity,ExtendedOwnerHold
from local_l02_hue_topology_repair_shadow import _bridge_one_component,TopologyRepairHold
from scipy import ndimage

class ColorOwnerConflictHold(ValueError): pass

def propose_color_owner_conflict_shadow(*,source_rgba,class_ids,independent_outerwear,frozen_owner):
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype!=np.uint8 or
        source_rgba.ndim!=3 or source_rgba.shape[2]!=4 or not source_rgba.size):
        raise ColorOwnerConflictHold('INVALID_SOURCE')
    shape=source_rgba.shape[:2]
    if any(type(a) is not np.ndarray or a.shape!=shape or a.dtype!=np.uint8
           for a in (class_ids,independent_outerwear,frozen_owner)):
        raise ColorOwnerConflictHold('INVALID_OBSERVERS')
    if np.any(class_ids>=47) or np.any(frozen_owner>2) or np.any(independent_outerwear>1):
        raise ColorOwnerConflictHold('INVALID_DOMAIN')
    if np.any((frozen_owner>0)&(source_rgba[...,3]==0)):
        raise ColorOwnerConflictHold('OUTSIDE_SIGNED_ALPHA')
    if np.any((frozen_owner==1)&~np.isin(class_ids,(5,32,29,30,31))) or np.any((frozen_owner==2)&~np.isin(class_ids,(10,32,29,30,31))):
        raise ColorOwnerConflictHold('OWNER_CLASS_MISMATCH')
    domain=(frozen_owner==2)&(class_ids==10)&(source_rgba[...,3]>0)
    count=int(domain.sum())
    if count<4000 or int(independent_outerwear[domain].sum())<1000:
        return frozen_owner.copy(),dict(reason='INSUFFICIENT_SUPPORT',removed_px=0,quality='FAIL')
    lab=cv2.cvtColor(source_rgba[...,:3],cv2.COLOR_RGB2LAB)
    values=lab[domain].astype(np.float32)
    samples=values[::max(1,len(values)//50000)]
    cv2.setRNGSeed(20261022)
    try:
        _,_,centers=cv2.kmeans(samples,4,None,(cv2.TERM_CRITERIA_MAX_ITER+cv2.TERM_CRITERIA_EPS,40,0.15),3,cv2.KMEANS_PP_CENTERS)
    except cv2.error as e:raise ColorOwnerConflictHold('CLUSTER_FAIL') from e
    ids=cKDTree(centers).query(values,workers=1)[1]
    sizes=np.bincount(ids,minlength=4)
    support=np.bincount(ids,weights=independent_outerwear[domain],minlength=4)
    rates=support/sizes
    ordered=np.argsort(rates,kind='stable')
    low,second=int(ordered[0]),int(ordered[1])
    # Fixed, exploratory evidence-separation policy. Not tuned against labels.
    if not (rates[low]*4<rates[second] and rates[ordered[-1]]>=.25 and sizes[low]>=.01*count):
        return frozen_owner.copy(),dict(reason='NO_CLEAR_SUPPORT_GAP',removed_px=0,quality='FAIL')
    # Preserve every pixel independently supported as outerwear.
    changed=(ids==low)&(independent_outerwear[domain]==0)
    out=frozen_owner.copy()
    out[domain]=np.where(changed,0,frozen_owner[domain])
    # Preserve topology with a minimal path of ORIGINAL owner pixels only.
    st4=ndimage.generate_binary_structure(2,1)
    st8=ndimage.generate_binary_structure(2,2)
    bridge_px=0
    for owner_id in (1,2):
        old_labels,n=ndimage.label(frozen_owner==owner_id,structure=st4)
        current=out==owner_id
        removed=(frozen_owner==owner_id)&~current
        removed_labels,removed_n=ndimage.label(removed,structure=st8)
        competing=(frozen_owner>0)&(frozen_owner!=owner_id)
        touched=removed & ndimage.binary_dilation(competing,structure=st8)
        blocked_ids=np.unique(removed_labels[touched]);blocked_ids=blocked_ids[blocked_ids>0]
        lookup=np.zeros(removed_n+1,dtype=bool);lookup[blocked_ids]=True
        blocked=lookup[removed_labels]&removed
        for k in range(1,n+1):
            component=old_labels==k
            if not np.any(component&current):raise ColorOwnerConflictHold('OWNER_COMPONENT_REMOVED')
            while ndimage.label(component&current,structure=st4)[1]>1:
                try:delta=_bridge_one_component(component,current,owner_id,blocked=blocked)
                except TopologyRepairHold as e:raise ColorOwnerConflictHold('NO_SAFE_ORIGINAL_OWNER_BRIDGE') from e
                if delta<=0:raise ColorOwnerConflictHold('NO_BRIDGE_PROGRESS')
                bridge_px+=delta
        out[(frozen_owner==owner_id)&current]=owner_id
        for connectivity in (4,8):
            try:_assert_component_identity(frozen_owner,out,owner_id,connectivity)
            except ExtendedOwnerHold as e:raise ColorOwnerConflictHold('OWNER_TOPOLOGY_CHANGED') from e
    if np.any((out>0)&(out!=frozen_owner)) or np.any((out>0)&(source_rgba[...,3]==0)):
        raise ColorOwnerConflictHold('SOURCE_OWNER_VIOLATION')
    return out,dict(schema='minimalizer/local-l02/color-owner-conflict-shadow/v0',reason='RESEARCH_ONLY',removed_px=int(np.count_nonzero((frozen_owner>0)&(out==0))),restored_bridge_px=int(bridge_px),cluster_sizes=sizes.astype(int).tolist(),independent_support_rates=[round(float(x),6) for x in rates],source_pixels_generated=0,owner_promotions=0,human_annotations_used_for_inference=False,unseen_character_pass=False,semantic_quality_pass=False,quality='FAIL',L02='HOLD',L03='NO_GO',Golden='HOLD',production='NO_GO')
