"""SA10.47: two-character, source-locked composited-visible SVG optimizer.

Research only: never embeds/paints a source raster, invents anatomy, changes the
signed source, or reuses another character's owner indexes/clothing assumptions.
Expanded SVG vertex accounting includes every path, overlay, and trim rectangle.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1043_boundary_compaction as edge
import sa1044_shared_geometry as shared
import sa1045_visible_geometry as raden45
import sa1046_gc001_positive_holdout as gc46

NS=edge.NS
EPS=(0.5,0.75,1.0,1.25,1.5,2.0,2.5)
PROTECTED=('face','left_arm','right_arm')


def load_case(case:str,root:Path)->dict:
    if case=='Raden':
        edge.frozen(root)
        masks,signed,records=raden45.source_authorities(root)
        source=ET.parse(root/'full_character_vector.svg').getroot()
        budget=edge.BUDGET
        original_vertices=2370
    elif case=='GC001':
        records,masks,signed,source,_,delta=gc46.load_signed(root)
        if delta!={'face':0,'left_arm':5,'right_arm':24}:
            raise ValueError('GC001 signed owner/source discrepancy changed')
        budget=gc46.BUDGET
        original_vertices=3604
    else:
        raise ValueError('Only explicitly signed Raden and GC001 sources are supported')
    # Resolve the paint order *from source*, no hardcoded indices.
    paint=[node for node in source if node.get('data-owner-index') is not None]
    idx=[int(x.get('data-owner-index')) for x in paint]
    if (idx!=sorted(idx) or set(idx)!={i for i,p in enumerate(records)
                                            if p.get('structural_support_only') is not True}):
        raise ValueError('Signed opaque paint/z order changed')
    for i,node in zip(idx,paint):
        if node.get('mask')!=f'url(#sa1041-owner-{i})' or len(node)==0 or node[0].tag!=NS+'rect':
            raise ValueError('Expected source-masked opaque owner group')
    end=list(source)[-1]
    if end.get('mask')!='url(#sa1041-original-face-guard)' or len(end)!=1 or end[0].tag!=NS+'rect':
        raise ValueError('Last signed face guard is not the expected opaque paint')
    if not np.array_equal(masks[f'sa1041-owner-{next(i for i,r in enumerate(records) if r["source_mask_owner"]=="face")}'],signed['face']):
        raise ValueError('Cannot prune nonidentical signed face-owner mask')
    # Only source masks / final signed guard are allowed inputs to optimizer.
    original=np.asarray(Image.open(root/'signed_full_opencv_reference.png').convert('RGB'))
    if original.shape!=(340,340,3):raise ValueError('Signed reference size differs')
    overlays=sum(len(n.attrib['points'].split()) for n in source.iter(NS+'polygon'))
    if overlays!=(12 if case=='Raden' else 55):
        raise ValueError('Stage9/37 source-owned color vertices changed')
    return {'case':case,'masks':masks,'signed':signed,'records':records,
        'source':source,'painted':idx,'original':original,'budget':budget,
        'historical_stage8_vertices':original_vertices,'overlay_vertices':overlays,
        'source_input_sha256':{f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in (edge.SHA if case=='Raden' else gc46.EXPECTED_SHA)}}


def visible_ownership(case:dict)->tuple[dict,dict]:
    """Prune only pixels unconditionally covered by later opaque owner painting."""
    masks,signed=case['masks'],case['signed']
    face=signed['face']
    painted=case['painted']
    result={}
    stats={}
    for i in painted:
        ident=f'sa1041-owner-{i}'
        source=masks[ident]
        later=[masks[f'sa1041-owner-{j}'] for j in painted if j>i]
        future=np.logical_or.reduce(later) if later else np.zeros_like(source)
        visible=source&~(future|face)
        name=case['records'][i]['source_mask_owner']
        stats[name]={'owner_index':i,'source_pixels':int(source.sum()),
                     'visible_pixels':int(visible.sum()),
                     'source_hidden_pixels':int(np.count_nonzero(source&~visible))}
        if name!='face':
            result[ident]=visible
        elif np.any(visible):
            raise ValueError('Face-source owner cannot be deleted because it remains visible')
    return result,stats


def prune_scene(case:dict)->ET.Element:
    root=copy.deepcopy(case['source'])
    painted=case['painted']
    records=case['records']
    face_idx=next(i for i in painted if records[i]['source_mask_owner']=='face')
    face_node=next(n for n in root if n.get('data-owner-index')==str(face_idx))
    if len(face_node)!=1 or face_node[0].tag!=NS+'rect':
        raise ValueError('Face owner contains unapproved face detail; refuse pruning')
    root.remove(face_node)
    defs=root.find(NS+'defs')
    dead=[face_idx]+[i for i,p in enumerate(records) if p.get('structural_support_only')]
    for i in dead:
        ident=f'sa1041-owner-{i}'
        nodes=[n for n in defs if n.tag==NS+'mask' and n.get('id')==ident]
        if len(nodes)!=1:raise ValueError('Expected exactly one removable source mask')
        if any(n.get('mask')==f'url(#{ident})' for n in root.iter()):
            raise ValueError('Mask still referenced after removing dead source owner')
        defs.remove(nodes[0])
    # GC001 has 5 real apparel panels. Raden's empty apparel group is only
    # removed when that character's signed historical source proofs match.
    if case['case']=='Raden':
        # Source Stage9 hair polygon must be independent of the clear mask.
        mask_users=[n for n in root.iter() if n.get('mask')=='url(#sa1041-protected-clear)']
        if len(mask_users)!=2:raise ValueError('Raden signed overlay count changed')
        empty=[n for n in mask_users if len(n)==0]
        nonempty=[n for n in mask_users if len(n)!=0]
        if len(empty)!=1 or len(nonempty)!=1 or len(nonempty[0])!=1 or nonempty[0][0].tag!=NS+'polygon':
            raise ValueError('Raden negative-apparel source safety failed')
        polygon=nonempty[0][0]
        parent=next(p for p in root.iter() if nonempty[0] in list(p))
        parent.remove(nonempty[0]);parent.append(polygon)
        parent=next(p for p in root.iter() if empty[0] in list(p));parent.remove(empty[0])
        for n in list(defs):
            if n.get('id')=='sa1041-protected-clear':defs.remove(n)
    else:
        # All signed GC001 Stage37 masks/colors survive; keep their order.
        protected=[n for n in root.iter() if n.get('mask')=='url(#sa1041-protected-clear)']
        if len(protected)!=4 or not any(sum(1 for z in p.iter(NS+'polygon'))==5 for p in protected):
            raise ValueError('GC001 protected Stage37 garment planes lost')
    if sum(len(n.attrib['points'].split()) for n in root.iter(NS+'polygon'))!=case['overlay_vertices']:
        raise ValueError('Original Stage9/37 colored planes unexpectedly removed')
    return root


def vector_path(binary:np.ndarray,eps:float)->tuple[str,int]:
    if eps not in EPS:raise ValueError('Unapproved approximation epsilon')
    loops=edge.pixel_edge_loops(binary)
    paths=[];vertices=0
    for loop in loops:
        points=np.asarray(loop,np.float32)
        outline=cv2.approxPolyDP(points.reshape(-1,1,2),eps,True).reshape(-1,2)
        if len(outline)>=3:points=outline
        if len(points)<3:raise ValueError('Source contour collapsed')
        vertices+=len(points)
        paths.append('M '+' L '.join(f'{int(x)} {int(y)}' for x,y in points)+' Z')
    return ' '.join(paths),vertices


def score(proposals:dict,limit:int)->dict:
    """Exact multiple-choice knapsack; does not treat source RGB as semantic ground truth."""
    dp={0:(0,())}
    for key,options in proposals.items():
        step={}
        for cost,(error,chosen) in dp.items():
            for option in options:
                total=cost+option['vertices']
                if total>limit:continue
                choice=(error+option['outside_protected_binary_error'],chosen+(option['epsilon'],))
                if total not in step or choice<step[total]:step[total]=choice
        if not step:return {'feasible':False,'reason':'No combination fits deployed budget','remaining_vertex_budget':limit}
        dp=step
    total,(error,options)=min(dp.items(),key=lambda x:(x[1][0],x[0],x[1][1]))
    return {'feasible':True,'picked_epsilons':dict(zip(proposals,options)),
            'candidate_path_and_trim_vertices':total,'binary_proxy_error':error,
            'remaining_vertex_budget':limit}


def count_svg(root:ET.Element,expected_overlay:int)->dict:
    defs=root.find(NS+'defs'); masks=[n for n in defs if n.tag==NS+'mask']
    referenced={n.get('mask')[5:-1] for n in root.iter()
                if n.get('mask','').startswith('url(#')}
    if referenced!={m.get('id') for m in masks}:
        raise ValueError('Dangling or unused SVG mask references')
    extra=sum(len(poly.get('points','').split()) for poly in root.iter(NS+'polygon'))
    if extra!=expected_overlay:raise ValueError('Color polygon vertex count changed')
    breakdown={}
    for m in masks:
        ident=m.get('id')
        paths=[p for p in m if p.tag==NS+'path']
        if len(paths)!=1:raise ValueError('Every active source mask must have one path')
        n=shared.path_vertices(paths[0].get('d',''))
        for c in m:
            if c.tag==NS+'path':continue
            if c.tag!=NS+'rect':raise ValueError('Unaccounted SVG geometry in mask')
            if c.get('data-sa1047-protected-trim')=='1':
                if c.get('fill')!='#000000':raise ValueError('Invalid trim fill')
                n+=4
            elif c.get('fill') not in ('#000000','#ffffff'):
                raise ValueError('Unrecognized mask background')
        breakdown[ident]=n
    return {'source_mask_vertices':breakdown,'mask_vertex_occurrences':sum(breakdown.values()),
            'source_colored_polygon_vertices':extra,'expanded_deployed_vertices':sum(breakdown.values())+extra}



def source_owner_rgb_partition(case:dict,rendered:np.ndarray)->dict:
    """Descriptive topmost source-owner attribution, not material diagnosis."""
    owners=np.full((340,340),-1,np.int16)
    for i in case['painted']:
        owners[case['masks'][f'sa1041-owner-{i}']]=i
    face=next(i for i,p in enumerate(case['records']) if p['source_mask_owner']=='face')
    owners[case['signed']['face']]=face
    changed=np.any(case['original']!=rendered,axis=2)
    errors={case['records'][i]['source_mask_owner']:int((changed&(owners==i)).sum())
            for i in range(len(case['records']))}
    errors['background']=int((changed&(owners==-1)).sum())
    if sum(errors.values())!=int(changed.sum()):
        raise AssertionError('Owner attribution does not partition all RGB differences')
    return errors


def render_case(case:dict,out:Path,page)->dict:
    case_name=case['case'];signed=case['signed'];reference=case['original']
    visible,vis_stats=visible_ownership(case)
    base=prune_scene(case)
    original=copy.deepcopy(case['source'])
    # Verify a fully exact source-derived, *visibility-pruned* browser scene.
    exact=copy.deepcopy(base)
    for ident,binary in visible.items():
        path,n=vector_path(binary,0.5)
        edge.replace_svg_mask(exact,ident,path)
    face, _=vector_path(signed['face'],0.5)
    edge.replace_svg_mask(exact,'sa1041-original-face-guard',face)
    if case_name=='GC001':
        protector=np.logical_or.reduce([signed[k] for k in PROTECTED])
        pro_path,_=vector_path(protector,0.5)
        edge.replace_svg_mask(exact,'sa1041-protected-clear',pro_path,inverse=True)
    original_exact=copy.deepcopy(original)
    for ident,binary in case['masks'].items():
        path,n=vector_path(binary,0.5)
        edge.replace_svg_mask(original_exact,ident,path,inverse=(ident=='sa1041-protected-clear'))
    frame_exact=edge.chromium_rgb(page,ET.tostring(exact,encoding='unicode'))
    frame_unpruned=edge.chromium_rgb(page,ET.tostring(original_exact,encoding='unicode'))
    exact_matches=bool(np.array_equal(frame_exact,frame_unpruned))
    if not exact_matches:raise AssertionError(case_name+' source-visible exact scene changed Chromium pixels; unsafe pruning')
    expected_exact=148 if case_name=='Raden' else 683
    if edge.metrics(reference,frame_exact,signed)['full_rgb_mismatch']!=expected_exact:
        raise AssertionError('Frozen exact full RGB metric changed')
    Image.fromarray(frame_exact).save(out/f'{case_name.lower()}_visible_exact.png')
    (out/f'{case_name.lower()}_visible_exact.svg').write_text(ET.tostring(exact,encoding='unicode'),'utf-8')
    exact_account=count_svg(exact,case['overlay_vertices'])
    # Research proposals on per-character signed masks, independently. Protect
    # only genuine *new* overpaint in protected pixels with source-proven holes.
    protected=np.logical_or.reduce([signed[k] for k in PROTECTED])
    active_protected={ident for ident in visible if case['records'][int(ident.rsplit('-',1)[1])]['source_mask_owner'] in PROTECTED}
    fixed={}
    for ident in active_protected:
        fixed[ident]=vector_path(visible[ident],0.5)
    fixed['sa1041-original-face-guard']=vector_path(signed['face'],0.5)
    if case_name=='GC001':
        fixed['sa1041-protected-clear']=vector_path(protected,0.5)
    fixed_count=sum(n for _,n in fixed.values())
    available=case['budget']-fixed_count-case['overlay_vertices']
    candidates={}; shapes={}; witness={}
    for ident,binary in visible.items():
        if ident in active_protected:continue
        candidates[ident]=[]
        for eps in EPS:
            path,n=vector_path(binary,eps)
            probe=copy.deepcopy(exact)
            edge.replace_svg_mask(probe,ident,path)
            observed=edge.chromium_rgb(page,edge.isolated_svg(probe,ident))[...,0]<128
            # Can't erase legitimate overlap with signed protected source.
            overpaint=observed&protected&~binary
            patches=raden45.pixel_rectangles(overpaint)
            after=observed&~overpaint
            proposal={'epsilon':eps,'vertices':n+4*len(patches),
                 'path_vertices':n,'protect_trim_rectangles':len(patches),
                 'before_protected_intrusion_px':int(overpaint.sum()),
                 'outside_protected_binary_error':int(np.count_nonzero((after!=binary)&~protected))}
            candidates[ident].append(proposal)
            shapes[(ident,eps)]=(path,patches)
    picked=score(candidates,available) if available>0 else {'feasible':False,'reason':'Fixed source guards exceed budget','remaining_vertex_budget':available}
    # Make one conservative candidate and one minimum complexity diagnostic.
    requested={ident:(picked['picked_epsilons'][ident] if picked['feasible'] else
                       min(options,key=lambda x:(x['vertices'],x['outside_protected_binary_error']))['epsilon'])
               for ident,options in candidates.items()}
    approx=copy.deepcopy(exact)
    for ident,ep in requested.items():
        path,patches=shapes[(ident,ep)]
        edge.replace_svg_mask(approx,ident,path)
        mask=next(m for m in approx.iter(NS+'mask') if m.get('id')==ident)
        for x,y,w,h in patches:
            ET.SubElement(mask,NS+'rect',{'x':str(x),'y':str(y),'width':str(w),'height':str(h),
                       'fill':'#000000','shape-rendering':'crispEdges',
                       'data-sa1047-protected-trim':'1'})
    approximation=edge.chromium_rgb(page,ET.tostring(approx,encoding='unicode'))
    approximate_metrics=edge.metrics(reference,approximation,signed)
    approximate_account=count_svg(approx,case['overlay_vertices'])
    approximate_pass=approximate_account['expanded_deployed_vertices']<=case['budget'] and not any(approximate_metrics['source_signed_protected'].values())
    # Neither private source nor forbidden fabricated face features enter the repo.
    if any(n.tag in (NS+'image',NS+'foreignObject',NS+'feImage') for n in approx.iter()):
        raise ValueError('Forbidden raster embedding detected')
    (out/f'{case_name.lower()}_visible_budget_probe.svg').write_text(ET.tostring(approx,encoding='unicode'),'utf-8')
    Image.fromarray(approximation).save(out/f'{case_name.lower()}_visible_budget_probe.png')
    return {'case':case_name,'source_order':[p['source_mask_owner'] for p in case['records']],
            'painted_indices_preserved':case['painted'],
            'original_source_ring_vertices':case['historical_stage8_vertices'],
            'original_source_budget':case['budget'],
            'source_ring_budget_pass':case['historical_stage8_vertices']<=case['budget'],
            'protected_signed_owner_delta_source_pixels':{
                k:int(np.count_nonzero(case['masks'][f'sa1041-owner-{next(i for i,p in enumerate(case["records"]) if p["source_mask_owner"]==k)}']!=signed[k])) for k in PROTECTED},
            'all_stage9_and_apparel_color_polygons_preserved':True,
            'apparel_color_polygons':0 if case_name=='Raden' else 5,
            'source_hidden_pixel_pruning':vis_stats,
            'visible_exact_equals_original_exact_chromium':exact_matches,
            'visible_exact':{**exact_account,'full_chrome':edge.metrics(reference,frame_exact,signed),
                            'topmost_source_owner_rgb_errors':source_owner_rgb_partition(case,frame_exact),
                            'budget_pass':exact_account['expanded_deployed_vertices']<=case['budget']},
            'protected_fixed_vertices':fixed_count,'available_unprotected_budget':available,
            'per_owner_candidates':candidates,'selection':picked,
            'budget_probe':{**approximate_account,'per_owner_epsilon':requested,
                            'full_chrome':approximate_metrics,
                            'topmost_source_owner_rgb_errors':source_owner_rgb_partition(case,approximation),
                            'all_protected_zero':not any(approximate_metrics['source_signed_protected'].values()),
                            'budget_pass':approximate_account['expanded_deployed_vertices']<=case['budget'],
                            'dual_gate_pass':approximate_pass},
            'golden_promotable':False,'production_change_authorized':False}


def evaluate(raden_root:Path,gc001_root:Path,output:Path,chromium='/usr/bin/chromium')->dict:
    roots=[raden_root.resolve(),gc001_root.resolve()]
    output=output.resolve()
    if len(set(roots))!=2 or any(output==r or r in output.parents or output in r.parents for r in roots):
        raise ValueError('Must keep signed source and generated outputs completely separate')
    cases=[load_case('Raden',roots[0]),load_case('GC001',roots[1])]
    output.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            results=[render_case(case,output,page) for case in cases]
            chrome=browser.version
        finally:browser.close()
    # Output must remain a research report with explicit ALL gates.
    board=Image.new('RGB',(340*3,2*380),(246,246,242))
    pencil=ImageDraw.Draw(board)
    for row,r in enumerate(results):
        case=cases[row]
        names=['SIGNED OPENCV','VISIBLE EXACT','VISIBLE BUDGET PROBE']
        frames=[case['original'],np.asarray(Image.open(output/f"{r['case'].lower()}_visible_exact.png").convert('RGB')),
                np.asarray(Image.open(output/f"{r['case'].lower()}_visible_budget_probe.png").convert('RGB'))]
        for col,(name,im) in enumerate(zip(names,frames)):
            board.paste(Image.fromarray(im),(col*340,row*380+40))
            pencil.text((col*340+5,row*380+13),f'{r["case"]}: {name}',fill=(22,22,22))
    board.save(output/'sa1047_two_case_comparison.png')
    results_by_case={r['case']:r for r in results}
    report={'stage':'SA10.47','schema':'sa1047-generic-visible-owned-protected-browser-optimizer-v1',
            'chromium':chrome,'cases':results_by_case,
            'two_case_source_exact_chrome_verified':all(r['visible_exact_equals_original_exact_chromium'] for r in results),
            'two_case_budget_and_protection_pass':all(r['budget_probe']['dual_gate_pass'] for r in results),
            'two_case_source_ring_budget_pass':all(r['source_ring_budget_pass'] for r in results),
            'human_visual_review':'PENDING','full_character_golden':'HOLD',
            'production_deployment':'UNCHANGED','use_of_generative_fill':False}
    names=sorted(x.name for x in output.iterdir() if x.is_file())
    report['artifact_sha256']={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in names}
    (output/'sa1047_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--raden',type=Path,required=True)
    ap.add_argument('--gc001',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--chromium',default='/usr/bin/chromium')
    args=ap.parse_args()
    data=evaluate(args.raden,args.gc001,args.out,args.chromium)
    print(json.dumps({'stage':data['stage'],'chromium':data['chromium'],
        'summary':{name:{'exact':p['visible_exact']['expanded_deployed_vertices'],
                         'candidate':p['budget_probe']['expanded_deployed_vertices'],
                         'rgb':p['budget_probe']['full_chrome'],
                         'selection':p['selection'],'dual_gate':p['budget_probe']['dual_gate_pass']}
                   for name,p in data['cases'].items()}},indent=2))

if __name__=='__main__':main()
