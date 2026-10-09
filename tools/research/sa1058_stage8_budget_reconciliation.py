"""SA10.58: immutable Stage8-ring provenance vs deployed SVG vertex-budget reconciliation.

Research-only. A budgeted Stage8 proposal is not accepted as source exact unless all
source visible ownership, signed arms/face, and source silhouette pixels match.
All coordinates come from signed source rings; no generated image, mask repair,
implicit vertex discount, or original budget change is permitted.
"""
from __future__ import annotations
import argparse,copy,hashlib,io,json,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1057_structure_boundary_guard as previous

CASES=('Raden','GC001')
SRC_ROOT={'Raden':'Raden_source.png','GC001':'GC001_source.png'}
SVG_SHA={'Raden':'a3927c5e2c0fd98012c64a1443b7fb399aaffb72def636ac3c79157bcc420e6d',
         'GC001':'bdea6fc36a953c01fe115032c10cb9313ecc900377f63954ff84bcb0392b2939'}
SVG_RENDER_SHA={'Raden':'610670713adb410595ca680903c9445d0130ba387da7afe9549be4970d01bbce',
                'GC001':'c51c8bac13f68802b1a7d0022eccd1eff66ae2e4b2f601a7e9b881b936eb4445'}
EPS=(0.0,0.4,0.5,0.75,1.0,1.25,1.5,2.0,2.5,3.0,4.0,6.0)
PROTECTED=('face','left_arm','right_arm')
# Budget includes original ring occurrences only. Stage9/37 paint vertices separately reported.
WEIGHT={'hair':5,'major_clothing':4,'torso':3,'lower_body':4,'neck':5,'accessory_or_held_object':4,'unknown':2,'head':1}
NS=previous.NS

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def authorities(name,root,svg):
    if name not in CASES:raise ValueError('Unknown signed Stage8 case')
    if digest(svg)!=SVG_SHA[name]:raise ValueError('SA1057_SVG_SHA_MISMATCH')
    # The SA10.57 input loader SHA-pins *previous* candidate. Here load genuine
    # original source without accidentally treating SA10.57 output as that input.
    data=previous.prior.previous.previous.prev.last.prior.prior.dual.load_case(name,root)
    case=previous.prior.previous.previous.prev.last.prior.prior.opt.load_case(name,root)
    tree=ET.parse(svg).getroot()
    previous.prior.previous.audit_default_faceless(tree)
    count=previous.prior.actual_svg_vertices(tree,case)
    if count!=previous.BASE_VERT[name]:raise ValueError('SA1057_DEPLOYED_VERTEX_COUNT_MISMATCH')
    ring_total=sum(len(r['points']) for item in case['records'] for r in item['parameters']['rings'])
    if ring_total!=case['historical_stage8_vertices']:raise ValueError('SIGNED_STAGE8_RING_COUNT_CHANGED')
    if sum(len(p.get('points','').split()) for p in tree.iter(NS+'polygon'))!=case['overlay_vertices']:
        raise ValueError('SOURCE_OVERLAY_VERTEX_COUNT_CHANGED')
    return data,case,tree

def topmost_owner_masks(masks,records,face):
    label=np.full(face.shape,-1,dtype=np.int16)
    for i,r in enumerate(records):
        if r.get('structural_support_only'):continue
        label[masks[i]]=i
    label[face]=next(i for i,r in enumerate(records) if r['source_mask_owner']=='face')
    return label

def choices_for_ring_owner(rec,original,visible,frozen,epsilons=EPS):
    opts=[];seen=set();role=rec['source_mask_owner']; protected=role in PROTECTED
    original_n=sum(len(r['points']) for r in rec['parameters']['rings'])
    for epsilon in epsilons:
        rings=[];cost=0
        for r in rec['parameters']['rings']:
            coords=np.asarray(r['points'],dtype=np.float32).reshape(-1,1,2)
            poly=cv2.approxPolyDP(coords,epsilon,True) if epsilon else coords
            if len(poly)<3:poly=coords
            pts=poly.reshape(-1,2).tolist()
            source_points=set(map(tuple,np.asarray(r['points'],dtype=np.float32).reshape(-1,2).tolist()))
            if not set(map(tuple,pts)).issubset(source_points):raise AssertionError('Approximation introduced unsourced points')
            rings.append({'depth':r['depth'],'role':r['role'],'points':pts})
            cost+=len(pts)
        if cost>original_n:raise AssertionError('Contour budget increased unexpectedly')
        mask=previous.prior.previous.previous.prev.last.prior.prior.opt.edge.source_ring_mask(rings)
        changed=mask^original
        protected_diff=int(changed.sum()) if protected else 0
        if protected_diff or np.any(changed&frozen):continue
        visible_diff=int(np.count_nonzero(changed&visible))
        full_diff=int(np.count_nonzero(changed))
        signature=(cost,mask.tobytes())
        if signature in seen:continue
        seen.add(signature)
        weight=WEIGHT.get(role,1)
        # Source-exact visible regions matter more than hidden ring pixels.
        loss=weight*(10*visible_diff+full_diff)
        opts.append({'epsilon':epsilon,'vertices':cost,'ring_mask_error_pixels':full_diff,
            'original_visible_error_pixels':visible_diff,'weighted_source_loss':loss,
            'original_unchanged':full_diff==0,'rings':rings,'mask':mask})
    if not opts:raise AssertionError('Signed original exact source ring missing')
    return sorted(opts,key=lambda x:(x['vertices'],x['weighted_source_loss'],x['epsilon']))

