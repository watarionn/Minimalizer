"""SA10.54 signed original 2D iris-chroma priority under existing expanded SVG budgets.

Research-only: source pixel medoids, no new path coordinates, no raster fills, no
inferred anatomy. Independently prove any SVG contour split is a full-scene
Chromium pixel-exact substitution before testing a different real-source fill.
"""
from __future__ import annotations
import argparse, copy, hashlib, io, json, sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import cv2
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1053_feature_roi as prev

NS=prev.NS
CASES=('Raden','GC001')
SHA={'Raden':'5ad0622f04540e77a002f2bcddf5e992c3b4f810f3aaede4f350bed5313263e3',
     'GC001':'e4033302ffefeeb74aa0caf77be4d61c08da40e3058b064618438c6fd4e7cd22'}
LIMIT={'Raden':1412,'GC001':1887}
HUE={'Raden':(85,135),'GC001':(35,90)}
EYES=('image_left_eye','image_right_eye')

def browser_rgb(page,svg):return prev.last.prior.svg_rgb(page,svg)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def source_color(values):
    if len(values)==0:raise ValueError('No source iris color pixels')
    center=np.median(values.astype(np.float64),axis=0)
    return tuple(int(x) for x in values[np.argmin(np.abs(values.astype(np.float64)-center).sum(axis=1))])
def hexc(color):return '#'+''.join(f'{int(c):02x}' for c in color)

def eye_evidence(photo,roi,name):
    hsv=cv2.cvtColor(photo,cv2.COLOR_RGB2HSV)
    lower,upper=HUE[name]
    mask=roi&(hsv[...,0]>=lower)&(hsv[...,0]<upper)&(hsv[...,1]>100)&(hsv[...,2]>70)
    if np.count_nonzero(mask)<12:raise ValueError('Not enough original source chromatic eye evidence')
    return mask,source_color(photo[mask])

def masks_and_shape_inventory(svg):
    return {'masks':[ET.tostring(x,encoding='unicode') for x in svg.iter(NS+'mask')],
            'source_polygon':[ET.tostring(x,encoding='unicode') for x in svg.iter(NS+'polygon')],
            'owner_order':[x.get('data-owner-index') for x in svg if x.get('data-owner-index') is not None],
            'face_guards':sum(n.get('mask')=='url(#sa1041-original-face-guard)' for n in svg.iter()),
            'nonface_paint':[ET.tostring(n,encoding='unicode') for n in svg.iter(NS+'path') if n.get('data-sa1051-observed')!='face']}

def face_contours(svg):
    out=[]
    for node in svg.iter(NS+'path'):
        if node.get('data-sa1051-observed')=='face':out.extend(prev.last.SEGMENT.findall(node.get('d','')))
    return sorted(out)

def verified_component_split(svg,baseline,page):
    """Split contours only when each whole-scene paint remains byte-pixel exact.
    Separate paths still live inside the same single face guard, no extra mask cost.
    """
    out=copy.deepcopy(svg);attempts=passed=0
    for parent in list(out.iter()):
        for node in list(parent):
            if node.get('data-sa1051-observed')!='face':continue
            pos=0
            while True:
                chunks=prev.last.SEGMENT.findall(node.get('d',''))
                if len(chunks)<2 or pos>=len(chunks):break
                if ''.join(chunks).replace(' ','') != node.get('d','').replace(' ',''):
                    raise AssertionError('Unknown source contour commands')
                part=copy.deepcopy(node);part.set('d',chunks[pos]);part.set('data-sa1054-separable','yes')
                node.set('d',' '.join(chunks[:pos]+chunks[pos+1:]))
                index=list(parent).index(node);parent.insert(index,part)
                attempts+=1
                if np.array_equal(browser_rgb(page,out),baseline):passed+=1
                else:
                    parent.remove(part);node.set('d',' '.join(chunks));pos+=1
    if not np.array_equal(browser_rgb(page,out),baseline):raise AssertionError('Contoured split changed any RGB pixels')
    if face_contours(out)!=face_contours(svg):raise AssertionError('Source contour positions changed')
    return out,{'attempts':attempts,'pixel_exact_restructures':passed,'prohibited_nonexact_restructures':attempts-passed}

def face_metrics(image,photo,roi,iris):
    def mae(mask):return round(float(np.abs(image[mask].astype(np.int16)-photo[mask].astype(np.int16)).mean()),6)
    return {'roi':{k:mae(v) for k,v in roi.items()},'iris':{k:mae(v) for k,v in iris.items()}}

