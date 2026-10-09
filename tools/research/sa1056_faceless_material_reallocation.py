"""SA10.56: allocate freed *real* expanded SVG vertices to signed-source material paint.

This is a research-only, no-generation experiment.  Faceless face guards, source
face mask, signed arms, source-owned material z order, and prior SVG are immutable.
Chromium compares proposals with the real signed image, never a flat reference.
"""
from __future__ import annotations
import argparse, copy, hashlib, io, json, re, sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1055_faceless_output_contract as previous

NS=previous.NS
CASES=('Raden','GC001')
BASE_SHA={'Raden':'fd65000ad4e814348f1158871e9e049b74fffbf7d84e4b4f25c35ee375d2d88a',
          'GC001':'ca077a2df9d134926a4c433746398dd5f9d3dc79818ded611fac32f9623e859b'}
ORIGINAL_SOURCE={'Raden':'Raden_source.png','GC001':'GC001_source.png'}
CAP={'Raden':1412,'GC001':1887}
BASE_COUNT={'Raden':1309,'GC001':1710}
# Remaining structure is most crucial in hair, clothes, and torso, not facial micro-details.
ROLES=('hair','major_clothing','torso','lower_body')
EPS=(2.5,4.0,6.0,8.0)
MIN_AREA=(20,45)


