"""SA10.49 non-generative source evidence dual-gate audit.

Research-only. Read signed source and frozen flat Stage37 reference; never invent,
reconstruct, draw or export facial features as new artwork. Fail closed on hashes.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1043_boundary_compaction as raden
import sa1046_gc001_positive_holdout as gc001

CASES={
 'Raden':{'root_required':raden.SHA,'image':'Raden_source.png','budget':1412,'champion':{'vertices':1409,'flat_rgb_mismatch':882}},
 'GC001':{'root_required':gc001.EXPECTED_SHA,'image':'GC001_source.png','budget':1887,'champion':{'vertices':1883,'flat_rgb_mismatch':1871}},
}
ROLES=('face','left_arm','right_arm')

def load_case(name: str, directory:Path)->dict:
    spec=CASES[name]
    root=directory.resolve()
    for filename, digest in spec['root_required'].items():
        if hashlib.sha256((root/filename).read_bytes()).hexdigest()!=digest:
            raise ValueError('SIGNED_SOURCE_HASH_MISMATCH '+name+' '+filename)
    photo=np.asarray(Image.open(root/spec['image']).convert('RGB'),dtype=np.uint8)
    frozen=np.asarray(Image.open(root/'signed_full_opencv_reference.png').convert('RGB'),dtype=np.uint8)
    if photo.shape != (340,340,3) or frozen.shape != photo.shape:raise ValueError('CANVAS_MISMATCH')
    masks={role:np.asarray(Image.open(root/f'signed_{role}_stage04_mask.png').convert('L'))>0 for role in ROLES}
    return {'photo':photo,'frozen':frozen,'masks':masks,'spec':spec,'root':root}

def audit(case:dict)->dict:
    photo,frozen=case['photo'],case['frozen']
    result={}; protected_union=np.logical_or.reduce(list(case['masks'].values()))
    for role,mask in case['masks'].items():
        a,b=photo[mask],frozen[mask]
        difference=np.any(a!=b,axis=1)
        photo_colors,ncounts=np.unique(a,axis=0,return_counts=True)
        flat_colors=np.unique(b,axis=0)
        dominant=photo_colors[np.argmax(ncounts)].tolist()
        # RGB differences measured in original source; not a reconstructed drawing.
        top3=sorted(ncounts.tolist(),reverse=True)[:3]
        gray=cv2.cvtColor(photo,cv2.COLOR_RGB2GRAY)
        gx=cv2.Sobel(gray,cv2.CV_32F,1,0,ksize=3)
        gy=cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3)
        gradient=cv2.magnitude(gx,gy)
        internal=cv2.erode(mask.astype(np.uint8),np.ones((3,3),np.uint8),iterations=2)>0
        result[role]={
          'source_pixels':int(mask.sum()),'source_vs_flat_rgb_mismatch':int(difference.sum()),
          'source_vs_flat_rgb_match':int((~difference).sum()),
          'source_distinct_rgb_colors':int(len(photo_colors)),
          'frozen_distinct_rgb_colors':int(len(flat_colors)),
          'photo_dominant_rgb':dominant,'top3_photo_color_frequencies':top3,
          'interior_edge_gradient_gt_64_pixels':int(np.count_nonzero(internal & (gradient>64))),
          'interior_edge_gradient_gt_128_pixels':int(np.count_nonzero(internal & (gradient>128))),
          'structural_preservation_target':'signed_stage04_mask',
          'source_detail_evidence_target':'original_source_rgb',
          'flat_rgb_parity_and_source_detail_can_both_be_exact':bool(not difference.any())
        }
    outside=~protected_union
    outside_changes=np.any(photo!=frozen,axis=2)&outside
    result['outside_protected']={'source_pixels':int(outside.sum()),'photo_vs_flat_mismatch':int(outside_changes.sum()),
       'source_color_unique':int(len(np.unique(photo[outside],axis=0))),
       'frozen_color_unique':int(len(np.unique(frozen[outside],axis=0)))}
    result['all_face_fidelity_and_flat_face_gate_simultaneously_satisfiable']=result['face']['flat_rgb_parity_and_source_detail_can_both_be_exact']
    return result

def evaluate(raden_root:Path,gc001_root:Path,out:Path)->dict:
    roots=[raden_root.resolve(),gc001_root.resolve()];out=out.resolve()
    if roots[0]==roots[1] or any(out==p or out in p.parents or p in out.parents for p in roots):
        raise ValueError('Source and output locations must be distinct')
    cases={n:load_case(n,p) for n,p in zip(CASES,roots)}
    report={'stage':'SA10.49','schema':'source-observed-detail-dual-gate-v1',
      'source_authority_hash_verified':True,'artistic_generation_performed':False,
      'new_facial_anatomy_synthesized':False,'svg_modified':False,
      'production_deployment':'UNCHANGED','full_character_golden':'HOLD',
      'gate_policy':{'source_shape':'signed Stage04 masks unchanged',
       'legacy_flat_rgb':'diagnostic of Stage37 flat reference only, not artistic identity',
       'source_detail':'compare original source RGB within signed original masks',
       'release':'Never equate flat-face RGB=0 with preserving facial features'},'cases':{}}
    out.mkdir(parents=True,exist_ok=True)
    board=Image.new('RGB',(340*2,380*2),(245,245,241));draw=ImageDraw.Draw(board)
    for row,(name,case) in enumerate(cases.items()):
        detail=audit(case)
        report['cases'][name]={'details':detail,'historical_budget':case['spec']['budget'],
           'previous_champion_unmodified':case['spec']['champion'],
           'input_source_sha256':hashlib.sha256((case['root']/case['spec']['image']).read_bytes()).hexdigest(),
           'source_fidelity_and_flat_face_parity_are_mutually_exclusive':not detail['all_face_fidelity_and_flat_face_gate_simultaneously_satisfiable']}
        for col,key in enumerate(('photo','frozen')):
            board.paste(Image.fromarray(case[key]),(col*340,row*380+40))
            draw.text((col*340+8,row*380+14),name+' / '+('ORIGINAL SOURCE' if col==0 else 'SIGNED FLAT CV2'),fill=(30,30,30))
    board.save(out/'two_case_source_vs_flat_authority.png')
    report['full_character_visual_quality_approved']=False
    report['face_detail_drawing_next_step']='Requires source-exact feature vectorization with distinct fidelity gate; forbidden to call flat-face RGB=0 a feature restoration.'
    report['asset_sha256']={'two_case_source_vs_flat_authority.png':hashlib.sha256((out/'two_case_source_vs_flat_authority.png').read_bytes()).hexdigest()}
    (out/'sa1049_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raden',type=Path,required=True);p.add_argument('--gc001',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();data=evaluate(args.raden,args.gc001,args.out)
    print(json.dumps({'stage':data['stage'],'cases':{k:v['details'] for k,v in data['cases'].items()}},ensure_ascii=False,indent=2))
