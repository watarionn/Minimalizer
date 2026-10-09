"""SA10.52: signed-source guided SVG path translation with zero new vertices.

For each already source-derived feature contour, test ±1px translations on real
Chromium. Only improvements against the signed RGB original can be accepted.
The original source, source palettes, Stage04 silhouette, role paint order,
Stage9/37 colored polygons and all path point counts are immutable.
Research/HOLD only. No generated art, pixel fills, source raster embedding, or
inferred eye/nose/mouth anatomy. Eye-like contrast is merely an edge proxy.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re, sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import cv2
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1051_budget_detail_optimizer as prior

NS=prior.NS
BASELINE_SHA={
 'Raden':'77fcf349ef6bd3fa6862357fbe42f511d6d360e39aa248071aca6315ef939276',
 'GC001':'41cde0b45192ebb276d0003c6449a1abd1ce2e48e1435a164a48831176782903'}
ORIGINAL_SOURCE_ROOT={'Raden':'Raden_source.png','GC001':'GC001_source.png'}
MOVES=((-1,0),(1,0),(0,-1),(0,1))
SEGMENT=re.compile(r'M\s+(?:[^Z]*?)\s*Z')
COORDINATE=re.compile(r'(-?\d+)\s+(-?\d+)')


def shift_source_segment(segment:str,dx:int,dy:int)->str:
    if (dx,dy) not in MOVES:raise ValueError('Translations must be source-local cardinal 1px')
    if not SEGMENT.fullmatch(segment):raise ValueError('Unrecognized source contour path geometry')
    out=COORDINATE.sub(lambda m:f'{int(m[1])+dx} {int(m[2])+dy}',segment)
    if len(COORDINATE.findall(out))!=len(COORDINATE.findall(segment)):
        raise AssertionError('Translation must not add points')
    return out


def source_gradient_roi(photo:np.ndarray,mask:np.ndarray,threshold=128):
    mono=cv2.cvtColor(photo,cv2.COLOR_RGB2GRAY)
    x=cv2.Sobel(mono,cv2.CV_32F,1,0,ksize=3)
    y=cv2.Sobel(mono,cv2.CV_32F,0,1,ksize=3)
    return (cv2.magnitude(x,y)>threshold)&mask


def source_mae(image,photo,mask):
    return float(np.abs(image[mask].astype(np.int16)-photo[mask].astype(np.int16)).mean())


def select_region_paths(svg,role):
    matches=[n for n in svg.iter(NS+'path') if n.get('data-sa1051-observed')==role]
    if role=='face' and len(matches)!=3:
        raise ValueError('Source face material paint policy changed; refuse editing')
    if role!='face' and len(matches)>1:
        raise ValueError('Unexpected material source feature path count')
    return matches


def optimize_region(page,svg,baseline,photo,region,forbidden,role,passes:int=2):
    """Greedy 1px source-difference minimization with complete Chromium validation.

    Avoid hidden visual heuristics: no edits to source masks, path topology, RGB
    paint or production artifacts. Ties do not authorize geometry changes.
    """
    if passes not in (1,2):raise ValueError('Only bounded deterministic replay')
    if not np.any(region):raise ValueError('Empty signed evaluation region')
    trace=[];trials=0;accepted=0
    best_image=prior.svg_rgb(page,svg)
    best_value=source_mae(best_image,photo,region)
    immutable_outside=baseline[forbidden].copy()
    for sweep in range(passes):
        for layer,node in enumerate(select_region_paths(svg,role)):
            chunks=SEGMENT.findall(node.get('d',''))
            if not chunks or ''.join(chunks).replace(' ','')!=node.get('d','').replace(' ',''):
                raise ValueError('Unparsed source path, refuse feature edits')
            for segment_i in range(len(chunks)):
                old=chunks[segment_i]
                winning=None
                for dx,dy in MOVES:
                    trial_chunks=chunks.copy()
                    trial_chunks[segment_i]=shift_source_segment(old,dx,dy)
                    node.set('d',' '.join(trial_chunks))
                    image=prior.svg_rgb(page,svg);trials+=1
                    if not np.array_equal(image[forbidden],immutable_outside):continue
                    quality=source_mae(image,photo,region)
                    if quality+1e-8 < best_value and (winning is None or quality<winning[0]):
                        winning=(quality,dx,dy,image)
                if winning is not None:
                    value,dx,dy,newimage=winning
                    chunks[segment_i]=shift_source_segment(old,dx,dy)
                    node.set('d',' '.join(chunks))
                    best_value=value;best_image=newimage;accepted+=1
                    trace.append({'pass':sweep+1,'layer':layer,'contour':segment_i,
                                  'delta':[dx,dy],'source_mae':round(value,6)})
                else:
                    node.set('d',' '.join(chunks))
    final_image=prior.svg_rgb(page,svg)
    if not np.array_equal(final_image,best_image):
        raise AssertionError('Real Chromium contour replay non-deterministic')
    if not np.array_equal(final_image[forbidden],immutable_outside):
        raise AssertionError('Immutable signed geometry region repainted')
    return final_image,{'role':role,'passes':passes,'attempted_chromium_renders':trials,
                        'accepted_1px_translations':accepted,'moves':trace,
                        'final_source_mae':round(best_value,6)}


def source_paint_inventory(root):
    """All existing source RGB colors and feature point counts must stay intact."""
    polygons=[]
    for n in root.iter(NS+'polygon'):
        polygons.append((n.get('points'),n.get('fill'),n.get('mask')))
    features=[(n.get('data-sa1051-observed'),n.get('fill'),prior.prior.shared.path_vertices(n.get('d','')))
              for n in root.iter(NS+'path') if n.get('data-sa1051-observed')]
    masks=tuple(ET.tostring(n,encoding='unicode') for n in root.iter(NS+'mask'))
    paint_order=tuple(n.get('data-owner-index') for n in root if n.get('data-owner-index') is not None)
    return {'polygons':polygons,'features':features,'masks':masks,'paint_order':paint_order}


def load_case(name,source_root,baseline_file):
    if name not in BASELINE_SHA:raise ValueError('Only two SHA-signed cases authorized')
    data=prior.prior.dual.load_case(name,source_root)
    case=prior.prior.opt.load_case(name,source_root)
    if hashlib.sha256(baseline_file.read_bytes()).hexdigest()!=BASELINE_SHA[name]:
        raise ValueError('SA1051_BASELINE_SHA_MISMATCH '+name)
    scene=ET.parse(baseline_file).getroot()
    accounted=prior.strict_vertices(scene,case)
    if accounted['expanded_deployed_vertices']!=(1412 if name=='Raden' else 1882):
        raise ValueError('SA1051_SVG_BUDGET_MISMATCH')
    return data,case,scene


def evaluate_case(name,source_root,baseline_svg,out,page):
    data,case,svg=load_case(name,source_root,baseline_svg)
    inventory=source_paint_inventory(svg)
    photo=data['photo'];face=data['masks']['face'];arms=data['masks']['left_arm']|data['masks']['right_arm']
    visible,_=prior.prior.opt.visible_ownership(case)
    foreground=np.logical_or.reduce([face,*visible.values()])
    before=prior.svg_rgb(page,svg)
    expected_image_sha={'Raden':'8dbf8749c43c76af86975496e2fa936d0c517f5a5cf0a93142b05edd1ebb18d3',
                        'GC001':'40e54db4a3bb600660ed58e420d554eac6991d65f45b2b4fafa610481c5333db'}[name]
    import io
    pixel_png=io.BytesIO();Image.fromarray(before).save(pixel_png,format='PNG')
    if hashlib.sha256(pixel_png.getvalue()).hexdigest()!=expected_image_sha:
        raise AssertionError('Signed SA10.51 Chrome baseline mismatch')
    edge=source_gradient_roi(photo,face,128)
    if int(edge.sum())<100:raise AssertionError('Source face edge evidence absent')
    first={'face':source_mae(before,photo,face),'foreground':source_mae(before,photo,foreground),
           'face_high_gradient':source_mae(before,photo,edge)}
    frame,face_trace=optimize_region(page,svg,before,photo,face,~face,'face',passes=2)
    if np.any(frame[arms]!=before[arms]):raise AssertionError('Signed source arms changed')
    mat_traces=[]
    for role in ('major_clothing','lower_body'):
        paths=select_region_paths(svg,role)
        if not paths:continue
        owner_idx=next(i for i,p in enumerate(case['records']) if p['source_mask_owner']==role)
        region=foreground
        # For material edits, nothing may change within signed face or left/right arm.
        frame,trace=optimize_region(page,svg,frame,photo,region,face|arms,role,passes=1)
        mat_traces.append(trace)
    end=prior.svg_rgb(page,svg)
    account=prior.strict_vertices(svg,case)
    if account['expanded_deployed_vertices']!=(1412 if name=='Raden' else 1882):
        raise AssertionError('Zero-new-vertex optimization added or deleted geometry')
    if account['expanded_deployed_vertices']>case['budget']:
        raise AssertionError('Strict source budget exceeded')
    if source_paint_inventory(svg)!=inventory:
        raise AssertionError('Material palette, topology, source masks or paint order changed')
    if np.any(end[arms]!=before[arms]) or np.any(end[~foreground]!=before[~foreground]):
        raise AssertionError('Signed arm or outside-source canvas changed')
    final={'face':source_mae(end,photo,face),'foreground':source_mae(end,photo,foreground),
           'face_high_gradient':source_mae(end,photo,edge)}
    if not final['face']<first['face'] or not final['foreground']<first['foreground']:
        raise AssertionError('Real source fidelity did not improve')
    if final['face_high_gradient']>first['face_high_gradient']:
        raise AssertionError('High-contrast source face details regressed')
    pref=name.lower()
    (out/f'{pref}_edge_refined.svg').write_text(ET.tostring(svg,encoding='unicode'),'utf-8')
    Image.fromarray(before).save(out/f'{pref}_sa1051_baseline.png')
    Image.fromarray(end).save(out/f'{pref}_edge_refined.png')
    return {'case':name,'signed_input_hashes':case['source_input_sha256'],
         'sa1051_input_svg_sha256':hashlib.sha256(baseline_svg.read_bytes()).hexdigest(),
         'chromium_replay_matches_baseline':True,'strict_expanded_vertices':account['expanded_deployed_vertices'],
         'vertex_budget':case['budget'],'source_metric_before':{k:round(v,6) for k,v in first.items()},
         'source_metric_after':{k:round(v,6) for k,v in final.items()},
         'face_source_high_gradient_pixels':int(edge.sum()),
         'face_refinement':face_trace,'material_refinement':mat_traces,
         'owner_masks_and_source_palette_unchanged':True,'signed_face_shape_unchanged':True,
         'arms_rgb_unchanged':True,'historical_stage8_source_budget_pass':False,
         'human_visual_approval':'PENDING','golden':'HOLD','production':'UNCHANGED'}


def evaluate(raden_root,gc001_root,raden_svg,gc001_svg,out,chromium='/usr/bin/chromium'):
    roots=[Path(raden_root).resolve(),Path(gc001_root).resolve()]
    svg_files=[Path(raden_svg).resolve(),Path(gc001_svg).resolve()]
    out=Path(out).resolve()
    if roots[0]==roots[1] or any(out==r or out in r.parents or r in out.parents for r in roots):
        raise ValueError('Research output and immutable signed authorities must be separate')
    if any(out==s or out in s.parents or s in out.parents for s in svg_files):
        raise ValueError('Cannot overwrite immutable SA10.51 candidates')
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            results=[evaluate_case(n,r,s,out,page) for n,r,s in zip(('Raden','GC001'),roots,svg_files)]
            version=browser.version
        finally:browser.close()
    board=Image.new('RGB',(340*3,380*2),(246,246,243));pen=ImageDraw.Draw(board)
    for row,name in enumerate(('raden','gc001')):
        original=np.asarray(Image.open(roots[row]/ORIGINAL_SOURCE_ROOT[name.title() if name=='raden' else 'GC001']).convert('RGB'))
        scenes=[original,np.asarray(Image.open(out/f'{name}_sa1051_baseline.png').convert('RGB')),
                np.asarray(Image.open(out/f'{name}_edge_refined.png').convert('RGB'))]
        for col,(frame,label) in enumerate(zip(scenes,('SIGNED ORIGINAL','SA10.51','SA10.52 EDGE-REFINED'))):
            board.paste(Image.fromarray(frame),(col*340,row*380+40))
            pen.text((col*340+6,row*380+14),f'{name.upper()} / {label}',fill=(24,24,24))
    board.save(out/'sa1052_two_case_edge_comparison.png')
    report={'stage':'SA10.52','schema':'source-measured-1px-feature-contour-local-replay-v1',
            'chromium':version,'source_pixel_medoid_colors_only':True,
            'new_vertices_added':0,'mask_geometry_unchanged':True,'generative_fill':False,
            'cases':{x['case']:x for x in results},'both_budget_pass':True,
            'both_original_face_source_fidelity_improved':True,
            'eye_nose_mouth_semantic_certification':False,
            'historical_stage8_source_budget_pass':False,'human_visual_review':'PENDING',
            'full_character_golden':'HOLD','production_deployment':'UNCHANGED'}
    report['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(out.iterdir()) if p.is_file()}
    (out/'sa1052_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for p in ('raden','gc001','raden_svg','gc001_svg','out'):
        parser.add_argument('--'+p.replace('_','-'),required=True,type=Path)
    args=parser.parse_args()
    report=evaluate(args.raden,args.gc001,args.raden_svg,args.gc001_svg,args.out)
    print(json.dumps({k:{'vertices':v['strict_expanded_vertices'],'before':v['source_metric_before'],
                'after':v['source_metric_after'],'face_moves':v['face_refinement']['accepted_1px_translations'],
                'materials':v['material_refinement']} for k,v in report['cases'].items()},ensure_ascii=False,indent=2))
