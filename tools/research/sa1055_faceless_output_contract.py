"""SA10.55: default faceless target-style release gate for signed two-case ZeroBase research.

Research-only validation.  Signed Stage04 face boundary remains, but no drawn
face feature survives the default output SVG.  Eye chroma SA10.54 remains a
SHA-pinned *diagnostic* baseline, not the default rendering policy.  This module
is not the production integration step; canonical routing follows at SA10.60.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1054_iris_component_palette as previous

NS=previous.NS
CASES=('Raden','GC001')
RESEARCH_SHA={'Raden':'11bfc1eb83116981ae6d4f07688af0c0aa165e074af10bf29881c16c938188f5',
              'GC001':'8ebbb1a44c4f893190c8f536c86397b52d13cbd1a6af3d2f3c60e8a46bf67cbb'}
TARGET_STYLE='faceless_subject'
BUDGET={'Raden':1412,'GC001':1887}
FACE_MASK='url(#sa1041-original-face-guard)'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def face_guard(root):
    guards=[n for n in root if n.tag==NS+'g' and n.get('mask')==FACE_MASK]
    if len(guards)!=1 or root[-1] is not guards[0]:
        raise ValueError('Signed final face painter must exist exactly once at known paint order')
    guard=guards[0]
    if not len(guard) or guard[0].tag!=NS+'rect' or not guard[0].get('fill'):
        raise ValueError('Signed source base skin rectangle missing')
    return guard

def direct_paint_inventory(svg):
    # Track all actual macro-geometry, source-proven apparel, owner order and masks.
    guard=face_guard(svg)
    return {'defs':ET.tostring(next(x for x in svg if x.tag==NS+'defs'),encoding='unicode'),
            'background_and_owner_paints':[ET.tostring(x,encoding='unicode') for x in svg if x is not guard],
            'face_base_tag':ET.tostring(guard[0],encoding='unicode'),
            'face_guard_mask':guard.get('mask')}

def face_feature_inventory(svg):
    guard=face_guard(svg)
    return {'face_children':len(guard)-1,
            'source_feature_paths':sum(n.tag==NS+'path' and n.get('data-sa1051-observed')=='face' for n in guard[1:]),
            'path_vertices':sum(previous.prev.last.prior.prior.shared.path_vertices(n.get('d',''))
                                 for n in guard[1:] if n.tag==NS+'path')}

def enforce_face_off(svg):
    root=copy.deepcopy(svg)
    old=face_guard(root);inv=face_feature_inventory(root)
    if inv['face_children']<1 or inv['face_children']!=inv['source_feature_paths']:
        raise ValueError('Unreviewed face painter child; fail closed')
    original_macro=direct_paint_inventory(root)
    source_base=old[0].get('fill')
    for child in list(old)[1:]:old.remove(child)
    root.set('data-minimalizer-target-style',TARGET_STYLE)
    root.set('data-minimalizer-face-features','off')
    audit_default_faceless(root)
    if direct_paint_inventory(root)!=original_macro:
        raise AssertionError('Source body, hair, mask or skin changed')
    return root,{'removed_face_paint_paths':inv['source_feature_paths'],
                 'freed_true_path_vertices':inv['path_vertices'],
                 'source_observed_skin_hex':source_base,
                 'extra_face_mask_references':0}

def audit_default_faceless(svg):
    # Structural shipping audit: no rendered face subpaths, re-added SVG eyes,
    # CSS tricks or hidden external raster imagery.  A synthetic face ellipse
    # cannot bypass this because only the signed final rect is allowed.
    if svg.get('data-minimalizer-target-style')!=TARGET_STYLE or svg.get('data-minimalizer-face-features')!='off':
        raise ValueError('FACE_OFF_TARGET_POLICY_UNDECLARED')
    guard=face_guard(svg)
    if len(guard)!=1 or guard[0].tag!=NS+'rect':
        raise ValueError('FACIAL_FEATURE_PAINT_FORBIDDEN')
    if sum(n.get('mask')==FACE_MASK for n in svg.iter())!=1:
        raise ValueError('EXTRA_FACE_MASK_REFERENCE_FORBIDDEN')
    for n in svg.iter():
        if n.tag in (NS+'image',NS+'foreignObject',NS+'feImage',NS+'text',NS+'use',NS+'style'):
            raise ValueError('NONCANONICAL_RENDERER_OBJECT_FORBIDDEN')
        if n.get('data-sa1051-observed')=='face' or n.get('data-sa1054-separable') is not None:
            raise ValueError('FACIAL_FEATURE_PAINT_FORBIDDEN')
    return True

def check_auth(name,root,svg_path):
    if name not in RESEARCH_SHA:raise ValueError('UNKNOWN_SIGNED_CASE')
    if sha(svg_path)!=RESEARCH_SHA[name]:raise ValueError('SA1054_RESEARCH_BASELINE_SHA_MISMATCH '+name)
    data=previous.prev.last.prior.prior.dual.load_case(name,root)
    case=previous.prev.last.prior.prior.opt.load_case(name,root)
    svg=ET.parse(svg_path).getroot()
    count=previous.prev.last.prior.strict_vertices(svg,case)['expanded_deployed_vertices']
    if count!=(1412 if name=='Raden' else 1882):raise ValueError('SOURCE_BUDGET_BASELINE_MISMATCH')
    return data,case,svg

def pixel_difference(before,after,mask):
    return int(np.count_nonzero(np.any(before!=after,axis=2)&mask))

def evaluate_case(name,root,svg_path,out,page):
    data,case,original=check_auth(name,root,svg_path)
    skin=face_guard(original)[0].get('fill')
    # Skin RGB remains a verbatim originally observed source medoid, confirmed
    # against actual source pixels rather than guessed by the current model.
    rgb=tuple(int(skin[n:n+2],16) for n in (1,3,5))
    if not np.any(np.all(data['photo'][data['masks']['face']]==rgb,axis=1)):
        raise AssertionError('SIGNED_ORIGINAL_SKIN_RGB_NOT_OBSERVED')
    reference=previous.browser_rgb(page,original)
    canonical,freed=enforce_face_off(original)
    frame=previous.browser_rgb(page,canonical)
    face=data['masks']['face'];arms=data['masks']['left_arm']|data['masks']['right_arm']
    if pixel_difference(reference,frame,~face)>0:raise AssertionError('FACE_OFF_PAINT_LEAK_OUTSIDE_SIGNED_FACE')
    if pixel_difference(reference,frame,arms)>0:raise AssertionError('SIGNED_ARMS_CHANGED')
    if pixel_difference(reference,frame,face)<20:raise AssertionError('FACE_FEATURE_PAINT_NOT_ACTUALLY_REMOVED')
    eroded=cv2.erode(face.astype('uint8'),np.ones((3,3),np.uint8)).astype(bool)
    inside_rgb=frame[eroded]
    nonuniform_pixels=int(np.count_nonzero(np.any(inside_rgb!=rgb,axis=1)))
    if nonuniform_pixels:raise AssertionError('VISIBLE_FACE_MICROCOLOR_OR_GEOMETRY_REMAINING')
    account=previous.prev.last.prior.strict_vertices(canonical,case)
    if account['expanded_deployed_vertices']>BUDGET[name]:raise AssertionError('CANONICAL_FACE_OFF_VERTEX_BUDGET_EXCEEDED')
    if account['expanded_deployed_vertices']+freed['freed_true_path_vertices']!=(1412 if name=='Raden' else 1882):
        raise AssertionError('FREED_VERTEX_LEDGER_INCONSISTENT')
    k=name.lower()
    (out/f'{k}_faceless.svg').write_text(ET.tostring(canonical,encoding='unicode'),'utf-8')
    Image.fromarray(frame).save(out/f'{k}_faceless.png')
    Image.fromarray(reference).save(out/f'{k}_face_detail_research_only.png')
    return {'name':name,'signed_source_sha256':case['source_input_sha256'],
            'sa1054_baseline_sha256':sha(svg_path),'face_off_by_default':True,
            'standard_output_svg_has_zero_facials':True,
            'rendered_face_interior_is_one_real_source_rgb':True,
            'face_interior_pixel_rgb':list(rgb),
            'signed_face_eroded_pixel_count':int(eroded.sum()),
            'nonuniform_eroded_face_pixels':nonuniform_pixels,
            'removed_face_feature_paths':freed['removed_face_paint_paths'],
            'reclaimed_face_vertices':freed['freed_true_path_vertices'],
            'expanded_vertex_count_before':1412 if name=='Raden' else 1882,
            'expanded_vertex_count_after':account['expanded_deployed_vertices'],
            'hard_budget':BUDGET[name],
            'changed_signed_face_pixels_to_remove_details':pixel_difference(reference,frame,face),
            'changed_outside_signed_face':pixel_difference(reference,frame,~face),
            'changed_signed_arms':pixel_difference(reference,frame,arms),
            'prior_face_photo_mae':previous.prev.last.source_mae(reference,data['photo'],face),
            'canonical_face_photo_mae':previous.prev.last.source_mae(frame,data['photo'],face),
            'legacy_stage8_source_ring_gate':'FAIL',
            'human_visual_review':'PENDING','full_character_golden':'HOLD','production_deployment':'UNCHANGED'}

def evaluate(raden_root,gc_root,raden_svg,gc_svg,out,chromium='/usr/bin/chromium'):
    roots=[Path(raden_root).resolve(),Path(gc_root).resolve()]
    svgs=[Path(raden_svg).resolve(),Path(gc_svg).resolve()]
    out=Path(out).resolve()
    if roots[0]==roots[1] or any(out==r or out in r.parents or r in out.parents for r in roots):
        raise ValueError('Research output must be separate from signed sources')
    if any(out==s or out in s.parents or s in out.parents for s in svgs):
        raise ValueError('Do not overwrite signed research SVG baseline')
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pl:
        browser=pl.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            cases=[evaluate_case(n,r,s,out,page) for n,r,s in zip(CASES,roots,svgs)]
            chrome=browser.version
        finally:browser.close()
    board=Image.new('RGB',(340*3,380*2),(246,246,244));draw=ImageDraw.Draw(board)
    for row,name in enumerate(CASES):
        src=Image.open(roots[row]/('Raden_source.png' if name=='Raden' else 'GC001_source.png')).convert('RGB')
        ref=Image.open(out/f'{name.lower()}_face_detail_research_only.png').convert('RGB')
        done=Image.open(out/f'{name.lower()}_faceless.png').convert('RGB')
        for col,(im,title) in enumerate(zip((src,ref,done),('SIGNED SOURCE','SA10.54 RESEARCH ONLY','SA10.55 FACELESS TARGET'))):
            board.paste(im,(col*340,row*380+40))
            draw.text((col*340+7,row*380+14),f'{name.upper()} / {title}',fill=(16,16,20))
    board.save(out/'sa1055_two_case_faceless_comparison.png')
    report={'stage':'SA10.55','schema':'signed-target-face-off-gate-v1','chromium':chrome,
            'target_style':TARGET_STYLE,'facial_microfeatures_default':'OFF',
            'face_research_diagnostics_retained_but_not_canonical':True,
            'test_corpus':['Raden','GC001'],'cases':{x['name']:x for x in cases},
            'two_case_faceless_output_policy_pass':True,
            'two_case_chromium_signed_protection_pass':True,
            'two_case_expanded_vertices_under_hard_budget':True,
            'historical_source_stage8_ring_budget':'FAIL',
            'full_character_golden':'HOLD','human_visual_review':'PENDING',
            'production_integration':'NOT_YET_WIRED','production_deployment':'UNCHANGED'}
    report['sha256']={x.name:sha(x) for x in sorted(out.iterdir()) if x.is_file()}
    (out/'sa1055_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('raden','gc001','raden_svg','gc001_svg','out'):
        p.add_argument('--'+n.replace('_','-'),required=True,type=Path)
    a=p.parse_args()
    results=evaluate(a.raden,a.gc001,a.raden_svg,a.gc001_svg,a.out)
    print(json.dumps({'stage':results['stage'],'cases':{n:{k:v[k] for k in ('removed_face_feature_paths','reclaimed_face_vertices','expanded_vertex_count_after','changed_outside_signed_face','changed_signed_arms','nonuniform_eroded_face_pixels')} for n,v in results['cases'].items()}},indent=2))
