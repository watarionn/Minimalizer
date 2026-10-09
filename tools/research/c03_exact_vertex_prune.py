"""Read-only, SHA-pinned per-ring raster-exact vertex pruning feasibility.

Not a candidate for production. Per-ring exactness at 1x and 2x is a
strict sufficient (not necessary) condition for raster parity. No topology
or owner changes may be promoted from this diagnostic alone.
"""
from pathlib import Path
import hashlib
import json
import cv2
import numpy as np
from c03_stage8_budget_bounds import SIGNED


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(case, path):
    if case not in SIGNED:
        raise ValueError('UNKNOWN_CASE')
    raw=Path(path).read_bytes()
    if sha(raw)!=SIGNED[case]['scene_sha256']:
        raise ValueError('SCENE_PIN_FAIL')
    scene=json.loads(raw)
    if scene.get('original_source_sha256')!=SIGNED[case]['source_sha256']:
        raise ValueError('SOURCE_PIN_FAIL')
    if scene.get('research_only') is not True or scene.get('production_authorized') is not False:
        raise ValueError('PROMOTION_GUARD_FAIL')
    return scene


def parity_masks(points, candidate):
    # Equal bbox by evaluating candidate inside the original bounding ROI.
    # Candidates only delete original points, so they cannot expand bbox.
    pts=np.asarray(points,dtype=np.float64)
    q=np.asarray(candidate,dtype=np.float64)
    for scale in (1,2):
        p=np.rint(pts*scale).astype(np.int32)
        c=np.rint(q*scale).astype(np.int32)
        x0=int(p[:,0].min())-2; y0=int(p[:,1].min())-2
        x1=int(p[:,0].max())+3; y1=int(p[:,1].max())+3
        a=np.zeros((y1-y0,x1-x0),np.uint8)
        b=np.zeros_like(a)
        p-=np.array([x0,y0],np.int32);c-=np.array([x0,y0],np.int32)
        cv2.fillPoly(a,[p],1);cv2.fillPoly(b,[c],1)
        if not np.array_equal(a,b):return False
    return True


def signed_area(pts):
    p=np.asarray(pts,dtype=np.float64)
    return float(np.sum(p[:,0]*np.roll(p[:,1],-1)-np.roll(p[:,0],-1)*p[:,1]))/2


def greedy_prune(points):
    """Remove only existing vertices; preserve winding and 1x/2x per-ring pixels."""
    original=np.asarray(points,dtype=np.float64)
    if len(original)<4:return original.tolist()
    winding=np.sign(signed_area(original))
    if winding==0:return original.tolist()
    current=original.tolist()
    # Multiple passes allow chained safe deletions without coordinate edits.
    while True:
        changed=False
        for i in range(len(current)-1,-1,-1):
            if len(current)<=3:break
            candidate=current[:i]+current[i+1:]
            if np.sign(signed_area(candidate))!=winding:continue
            if parity_masks(original,candidate):
                current=candidate;changed=True
        if not changed:break
    return current


def audit(case,path):
    scene=load(case,path)
    orig=0;reduced=0;changed_rings=0;by_owner={};errors=[]
    for primitive in scene['primitives_back_to_front']:
        owner=primitive['composition_part']
        for ring in primitive['parameters']['rings']:
            pts=ring['points']; orig+=len(pts)
            after=greedy_prune(pts)
            reduced+=len(after)
            if len(after)!=len(pts):
                changed_rings+=1
                if not parity_masks(pts,after):errors.append('PIXEL_PARITY_FAIL')
            by_owner.setdefault(owner,{'before':0,'after':0})
            by_owner[owner]['before']+=len(pts);by_owner[owner]['after']+=len(after)
    if orig!=SIGNED[case]['ring_vertices']:raise ValueError('ORIGINAL_COUNT_FAIL')
    if errors:raise ValueError('RING_PARITY_FAIL')
    cap=SIGNED[case]['cap']
    return {'case':case,'source_scene_sha256':SIGNED[case]['scene_sha256'],
            'original_vertices':orig,'strict_pruned_vertices':reduced,
            'removed_vertices':orig-reduced,'rings_with_any_reduction':changed_rings,
            'immutable_original_cap':cap,'original_over_cap':orig-cap,
            'candidate_over_cap':max(0,reduced-cap),
            'by_owner':by_owner,'all_changed_rings_1x_2x_exact':True,
            'human_visual':'PENDING','topology_validation':'NOT_PROVEN',
            'whole_scene_chromium':'NOT_RUN','release_authorized':False,
            'production_changed':False}

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument('--gc-scene',type=Path,required=True)
    a.add_argument('--raden-scene',type=Path,required=True)
    a.add_argument('--output',type=Path,required=True)
    args=a.parse_args()
    v=[audit('GC001',args.gc_scene),audit('Raden',args.raden_scene)]
    args.output.write_text(json.dumps({'schema':'c03-strict-1x2x-ring-vertex-prune-v1','results':v,'production_changed':False,'release_authorized':False},ensure_ascii=False,indent=2)+'\n')
