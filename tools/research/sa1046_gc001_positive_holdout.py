"""SA10.46: GC001 positive-character source-locked real Chromium holdout.

Research only. Never reuses Raden owner indices, empty-clothing proofs, budgets,
or signed-arm geometry. The SVG stays geometrical; no raster/fill generation.
"""
from __future__ import annotations
import argparse
import copy
from hashlib import sha256
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

# Installed repo workflow puts SA10.43 in the same research tools folder.
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1043_boundary_compaction as contour

CASE='GC001'
ORDER=('hair','lower_body','right_arm','face','torso','major_clothing',
       'unknown','left_arm','neck','head','accessory_or_held_object')
BUDGET=1887
EXPECTED_SHA={
'GC001_source.png':'75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e',
'phase8_adaptive_source_contour_research.json':'7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08',
'full_character_vector.svg':'0f10af9aaddad0ee96c7acbafb73361ee0000ee6833b9d581025659895718b34',
'signed_full_opencv_reference.png':'b155651a9aac6979472f391564756a3866ab0ed4fe0e955af58a3ab3557d39c9',
'signed_face_stage04_mask.png':'b4812364eaec7da9930a18ae85270d6612555d3fb3d80283efcf69b03aa6a72f',
'signed_left_arm_stage04_mask.png':'49986981c02f472a888e1717205799c254b16c1bca7ef96beba2dc6b4f696b5f',
'signed_right_arm_stage04_mask.png':'4900beccaf0ca4a9ca33600339df77976a4500f1db932fcb240a41907b935b91',
'full_character_svg_metrics.json':'c0d4a730289024090f4a77fe61563d56de32e7e9158790a29768a546e0265cc2',
}
NS=contour.NS
PROTECTED=('face','left_arm','right_arm')
EPSILONS=(0.5,1.0,1.5)


def load_signed(root:Path):
    for name,expected in EXPECTED_SHA.items():
        path=root/name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Source authority hash mismatch: '+name)
    scene=json.loads((root/'phase8_adaptive_source_contour_research.json').read_text('utf-8'))
    metrics=json.loads((root/'full_character_svg_metrics.json').read_text('utf-8'))
    records=scene['primitives_back_to_front']
    if (len(records)!=11 or tuple(p['source_mask_owner'] for p in records)!=ORDER
        or scene['original_source_sha256']!=EXPECTED_SHA['GC001_source.png']
        or metrics['original_source_sha256']!=EXPECTED_SHA['GC001_source.png']
        or metrics['original_source_ring_vertex_budget_limit']!=BUDGET
        or metrics['phase9_interior_polygon_vertices']!=28
        or metrics['phase37_apparel_polygon_vertices']!=27
        or metrics['original_source_ring_vertices_including_support']!=3604
        or metrics['production_promotion_authorized'] is not False):
        raise ValueError('GC001 Stage8/9/37 source lineage, owner order or budget changed')
    source={f'sa1041-owner-{i}':contour.source_ring_mask(p['parameters']['rings'])
            for i,p in enumerate(records)}
    signed={role:np.asarray(Image.open(root/f'signed_{role}_stage04_mask.png').convert('L'))>0
            for role in PROTECTED}
    source['sa1041-original-face-guard']=signed['face']
    source['sa1041-protected-clear']=np.logical_or.reduce(list(signed.values()))
    delta={role:int(np.count_nonzero(source[f'sa1041-owner-{ORDER.index(role)}']!=signed[role]))
           for role in PROTECTED}
    if delta!={'face':0,'left_arm':5,'right_arm':24}:
        raise ValueError('GC001 signed face/arms cannot be aliased or silently changed')
    svg=ET.parse(root/'full_character_vector.svg').getroot()
    if len(list(svg.iter(NS+'mask')))!=13:
        raise ValueError('Original 13 source masks required')
    if ([e.get('data-owner-index') for e in svg if e.get('data-owner-index') is not None] !=
       ['0','1','2','3','4','5','6','7','8','10']):
        raise ValueError('Original GC001 opaque z-order cannot be rewritten')
    apparel_group=next(n for n in svg if n.get('data-owner-index')=='1')
    protected=[n for n in apparel_group if n.get('mask')=='url(#sa1041-protected-clear)']
    if len(protected)!=1 or len(list(protected[0].iter(NS+'polygon')))!=5:
        raise ValueError('GC001 clothing panel guard is nonempty and mandatory')
    polygons=list(svg.iter(NS+'polygon'))
    if sum(len(poly.attrib['points'].split()) for poly in polygons)!=55:
        raise ValueError('GC001 Stage9 and Stage37 extra polygons changed')
    if any(n.tag in (NS+'image',NS+'foreignObject',NS+'feImage') for n in svg.iter()):
        raise ValueError('No source-raster/image embedding in SVG')
    expected=np.asarray(Image.open(root/'signed_full_opencv_reference.png').convert('RGB'))
    if expected.shape!=(340,340,3):
        raise ValueError('Wrong GC001 source canvas')
    return records,source,signed,svg,expected,delta