def optimize_chroma(svg,page,baseline,photo,face,rois,name):
    chroma={};palette={}
    for eye in EYES:
        chroma[eye],palette[eye]=eye_evidence(photo,rois[eye],name)
    current=browser_rgb(page,svg)
    safe=current[~face].copy()
    before=face_metrics(current,photo,rois,chroma)
    face_mae=lambda im:float(np.abs(im[face].astype(np.int16)-photo[face].astype(np.int16)).mean())
    score=before
    trials=0;accepted=[]
    for eye in EYES:
        yy,xx=np.nonzero(rois[eye]); bounds=(int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max()))
        color=hexc(palette[eye])
        choices=[]
        for ix,node in enumerate(n for n in svg.iter(NS+'path') if n.get('data-sa1051-observed')=='face'):
            coords=[(int(x),int(y)) for x,y in prev.CORD.findall(node.get('d',''))]
            if not coords:continue
            x0,y0,x1,y1=min(x for x,y in coords),min(y for x,y in coords),max(x for x,y in coords),max(y for x,y in coords)
            if x1<bounds[0] or x0>bounds[2] or y1<bounds[1] or y0>bounds[3]:continue
            old=node.get('fill')
            if old==color:continue
            node.set('fill',color)
            img=browser_rgb(page,svg);trials+=1
            node.set('fill',old)
            if not np.array_equal(img[~face],safe):continue
            trial=face_metrics(img,photo,rois,chroma)
            # The two chromatic ROIs must not get worse. Whole face, all 5
            # historic ROI metrics may not regress either.
            # Source-chroma priority: eyes and mouth never regress; permit at most
            # 0.25 MAE in the approximate overlapping brow ROIs (explicit ledger).
            if any(trial['roi'][r]>score['roi'][r]+(0.25 if 'brow' in r else 1e-5) for r in rois):continue
            if any(trial['iris'][r]>score['iris'][r]+1e-5 for r in EYES):continue
            if trial['iris'][eye]>=score['iris'][eye]-1e-5:continue
            if face_mae(img)>face_mae(current)+1e-7:continue
            choices.append((trial['iris'][eye],face_mae(img),ix,node,old,color,img,trial))
        if choices:
            best=min(choices,key=lambda q:(q[0],q[1],q[2]))
            _,_,ix,node,old,color,img,trial=best
            node.set('fill',color)
            current=img;score=trial
            accepted.append({'eye':eye,'source_medoid_rgb':list(palette[eye]),'recolored_source_contour_index':ix,
              'previous_fill':old,'source_chroma_mae_after':trial['iris'][eye]})
    final=browser_rgb(page,svg)
    if not np.array_equal(final,current):raise AssertionError('Recolored composite render not deterministic')
    if not np.array_equal(final[~face],safe):raise AssertionError('Recolor leaks outside signed face')
    return final,{'source_palette':{k:list(v) for k,v in palette.items()},
      'source_chroma_pixels':{k:int(v.sum()) for k,v in chroma.items()},
      'pixel_rgb_before':before,'pixel_rgb_after':score,'max_approved_brow_roi_mae_slack':0.25,'chromium_candidate_trials':trials,
      'accepted_contour_recolors':accepted,'source_medoid_pixel_origin_verified':True}

def run_case(name,root,prior_svg,out,page):
    if digest(prior_svg)!=SHA[name]:raise ValueError('SA1053_CHAMPION_SHA_MISMATCH '+name)
    data=prev.last.prior.prior.dual.load_case(name,root)
    case=prev.last.prior.prior.opt.load_case(name,root)
    svg=ET.parse(prior_svg).getroot()
    photo=data['photo'];face=data['masks']['face']
    original=browser_rgb(page,svg)
    initial_inv=masks_and_shape_inventory(svg);contours=face_contours(svg)
    original_vertices=prev.last.prior.strict_vertices(svg,case)['expanded_deployed_vertices']
    rois,_=prev.get_rois(name,face)
    split,split_proof=verified_component_split(svg,original,page)
    if masks_and_shape_inventory(split)!=initial_inv or face_contours(split)!=contours:
        raise AssertionError('Original signed paint/contour inventory was altered')
    frame,recolor=optimize_chroma(split,page,original,photo,face,rois,name)
    count=prev.last.prior.strict_vertices(split,case)['expanded_deployed_vertices']
    if count!=original_vertices or count>LIMIT[name]:raise AssertionError('Budget change during face component research')
    if masks_and_shape_inventory(split)!=initial_inv or face_contours(split)!=contours:
        raise AssertionError('Not a color-only source-conservation experiment')
    if not np.array_equal(frame[~face],original[~face]):raise AssertionError('Arm/silhouette paint changed')
    m_before=prev.last.source_mae(original,photo,face);m_after=prev.last.source_mae(frame,photo,face)
    if m_after>m_before+1e-7:raise AssertionError('Overall source face fidelity declined')
    if not recolor['accepted_contour_recolors']:
        raise AssertionError('No provenance-correct source color improvement; fail closed')
    pre=name.lower()
    (out/f'{pre}_source_chroma.svg').write_text(ET.tostring(split,encoding='unicode'),'utf-8')
    Image.fromarray(original).save(out/f'{pre}_sa1053_baseline.png')
    Image.fromarray(frame).save(out/f'{pre}_source_chroma.png')
    return {'name':name,'signed_inputs':case['source_input_sha256'],
      'source_baseline_sha256':digest(prior_svg),'source_face_mismatch_mae_before':round(m_before,6),
      'source_face_mismatch_mae_after':round(m_after,6),'expanded_vertices':count,
      'budget':LIMIT[name],'full_source_stage8_ring_budget_pass':False,'component_split_proof':split_proof,
      'iris_chroma_roi':recolor,'signed_face_mask_pixels_identical':True,
      'signed_both_arms_rgb_identical':True,'no_new_vertex_or_mask_reference':True,
      'face_contours_and_stage9_stage37_colored_polygons_conserved':True}