def pareto_options(opts):
    # For any given vertex count, keep the cheapest source-damage proposal.
    by={}
    for c in opts:
        n=c['vertices'];v=by.get(n)
        if v is None or (c['weighted_source_loss'],c['epsilon'])<(v['weighted_source_loss'],v['epsilon']):by[n]=c
    best=float('inf');efficient=[]
    for n,c in sorted(by.items()):
        if c['weighted_source_loss']<best:
            efficient.append(c);best=c['weighted_source_loss']
    return efficient

def select_budgeted(all_options,budget):
    dp={0:(0,())}
    for opts in all_options:
        newer={}
        for spent,(loss,picks) in dp.items():
            for j,c in enumerate(opts):
                used=spent+c['vertices']
                if used>budget:continue
                trial=(loss+c['weighted_source_loss'],picks+(j,))
                old=newer.get(used)
                if old is None or trial<old:newer[used]=trial
        if not newer:raise ValueError('NO_BUDGET_FEASIBLE_SOURCE_RING_CANDIDATE')
        dp=newer
    cost,(loss,chosen)=min(dp.items(),key=lambda x:(x[1][0],x[0],x[1][1]))
    return cost,loss,[opts[ix] for opts,ix in zip(all_options,chosen)]

def matte_source_svg(page,svg):
    image=copy.deepcopy(svg)
    if image.get('data-minimalizer-face-features')!='off':raise ValueError('Faceless SVG required')
    for c in list(image):
        if c.tag==NS+'defs':continue
        for n in c.iter():
            if n.get('fill') and n.tag in (NS+'rect',NS+'polygon',NS+'path'):n.set('fill','#000000')
    background=next(x for x in image if x.tag==NS+'rect')
    background.set('fill','#ffffff')
    pix=previous.chromium(page,image)
    return pix[...,0]<128

def compare_partition(masks,original,records,face,arms):
    base=topmost_owner_masks(original,records,face)
    out=topmost_owner_masks(masks,records,face)
    fb=base!=-1;fo=out!=-1
    assert fb.sum()>0
    mismatch=out!=base
    intersection=int((fb&fo).sum());union=int((fb|fo).sum())
    return {'source_ownership_mismatched_pixels':int(mismatch.sum()),
       'changed_signed_face_pixels':int(np.count_nonzero(mismatch&face)),
       'changed_signed_arm_ownership_pixels':int(np.count_nonzero(mismatch&arms)),
       'source_visible_silhouette_symmetric_difference_pixels':int(np.count_nonzero(fb^fo)),
       'source_visible_silhouette_iou':round(intersection/union,8),
       'source_reference_silhouette_pixels':int(fb.sum()),'proposed_silhouette_pixels':int(fo.sum())},fb,fo