def sign(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def actual_svg_vertices(root,case):
    initial=previous.previous.prev.last.prior.strict_vertices(root,case)['expanded_deployed_vertices']
    new=sum(previous.previous.prev.last.prior.prior.shared.path_vertices(x.get('d',''))
            for x in root.iter(NS+'path') if x.get('data-sa1056-material'))
    return initial+new

def actual_chromium(page,root):return previous.previous.browser_rgb(page,root)

def foreground_masks(case,face):
    visible,_=previous.previous.prev.last.prior.prior.opt.visible_ownership(case)
    return visible,np.logical_or.reduce([face,*visible.values()])

def score(img,photo,mask):
    return float(np.abs(img[mask].astype(np.int16)-photo[mask].astype(np.int16)).mean())

def signed_case(name,source_root,baseline):
    if name not in BASE_SHA:raise ValueError('UNKNOWN_CASE')
    if sign(baseline)!=BASE_SHA[name]:raise ValueError('SA1055_SIGNED_BASELINE_SHA_MISMATCH')
    data=previous.previous.prev.last.prior.prior.dual.load_case(name,source_root)
    case=previous.previous.prev.last.prior.prior.opt.load_case(name,source_root)
    root=ET.parse(baseline).getroot()
    previous.audit_default_faceless(root)
    if actual_svg_vertices(root,case)!=BASE_COUNT[name]:raise ValueError('SA1055_BASE_VERTEX_MISMATCH')
    return data,case,root

def protected_inventory(svg):
    """Enforce signed face, masks, source Stage9/37 colored panels and geometry."""
    return previous.direct_paint_inventory(svg)['defs'], [ET.tostring(x,encoding='unicode') for x in svg.iter(NS+'polygon')], [n.get('data-owner-index') for n in svg if n.get('data-owner-index') is not None], ET.tostring(previous.face_guard(svg),encoding='unicode')

def role_color_proposals(name,photo,mask):
    """Source-only LAB clusters; verify each actual stroke color in its owner region.

    Use one layer at a time; never embed the signed original raster in SVG.
    """
    source=previous.previous.prev.last.prior.prior
    ret=[];seen=set()
    for epsilon in EPS:
        for area in MIN_AREA:
            clusters=source.observe_palette(photo,mask,{'k':3,'epsilon':epsilon,'min_area':area})
            for item in clusters['details']:
                if item['vertices']<3:continue
                # Some simplifications are geometrically identical across policies.
                key=(tuple(item['rgb']),item['path'])
                if key in seen:continue
                seen.add(key)
                assert np.any(np.all(photo[mask]==np.asarray(item['rgb']),axis=1))
                ret.append({'source_role':name,'rgb':item['rgb'],'path':item['path'],
                    'vertices':item['vertices'],'epsilon':epsilon,'min_area':area,
                    'cluster_source_pixels':item['source_cluster_pixels']})
    return ret

def add_layer(svg,case,role,observation):
    result=copy.deepcopy(svg)
    owner_id=next(i for i,r in enumerate(case['records']) if r['source_mask_owner']==role)
    owner=next(n for n in result if n.get('data-owner-index')==str(owner_id))
    if owner.get('mask')!=f'url(#sa1041-owner-{owner_id})' or owner[0].tag!=NS+'rect':
        raise ValueError('UNVERIFIED_SOURCE_OWNER_GROUP')
    # Last in owner group but still lower z than subsequent original owner groups
    # and than the single final signed-face guard.  Preserve old material regions.
    ET.SubElement(owner,NS+'path',{'d':observation['path'],
       'fill':previous.previous.prev.last.prior.prior.hex_rgb(observation['rgb']),
       'fill-rule':'evenodd','data-sa1056-material':role,
       'data-source-pixel-medoid':'true'})
    return result

def evaluate_one(name,root_dir,baseline_svg,out,page):
    data,case,root=signed_case(name,root_dir,baseline_svg)
    face=data['masks']['face'];arms=data['masks']['left_arm']|data['masks']['right_arm']
    visible,foreground=foreground_masks(case,face)
    original=actual_chromium(page,root)
    # Chromium SHA pins the *actual* previous stage, not a declared MAE alone.
    expected={'Raden':'54997a07a90e18607f491f95178b7e5f91f1fa6e4acf4c58bb7fd20226edb3bd',
              'GC001':'921a871af5e609d812187236641270562c852222e3d3d5de4b83d406f85ef1fb'}[name]
    by=io.BytesIO();Image.fromarray(original).save(by,format='PNG')
    if hashlib.sha256(by.getvalue()).hexdigest()!=expected:raise AssertionError('SIGNED_CHROMIUM_BASELINE_REPLAY_FAILED')
    photo=data['photo'];initial_foreground=score(original,photo,foreground)
    initial_inventory=protected_inventory(root)
    current=root;frame=original;current_global=initial_foreground
    allowed=np.logical_and(foreground,~face)
    accepted=[];rejected=[];trials=0
    # Priority order is explicit; do not allow low-value apparel at the expense of hair.
    for role in ROLES:
        owner_id=next(i for i,r in enumerate(case['records']) if r['source_mask_owner']==role)
        mask=visible[f'sa1041-owner-{owner_id}']
        baseline_role=score(frame,photo,mask)
        candidates=role_color_proposals(role,photo,mask)
        remaining=CAP[name]-actual_svg_vertices(current,case)
        feasible=[]
        for cand in candidates:
            if cand['vertices']>remaining:continue
            modified=add_layer(current,case,role,cand)
            if actual_svg_vertices(modified,case)>CAP[name]:continue
            trial=actual_chromium(page,modified);trials+=1
            if not np.array_equal(trial[~allowed],original[~allowed]):continue
            fg=score(trial,photo,foreground);local=score(trial,photo,mask)
            if fg>=current_global-1e-8 or local>=baseline_role-1e-8:continue
            # Explicitly rank by original-source role gain and constrained total cost.
            gain=baseline_role-local
            feasible.append((fg, -gain, cand['vertices'],cand['epsilon'],cand['min_area'],cand,modified,trial,local))
        if not feasible:
            rejected.append({'role':role,'reason':'no source-improving color boundary within protected budget','remaining_vertices':remaining})
            continue
        best=min(feasible,key=lambda x:x[:5]);fg,_,num,epsilon,area,cand,newsvg,newframe,local=best
        accepted.append({'role':role,'vertices':num,'epsilon':epsilon,'min_area':area,
                         'source_rgb':list(cand['rgb']),'owner_source_mae_before':round(baseline_role,6),
                         'owner_source_mae_after':round(local,6),
                         'foreground_source_mae_after':round(fg,6),
                         'source_cluster_pixels':cand['cluster_source_pixels']})
        current,frame,current_global=newsvg,newframe,fg
    account=actual_svg_vertices(current,case)
    previous.audit_default_faceless(current)
    if protected_inventory(current)[1:]!=initial_inventory[1:]:
        raise AssertionError('IMMUTABLE_STAGE9_FACE_OWNER_ORDER_CHANGED')
    # Masks/trim within defs are also immutably inherited.
    if protected_inventory(current)[0]!=initial_inventory[0]:
        raise AssertionError('IMMUTABLE_SOURCE_MASKS_CHANGED')
    if not np.array_equal(frame[~allowed],original[~allowed]):
        raise AssertionError('PROTECTED_SOURCE_BACKGROUND_FACE_ARMS_CHANGED')
    if not np.array_equal(frame[face],original[face]):raise AssertionError('FACELESS_FACE_REPAINTED')
    if not np.array_equal(frame[arms],original[arms]):raise AssertionError('SIGNATURE_ARMS_CHANGED')
    if account>CAP[name] or account!=BASE_COUNT[name]+sum(a['vertices'] for a in accepted):
        raise AssertionError('REAL_EXPANDED_VERTEX_BUDGET_LEDGER_FAILED')
    if not current_global<initial_foreground:raise AssertionError('NO_MATERIAL_FIDELITY_IMPROVEMENT')
    if len(accepted)<1:raise AssertionError('NO_REAL_SOURCE_COLOR_DETAIL_WAS_RETAINED')
    if any(n.tag in (NS+'image',NS+'foreignObject',NS+'feImage') for n in current.iter()):
        raise AssertionError('SOURCE_IMAGE_EMBEDDED')
    stem=name.lower()
    (out/f'{stem}_faceless_material.svg').write_text(ET.tostring(current,encoding='unicode'),'utf-8')
    Image.fromarray(original).save(out/f'{stem}_sa1055_baseline.png')
    Image.fromarray(frame).save(out/f'{stem}_faceless_material.png')
    return {'case':name,'source_authority_sha256':case['source_input_sha256'],
      'sa1055_svg_sha256':sign(baseline_svg),'chromium_baseline_sha256':expected,
      'expanded_vertices_baseline':BASE_COUNT[name],'expanded_vertices_final':account,'hard_limit':CAP[name],
      'actual_added_vertices':account-BASE_COUNT[name],'remaining_vertices':CAP[name]-account,
      'rendered_original_source_foreground_mae_before':round(initial_foreground,6),
      'rendered_original_source_foreground_mae_after':round(current_global,6),
      'material_layers_accepted':accepted,'material_layers_rejected':rejected,
      'tested_chromium_proposals':trials,'faceless_policy_pass':True,
      'face_changed_pixels':0,'both_arms_changed_pixels':0,
      'outside_source_visible_changed_pixels':0,'stage8_original_source_ring_policy':'FAIL',
      'human_visual_review':'PENDING','full_character_golden':'HOLD','production_deployment':'UNCHANGED'}

def evaluate(raden_root,gc_root,raden_svg,gc_svg,out,chromium='/usr/bin/chromium'):
    roots=[Path(raden_root).resolve(),Path(gc_root).resolve()]
    sources=[Path(raden_svg).resolve(),Path(gc_svg).resolve()]
    out=Path(out).resolve()
    if roots[0]==roots[1] or any(out==r or out in r.parents or r in out.parents for r in roots):
        raise ValueError('Signed originals and output must be separate')
    if any(out==p or out in p.parents or p in out.parents for p in sources):
        raise ValueError('Cannot overwrite immutable source SVG')
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pl:
        browser=pl.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            cases=[evaluate_one(n,r,b,out,page) for n,r,b in zip(CASES,roots,sources)]
            version=browser.version
        finally:browser.close()
    board=Image.new('RGB',(340*3,380*2),(246,246,244));draw=ImageDraw.Draw(board)
    for row,name in enumerate(CASES):
        src=Image.open(roots[row]/ORIGINAL_SOURCE[name]).convert('RGB')
        before=Image.open(out/f'{name.lower()}_sa1055_baseline.png').convert('RGB')
        after=Image.open(out/f'{name.lower()}_faceless_material.png').convert('RGB')
        for col,(im,title) in enumerate(zip((src,before,after),('SIGNED SOURCE','SA10.55 FACELESS','SA10.56 MATERIAL'))):
            board.paste(im,(col*340,row*380+40))
            draw.text((col*340+5,row*380+13),f'{name.upper()} / {title}',fill=(20,20,22))
    board.save(out/'sa1056_two_case_material_board.png')
    result={'stage':'SA10.56','schema':'signed-faceless-material-budgeted-source-palette-v1','chromium':version,
       'cases':{c['case']:c for c in cases},'two_case_faceless_preserved':True,
       'two_case_source_fidelity_improved':True,'two_case_true_expanded_vertex_budget_pass':True,
       'no_generation_raster_embeds_or_facials':True,'historical_stage8_source_ring_gate':'FAIL',
       'human_visual_review':'PENDING','full_character_golden':'HOLD','production_deployment':'UNCHANGED'}
    result['artifact_sha256']={x.name:sign(x) for x in sorted(out.iterdir()) if x.is_file()}
    (out/'sa1056_metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('raden','gc001','raden_svg','gc001_svg','out'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    a=p.parse_args()
    r=evaluate(a.raden,a.gc001,a.raden_svg,a.gc001_svg,a.out)
    print(json.dumps({k:{'vertices':v['expanded_vertices_final'],'budget':v['hard_limit'],
      'MAE':(v['rendered_original_source_foreground_mae_before'],v['rendered_original_source_foreground_mae_after']),
      'selected':v['material_layers_accepted']} for k,v in r['cases'].items()},indent=2))
