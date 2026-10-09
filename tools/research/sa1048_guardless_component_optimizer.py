"""SA10.48: GC001 case-specific source-proof protector pruning and component budgets.

Research only, no production changes. No source raster embedding, invented geometry,
material segmentation inference or fabricated face. Source signatures verified by SA10.46.
All mask vertices, every corrective rectangle (4), and Stage9/37 polygons counted.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sa1047_two_case_visible_optimizer as previous

NS = previous.NS
PROTECTED = previous.PROTECTED
CASE = 'GC001'
# Source-specific, frozen after measured Chromium candidate exploration.
# A nonzero min_component_area removes only a disconnected component of the
# indicated source owner's *visible* binary mask. Loss is measured, not hidden.
POLICY = {
    'hair':                 {'epsilon': 2.0,  'min_component_area': 4},
    'lower_body':           {'epsilon': 1.25, 'min_component_area': 0},
    'torso':                {'epsilon': 1.5,  'min_component_area': 2},
    'major_clothing':       {'epsilon': 1.0,  'min_component_area': 0},
    'unknown':              {'epsilon': 1.25, 'min_component_area': 8},
    'neck':                 {'epsilon': 1.0,  'min_component_area': 0},
    'accessory_or_held_object': {'epsilon': 1.0,'min_component_area': 0},
}
EXPECTED = {'deployed_vertices':1883, 'full_rgb_mismatch':1871,
            'exact_unprotected_rgb_mismatch':683, 'protected_rgb':{'face':0,'left_arm':0,'right_arm':0}}


def source_case(root:Path):
    return previous.load_case(CASE,root)


def component_filter(source:np.ndarray, min_area:int):
    if min_area < 0: raise ValueError('Negative component area threshold')
    if min_area == 0: return source.copy(), {'removed_pixels':0,'removed_components':0}
    n, labels, stats, _ = cv2.connectedComponentsWithStats(source.astype(np.uint8),8)
    ids=[i for i in range(1,n) if stats[i,cv2.CC_STAT_AREA]>min_area]
    result=np.isin(labels,ids)
    return result, {'removed_pixels':int(np.count_nonzero(source & ~result)),
                    'removed_components':n-1-len(ids)}


def build_exact(case):
    visible,_ = previous.visible_ownership(case)
    scene=previous.prune_scene(case)
    for ident,source in visible.items():
        path,_=previous.vector_path(source,0.5)
        previous.edge.replace_svg_mask(scene,ident,path)
    path,_=previous.vector_path(case['signed']['face'],0.5)
    previous.edge.replace_svg_mask(scene,'sa1041-original-face-guard',path)
    protected=np.logical_or.reduce([case['signed'][x] for x in PROTECTED])
    path,_=previous.vector_path(protected,0.5)
    previous.edge.replace_svg_mask(scene,'sa1041-protected-clear',path,inverse=True)
    if previous.count_svg(scene,55)['expanded_deployed_vertices']!=5327:
        raise AssertionError('GC001 exact source-view geometry changed')
    return scene,visible


def remove_redundant_protector(svg):
    out=copy.deepcopy(svg)
    users=[n for n in out.iter() if n.get('mask')=='url(#sa1041-protected-clear)']
    if len(users)!=4 or not any(len(list(n.iter(NS+'polygon')))==5 for n in users):
        raise ValueError('GC001 four signed Stage9/37 overlay groups were modified')
    for user in users: user.attrib.pop('mask')
    defs=out.find(NS+'defs')
    protectors=[n for n in defs if n.get('id')=='sa1041-protected-clear']
    if len(protectors)!=1:raise ValueError('Missing guard mask or duplicate')
    defs.remove(protectors[0])
    if any(n.get('mask')=='url(#sa1041-protected-clear)' for n in out.iter()):
        raise AssertionError('Dangling source protector')
    if sum(len(n.get('points','').split()) for n in out.iter(NS+'polygon'))!=55:
        raise AssertionError('Stage9/37 source color planes disappeared')
    return out


def prove_guard_non_effect(page,exact,case):
    """All 16 independent combinations of 4 overlays must yield exact same RGB.
    Necessary evidence before removing guard; this holds only on signed GC001.
    """
    baseline=previous.edge.chromium_rgb(page,ET.tostring(exact,encoding='unicode'))
    changed=[]
    for bits in range(16):
        proof=copy.deepcopy(exact)
        users=[n for n in proof.iter() if n.get('mask')=='url(#sa1041-protected-clear)']
        for i,user in enumerate(users):
            if (bits>>i)&1:user.attrib.pop('mask')
        observed=previous.edge.chromium_rgb(page,ET.tostring(proof,encoding='unicode'))
        mismatch=int(np.count_nonzero(np.any(baseline!=observed,axis=2)))
        changed.append(mismatch)
        if mismatch:raise AssertionError('Protected apparel guard has semantic effect, remove prohibited')
    return baseline,{'tested_combinations':len(changed),'mismatched_rgb_pixels_per_combination':changed}


def build_candidate(page,case,exact,visible):
    svg=remove_redundant_protector(exact)
    protected=np.logical_or.reduce([case['signed'][k] for k in PROTECTED])
    details={}
    encountered=set()
    for ident,binary in visible.items():
        index=int(ident.rsplit('-',1)[1]); role=case['records'][index]['source_mask_owner']
        if role in PROTECTED: continue
        if role not in POLICY: raise AssertionError('Unknown nonprotected source owner: '+role)
        config=POLICY[role]; encountered.add(role)
        shape,filtered=component_filter(binary,config['min_component_area'])
        path,n=previous.vector_path(shape,config['epsilon'])
        previous.edge.replace_svg_mask(svg,ident,path)
        observed=previous.edge.chromium_rgb(page,previous.edge.isolated_svg(svg,ident))[...,0]<128
        foreign=observed & protected & ~binary
        patches=previous.raden45.pixel_rectangles(foreign)
        node=next(n for n in svg.iter(NS+'mask') if n.get('id')==ident)
        for x,y,w,h in patches:
            ET.SubElement(node,NS+'rect',{'x':str(x),'y':str(y),'width':str(w),'height':str(h),
                'fill':'#000000','shape-rendering':'crispEdges','data-sa1047-protected-trim':'1'})
        details[role]={**config,**filtered,'mask_path_vertices':n,
                       'trim_rectangles':len(patches),'trim_vertices':4*len(patches),
                       'protected_new_overpaint_removed_pixels':int(foreign.sum())}
    if encountered!=set(POLICY):raise AssertionError('Per-owner optimized policy missing signed masks')
    if any(n.tag in (NS+'image',NS+'foreignObject',NS+'feImage') for n in svg.iter()):
        raise AssertionError('No bitmap or generated filler allowed')
    account=previous.count_svg(svg,55)
    return svg,account,details


def evaluate(gc001_root:Path, out:Path, chromium:str='/usr/bin/chromium'):
    gc001_root,out=gc001_root.resolve(),out.resolve()
    if gc001_root==out or out in gc001_root.parents or gc001_root in out.parents:
        raise ValueError('Do not modify source-authority directory')
    case=source_case(gc001_root)
    exact,visible=build_exact(case)
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pl:
        browser=pl.chromium.launch(headless=True,executable_path=chromium,
            args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            exact_frame,proof=prove_guard_non_effect(page,exact,case)
            guardless=remove_redundant_protector(exact)
            guardless_frame=previous.edge.chromium_rgb(page,ET.tostring(guardless,encoding='unicode'))
            if not np.array_equal(exact_frame,guardless_frame):
                raise AssertionError('Full protector removal unexpectedly changes signed scene')
            exact_result=previous.edge.metrics(case['original'],exact_frame,case['signed'])
            if exact_result['full_rgb_mismatch']!=EXPECTED['exact_unprotected_rgb_mismatch']:
                raise AssertionError('GC001 frozen source baseline changed')
            candidate,account,details=build_candidate(page,case,exact,visible)
            output=previous.edge.chromium_rgb(page,ET.tostring(candidate,encoding='unicode'))
            measured=previous.edge.metrics(case['original'],output,case['signed'])
            chrome=browser.version
        finally:browser.close()
    if measured['source_signed_protected']!=EXPECTED['protected_rgb']:
        raise AssertionError('Face / either arm was corrupted')
    if account['expanded_deployed_vertices']!=EXPECTED['deployed_vertices'] or measured['full_rgb_mismatch']!=EXPECTED['full_rgb_mismatch']:
        raise AssertionError('SA10.48 candidate cost or Chromium rendering changed')
    if account['expanded_deployed_vertices']>case['budget']:
        raise AssertionError('Hard signed GC001 vertex budget exceeded')
    svg=(out/'gc001_guardless_component_budget.svg')
    svg.write_text(ET.tostring(candidate,encoding='unicode'),'utf-8')
    Image.fromarray(output).save(out/'gc001_guardless_component_budget.png')
    Image.fromarray(exact_frame).save(out/'gc001_guarded_exact.png')
    Image.fromarray(guardless_frame).save(out/'gc001_guardless_exact.png')
    # Baseline is Stage9/37 derived signed full OpenCV, not original artistic photo.
    board=Image.new('RGB',(340*3,380),(246,246,243));pen=ImageDraw.Draw(board)
    images=[('SIGNED CV2',case['original']),('VISIBLE EXACT',exact_frame),('SA10.48 BUDGET',output)]
    for i,(label,im) in enumerate(images):
        board.paste(Image.fromarray(im),(340*i,40))
        pen.text((340*i+8,12),label,fill=(10,15,20))
    board.save(out/'gc001_sa1048_three_way.png')
    report={'stage':'SA10.48','schema':'gc001-source-signed-guardless-component-budget-v1',
        'source_hashes':case['source_input_sha256'],'chromium':chrome,
        'original_case_stage8_vertices':3604,'original_case_stage8_budget':1887,
        'source_ring_budget_pass':False,'historical_sa1047_candidate':{'expanded_deployed_vertices':2925,'full_rgb_mismatch':1980,'protected':EXPECTED['protected_rgb']},
        'guard_non_effect_proof':proof,'exact_guarded_and_guardless_rgb_identical':True,
        'exact_full_rgb_mismatch':exact_result['full_rgb_mismatch'],
        'exact_guarded_expanded_vertices':previous.count_svg(exact,55)['expanded_deployed_vertices'],
        'exact_guardless_expanded_vertices':previous.count_svg(guardless,55)['expanded_deployed_vertices'],
        'policy':POLICY,'details':details,'budget_candidate':{**account,'full_chromium':measured,
          'owner_error_partition':previous.source_owner_rgb_partition(case,output)},
        'stage9_polygon_vertices':28,'stage37_apparel_polygon_vertices':27,
        'all_source_color_polygons_preserved':True,'two_case_worst_regression_prohibited':True,
        'raden_champion':{'vertices':1409,'rgb_mismatch':882,'status':'UNCHANGED'},
        'full_character_golden':'HOLD','production_deployment':'UNCHANGED',
        'human_visual_review':'PENDING','use_of_generative_fill':False}
    names=sorted(f.name for f in out.iterdir() if f.is_file())
    report['artifact_sha256']={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in names}
    (out/'sa1048_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--gc001',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--chromium',default='/usr/bin/chromium')
    args=p.parse_args()
    result=evaluate(args.gc001,args.out,args.chromium)
    print(json.dumps({'stage':result['stage'],'chrome':result['chromium'],
        'vertices':result['budget_candidate']['expanded_deployed_vertices'],
        'budget':1887,'rgb':result['budget_candidate']['full_chromium'],
        'guard_combinations':result['guard_non_effect_proof']['tested_combinations']},indent=2))

if __name__=='__main__':main()