def measure_case(name,source,old_svg,out,page):
    data,case,svg=authorities(name,source,old_svg)
    original=[case['masks'][f'sa1041-owner-{i}'] for i in range(len(case['records']))]
    visible,_=previous.prior.previous.previous.prev.last.prior.prior.opt.visible_ownership(case)
    face=data['masks']['face']; arms=data['masks']['left_arm']|data['masks']['right_arm']
    source_mat=topmost_owner_masks(original,case['records'],face)
    exact_support=np.count_nonzero(source_mat!=-1)
    if exact_support<=1000:raise AssertionError('Source owner partition empty')
    opts=[];all_pareto=[];strict_minimum=0;strict_per_owner=[]
    for i,rec in enumerate(case['records']):
        key=f'sa1041-owner-{i}'
        mask=visible.get(key,np.zeros_like(face))
        strict_options=choices_for_ring_owner(rec,original[i],mask,face|arms)
        strict_minimum+=min(x['vertices'] for x in strict_options)
        strict_per_owner.append({'role':rec['source_mask_owner'],'minimum_preserving_every_protected_pixel':min(x['vertices'] for x in strict_options)})
        options=choices_for_ring_owner(rec,original[i],mask,np.zeros_like(face))
        frontier=pareto_options(options)
        opts.append(options);all_pareto.append(frontier)
    lowest_exact=sum(min(c['vertices'] for c in o if c['ring_mask_error_pixels']==0) for o in opts)
    candidate_vertices,optimization_loss,selected=select_budgeted(all_pareto,case['budget'])
    candidate_masks=[c['mask'] for c in selected]
    audit,base_mask,trial_mask=compare_partition(candidate_masks,original,case['records'],face,arms)
    if any(selected[i]['ring_mask_error_pixels']!=0 for i,r in enumerate(case['records']) if r['source_mask_owner'] in PROTECTED):
        raise AssertionError('PROTECTED_SOURCE_RING_WAS_MODIFIED')
    # Full-screen rendered silhouette independently measured from final SVG.
    svg_baseline=previous.chromium(page,svg)
    bytesio=io.BytesIO();Image.fromarray(svg_baseline).save(bytesio,format='PNG')
    if hashlib.sha256(bytesio.getvalue()).hexdigest()!=SVG_RENDER_SHA[name]:raise AssertionError('SIGNED_SA1057_BROWSER_RENDER_SHA_MISMATCH')
    Image.fromarray(svg_baseline).save(out/f'{name.lower()}_sa1057_baseline.png')
    display_silhouette=matte_source_svg(page,svg)
    displayed_iou=round(float((display_silhouette&base_mask).sum())/float((display_silhouette|base_mask).sum()),8)
    discrepancy=int(np.count_nonzero(display_silhouette^base_mask))
    # No hidden relaxation of historical Stage8 cap, and no substitution of
    # the compact output SVG result for the original-source ring source gate.
    full_exact=(audit['source_ownership_mismatched_pixels']==0 and
                audit['changed_signed_arm_ownership_pixels']==0 and
                audit['source_visible_silhouette_symmetric_difference_pixels']==0)
    within=candidate_vertices<=case['budget']
    certified=within and full_exact
    if not within:raise AssertionError('Stage8 compressed proposal exceeds actual cap')
    name_low=name.lower()
    # Full signed original and candidate masks are preserved as private bitmap evidence.
    rgb=np.full((340,340,3),255,np.uint8);rgb[base_mask]=[45,62,77]
    altered=base_mask^trial_mask;rgb[altered]=[221,73,72]
    protected_disagree=(source_mat!=topmost_owner_masks(candidate_masks,case['records'],face))&arms
    rgb[protected_disagree]=[180,0,200]
    Image.fromarray(rgb).save(out/f'{name_low}_stage8_source_difference.png')
    # Not promoted! Derived hypothetical ring geometry is private only.
    candidate={'schema':'SA1058_UNAPPROVED_DERIVED_STAGE8_RINGS_V1','case':name,
       'signed_source_image_sha256':case['source_input_sha256'][SRC_ROOT[name]],
       'source_stage8_json_sha256':case['source_input_sha256']['phase8_adaptive_source_contour_research.json'],
       'source_svg_sha256':digest(old_svg),'ring_budget_limit':case['budget'],
       'parts':[{'source_mask_owner':r['source_mask_owner'],'rings':s['rings']} for r,s in zip(case['records'],selected)]}
    (out/f'{name_low}_unapproved_stage8_candidate.json').write_text(json.dumps(candidate,ensure_ascii=False,separators=(',',':'))+'\n','utf-8')
    rows=[]
    for rec,choice,variants in zip(case['records'],selected,opts):
        rows.append({'role':rec['source_mask_owner'],
           'source_vertices':sum(len(r['points']) for r in rec['parameters']['rings']),
           'candidate_vertices':choice['vertices'],'approximation_epsilon':choice['epsilon'],
           'source_mask_changed_pixels':choice['ring_mask_error_pixels'],
           'original_visible_region_changed_pixels':choice['original_visible_error_pixels'],
           'protected_source_mask_unchanged':rec['source_mask_owner'] not in PROTECTED or choice['ring_mask_error_pixels']==0,
           'exact_candidate_min_vertices':min(x['vertices'] for x in variants if x['ring_mask_error_pixels']==0)})
    return {'name':name,'source_input_sha256':case['source_input_sha256'],
       'signed_sa1057_svg_sha256':digest(old_svg),'original_stage8_ring_vertices':case['historical_stage8_vertices'],
       'original_stage8_budget':case['budget'],'source_stage8_budget_pass':False,
       'stage9_stage37_overlay_vertices':case['overlay_vertices'],
       'sa1057_deployed_expanded_vertices':previous.BASE_VERT[name],
       'sa1057_expanded_budget_pass':True,
       'source_ring_overrun':case['historical_stage8_vertices']-case['budget'],
       'candidate_ring_vertices':candidate_vertices,'candidate_ring_budget_pass':within,
       'minimum_exact_ring_vertices_in_tested_epsilon_family':lowest_exact,
       'minimum_all_protected_face_arm_pixel_safe_vertices_in_tested_epsilon_family':strict_minimum,
       'all_protected_face_arm_pixels_safe_within_source_budget_in_tested_epsilon_family':strict_minimum<=case['budget'],
       'strict_protected_minima_by_owner':strict_per_owner,
       'all_source_ring_parts_exact_within_budget_in_tested_epsilon_family':lowest_exact<=case['budget'],
       'candidate_optimization_proxy_weighted_loss':optimization_loss,
       'per_owner':rows,'full_source_ownership_replay':audit,
       'rendered_current_svg_vs_source_geometry':{'binary_silhouette_disagreement_pixels':discrepancy,
             'silhouette_iou':displayed_iou,'actual_chromium_matte_render':True},
       'candidate_source_exact_release_gate':certified,
       'signed_source_face_arm_ring_masks_unchanged':True,
       'human_visual_review':'PENDING','golden':'HOLD','production':'UNCHANGED'}