def visible_partition(records:list,owners:dict,signed:dict)->np.ndarray:
    """Report geometric topmost source ownership, not material segmentation."""
    idx=np.full((340,340),-1,np.int16)
    for i,record in enumerate(records):
        if record.get('structural_support_only') is not True:
            idx[owners[f'sa1041-owner-{i}']]=i
    idx[signed['face']]=ORDER.index('face')
    return idx


def compile_candidate(svg:ET.Element, masks:dict,epsilon:float)->tuple[ET.Element,dict]:
    if epsilon not in EPSILONS:
        raise ValueError('Unapproved epsilon')
    out=copy.deepcopy(svg)
    counts={}
    for ident,mask in masks.items():
        if ident=='sa1041-original-face-guard' or ident=='sa1041-protected-clear':
            eps=0.5
        else:
            owner=ident.replace('sa1041-owner-','')
            signed_owner=ORDER[int(owner)]
            eps=0.5 if signed_owner in PROTECTED else epsilon
        path,verts=contour.boundary_path(contour.pixel_edge_loops(mask),eps)
        contour.replace_svg_mask(out,ident,path,inverse=ident=='sa1041-protected-clear')
        counts[ident]=verts
    extras=sum(len(x.attrib['points'].split()) for x in out.iter(NS+'polygon'))
    if extras!=55:
        raise AssertionError('Stage9/37 colored geometric vertices were dropped')
    total=sum(counts.values())+extras
    return out,{'expanded_mask_vertices':sum(counts.values()),
                'stage9_and_clothing_polygon_vertices':extras,
                'expanded_deployed_vertices':total,
                'original_budget_limit':BUDGET,
                'budget_pass':total<=BUDGET,
                'source_mask_vertices':counts}


def errors_by_owner(reference,actual,indices)->dict:
    diff=np.any(reference!=actual,axis=2)
    result={}
    for i,name in enumerate(ORDER):
        region=indices==i
        result[name]={'visible_source_owned_pixels':int(region.sum()),
                      'rgb_mismatched_pixels':int((diff&region).sum())}
    result['background']={'visible_source_owned_pixels':int((indices<0).sum()),
                          'rgb_mismatched_pixels':int((diff&(indices<0)).sum())}
    if sum(v['rgb_mismatched_pixels'] for v in result.values())!=int(diff.sum()):
        raise AssertionError('Owner partition did not account for every RGB mismatch')
    return result


