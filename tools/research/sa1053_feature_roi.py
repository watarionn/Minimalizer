"""SA10.53: original-2D visually anchored facial-region audits and source-only SVG micro-adjustment.

Two signed cases only. Eye/brow/mouth rectangle hypotheses are annotated from original
2D imagery, NOT inferred or certified semantic landmarks. No synthetic anatomy, no
raster SVG embedding, unchanged masks/colors/vertex counts. Real Chromium fidelity.
"""
from __future__ import annotations
import argparse,copy,hashlib,io,json,re,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1052_source_edge_refinement as last

NS=last.NS
CASES=('Raden','GC001')
BASE_SHA={'Raden':'68b9ad6ad24c92d14dd5c5b9cc7ce9fc68a9b43caf5c194df162fc731a04a7b6',
          'GC001':'f087a89d5918eb7f606ba60eaad9ff051ef6c1ea8a3facdef9ef1d18a6eb5f5f'}
BASE_RGB={'Raden':{'face':33.651530,'foreground':27.758737},
          'GC001':{'face':27.575788,'foreground':44.469572}}
# Original-image visually inspected, *approximate* rectangles relative to signed
# face bounding box. No automatic landmark detector or semantic position claim.
ROI_PROPORTIONS={
 'Raden':{'image_left_brow':(-.04,.08,.35,.32),
          'image_right_brow':(.44,-.05,.90,.24),
          'image_left_eye':(-.07,.17,.39,.53),
          'image_right_eye':(.43,.04,.93,.45),
          'mouth':(.31,.58,.78,.88)},
 'GC001':{'image_left_brow':(.07,-.06,.46,.23),
          'image_right_brow':(.52,-.12,.94,.16),
          'image_left_eye':(.09,.09,.50,.39),
          'image_right_eye':(.52,.075,.95,.39),
          'mouth':(.27,.55,.69,.80)} }
# deliberately prefer actual eye and mouth regions to eyebrow measurements
PRIORITY=('image_left_eye','image_right_eye','mouth','image_left_brow','image_right_brow')
RANGE={'image_left_eye':5,'image_right_eye':5,'mouth':5,'image_left_brow':3,'image_right_brow':3}
CORD=re.compile(r'(-?\d+)\s+(-?\d+)')


def box_from_mask(face,normalized):
    yy,xx=np.nonzero(face)
    if not len(xx):raise ValueError('Signed face mask has no pixels')
    left,top=int(xx.min()),int(yy.min());width=int(xx.max())-left+1;height=int(yy.max())-top+1
    a,b,c,d=normalized
    x0=max(0,min(339,int(round(left+a*width))));x1=max(1,min(340,int(round(left+c*width))))
    y0=max(0,min(339,int(round(top+b*height))));y1=max(1,min(340,int(round(top+d*height))))
    if x1<=x0 or y1<=y0:raise ValueError('Degenerate signed visual ROI')
    return (x0,y0,x1,y1)


def get_rois(name,face):
    out={};bounds={}
    for role,norm in ROI_PROPORTIONS[name].items():
        b=box_from_mask(face,norm);bounds[role]=b
        x0,y0,x1,y1=b
        region=np.zeros_like(face);region[y0:y1,x0:x1]=face[y0:y1,x0:x1]
        if region.sum()<25:raise ValueError('No signed face source pixels in '+role)
        out[role]=region
    return out,bounds


def gray_edge_mask(rgb,region):
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    dx=cv2.Sobel(gray,cv2.CV_32F,1,0,ksize=3)
    dy=cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3)
    return (cv2.magnitude(dx,dy)>128)&region


def roi_metrics(rendered,photo,region,high):
    return {'pixels':int(region.sum()),'rgb_mae':round(last.source_mae(rendered,photo,region),6),
            'high_gradient_pixels':int(high.sum()),
            'high_gradient_rgb_mae':round(last.source_mae(rendered,photo,high),6) if high.any() else None}


