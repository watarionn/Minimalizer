"""SA10.51 source-locked composited-dead trim reclamation and face feature budget allocation.

Research only. Nothing may be generated, inferred or raster-embedded. Any mask
trim removed must be proven a complete-scene no-op in real Chromium. Source
face colors are original-image medoids and paths are inside its existing signed
face guard, so no extra reference to the existing face mask is hidden.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1050_source_color_vectorization as prior

NS=prior.NS
CASES=('Raden','GC001')
FACE_POLICIES=tuple((eps, minarea) for eps in (1.4,1.8,2.0,2.5,3.0,4.0,5.0,6.0,8.0,10.0) for minarea in (7,15))
TRIM_TAGS=('data-sa1045-protected-trim','data-sa1047-protected-trim')
REGIONS=('major_clothing','lower_body','torso','hair')


def svg_rgb(page,root):
    return prior.edge.chromium_rgb(page,ET.tostring(root,encoding='unicode'))


def all_trimmed(svg):
    return [(p,c) for p in svg.iter() for c in p if c.tag==NS+'rect' and any(c.get(k)=='1' for k in TRIM_TAGS)]


def strict_vertices(svg,case,original_trim_count=None):
    """Count expanded masked geometry, every trim rect and all feature paths."""
    base=prior.opt.count_svg(svg,case['overlay_vertices'])['expanded_deployed_vertices']
    extra_trims=sum(4 for p,c in all_trimmed(svg) if c.get(TRIM_TAGS[0])=='1')
    details=[x for x in svg.iter(NS+'path') if x.get('data-sa1051-observed')]
    vertex_count=sum(prior.shared.path_vertices(x.get('d','')) for x in details)
    return {'mask_and_color_vertices':base+extra_trims,
        'face_and_material_path_vertices':vertex_count,
        'expanded_deployed_vertices':base+extra_trims+vertex_count,
        'live_protected_trim_rectangles':len(all_trimmed(svg)),
        'source_color_polygon_vertices':case['overlay_vertices'],
        'signed_face_mask_references':sum(n.get('mask')=='url(#sa1041-original-face-guard)' for n in svg.iter())}


def reclaim_source_proven_trims(source,original,page):
    """Greedily delete only complete Chromium-composite pixel-dead trim rectangles.

    Removing rectangles that are hidden by later source paints is not a source
    geometry invention, but this proof is signed-scene and browser-specific.
    """
    root=copy.deepcopy(source)
    start=all_trimmed(root)
    removed=[]
    for parent,child in start:
        i=list(parent).index(child)
        parent.remove(child)
        changed=svg_rgb(page,root)
        if np.array_equal(changed,original):
            removed.append({'owner_mask':parent.get('id'),'source_rect':{k:child.get(k) for k in ('x','y','width','height')}})
        else:
            parent.insert(i,child)
    frame=svg_rgb(page,root)
    if not np.array_equal(frame,original):
        raise AssertionError('All source trim removals must be exact Chromium no-ops')
    return root,{'source_trim_count':len(start),'removed_count':len(removed),
        'saved_expanded_vertices':4*len(removed),
        'preserved_count':len(all_trimmed(root)),
        'removed_mask_count_by_owner':{k:sum(a['owner_mask']==k for a in removed) for k in sorted({x['owner_mask'] for x in removed})},
        'all_old_chromium_pixels_unchanged':True}


def embed_face(scene,photo,signed_face,policy):
    root=copy.deepcopy(scene)
    evidence=prior.observe_palette(photo,signed_face,policy)
    guard=[n for n in root if n.get('mask')=='url(#sa1041-original-face-guard)']
    if len(guard)!=1 or len(guard[0])!=1 or guard[0][0].tag!=NS+'rect':
        raise ValueError('Source final opaque face guard must be single rect')
    guard[0][0].set('fill',prior.hex_rgb(evidence['base_rgb']))
    for detail in evidence['details']:
        ET.SubElement(guard[0],NS+'path',{'d':detail['path'], 'fill':prior.hex_rgb(detail['rgb']),
            'fill-rule':'evenodd','data-sa1051-observed':'face','data-source-cluster':str(detail['cluster'])})
    # Appending inside the *existing final masked face group* costs no extra
    # expanded mask reference unlike the SA10.50 appended separate group.
    evidence['true_new_path_vertices']=sum(x['vertices'] for x in evidence['details'])
    evidence['duplicate_mask_reference_vertices']=0
    return root,evidence


def guarded_fidelity(observed,original,photo,face,left_arm,right_arm,foreground):
    return {'face_rgb_mae':prior.rgb_mae(observed,photo,face),
        'foreground_rgb_mae':prior.rgb_mae(observed,photo,foreground),
        'left_arm_changed_vs_champion':prior.changed_pixels(observed,original,left_arm),
        'right_arm_changed_vs_champion':prior.changed_pixels(observed,original,right_arm),
        'outside_signed_face_changed_vs_champion':prior.changed_pixels(observed,original,~face)}


def best_face(page,root,data,case,original,foreground):
    face=data['masks']['face'];photo=data['photo']
    budgets=[];winner=None
    for eps,minarea in FACE_POLICIES:
        policy={'k':4,'epsilon':eps,'min_area':minarea}
        svg,details=embed_face(root,photo,face,policy)
        account=strict_vertices(svg,case)
        if account['expanded_deployed_vertices']>case['budget']:
            budgets.append({'epsilon':eps,'min_area':minarea,'vertices':account['expanded_deployed_vertices'],
                'budget_fit':False})
            continue
        frame=svg_rgb(page,svg)
        score=guarded_fidelity(frame,original,photo,face,data['masks']['left_arm'],data['masks']['right_arm'],foreground)
        if (score['left_arm_changed_vs_champion'] or score['right_arm_changed_vs_champion'] or
            score['outside_signed_face_changed_vs_champion']):
            raise AssertionError('Source-derived face color painted beyond signed face or arms')
        entry={'epsilon':eps,'min_area':minarea,'vertices':account['expanded_deployed_vertices'],
            'feature_path_vertices':details['true_new_path_vertices'], 'budget_fit':True,
            'face_mae':score['face_rgb_mae'],'foreground_mae':score['foreground_rgb_mae']}
        budgets.append(entry)
        rank=(score['face_rgb_mae'],score['foreground_rgb_mae'],account['expanded_deployed_vertices'],eps,minarea)
        if winner is None or rank<winner['rank']:
            winner={'rank':rank,'svg':svg,'frame':frame,'meta':details,'score':score,'account':account,'policy':policy}
    if winner is None:raise AssertionError('No source color face prototype fits hard deployed vertex budget')
    return winner,budgets


def try_materials(page,case,original,data,foreground,scene,frame):
    """Budget-limited source-observed palette parts; test *actual* Chromium RGB.

    Source material may be represented by one of its measured color planes
    without introducing the other plane or an unverified flat base. We try
    contour simplifications and require source-global improvement.
    """
    visible,_=prior.opt.visible_ownership(case)
    accepted=[];rejected=[]
    working,current=scene,frame
    initial=prior.rgb_mae(current,data['photo'],foreground)
    face=data['masks']['face'];arms=data['masks']['left_arm']|data['masks']['right_arm']
    for role in REGIONS:
        idx=next(i for i,p in enumerate(case['records']) if p['source_mask_owner']==role)
        owner_visible=visible[f'sa1041-owner-{idx}']
        choices=[]
        budget_rem=case['budget']-strict_vertices(working,case)['expanded_deployed_vertices']
        for eps in (prior.PALETTE_POLICY[role]['epsilon'],2.5,3.5,5.0,8.0):
            pol={**prior.PALETTE_POLICY[role],'epsilon':eps}
            evidence=prior.observe_palette(data['photo'],owner_visible,pol)
            for detail in evidence['details']:
                if detail['vertices']>budget_rem:continue
                for replace_base in (False,True):
                    proposal=copy.deepcopy(working)
                    owner=next(n for n in proposal if n.get('data-owner-index')==str(idx))
                    if replace_base:owner[0].set('fill',prior.hex_rgb(evidence['base_rgb']))
                    owner.insert(1,ET.Element(NS+'path',{'d':detail['path'],'fill':prior.hex_rgb(detail['rgb']),
                        'fill-rule':'evenodd','data-sa1051-observed':role,
                        'data-source-cluster':str(detail['cluster'])}))
                    verts=strict_vertices(proposal,case)['expanded_deployed_vertices']
                    if verts>case['budget']:continue
                    img=svg_rgb(page,proposal)
                    if prior.changed_pixels(img,original,arms) or prior.changed_pixels(img,current,face):continue
                    mae=prior.rgb_mae(img,data['photo'],foreground)
                    if mae>=initial:continue
                    local_before=prior.rgb_mae(current,data['photo'],owner_visible)
                    local_after=prior.rgb_mae(img,data['photo'],owner_visible)
                    if local_after>=local_before:continue
                    choices.append((mae,verts,eps,replace_base,proposal,img,detail,local_before,local_after))
        if choices:
            choice=min(choices,key=lambda x:(x[0],x[1],x[2],x[3]))
            mae,verts,eps,base,working,current,detail,prior_owner,new_owner=choice
            accepted.append({'role':role,'feature_path_vertices':detail['vertices'],
                'total_vertices':verts,'epsilon':eps,'replace_source_owner_base':base,
                'source_color_rgb':list(detail['rgb']), 'foreground_mae_after':mae,
                'owner_mae_before':prior_owner,'owner_mae_after':new_owner})
            initial=mae
        else:rejected.append({'role':role,'why':'no source-improving source-pixel-only paint candidate within real vertex budget'})
    return working,current,accepted,rejected


def evaluate_case(name,root,champion,out,page):
    data,case,svg=prior.load_signed(name,root,champion)
    baseline=svg_rgb(page,svg)
    baseline_flat=prior.edge.metrics(case['original'],baseline,case['signed'])['full_rgb_mismatch']
    if baseline_flat!=prior.CHAMPION_FLAT_RGB[name]:raise AssertionError('Frozen champion browser baseline changed')
    trims,trimproof=reclaim_source_proven_trims(svg,baseline,page)
    trim_account=strict_vertices(trims,case)
    if trim_account['expanded_deployed_vertices']!=prior.CHAMPION_VERTEX[name]-trimproof['saved_expanded_vertices']:
        raise AssertionError('Trim savings do not equal actual expanded SVG geometry')
    visible,_=prior.opt.visible_ownership(case)
    foreground=np.logical_or.reduce([*visible.values(),data['masks']['face']])
    initial_score=guarded_fidelity(baseline,baseline,data['photo'],data['masks']['face'],
        data['masks']['left_arm'],data['masks']['right_arm'],foreground)
    picked,frontier=best_face(page,trims,data,case,baseline,foreground)
    scene,frame,selected,rejected=try_materials(page,case,baseline,data,foreground,picked['svg'],picked['frame'])
    account=strict_vertices(scene,case)
    final=guarded_fidelity(frame,baseline,data['photo'],data['masks']['face'],
        data['masks']['left_arm'],data['masks']['right_arm'],foreground)
    if (final['face_rgb_mae']>=initial_score['face_rgb_mae'] or
        final['foreground_rgb_mae']>=initial_score['foreground_rgb_mae'] or
        final['left_arm_changed_vs_champion'] or final['right_arm_changed_vs_champion'] or
        account['expanded_deployed_vertices']>case['budget']):
        raise AssertionError('Source detail/arm/budget gates failed')
    if len([n for n in scene.iter() if n.get('mask')=='url(#sa1041-original-face-guard)'])!=1:
        raise AssertionError('Unexpected duplicate face signed mask usage')
    if any(n.tag in (NS+'image',NS+'foreignObject',NS+'feImage') for n in scene.iter()):
        raise AssertionError('Source raster embedding/inferred features forbidden')
    stem=name.lower();(out/f'{stem}_budget_detail.svg').write_text(ET.tostring(scene,encoding='unicode'),'utf-8')
    Image.fromarray(frame).save(out/f'{stem}_budget_detail.png')
    Image.fromarray(baseline).save(out/f'{stem}_previous_champion.png')
    report={'case':name,'source_sha256':case['source_input_sha256'],
        'immutable_champion_svg_sha256':hashlib.sha256(champion.read_bytes()).hexdigest(),
        'baseline_vertices':prior.CHAMPION_VERTEX[name], 'budget':case['budget'],
        'champion_legacy_flat_opencv_error':baseline_flat,'dead_trim_composite_proof':trimproof,
        'trimmed_exact_account':trim_account,'face_policy':picked['policy'],
        'face_options':frontier,
        'face_feature_path_vertices':picked['meta']['true_new_path_vertices'],
        'extra_face_mask_reference_vertex_occurrences':0,
        'accepted_material_details':selected,'rejected_material_details':rejected,
        'strict_account':account,'prior_source_fidelity':initial_score,
        'budget_source_fidelity':final,
        'geometric_budget_pass':True,'signed_arms_unchanged':True,
        'human_visual_review':'PENDING','full_character_golden':'HOLD','production_deployment':'UNCHANGED'}
    return report


def evaluate(raden_root,gc001_root,raden_champion,gc001_champion,out,chromium='/usr/bin/chromium'):
    roots=[Path(raden_root).resolve(),Path(gc001_root).resolve()];out=Path(out).resolve()
    if roots[0]==roots[1] or any(out==r or r in out.parents or out in r.parents for r in roots):
        raise ValueError('Signed input sources and outputs must be separate')
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            cases=[evaluate_case(n,r,c,out,page) for n,r,c in zip(CASES,roots,(Path(raden_champion),Path(gc001_champion)))]
            chrome=browser.version
        finally:browser.close()
    board=Image.new('RGB',(340*3,380*2),(244,244,241));pen=ImageDraw.Draw(board)
    for row,case in enumerate(cases):
        pref=case['case'].lower()
        original=np.asarray(Image.open(roots[row]/('Raden_source.png' if row==0 else 'GC001_source.png')).convert('RGB'))
        frames=[original,np.asarray(Image.open(out/f'{pref}_previous_champion.png').convert('RGB')),
                np.asarray(Image.open(out/f'{pref}_budget_detail.png').convert('RGB'))]
        for col,(frame,title) in enumerate(zip(frames,('SIGNED ORIGINAL','PRIOR BUDGET CHAMPION','SA10.51 SOURCE DETAIL'))):
            board.paste(Image.fromarray(frame),(col*340,row*380+40))
            pen.text((col*340+6,row*380+13),f'{pref.upper()}: {title}',fill=(19,19,20))
    board.save(out/'sa1051_two_case_budget_comparison.png')
    report={'stage':'SA10.51','schema':'signed-chromium-dead-trim-reclaim-face-color-budget-v1',
        'chromium':chrome,'cases':{x['case']:x for x in cases},
        'two_case_proven_dead_trim_pass':True,'two_case_expanded_vertex_budget_pass':True,
        'two_case_source_face_fidelity_improved':True,'two_case_signed_arms_stable':True,
        'source_colors_only':True,'generated_or_raster_embedded':False,
        'historical_source_ring_budget_pass':False,'full_character_golden':'HOLD',
        'human_visual_review':'PENDING','production_deployment':'UNCHANGED'}
    artifacts=sorted(p.name for p in out.iterdir() if p.is_file())
    report['artifact_sha256']={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in artifacts}
    (out/'sa1051_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report


def main():
    ap=argparse.ArgumentParser()
    for name in ('raden','gc001','raden_svg','gc001_svg','out'):ap.add_argument('--'+name.replace('_','-'),required=True,type=Path)
    a=ap.parse_args()
    result=evaluate(a.raden,a.gc001,a.raden_svg,a.gc001_svg,a.out)
    print(json.dumps({'stage':result['stage'],'summaries':{c:{'vertices':x['strict_account']['expanded_deployed_vertices'],
        'budget':x['budget'],'face_mae_before':x['prior_source_fidelity']['face_rgb_mae'],
        'face_mae_after':x['budget_source_fidelity']['face_rgb_mae'],'foreground_mae_after':x['budget_source_fidelity']['foreground_rgb_mae'],
        'trim_removed':x['dead_trim_composite_proof']['removed_count'],
        'face_epsilon':x['face_policy']['epsilon'], 'material_selected':x['accepted_material_details']} for c,x in result['cases'].items()}},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