def evaluate(root:Path,out:Path,chromium:str='/usr/bin/chromium'):
    root,out=root.resolve(),out.resolve()
    if root==out or root in out.parents or out in root.parents:
        raise ValueError('Do not overwrite approved signed source inputs')
    records,masks,signed,source_svg,reference,delta=load_signed(root)
    idx=visible_partition(records,masks,signed)
    out.mkdir(parents=True,exist_ok=True)
    variants={name:compile_candidate(source_svg,masks,eps)
              for name,eps in [('exact',0.5),('approx_1',1.0),('approx_1p5',1.5)]}
    all_metrics={}
    visuals=[('SIGNED OPENCV',reference)]
    with sync_playwright() as pl:
        browser=pl.chromium.launch(headless=True,executable_path=chromium,
                                   args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            old=contour.chromium_rgb(page,ET.tostring(source_svg,encoding='unicode'))
            baseline=contour.metrics(reference,old,signed)
            if (baseline['full_rgb_mismatch']!=3919 or baseline['source_signed_protected']!=
                    {'face':140,'left_arm':206,'right_arm':199}):
                raise AssertionError('GC001 original real Chromium baseline changed')
            Image.fromarray(old).save(out/'original_svg.png')
            visuals.append(('OLD CHROME',old))
            for name,(candidate,stats) in variants.items():
                markup=ET.tostring(candidate,encoding='unicode')
                (out/f'{name}.svg').write_text(markup,'utf-8')
                rendered=contour.chromium_rgb(page,markup)
                Image.fromarray(rendered).save(out/f'{name}.png')
                mask_errors={}
                for ident,mask in masks.items():
                    observed=contour.chromium_rgb(page,contour.isolated_svg(candidate,ident))[...,0]<128
                    expectation=~mask if ident=='sa1041-protected-clear' else mask
                    mask_errors[ident]=int(np.count_nonzero(observed!=expectation))
                all_metrics[name]={**stats,'rgb':contour.metrics(reference,rendered,signed),
                    'visible_owner_error_partition':errors_by_owner(reference,rendered,idx),
                    'isolated_browser_mask_mismatch':mask_errors,
                    'all_13_signed_masks_exact':not any(mask_errors.values())}
                visuals.append((name.upper(),rendered))
            chrome_version=browser.version
        finally:
            browser.close()
    exact=all_metrics['exact']
    if (exact['rgb']['full_rgb_mismatch']!=683 or exact['rgb']['source_signed_protected']!=
       {'face':0,'left_arm':0,'right_arm':0} or not exact['all_13_signed_masks_exact']):
        raise AssertionError('GC001 protected source exactness / chromium gate FAILED')
    if exact['budget_pass'] or all_metrics['approx_1']['budget_pass'] or all_metrics['approx_1p5']['budget_pass']:
        raise AssertionError('Budget exceeded but positive source passed')
    board=Image.new('RGB',(340*len(visuals),380),(246,246,243))
    pen=ImageDraw.Draw(board)
    for i,(name,im) in enumerate(visuals):
        board.paste(Image.fromarray(im),(340*i,40))
        pen.text((340*i+8,15),name,fill=(15,15,20))
    board.save(out/'gc001_four_way.png')
    report={'stage':'SA10.46','schema':'sa1046-gc001-positive-source-locked-crosscase-v1',
            'case':CASE,'source_hashes':EXPECTED_SHA,
            'chromium_version':chrome_version,
            'record_order':ORDER,'signed_protected_source_owner_delta_px':delta,
            'baseline':baseline,'candidates':all_metrics,
            'original_stage8_vertices':3604,'original_stage8_budget':BUDGET,
            'gc001_stage37_five_apparel_panels_preserved':True,
            'raden_sa1045_empty_apparel_pruning_not_transferred':True,
            'local_public_worker_production_unchanged':True,
            'full_character_golden_pass':False,'production_promotion_authorized':False,
            'result':'POSITIVE_SECOND_CHARACTER_EXACT_MASK_PASS_COMPLEXITY_AND_FULL_SCENE_HOLD',
            'next':'Protect signed face/arms while reducing visible clothing and hair geometry for both cases; prove 2-case budgets and visual review.'}
    signed_outputs=('original_svg.png','exact.svg','exact.png','approx_1.svg',
                    'approx_1.png','approx_1p5.svg','approx_1p5.png','gc001_four_way.png')
    report['artifact_sha256']={name:sha256((out/name).read_bytes()).hexdigest()
         for name in signed_outputs}
    (out/'sa1046_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report


def main():
    a=argparse.ArgumentParser()
    a.add_argument('--root',required=True,type=Path)
    a.add_argument('--out',required=True,type=Path)
    a.add_argument('--chromium',default='/usr/bin/chromium')
    args=a.parse_args()
    r=evaluate(args.root,args.out,args.chromium)
    print(json.dumps({'result':r['result'],'chromium':r['chromium_version'],
         'baseline':r['baseline'],'summary':{k:{'vertices':v['expanded_deployed_vertices'],
         'rgb':v['rgb'],'masked_source_delta_sum':sum(v['isolated_browser_mask_mismatch'].values())}
         for k,v in r['candidates'].items()}},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