def signed_inputs(name,root,svg_file):
    data=last.prior.prior.dual.load_case(name,root)
    case=last.prior.prior.opt.load_case(name,root)
    if hashlib.sha256(svg_file.read_bytes()).hexdigest()!=BASE_SHA[name]:
        raise ValueError('SA1052_FEATURE_BASELINE_SHA_MISMATCH')
    svg=ET.parse(svg_file).getroot()
    count=last.prior.strict_vertices(svg,case)['expanded_deployed_vertices']
    if count!=(1412 if name=='Raden' else 1882):raise ValueError('SA1052_STRICT_VERTEX_CHANGED')
    if len(last.select_region_paths(svg,'face'))!=3:raise ValueError('Signed face layer count changed')
    return data,case,svg


def locate_vertices(svg,rois,photo,limit):
    # Use existing traced SVG faces, not new paths. A candidate is within or near
    # the visually annotated box and prioritizes original measured sharp contrast.
    nodes=last.select_region_paths(svg,'face')
    todo=[]
    gray=cv2.cvtColor(photo,cv2.COLOR_RGB2GRAY)
    gx=cv2.Sobel(gray,cv2.CV_32F,1,0,ksize=3);gy=cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3)
    grad=cv2.magnitude(gx,gy)
    for layer,node in enumerate(nodes):
        d=node.get('d','')
        for j,m in enumerate(CORD.finditer(d)):
            x,y=int(m[1]),int(m[2]);x0=max(0,x-2);x1=min(340,x+3);y0=max(0,y-2);y1=min(340,y+3)
            if y0>=y1 or x0>=x1 or not rois[y0:y1,x0:x1].any():continue
            signal=float(grad[y0:y1,x0:x1].max())
            todo.append((layer,j,signal,x,y))
    # Highest-gradient source evidence first, stable tie-break by source path index.
    return sorted(todo,key=lambda x:(-x[2],x[0],x[1]))[:limit]


def inventory(svg):
    return last.source_paint_inventory(svg)


