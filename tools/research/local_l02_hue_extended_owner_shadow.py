"""Source-only H06 research: hue abstention with preserved frozen lapel owner.

A frozen owner may contain class29/30/31 extension pixels. This adapter runs
an existing, fixed hue-conflict hypothesis on class5/10/32 only and preserves
those extensions unchanged. Fail closed if 4/8 component identity changes.
Human labels are strictly postscore-only. Not a release/Phase4 approval.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage
from local_l02_hue_topology_repair_shadow import propose_hue_topology_repair_shadow

class ExtendedOwnerHold(ValueError):
    pass

def _assert_component_identity(before, after, owner_id, connectivity):
    st=ndimage.generate_binary_structure(2,1 if connectivity==4 else 2)
    old_labels, old_n=ndimage.label(before==owner_id,structure=st)
    new_labels, new_n=ndimage.label(after==owner_id,structure=st)
    if old_n != new_n:
        raise ExtendedOwnerHold('OWNER_COMPONENT_COUNT_CHANGED')
    if old_n == 0:
        return 0
    # Every original component must survive, remain whole, and map to a
    # different new component. No component may be joined or split.
    survivor=(before==owner_id)&(after==owner_id)
    pairs=np.unique(np.stack((old_labels[survivor],new_labels[survivor]),axis=1),axis=0)
    if (len(pairs)!=old_n or np.any(pairs==0) or
        len(np.unique(pairs[:,0]))!=old_n or len(np.unique(pairs[:,1]))!=new_n):
        raise ExtendedOwnerHold('OWNER_COMPONENT_IDENTITY_CHANGED')
    return int(old_n)

def propose_hue_extended_owner_shadow(*, source_rgba, class_ids, frozen_owner):
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype!=np.uint8
        or source_rgba.ndim!=3 or source_rgba.shape[-1]!=4 or not source_rgba.size):
        raise ExtendedOwnerHold('INVALID_RGBA')
    shape=source_rgba.shape[:2]
    if any(type(a) is not np.ndarray or a.dtype!=np.uint8 or a.shape!=shape
           for a in (class_ids,frozen_owner)):
        raise ExtendedOwnerHold('INVALID_CLASS_OR_OWNER')
    if np.any(class_ids>=47) or np.any(frozen_owner>2):
        raise ExtendedOwnerHold('CLASS_DOMAIN')
    if np.any((frozen_owner>0)&(source_rgba[...,3]==0)):
        raise ExtendedOwnerHold('OWNER_OUTSIDE_SOURCE')
    if (np.any((frozen_owner==1)&~np.isin(class_ids,(5,32,29,30,31))) or
        np.any((frozen_owner==2)&~np.isin(class_ids,(10,32,29,30,31)))):
        raise ExtendedOwnerHold('OWNER_CLASS_CONFLICT')
    extension=(frozen_owner>0)&np.isin(class_ids,(29,30,31))
    core=frozen_owner.copy()
    core[extension]=0
    core_result,hue_meta=propose_hue_topology_repair_shadow(source_rgba,class_ids,core)
    result=core_result.copy()
    result[extension]=frozen_owner[extension]
    removed=(frozen_owner>0)&(result==0)
    if (np.any((result!=0)&(result!=frozen_owner)) or
        np.any(removed&(class_ids!=32)) or
        np.any(result[extension]!=frozen_owner[extension]) or
        np.any((result>0)&(source_rgba[...,3]==0))):
        raise ExtendedOwnerHold('FROZEN_SOURCE_OR_EXTENSION_VIOLATION')
    components={}
    for owner_id in (1,2):
        for connectivity in (4,8):
            components[f'owner{owner_id}_{connectivity}']=_assert_component_identity(
                frozen_owner,result,owner_id,connectivity)
    return result,{
        'schema':'minimalizer/local-l02/hue-extended-owner-shadow/v1',
        'removed_class32_owner_pixels':int(removed.sum()),
        'unchanged_extension_pixels':int(extension.sum()),
        'source_pixels_generated':0,'owner_promotions':0,
        'component_identity_4_8_preserved':components,
        'hue_stage':hue_meta,
        'human_annotations_used_for_inference':False,
        'semantic_quality_pass':False,'unseen_character_pass':False,
        'L02':'HOLD','L03':'NO_GO','Golden':'HOLD','production':'NO_GO',
    }
