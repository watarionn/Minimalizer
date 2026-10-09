"""Minimalizer C02b1: source-signed structural-pose arm corridor *risk proposal*.

No synthetic pixels; never replace source owner, Stage8 history or SVG. The
COCO17 wrist confidence must pass independently before artwork promotion.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
from io import BytesIO
import cv2,numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1060c_phase03_phase04_provenance as phase
import sa1060b_first_bad_stage_audit as old

FACTORS=(0.20,0.27,0.34)
RIGHT_INDICES=(6,8,10)  # COCO17 right shoulder/elbow/wrist; verify confidence.
MIN_POSE_SCORE=0.60

def signed_corridor(mask:np.ndarray,points:np.ndarray,scores:np.ndarray,span:float,factor:float):
    if factor not in FACTORS:raise ValueError('UNAPPROVED_CORRIDOR_FACTOR')
    if mask.shape!=(340,340) or points.shape!=(17,2) or scores.shape!=(17,):raise ValueError('UNVERIFIED_POSE_CANVAS')
    if not np.all(np.isfinite(points)) or not np.all(np.isfinite(scores)) or not np.isfinite(span) or span<=0:
        raise ValueError('INVALID_POSE_EVIDENCE')
    corridor=np.zeros(mask.shape,np.uint8)
    thick=max(5,int(round(2*span*factor)))
    for a,b in ((6,8),(8,10)):
        cv2.line(corridor,tuple(np.rint(points[a]).astype(int)),tuple(np.rint(points[b]).astype(int)),1,thick,cv2.LINE_8)
    candidate=mask & (corridor>0)
    confidence=[float(scores[i]) for i in RIGHT_INDICES]
    min_conf=min(confidence)
    cc,_=cv2.connectedComponents(candidate.astype(np.uint8),8)
    return candidate,corridor>0,{'factor':factor,'width_px':thick,'mask_pixels_before':int(mask.sum()),
            'candidate_pixels':int(candidate.sum()),'removed_pixels':int(np.count_nonzero(mask&~candidate)),
            'added_pixels':int(np.count_nonzero(candidate&~mask)),
            'candidate_connected_components':cc-1,
            'right_shoulder_elbow_wrist_scores':confidence,
            'min_right_pose_score':min_conf,'pose_confidence_pass':min_conf>=MIN_POSE_SCORE}

def run(source:Path,signed_root:Path,snapshot:Path,out:Path):
    if out.resolve()==signed_root.resolve() or signed_root.resolve() in out.resolve().parents:
        raise ValueError('OUTPUT_INSIDE_SIGNED_AUTHORITY')
    if out.exists() and any(out.iterdir()):raise ValueError('OUTPUT_NOT_EMPTY')
    stages,files,manifest,metadata=phase.validate_archive(snapshot)
    if old.digest(source)!=phase.SOURCE_SHA:raise ValueError('ORIGINAL_RGB_PIN_FAIL')
    old.signed_check(signed_root,old.GC_SHA)
    x=np.asarray(Image.open(source).convert('RGBA'));photo=x[:,:,:3];alpha=x[:,:,3]
    mask=phase.read_mask(files['phase_04/part_masks/right_arm.png'])
    historical=old.mask_at(signed_root,'gc001_right.png')
    if not np.array_equal(mask,historical):raise ValueError('CURRENT_RIGHT_NOT_MATCH_HISTORIC_SIGNED')
    structural=stages[4]['structural'];points=np.asarray(structural['keypoints_body17'],dtype=np.float32)
    scores=np.asarray(structural['scores_body17'],dtype=np.float32)
    span=float(np.linalg.norm(points[5]-points[6]))
    exact_bg,_=old.source_connected_background(photo,alpha)
    candidates={}
    masks={}
    for factor in FACTORS:
        m,support,stats=signed_corridor(mask,points,scores,span,factor)
        stats['source_rgb_border_connected_remaining']=int(np.count_nonzero(m&exact_bg))
        stats['source_rgb_border_connected_removed']=int(np.count_nonzero(mask&exact_bg&~m))
        stats['unchanged_historical_face_left_arm_mask']=True
        stats['same_or_less_source_pixel_coverage']=not np.any(m&~mask)
        stats['release_candidate_valid']=False  # No Stage8 or Golden; COCO wrist below confidence.
        candidates[str(factor)]=stats;masks[str(factor)]=m
    if any(x['source_rgb_border_connected_remaining']!=0 for x in candidates.values()):
        raise ValueError('SIGNED_SOURCE_CORRIDOR_OBSERVATION_DRIFT')
    if any(x['pose_confidence_pass'] for x in candidates.values()):
        raise ValueError('EXPECTED_LOW_CONFIDENCE_GC001_WRIST_DRIFT')
    if any(x['candidate_connected_components']!=1 for x in candidates.values()):
        raise ValueError('SOURCE_POSE_CORRIDOR_COMPONENT_DRIFT')
    out.mkdir(parents=True,exist_ok=True)
    def over(m,c):
        base=photo.astype(float);base[m]=base[m]*.55+np.asarray(c)*.45
        return Image.fromarray(np.clip(base,0,255).astype('uint8'))
    panels=[('SIGNED RGB ORIGINAL',Image.fromarray(photo)),('SIGNED RIGHT OWNER',over(mask,(241,47,153)))]
    for factor in FACTORS:panels.append((f'POSE CORRIDOR {factor} HOLD',over(masks[str(factor)],(24,185,111))))
    board=Image.new('RGB',(340*len(panels),385),(248,247,245));pen=ImageDraw.Draw(board)
    for i,(label,im) in enumerate(panels):board.paste(im,(i*340,44));pen.text((i*340+7,13),label,fill=(20,20,20))
    board.save(out/'gc001_pose_corridor_three_variants_PRIVATE.png')
    report={'stage':'C02b1','schema':'sa1060d-structural-right-arm-corridor-risk-v1',
       'source_original_verified':True,'phase03_phase04_zip_pin_verified':True,'right_arm_current_matches_historical':True,
       'source_model':'rtmlib-wholebody-balanced COCO17 original recorded keypoints',
       'body_pose_score_minimum_required':MIN_POSE_SCORE,'pose_confidence_gate':'HOLD',
       'artistic_golden':'PENDING','original_stage8_budget':'HOLD','true_expanded_svg_budget':'NOT_MEASURED',
       'chromium_full_character':'NOT_RUN','independent_raden_control':'NOT_RUN',
       'faceless_features':'OFF','generated_pixels':False,'production_changed':False,'release_authorized':False,
       'candidates':candidates,'private_source_sha256':phase.SOURCE_SHA}
    (out/'c02b1_PRIVATE_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    public={k:report[k] for k in report if k!='private_source_sha256'}
    (out/'c02b1_coordinate_free_public.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser()
    for k in ('source','signed-root','snapshot','out'):p.add_argument('--'+k,required=True,type=Path)
    a=p.parse_args();r=run(a.source,a.signed_root,a.snapshot,a.out)
    print(json.dumps({'status':'RESEARCH_CORRIDOR_HOLD','candidate_count':len(r['candidates']),
         'score_gate':r['pose_confidence_gate'],'right20':r['candidates']['0.2']['candidate_pixels'],
         'source_background_overlap_remaining':r['candidates']['0.2']['source_rgb_border_connected_remaining']}))
if __name__=='__main__': main()