def evaluate(raden_root,gc001_root,raden_svg,gc001_svg,out,chromium='/usr/bin/chromium'):
    roots=[Path(raden_root).resolve(),Path(gc001_root).resolve()]
    svg=[Path(raden_svg).resolve(),Path(gc001_svg).resolve()]
    out=Path(out).resolve()
    if roots[0]==roots[1] or any(out==r or r in out.parents or out in r.parents for r in roots):raise ValueError('Signed source and output must be separate')
    if any(out==s or s in out.parents or out in s.parents for s in svg):raise ValueError('Previous SVG and output must be separate')
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pl:
        browser=pl.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            metrics=[measure_case(n,r,s,out,page) for n,r,s in zip(CASES,roots,svg)]
            version=browser.version
        finally:browser.close()
    board=Image.new('RGB',(340*3,380*2),(244,244,242));pen=ImageDraw.Draw(board)
    for row,(name,root) in enumerate(zip(CASES,roots)):
        originals=Image.open(root/SRC_ROOT[name]).convert('RGB')
        before=Image.open(out/f'{name.lower()}_sa1057_baseline.png').convert('RGB')
        after=Image.open(out/f'{name.lower()}_stage8_source_difference.png').convert('RGB')
        # Rendered candidate only for original output, no hypothetical artwork.
        current=before
        for col,(pic,heading) in enumerate(zip((originals,current,after),('SIGNED ORIGINAL','SA10.57 FACELESS SVG','Stage8 SOURCE DIFFERENCE'))):
            board.paste(pic,(col*340,row*380+40));pen.text((col*340+8,row*380+10),name+' / '+heading,fill=(20,20,24))
    board.save(out/'sa1058_source_budget_review.png')
    result={'stage':'SA10.58','schema':'signed-source-ring-vertex-budget-release-gate-v1',
      'chromium':version,'immutable_original_stage8_vertex_caps':{'Raden':1412,'GC001':1887},
      'separate_source_lineage_vs_deployed_svg_counts':True,
      'candidate_family_epsilons':list(EPS),'candidate_paints_not_promoted':True,
      'cases':{x['name']:x for x in metrics},'source_stage8_release_gate':'HOLD',
      'candidate_source_equivalence_release_gate':'HOLD',
      'human_visual_golden':'HOLD','production_deployment':'UNCHANGED',
      'next_stage':'SA10.59 multi-image and human visual Golden review; no release until Stage8 gate is formally resolved'}
    result['artifact_sha256']={x.name:digest(x) for x in sorted(out.iterdir()) if x.is_file()}
    (out/'sa1058_metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('raden','gc001','raden_svg','gc001_svg','out'):p.add_argument('--'+name.replace('_','-'),required=True,type=Path)
    a=p.parse_args();rep=evaluate(a.raden,a.gc001,a.raden_svg,a.gc001_svg,a.out)
    for n,v in rep['cases'].items():print(n,'source',v['original_stage8_ring_vertices'],'budget',v['original_stage8_budget'],'candidate',v['candidate_ring_vertices'],'owner_changed',v['full_source_ownership_replay']['source_ownership_mismatched_pixels'],'protected',v['full_source_ownership_replay']['changed_signed_arm_ownership_pixels'],'SVG IoU',v['rendered_current_svg_vs_source_geometry']['silhouette_iou'])