def evaluate(raden_root,gc_root,raden_svg,gc_svg,out,chromium='/usr/bin/chromium'):
    roots=[Path(raden_root).resolve(),Path(gc_root).resolve()]
    bases=[Path(raden_svg).resolve(),Path(gc_svg).resolve()]
    out=Path(out).resolve()
    if roots[0]==roots[1] or any(out==r or out in r.parents or r in out.parents for r in roots):raise ValueError('Separate signed source and output required')
    if any(out==b or out in b.parents or b in out.parents for b in bases):raise ValueError('Cannot overwrite signed champion SVG')
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pl:
        browser=pl.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            cases=[run_case(name,root,svg,out,page) for name,root,svg in zip(CASES,roots,bases)]
            version=browser.version
        finally:browser.close()
    board=Image.new('RGB',(340*3,380*2),(246,246,244));draw=ImageDraw.Draw(board)
    for row,name in enumerate(CASES):
        pre=name.lower();original=Image.open(roots[row]/('Raden_source.png' if name=='Raden' else 'GC001_source.png')).convert('RGB')
        frames=(original,Image.open(out/f'{pre}_sa1053_baseline.png').convert('RGB'),Image.open(out/f'{pre}_source_chroma.png').convert('RGB'))
        for col,(pic,label) in enumerate(zip(frames,('SIGNED ORIGINAL','SA10.53','SA10.54 SOURCE CHROMA'))):
            board.paste(pic,(340*col,380*row+40));draw.text((340*col+8,380*row+12),name+' / '+label,fill=(20,20,24))
    board.save(out/'sa1054_two_case_iris_comparison.png')
    # Signed source-inclusive nearest-neighbor face crops for private review only.
    closeup=Image.new('RGB',(320*3,320*2),(246,246,244));caption=ImageDraw.Draw(closeup)
    for row,name in enumerate(CASES):
        d=prev.last.prior.prior.dual.load_case(name,roots[row]);yy,xx=np.where(d['masks']['face'])
        x0=max(0,int(xx.min())-10);x1=min(340,int(xx.max())+12)
        y0=max(0,int(yy.min())-10);y1=min(340,int(yy.max())+12)
        pic=(Image.open(roots[row]/('Raden_source.png' if name=='Raden' else 'GC001_source.png')).convert('RGB'),
            Image.open(out/f'{name.lower()}_sa1053_baseline.png').convert('RGB'),
            Image.open(out/f'{name.lower()}_source_chroma.png').convert('RGB'))
        for col,(im,heading) in enumerate(zip(pic,('ORIGINAL','SA10.53','SA10.54'))):
            closeup.paste(im.crop((x0,y0,x1,y1)).resize((300,285),Image.Resampling.NEAREST),(col*320+10,row*320+26))
            caption.text((col*320+10,row*320+8),name+' / '+heading,fill=(20,20,24))
    closeup.save(out/'sa1054_face_closeup.png')
    report={'stage':'SA10.54','schema':'signed-source-pixel-eye-chroma-conserved-svg-recolor-v1',
      'chromium':version,'cases':{r['name']:r for r in cases},
      'all_rgb_from_source_pixels':True,'no_raster_embeds_or_generative_fill':True,
      'no_source_path_contour_coordinate_change':True,
      'signed_arm_shape_color_unchanged':True,
      'both_hard_vertex_budgets_pass':True,'source_stage8_ring_budget_pass':False,
      'semantic_iris_eye_lid_mouth_accuracy_certified':False,
      'human_visual_review':'PENDING','full_character_golden':'HOLD','production_deployment':'UNCHANGED'}
    report['artifacts_sha256']={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(out.iterdir()) if x.is_file()}
    (out/'sa1054_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for arg in ('raden','gc001','raden_svg','gc001_svg','out'):parser.add_argument('--'+arg.replace('_','-'),type=Path,required=True)
    a=parser.parse_args();r=evaluate(a.raden,a.gc001,a.raden_svg,a.gc001_svg,a.out)
    print(json.dumps({k:{'vertices':v['expanded_vertices'],'face_before':v['source_face_mismatch_mae_before'],
     'face_after':v['source_face_mismatch_mae_after'],'chroma':v['iris_chroma_roi']['pixel_rgb_after'],
     'accepted':v['iris_chroma_roi']['accepted_contour_recolors']} for k,v in r['cases'].items()},indent=2))
