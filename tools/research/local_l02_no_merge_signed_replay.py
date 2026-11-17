"""Known H06/H08 signed replay of source-only guarded sleeve topology.

Reads PRIVATE Drive bundles supplied by the operator. No private bytes, masks,
coordinates or human annotation geometry are written to stdout or GitHub.
Human review masks are loaded strictly AFTER both proposals have returned.
Known cases are exposed research, never an unseen holdout or Golden approval.
"""
from __future__ import annotations
import argparse,base64,hashlib,io,json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
from PIL import Image
from scipy import ndimage
from local_l02_guarded_sleeve_geodesic_shadow import propose_guarded_sleeve
from local_l02_sleeve_no_merge_shadow import propose_sleeve_without_frozen_component_merges

REVIEW='MinimalizerLocal_L02_ReviewedEvidence_PRIVATE_20261016.zip'
SLEEVE='MinimalizerLocal_L02_SleeveSemanticIndependent_PRIVATE_20261016.zip'
OWNER='LaneA_L02_Run30_KnownCase_OwnerMasks_PRIVATE_20261019.zip'
ANIME='Minimalizer_L02_AnimeSeg_H06_H08_Offline384_PRIVATE_20261015.zip'
PIN={
 REVIEW:'6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598',
 OWNER:'6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c',
 SLEEVE:'a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7',
 ANIME:'9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26',
}

def verify_archives(folder):
    for fn,sha in PIN.items():
        if hashlib.sha256((folder/fn).read_bytes()).hexdigest()!=sha:
            raise ValueError('PRIVATE_ARCHIVE_SHA_MISMATCH: '+fn)
    checks={}
    for fn,manifest_name in ((REVIEW,'MANIFEST_SHA256.json'),
                             (OWNER,'SHA256_MANIFEST.json'),
                             (ANIME,'PRIVATE_FILE_SHA256_MANIFEST.json')):
        with ZipFile(folder/fn) as z:
            d=json.loads(z.read(manifest_name))
            for name,digest in d.items():
                if hashlib.sha256(z.read(name)).hexdigest()!=digest:
                    raise ValueError('PRIVATE_MEMBER_SHA_MISMATCH')
            checks[fn]=len(d)
    return checks

def load_source_only(folder,name):
    if name not in ('H06','H08'):raise ValueError('UNPINNED_EXPOSED_CASE')
    with ZipFile(folder/REVIEW) as z:
        trace=json.loads(z.read(f'signed_human_review/{name}_trace.json'))
        audit=json.loads(z.read('reviews/H04_H06_H08_REVIEWED_ANNOTATION_AUDIT_PRIVATE.json'))
    raw=base64.b64decode(trace['image']['dataURL'].split(',',1)[1],validate=True)
    raw_sha=hashlib.sha256(raw).hexdigest()
    if raw_sha!=audit[name]['source_sha256']:
        raise ValueError('SIGNED_ORIGINAL_SOURCE_SHA_MISMATCH')
    rgba=np.asarray(Image.open(io.BytesIO(raw)).convert('RGBA')).copy()
    with ZipFile(folder/SLEEVE) as z:
        with np.load(io.BytesIO(z.read(f'{name}_SLEEVE_SEMANTIC_PRIVATE.npz')),allow_pickle=False) as data:
            cls=data['classids'].copy()
    with ZipFile(folder/OWNER) as z:
        with np.load(io.BytesIO(z.read(f'{name}_OWNER_4_PRIVATE.npz')),allow_pickle=False) as data:
            owner=data['owner'].copy()
    with ZipFile(folder/ANIME) as z:
        anime=np.asarray(Image.open(io.BytesIO(z.read(f'{name}_ANIMESEG_384_CLASSIDS_PRIVATE.png')))).copy()
    if any(x.shape!=rgba.shape[:2] for x in (cls,owner,anime)):
        raise ValueError('SIGNED_SHAPE_MISMATCH')
    return rgba,cls,owner,anime

def postscore(folder,name,owner):
    # No human masks have been loaded before this point.
    with ZipFile(folder/REVIEW) as z:
        with np.load(io.BytesIO(z.read(f'reviews/{name}_HUMAN_VISIBLE_MASKS_PRIVATE.npz')),allow_pickle=False) as data:
            positives=data['outerwear']>0
            known=np.zeros_like(positives,dtype=bool)
            for k in ('outerwear','underlayer','arm_skin','neck_skin','lower_body','face_skin','hair','accessory'):
                known |= data[k]>0
            tp=int(np.count_nonzero((owner>0)&positives))
            fp=int(np.count_nonzero((owner>0)&known&~positives))
            fn=int(np.count_nonzero((owner==0)&positives))
            return {'TP':tp,'known_FP':fp,'known_FN':fn,
                'known_IoU':round(tp/(tp+fp+fn),6),
                'known_arm_FP':int(np.count_nonzero((owner>0)&(data['arm_skin']>0))),
                'known_underlayer_FP':int(np.count_nonzero((owner>0)&(data['underlayer']>0)))}

def components(owner):
    return {f'owner{i}_{conn}':int(ndimage.label(owner==i,structure=ndimage.generate_binary_structure(2,1 if conn==4 else 2))[1]) for i in (1,2) for conn in (4,8)}

def run(folder):
    archive_checks=verify_archives(folder)
    rows=[]
    for name in ('H06','H08'):
        rgba,cls,owner,anime=load_source_only(folder,name)
        cand=(rgba[...,3]>0)&np.isin(cls,(5,10,32))
        kw=dict(class_ids=cls,anime_classes=anime,source_alpha=rgba[...,3],frozen_candidate=cand,frozen_owner=owner,connectivity=4)
        raw,_=propose_guarded_sleeve(**kw)
        safe,meta=propose_sleeve_without_frozen_component_merges(**kw)
        # Independently verify owner subset, no alpha0, frozen pixels unchanged.
        if (np.any((safe!=owner)&(owner!=0)) or np.any((safe>0)&(rgba[...,3]==0)) or
            np.any((safe!=owner)&~cand) or np.any((safe>0)&~np.isin(cls,(5,10,32)))):
            raise ValueError('INDEPENDENT_SOURCE_OR_OWNER_VIOLATION')
        rows.append({'case':name,'known_exposed_case_only':True,
                     'baseline':postscore(folder,name,owner),
                     'unguarded':postscore(folder,name,raw),
                     'topology_safe':postscore(folder,name,safe),
                     'components_before':components(owner),
                     'components_unguarded':components(raw),
                     'components_safe':components(safe),
                     'added_safe_pixels':meta['safe_added_pixels'],
                     'removed_unsafe_additions':meta['removed_uncertain_additions'],
                     'safe_owner_sha256':hashlib.sha256(safe.tobytes()).hexdigest()})
    return {'schema':'minimalizer/local-l02/signed-sleeve-topology-no-merge/v1',
            'archive_member_sha_checks':archive_checks,
            'cases':rows,'new_unseen_character_evaluation':'PENDING',
            'Phase4_semantic_quality':'FAIL','L02':'HOLD','L03':'NO_GO',
            'Golden':'HOLD','production':'NO_GO'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-dir',type=Path,required=True)
    args=p.parse_args();print(json.dumps(run(args.private_dir),sort_keys=True,indent=2))