def run_case(name,root,source_svg,out,page):
    data,case,svg=signed_inputs(name,root,source_svg)
    orig=copy.deepcopy(svg);constant=inventory(svg)
    photo=data['photo'];face=data['masks']['face'];arms=data['masks']['left_arm']|data['masks']['right_arm']
    visible,_=last.prior.prior.opt.visible_ownership(case)
    fg=np.logical_or.reduce([face,*visible.values()])
    img=last.prior.svg_rgb(page,svg)
    if abs(last.source_mae(img,photo,face)-BASE_RGB[name]['face'])>1e-5:raise AssertionError('FACE_BASELINE_REPLAY_CHANGED')
    if abs(last.source_mae(img,photo,fg)-BASE_RGB[name]['foreground'])>1e-5:raise AssertionError('FOREGROUND_BASELINE_REPLAY_CHANGED')
    rois,bounds=get_rois(name,face)
    roi_gradient={k:gray_edge_mask(photo,roi) for k,roi in rois.items()}
    before={k:roi_metrics(img,photo,rois[k],roi_gradient[k]) for k in PRIORITY}
    initial=img.copy();current_global=last.source_mae(img,photo,face)
    score={k:last.source_mae(img,photo,rois[k]) for k in PRIORITY}
    moves=[];trials=0;source_paths=last.select_region_paths(svg,'face')
    for target in PRIORITY:
        candidates=locate_vertices(svg,rois[target],photo,RANGE[target]);changed=0
        for layer,index,signal,x,y in candidates:
            path=source_paths[layer];old=path.get('d','');matches=list(CORD.finditer(old))
            if index>=len(matches):raise AssertionError('SVG path unexpectedly mutated')
            m=matches[index];current=(int(m[1]),int(m[2]));winner=None
            for dx,dy in last.MOVES:
                new=old[:m.start()]+f'{current[0]+dx} {current[1]+dy}'+old[m.end():]
                path.set('d',new)
                test=last.prior.svg_rgb(page,svg);trials+=1
                if not np.array_equal(test[~face],initial[~face]):continue
                # Do not improve one feature by making other signed feature ROIs worse.
                new_global=last.source_mae(test,photo,face)
                if new_global>current_global+1e-7:continue
                check={k:last.source_mae(test,photo,rois[k]) for k in PRIORITY}
                if any(check[k]>score[k]+1e-7 for k in PRIORITY):continue
                if check[target]>=score[target]-1e-7:continue
                rank=(check[target],new_global,PRIORITY.index(target),dx,dy)
                if winner is None or rank<winner[0]:winner=(rank,new,test,check,new_global,dx,dy)
            if winner:
                _,new,img,score,current_global,dx,dy=winner
                path.set('d',new);changed+=1
                moves.append({'region':target,'layer':layer,'vertex_ordinal':index,
                              'shift':[dx,dy],'source_region_mae':round(score[target],6)})
            else:path.set('d',old)
        # Preserve stage trace, no magic success implied.
    final=last.prior.svg_rgb(page,svg)
    if not np.array_equal(final,img):raise AssertionError('Chromium final frame not reproduced')
    if not np.array_equal(final[~face],initial[~face]):raise AssertionError('Outside signed face changed')
    if inventory(svg)!=constant:raise AssertionError('Non-coordinate source paint inventory changed')
    count=last.prior.strict_vertices(svg,case)['expanded_deployed_vertices']
    if count!=(1412 if name=='Raden' else 1882):raise AssertionError('SVG cost changed')
    after={k:roi_metrics(img,photo,rois[k],roi_gradient[k]) for k in PRIORITY}
    original_error=last.source_mae(initial,photo,face);new_error=last.source_mae(img,photo,face)
    if new_error>original_error+1e-7:raise AssertionError('Source face RGB regressed')
    if any(after[k]['rgb_mae']>before[k]['rgb_mae']+1e-5 for k in PRIORITY):raise AssertionError('Feature ROI regressed')
    base=out/f'{name.lower()}_sa1052.png';Image.fromarray(initial).save(base)
    Image.fromarray(final).save(out/f'{name.lower()}_sa1053.png')
    (out/f'{name.lower()}_sa1053.svg').write_text(ET.tostring(svg,encoding='unicode'),'utf-8')
    return {'role':name,'source_authority_sha256':case['source_input_sha256'],
            'baseline_svg_sha256':BASE_SHA[name],
            'annotation_method':'approximate human-observed ROIs on original 2D (not semantic classifier)',
            'roi_signed_face_pixel_counts':{k:int(rois[k].sum()) for k in PRIORITY},
            'roi_result':{k:{'before':before[k],'after':after[k]} for k in PRIORITY},
            'original_source_face_mae_before':round(original_error,6),
            'original_source_face_mae_after':round(new_error,6),
            'original_source_foreground_mae_before':round(last.source_mae(initial,photo,fg),6),
            'original_source_foreground_mae_after':round(last.source_mae(final,photo,fg),6),
            'candidate_trials':trials,'accepted_vertex_micro_moves':len(moves),
            'move_trace':moves,'vertex_cost':count,'hard_limit':case['budget'],
            'arms_unchanged':np.array_equal(final[arms],initial[arms]),
            'outside_face_unchanged':np.array_equal(final[~face],initial[~face]),
            'source_color_and_mask_inventory_unchanged':True,
            'semantic_eye_nose_mouth_detection':'NOT_PERFORMED',
            'original_stage8_ring_gate':'FAIL','human_visual_review':'PENDING','golden':'HOLD'}


