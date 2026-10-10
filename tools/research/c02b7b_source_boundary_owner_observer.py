"""C02b7b: SHA-pinned, two-case source-boundary owner observation, NOT repair.

Independent image gradient, alpha, owner overlap, and GC001 historical revision
are observational signals, never ground-truth labels. No image pixels are generated.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import cv2
from c02b4_alpha_owner_authority_audit import PINS, read_source, read_scene, owner_mask
from c02b5_historical_phase04_lineage_audit import read_historical, read_current

OWNERS = ('right_arm', 'left_arm', 'hair', 'major_clothing')

def border(mask: np.ndarray) -> np.ndarray:
    if mask.dtype != np.bool_ or mask.shape != (340,340):
        raise ValueError('MASK_BOOL_SHAPE_REQUIRED')
    return mask & ~cv2.erode(mask.astype('uint8'),np.ones((3,3),np.uint8)).astype(bool)

def edge_cue(rgba: np.ndarray) -> np.ndarray:
    if rgba.shape!=(340,340,4): raise ValueError('SOURCE_RGBA_SHAPE_REQUIRED')
    gray=cv2.cvtColor(np.ascontiguousarray(rgba[:,:,:3]), cv2.COLOR_RGB2GRAY)
    edges=cv2.Canny(gray,50,120)>0
    return cv2.dilate(edges.astype('uint8'),np.ones((3,3),np.uint8)).astype(bool)

def inspect_owner(owner:np.ndarray, competitors:np.ndarray, rgba:np.ndarray, edges:np.ndarray) -> dict:
    if any(x.shape!=(340,340) for x in (owner,competitors,edges)) or rgba.shape!=(340,340,4):
        raise ValueError('MASK_SHAPE_REQUIRED')
    if any(x.dtype != np.bool_ for x in (owner,competitors,edges)):
        raise ValueError('MASK_BOOL_REQUIRED')
    b=border(owner)
    # Core only means stable raster interior, not an anatomical true-positive.
    core=cv2.erode(owner.astype('uint8'),np.ones((5,5),np.uint8)).astype(bool)
    alpha=rgba[:,:,3]
    return {'pixels':int(owner.sum()),'raster_core_5x5_pixels':int(core.sum()),
            'border_pixels':int(b.sum()),'border_near_source_canny_pixels':int((b & edges).sum()),
            'border_without_source_canny_pixels':int((b & ~edges).sum()),
            'overlap_with_other_declared_owners_pixels':int((owner & competitors).sum()),
            'alpha_zero_pixels':int((owner & (alpha==0)).sum()),
            'partial_alpha_pixels':int((owner & (alpha>0) & (alpha<255)).sum()),
            'source_boundary_is_anatomical_truth':False,'raster_core_is_semantic_truth':False}

def inspect_case(case:str, source:Path, scene:Path, snapshot:Path|None=None, historical:Path|None=None):
    if case not in PINS:raise ValueError('UNKNOWN_CASE')
    rgba=read_source(source,case)
    js=read_scene(scene,case)
    edges=edge_cue(rgba)
    owners={k:owner_mask(js,k) for k in OWNERS}
    records={}
    for k in OWNERS:
        other=np.logical_or.reduce([m for p,m in owners.items() if p!=k])
        records[k]=inspect_owner(owners[k],other,rgba,edges)
    historic_status='NOT_AVAILABLE'
    if case=='GC001':
        if snapshot is None or historical is None: raise ValueError('GC001_SIGNED_REVISION_INPUTS_REQUIRED')
        # Full SHA checks performed inside imported functions, including ZIP manifest.
        contrasts={}
        for arm in ('right_arm','left_arm'):
            h=read_historical(historical,arm)
            c=read_current(snapshot,arm)
            s=owners[arm]
            contrasts[arm]={'historical_stage8_xor':int((h^s).sum()),
                            'current_stage8_xor':int((c^s).sum()),
                            'historical_current_xor':int((h^c).sum()),
                            'historical_and_current_and_stage8_pixels':int((h&c&s).sum()),
                            'equivalence_is_semantic_ground_truth':False}
        historic_status=contrasts
    elif snapshot is not None or historical is not None:
        raise ValueError('RADEN_GC001_LINEAGE_INPUTS_FORBIDDEN')
    return {'case':case,'source_sha256':PINS[case]['source'],
            'stage8_scene_sha256':PINS[case]['stage8'],
            'owners':records,'GC001_lineage_differences':historic_status,
            'independent_semantic_ground_truth':'NOT_AVAILABLE',
            'suitable_for_owner_mutation':False}

def run(gc_source:Path,gc_scene:Path,raden_source:Path,raden_scene:Path,gc_snapshot:Path,historical:Path):
    cases=[inspect_case('GC001',gc_source,gc_scene,gc_snapshot,historical),
           inspect_case('Raden',raden_source,raden_scene)]
    return {'schema':'sa1060k-c02b7b-source-boundary-owner-observer-v1',
            'cases':cases,'candidate':'NONE',
            'reason':'NO_INDEPENDENT_SEMANTIC_OWNER_GROUND_TRUTH',
            'valid_observations':['source_rgb_edge_proximity','raster_core','declared_owner_overlap',
                'source_alpha','gc001_revision_comparison'],
            'all_observations_are_non_authoritative':True,
            'C02':'IN_PROGRESS','C03':'HOLD','C04':'HOLD','C05_C08':'BLOCKED',
            'human_golden':'PENDING','real_canonical_chromium':'NOT_RUN',
            'approved18_78':'NOT_RUN','release_authorized':False,
            'production_changed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('gc_source','gc_scene','raden_source','raden_scene','gc_snapshot','historical','output'):
        p.add_argument('--'+k.replace('_','-'),required=True,type=Path)
    a=p.parse_args(); dest=a.output.resolve(); sources=[a.gc_source,a.gc_scene,a.raden_source,a.raden_scene,a.gc_snapshot]
    if any(dest==x.resolve() for x in sources) or dest==a.historical.resolve():
        raise ValueError('OUTPUT_OVERWRITES_INPUT')
    data=run(a.gc_source,a.gc_scene,a.raden_source,a.raden_scene,a.gc_snapshot,a.historical)
    if dest.exists():raise ValueError('OUTPUT_EXISTS')
    dest.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'schema':data['schema'],'cases':[{'case':z['case'],'owners':list(z['owners'])} for z in data['cases']], 'release_authorized':False}))
