"""SA10.45 research-only visible-owner SVG pruning and honest accounting.

Signed Stage04/08/41 source inputs are never rewritten. Remove geometry only
where signed source and actual rendered SVG painting prove it unreachable.
All actual referenced geometry is counted when expanded, regardless of defs.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import cv2
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
import sa1043_boundary_compaction as prior
import sa1044_shared_geometry as prior44

NS=prior.NS
BUDGET=prior.BUDGET
STAGE9_VERTICES=prior.EXTRAS
PAINTED_INDICES=(0,1,2,3,4,5,6,7,9,10)
PROTECTED_INDICES=(2,3)
CHOSEN_EPS=(0.5,0.75,1.0,1.25,1.5)


def source_authorities(path:Path):
    masks,signed,delta=prior44.original_masks(path)
    scene=json.loads((path/'phase8_adaptive_source_contour_research.json').read_text())
    records=scene['primitives_back_to_front']
    if len(records)!=11 or tuple(x['source_mask_owner'] for x in records)!=prior.ORDER:
        raise ValueError('Owner provenance changed')
    if delta!=2 or any(x.shape!=(340,340) for x in masks.values()):
        raise ValueError('Source geometry or signed right arm changed')
    return masks,signed,records


def source_visible_owner_masks(masks:dict,signed:dict,records:list)->tuple[dict,dict]:
    """Source pixel visibility after later opaque owners and final flat face guard.

    Internal Stage9 colors remain descendants of the same opaque parent mask.
    For this signed Raden case Stage37 apparel list is empty, proven in SVG.
    """
    face=signed['face']
    visible={}
    before_after={}
    for i,entry in enumerate(records):
        source=masks[f'sa1041-owner-{i}']
        if entry.get('structural_support_only'):
            before_after[str(i)]={'original_pixels':int(source.sum()), 'painted':False,'reason':'structural-source-support'}
            continue
        future=[masks[f'sa1041-owner-{j}'] for j in PAINTED_INDICES if j>i]
        covered=np.logical_or.reduce(future) if future else np.zeros_like(source)
        exact=source & ~(covered|face)
        visible[i]=exact
        before_after[str(i)]={'original_pixels':int(source.sum()),'visible_pixels':int(exact.sum()),
           'proven_hidden_pixels':int(np.count_nonzero(source&~exact)), 'painted':True}
    return visible,before_after


def verify_render_structure(root:ET.Element,masks:dict,signed:dict,visible:dict)->dict:
    defs=root.find(NS+'defs')
    if defs is None:raise ValueError('Expected SVG defs')
    paint={int(x.get('data-owner-index')):x for x in root if x.get('data-owner-index') is not None}
    if set(paint)!=set(PAINTED_INDICES):
        raise ValueError('Unexpected actual source paint order/owner count')
    if tuple(paint)!=PAINTED_INDICES:raise ValueError('Original source paint z-order changed')
    if any(len(paint[i])<1 or paint[i][0].tag!=NS+'rect' for i in paint):
        raise ValueError('Source owner painting is not opaque rect')
    if not np.array_equal(masks['sa1041-owner-5'],signed['face']):
        raise ValueError('Face-guard is not exactly equal to source face owner')
    if not (list(root)[-1].get('mask')=='url(#sa1041-original-face-guard)' and
        list(root)[-1][0].tag==NS+'rect'):
        raise ValueError('Face guard is not final opaque source paint')
    protector_users=[]
    for i,owner in paint.items():
        for node in owner.iter():
            if node.get('mask')!='url(#sa1041-protected-clear)':continue
            protector_users.append(i)
            if i==7 and len(node)!=0:raise ValueError('Apparel protection cannot be safely removed when nonempty')
            if i!=7 and i!=1:raise ValueError('Unexpected protected mask use')
            if i==1 and np.any(masks['sa1041-owner-1'] &
                                (signed['face']|signed['left_arm']|signed['right_arm'])):
                raise ValueError('Stage9 owner intersects protected pixels; cannot remove protector')
    if sorted(protector_users)!=[1,7]:raise ValueError('Protected overlays changed')
    if np.any(visible[5]):raise ValueError('Face owner still has visible source pixels')
    return {'protected_overlay_owner_indices':protector_users,
        'face_fully_overwritten_by_original_final_guard':True,
        'structural_unpainted_owner_index':8,
        'stage37_apparel_is_empty':True}


def simplify_proven_dead_overlays(svg:ET.Element)->ET.Element:
    """Remove no-op face owner and unused support/protection masks; retain source order."""
    root=copy.deepcopy(svg)
    paint={int(x.get('data-owner-index')):x for x in root if x.get('data-owner-index') is not None}
    # The final, fully covering guard is kept. Source face owner is not painted.
    root.remove(paint[5])
    hair=paint[1]
    wrapped=[x for x in hair if x.get('mask')=='url(#sa1041-protected-clear)']
    if len(wrapped)!=1 or len(wrapped[0])!=1 or wrapped[0][0].tag!=NS+'polygon':
        raise ValueError('Expected signed Stage9 hair plane')
    polygon=wrapped[0][0]
    wrapped[0].remove(polygon)
    hair.remove(wrapped[0])
    hair.append(polygon)
    lower=paint[7]
    protected=[x for x in lower if x.get('mask')=='url(#sa1041-protected-clear)']
    if len(protected)!=1 or len(protected[0])!=0:
        raise ValueError('Only zero-apparel negative control may be optimized')
    lower.remove(protected[0])
    defs=root.find(NS+'defs')
    for identifier in ('sa1041-owner-5','sa1041-owner-8','sa1041-protected-clear'):
        target=[x for x in defs if x.tag==NS+'mask' and x.get('id')==identifier]
        if len(target)!=1:raise ValueError('Source mask not uniquely present: '+identifier)
        defs.remove(target[0])
    return root


def replace_visible_masks(svg:ET.Element,masks:dict,signed:dict,records:list,
                          epsilon:float)->tuple[ET.Element,dict]:
    if epsilon not in CHOSEN_EPS:raise ValueError('Undeclared approximation parameter')
    visible,provenance=source_visible_owner_masks(masks,signed,records)
    root=simplify_proven_dead_overlays(svg)
    defs=root.find(NS+'defs')
    tally={}
    for i in PAINTED_INDICES:
        if i==5:continue
        ident=f'sa1041-owner-{i}'
        exact=visible[i]
        # Exact protected shapes are never approximated.
        ep=0.5 if i in PROTECTED_INDICES else epsilon
        if not np.any(exact):
            raise AssertionError(f'No visible geometry for active owner {i}')
        path,verts=prior.boundary_path(prior.pixel_edge_loops(exact),ep)
        prior.replace_svg_mask(root,ident,path)
        tally[ident]={'vertex_occurrences':verts,'epsilon':ep,
                     'source_visible_pixels':int(exact.sum())}
    face_path,face_v=prior.boundary_path(prior.pixel_edge_loops(signed['face']),0.5)
    prior.replace_svg_mask(root,'sa1041-original-face-guard',face_path)
    tally['sa1041-original-face-guard']={'vertex_occurrences':face_v,'epsilon':0.5,
                                         'source_visible_pixels':int(signed['face'].sum())}
    painted_mask_v=sum(x['vertex_occurrences'] for x in tally.values())
    stats={'painted_mask_vertices_expanded':painted_mask_v,
        'stage9_vertices':STAGE9_VERTICES,
        'expanded_deployed_vertices':painted_mask_v+STAGE9_VERTICES,
        'deployed_within_original_budget':painted_mask_v+STAGE9_VERTICES<=BUDGET,
        'historical_stage8_source_ring_vertices':2370,
        'historical_stage8_source_vertex_budget_pass':False,
        'signed_original_face_and_arm_geometry_unchanged':True,
        'deleted_unpainted_source_masks_only':True,
        'source_owner_original_11_records_preserved_in_provenance':True,
        'owner_visibility_stats':provenance,
        'remaining_mask_vertex_breakdown':tally}
    return root,stats


def current_mask_count(svg:ET.Element)->int:
    defs=svg.find(NS+'defs')
    masks=[x for x in defs if x.tag==NS+'mask']
    if len(masks)!=10:raise ValueError('Expected nine active source masks plus final face guard')
    used=set()
    for node in svg.iter():
        if node.get('mask','').startswith('url(#'):
            used.add(node.get('mask')[5:-1])
    expected={f'sa1041-owner-{i}' for i in PAINTED_INDICES if i!=5}|{'sa1041-original-face-guard'}
    if used!=expected or {x.get('id') for x in masks}!=expected:
        raise ValueError('Uncounted source/mask reference after dead paint removal')
    for node in defs:
        if node.tag not in (NS+'mask',):raise ValueError('Unexpected shared shape retained')
    vertices=0
    for mask in masks:
        p=[x for x in mask if x.tag==NS+'path']
        if len(p)!=1:raise ValueError('No per-mask source path counted')
        vertices+=prior44.path_vertices(p[0].get('d',''))
    return vertices+STAGE9_VERTICES


def render(page,svg:ET.Element):
    return prior.chromium_rgb(page,ET.tostring(svg,encoding='unicode'))


def mask_alpha_mismatch(page,svg:ET.Element,vis:dict,signed:dict)->dict:
    output={}
    for i in PAINTED_INDICES:
        if i==5:continue
        ident=f'sa1041-owner-{i}'
        bitmap=prior.chromium_rgb(page,prior.isolated_svg(svg,ident))[...,0]<128
        output[ident]=int(np.count_nonzero(bitmap!=vis[i]))
    face=prior.chromium_rgb(page,prior.isolated_svg(svg,'sa1041-original-face-guard'))[...,0]<128
    output['sa1041-original-face-guard']=int(np.count_nonzero(face!=signed['face']))
    return output


def metrics(reference:np.ndarray,chrome:np.ndarray,signed:dict)->dict:
    diff=np.any(reference!=chrome,axis=2)
    return {'full_rgb_mismatched_pixels':int(diff.sum()),
        'signed_protected_mismatch_pixels':{k:int(np.count_nonzero(diff&v)) for k,v in signed.items()},
        'rgb_mean_absolute_error':round(float(np.abs(reference.astype(np.int16)-chrome.astype(np.int16)).mean()),6)}



def pixel_rectangles(binary:np.ndarray)->list[tuple[int,int,int,int]]:
    """Run/vertical merge solely of Chromium-detected foreign paint pixels."""
    if binary.shape!=(340,340) or binary.dtype!=bool:
        raise ValueError('Protection intrusion witness must be source-sized binary')
    active,output={},[]
    for y,row in enumerate(binary):
        ends=np.flatnonzero(np.diff(np.r_[False,row,False].astype(np.int8)))
        following={}
        for x0,x1 in zip(ends[::2],ends[1::2]):
            following[(int(x0),int(x1))]=active.get((int(x0),int(x1)),y)
        for (x0,x1),top in active.items():
            if (x0,x1) not in following:
                output.append((x0,top,x1-x0,y-top))
        active=following
    for (x0,x1),top in active.items():
        output.append((x0,top,x1-x0,340-top))
    return output


def choose_guarded_options(proposals:dict[str,list[dict]], limit:int)->dict:
    """Finite exact knapsack: only options that REMOVE ALL source-protected leak.

    Rank remaining source-mask disagreement first, then budget and tie order.
    This is an exploratory pixel-mask proxy, NOT global RGB Golden evidence.
    """
    if limit < 0 or not proposals:raise ValueError('Invalid deployment budget')
    dp={0:(0,())}
    for name,options in proposals.items():
        next_dp={}
        if not options:raise ValueError('Owner has no candidate options')
        for current,(error,selection) in dp.items():
            for variant in options:
                cost=current+variant['expanded_vertices']
                if cost>limit:continue
                attempted=(error+variant['unprotected_source_error'],
                    selection+(variant['epsilon'],))
                if cost not in next_dp or attempted<next_dp[cost]:
                    next_dp[cost]=attempted
        if not next_dp:raise ValueError('No safe protected-fence candidate fits hard cap')
        dp=next_dp
    cost,(score,chosen)=min(dp.items(),key=lambda x:(x[1][0],x[0],x[1][1]))
    return {'nonprotected_mask_vertices':cost,'unprotected_source_mask_error':score,
       'epsilons':dict(zip(proposals,chosen)),'budget_limit_for_nonprotected':limit}


def browser_guarded_visible(page,original:ET.Element,masks:dict,signed:dict,
                             records:list)->tuple[ET.Element,dict]:
    """Record + repair each measured intrusion only where source proof forbids paint."""
    visible,_=source_visible_owner_masks(masks,signed,records)
    protected=signed['face']|signed['left_arm']|signed['right_arm']
    for i in (0,1,4,6,7,9,10):
        if np.any(visible[i]&protected):
            raise ValueError('Cannot erase legitimate source-owned protected pixels')
    base=simplify_proven_dead_overlays(original)
    search={}
    geometry={}
    for i in (0,1,4,6,7,9,10):
        ident=f'sa1041-owner-{i}'
        loops=prior.pixel_edge_loops(visible[i])
        variants=[]
        for eps in CHOSEN_EPS:
            data,vertices=prior.boundary_path(loops,eps)
            probe=copy.deepcopy(base)
            prior.replace_svg_mask(probe,ident,data)
            actual=prior.chromium_rgb(page,prior.isolated_svg(probe,ident))[...,0]<128
            forbidden=actual&protected
            patches=pixel_rectangles(forbidden)
            fixed=actual&~forbidden
            record={'epsilon':eps, 'path_vertices':vertices,
                'protected_trim_rectangles':len(patches),
                'expanded_vertices':vertices+len(patches)*4,
                'unprotected_source_error':int(np.count_nonzero(fixed!=visible[i])),
                'witness_forbidden_pixels_before_trim':int(forbidden.sum())}
            variants.append(record)
            geometry[(ident,eps)]=(data,patches)
        search[ident]=variants
    rightmask=prior.boundary_path(prior.pixel_edge_loops(visible[2]),0.5)
    leftmask=prior.boundary_path(prior.pixel_edge_loops(visible[3]),0.5)
    guard=prior.boundary_path(prior.pixel_edge_loops(signed['face']),0.5)
    frozen_protected_vertices=rightmask[1]+leftmask[1]+guard[1]
    limit=BUDGET-STAGE9_VERTICES-frozen_protected_vertices
    pick=choose_guarded_options(search,limit)
    for index,(data,verts) in ((2,rightmask),(3,leftmask)):
        prior.replace_svg_mask(base,f'sa1041-owner-{index}',data)
    prior.replace_svg_mask(base,'sa1041-original-face-guard',guard[0])
    defs=base.find(NS+'defs')
    for ident,eps in pick['epsilons'].items():
        path,patches=geometry[(ident,eps)]
        prior.replace_svg_mask(base,ident,path)
        node=next(e for e in defs if e.get('id')==ident)
        for x,y,w,h in patches:
            ET.SubElement(node,NS+'rect',{'x':str(x),'y':str(y),
                'width':str(w),'height':str(h),'fill':'#000000',
                'shape-rendering':'crispEdges','data-sa1045-protected-trim':'1'})
    # Expanded accounting includes every patch rectangle as 4 vertices, not zero.
    budgeted=expanded_vertex_count_with_corrections(base)
    if budgeted!=frozen_protected_vertices+pick['nonprotected_mask_vertices']+STAGE9_VERTICES:
        raise AssertionError('Budget omits source-protected correction vertices')
    if budgeted>BUDGET:raise AssertionError('Budget violation passed optimizer')
    return base,{'expanded_deployed_vertices':budgeted,'original_budget_limit':BUDGET,
        'frozen_source_face_both_arms_vertices':frozen_protected_vertices,
        'stage9_vertices':STAGE9_VERTICES,
        'optimization':pick,'per_owner_protected_mask_options':search,
        'all_trim_geometries_in_budget':True,'research_only':True}


def expanded_vertex_count_with_corrections(svg:ET.Element)->int:
    defs=svg.find(NS+'defs')
    allowed={f'sa1041-owner-{i}' for i in PAINTED_INDICES if i!=5}|{'sa1041-original-face-guard'}
    masks=[x for x in defs if x.tag==NS+'mask']
    if len(masks)!=10 or {x.get('id') for x in masks}!=allowed:
        raise ValueError('Unexpected rendered source masks')
    count=STAGE9_VERTICES
    for node in masks:
        filled=[x for x in node if x.tag==NS+'path']
        if len(filled)!=1:raise ValueError('Missing expected source contour path')
        count+=prior44.path_vertices(filled[0].get('d',''))
        for part in node:
            if part.tag==NS+'path':continue
            if part.tag!=NS+'rect':raise ValueError('Uncounted SVG mask geometry')
            if part.get('data-sa1045-protected-trim')=='1':
                if part.get('fill')!='#000000' or int(part.get('width','0'))<1 or int(part.get('height','0'))<1:
                    raise ValueError('Invalid paint-erasure correction')
                count+=4
            elif part.get('fill')!='#000000':
                raise ValueError('Unexpected luminance mask background')
    return count


def evaluate(input_root:Path,out:Path,chromium='/usr/bin/chromium')->dict:
    input_root,out=input_root.resolve(),out.resolve()
    if input_root==out or input_root in out.parents or out in input_root.parents:
        raise ValueError('Output must not overwrite signed provenance')
    masks,signed,records=source_authorities(input_root)
    svg=ET.parse(input_root/'full_character_vector.svg').getroot()
    visible,provenance=source_visible_owner_masks(masks,signed,records)
    safety=verify_render_structure(svg,masks,signed,visible)
    ref=np.asarray(Image.open(input_root/'signed_full_opencv_reference.png').convert('RGB'))
    if ref.shape!=(340,340,3):raise ValueError('Wrong signed source canvas')
    prepared={e:replace_visible_masks(svg,masks,signed,records,e) for e in CHOSEN_EPS}
    out.mkdir(parents=True,exist_ok=True)
    evaluations={}
    visual=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=chromium,
                    args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            exact_before,_=prior44.compile_candidate(svg,masks,signed,0.5)
            old=render(page,svg)
            before=render(page,exact_before)
            Image.fromarray(old).save(out/'baseline_sa1041.png')
            Image.fromarray(before).save(out/'baseline_sa1044_exact.png')
            visual.extend([('SIGNED OPENCV',ref),('SA1044 EXACT',before)])
            for eps,(trial,summary) in prepared.items():
                ident=f'visible_e{str(eps).replace(".","p")}'
                compiled=ET.tostring(trial,encoding='unicode')
                (out/f'{ident}.svg').write_text(compiled,'utf-8')
                rendered=render(page,trial)
                Image.fromarray(rendered).save(out/f'{ident}.png')
                measured=metrics(ref,rendered,signed)
                mask_mismatches=mask_alpha_mismatch(page,trial,visible,signed)
                equals_prior_chrome=bool(np.array_equal(rendered,before))
                genuine_count=current_mask_count(trial)
                if summary['expanded_deployed_vertices']!=genuine_count:
                    raise AssertionError('SVG contains uncounted geometric vertices')
                evaluations[ident]={**summary,'real_chrome_composite_equals_sa1044_exact':equals_prior_chrome,
                                     'real_chrome_metrics':measured,
                                     'mask_binary_mismatch':mask_mismatches,
                                     'visible_source_masks_exact':not any(mask_mismatches.values()),
                                     'remaining_counted_svg_masks':10}
                if eps in (0.5,1.25,1.5):
                    visual.append((f'VISIBLE EPS {eps}',rendered))
            guarded,guarded_stats=browser_guarded_visible(page,svg,masks,signed,records)
            protected_composite=render(page,guarded)
            (out/'visible_guarded_budget.svg').write_text(ET.tostring(guarded,encoding='unicode'),'utf-8')
            Image.fromarray(protected_composite).save(out/'visible_guarded_budget.png')
            corrected_probe=mask_alpha_mismatch(page,guarded,visible,signed)
            guarded_metric=metrics(ref,protected_composite,signed)
            evaluations['visible_guarded_budget']={**guarded_stats,
                'real_chrome_composite_equals_sa1044_exact':bool(np.array_equal(protected_composite,before)),
                'real_chrome_metrics':guarded_metric,
                'mask_binary_mismatch':corrected_probe,
                'visible_source_masks_exact':not any(corrected_probe.values()),
                'protected_zero_rgb_error':not any(guarded_metric['signed_protected_mismatch_pixels'].values())}
            visual.append(('GUARDED BUDGET',protected_composite))
            chrome_version=browser.version
        finally:browser.close()
    if evaluations['visible_e0p5']['real_chrome_composite_equals_sa1044_exact'] is not True:
        raise AssertionError('Pruned exact source must preserve real Chromium composite, otherwise HOLD')
    if not evaluations['visible_e0p5']['visible_source_masks_exact']:
        raise AssertionError('Exact source visible masks changed, otherwise HOLD')
    if evaluations['visible_e0p5']['real_chrome_metrics']['signed_protected_mismatch_pixels']!={'face':0,'left_arm':0,'right_arm':0}:
        raise AssertionError('Exact protected source changed, otherwise HOLD')
    if not evaluations['visible_guarded_budget']['protected_zero_rgb_error']:
        raise AssertionError('Budgeted browser-corrected visible source still repaints signed face/arms')
    if evaluations['visible_guarded_budget']['expanded_deployed_vertices']>BUDGET:
        raise AssertionError('Hard expanded geometry budget violated')
    board=Image.new('RGB',(len(visual)*340,380),(247,247,244))
    drawer=ImageDraw.Draw(board)
    for i,(name,im) in enumerate(visual):
        board.paste(Image.fromarray(im),(i*340,40))
        drawer.text((i*340+10,14),name,fill=(25,25,30))
    board.save(out/'sa1045_five_way.png')
    report={'stage':'SA10.45','schema':'sa1045-composited-visible-source-geometry-v1',
        'frozen_source_sha256':prior.SHA,'chromium_version':chrome_version,
        'source_image':'Juufuutei-Raden','source_owner_order':prior.ORDER,
        'structural_proofs':safety,'source_original_11_owner_masks_untouched_in_authority':True,
        'source_geometry_archival_budget_pass':False,
        'original_stage8_source_vertices':2370,
        'original_stage8_budget':BUDGET,
        'baseline_sa1041':metrics(ref,old,signed),
        'baseline_sa1044_exact':metrics(ref,before,signed),
        'candidates':evaluations,
        'production_promoted':False,'full_character_golden_pass':False,
        'release_decision':'RESEARCH_VISIBLE_PRUNING_AND_GUARDED_BUDGET_PROBE_PRODUCTION_HOLD',
        'next':'Validate all owner material and silhouette gates, GC001 positive holdout, original Stage8 lineage, and visual review before any product approval.'}
    report['output_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(out.iterdir()) if f.suffix in ('.png','.svg')}
    (out/'sa1045_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--chromium',default='/usr/bin/chromium')
    args=p.parse_args()
    result=evaluate(args.root,args.out,args.chromium)
    print(json.dumps({'status':result['release_decision'],
        'source':result['baseline_sa1044_exact'],
        'candidates':{k:{'expanded':v['expanded_deployed_vertices'],
            'budget':v.get('deployed_within_original_budget',v['expanded_deployed_vertices']<=BUDGET),
            'rgb_mismatch':v['real_chrome_metrics']['full_rgb_mismatched_pixels'],
            'protected':v['real_chrome_metrics']['signed_protected_mismatch_pixels'],
            'source_pixel_equal':v['real_chrome_composite_equals_sa1044_exact']}
            for k,v in result['candidates'].items()}},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