def evaluate(raden_root,gc001_root,raden_svg,gc001_svg,out,chromium='/usr/bin/chromium'):
    roots=[Path(raden_root).resolve(),Path(gc001_root).resolve()]
    svg=[Path(raden_svg).resolve(),Path(gc001_svg).resolve()];out=Path(out).resolve()
    if roots[0]==roots[1] or any(out==r or r in out.parents or out in r.parents for r in roots):
        raise ValueError('Original source and output dirs must be separate')
    if any(out==s or out in s.parents or s in out.parents for s in svg):
        raise ValueError('May not overwrite immutable prior SVG')
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            results=[run_case(n,r,s,out,page) for n,r,s in zip(CASES,roots,svg)]
            version=browser.version
        finally:browser.close()
    board=Image.new('RGB',(340*3,380*2),(246,246,244));draw=ImageDraw.Draw(board)
    for row,name in enumerate(CASES):
        photo=Image.open(roots[row]/last.ORIGINAL_SOURCE_ROOT[name]).convert('RGB')
        frames=(photo,Image.open(out/f'{name.lower()}_sa1052.png').convert('RGB'),Image.open(out/f'{name.lower()}_sa1053.png').convert('RGB'))
        for col,(img,title) in enumerate(zip(frames,('SIGNED ORIGINAL','SA10.52 BASELINE','SA10.53 REGION-TESTED'))):
            board.paste(img,(340*col,380*row+40))
            draw.text((340*col+5,380*row+12),name.upper()+' / '+title,fill=(20,20,20))
    board.save(out/'sa1053_two_case_comparison.png')
    # Source-inclusive closeups are private review evidence, not GitHub assets.
    details=Image.new('RGB',(330*3,320*2),(244,244,241));pen=ImageDraw.Draw(details)
    for row,name in enumerate(CASES):
        data=last.prior.prior.dual.load_case(name,roots[row])
        yy,xx=np.where(data['masks']['face']);x0=max(0,int(xx.min())-12);x1=min(340,int(xx.max())+14)
        y0=max(0,int(yy.min())-12);y1=min(340,int(yy.max())+14)
        pic=[Image.open(roots[row]/last.ORIGINAL_SOURCE_ROOT[name]).convert('RGB'),
             Image.open(out/f'{name.lower()}_sa1052.png').convert('RGB'),
             Image.open(out/f'{name.lower()}_sa1053.png').convert('RGB')]
        for col,(im,heading) in enumerate(zip(pic,('SIGNED ORIGINAL','SA10.52','SA10.53'))):
            crop=im.crop((x0,y0,x1,y1));crop.thumbnail((306,280))
            # Fixed nearest-neighbor magnification exposes missing face detail.
            target=im.crop((x0,y0,x1,y1)).resize((306,280),Image.Resampling.NEAREST)
            details.paste(target,(col*330+12,row*320+28))
            pen.text((col*330+12,row*320+8),name+' / '+heading,fill=(10,10,10))
    details.save(out/'sa1053_face_closeup.png')
    result={'stage':'SA10.53','schema':'visual-source-roi-faithful-vertex-microsearch-v1',
            'chromium':version,'cases':{r['role']:r for r in results},
            'signed_roi_annotations_are_hypotheses':True,'semantic_landmark_detector_used':False,
            'original_2d_only':True,'no_raster_embeds_or_generative_fill':True,
            'two_case_budget_pass':all(x['vertex_cost']<=x['hard_limit'] for x in results),
            'two_case_protected_regions_exact':all(x['arms_unchanged'] and x['outside_face_unchanged'] for x in results),
            'historical_stage8_source_ring_budget':'FAIL','full_character_golden':'HOLD',
            'human_review':'PENDING','production_deployment':'UNCHANGED'}
    result['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()}
    (out/'sa1053_metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for name in ('raden','gc001','raden_svg','gc001_svg','out'):
        ap.add_argument('--'+name.replace('_','-'),required=True,type=Path)
    args=ap.parse_args()
    print(json.dumps(evaluate(args.raden,args.gc001,args.raden_svg,args.gc001_svg,args.out),ensure_ascii=False,indent=2))
