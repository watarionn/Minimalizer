"""SA10.59: signed, *non-promoting* cross-image faceless visual Golden review harness.

Two immutable signed images, three SHA-pinned prior candidate SVGs per image. Actual
Chromium rendering; original-source silhouette/role diagnostics. Human artistic
judgment stays PENDING. No SVG candidate modifications or automatic deployment.
"""
from __future__ import annotations
import argparse, hashlib, io, json, sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1058_stage8_budget_reconciliation as old

CASES=('Raden','GC001')
STAGES=('SA10.55','SA10.56','SA10.57')
VECTORS={
 'Raden':{'SA10.55':('fd65000ad4e814348f1158871e9e049b74fffbf7d84e4b4f25c35ee375d2d88a',1309),
          'SA10.56':('18474c41978f257ebf605040de4cfe2c532f6cc5f171b69089d8f48d921d349d',1409),
          'SA10.57':('a3927c5e2c0fd98012c64a1443b7fb399aaffb72def636ac3c79157bcc420e6d',1409)},
 'GC001':{'SA10.55':('ca077a2df9d134926a4c433746398dd5f9d3dc79818ded611fac32f9623e859b',1710),
          'SA10.56':('858080f4a738f41cade641fa24bf6414726f2bc9ce1b364f02400d9e0f37ed7e',1873),
          'SA10.57':('bdea6fc36a953c01fe115032c10cb9313ecc900377f63954ff84bcb0392b2939',1873)}
}
RENDER_SHA={
 'Raden':{'SA10.55':'54997a07a90e18607f491f95178b7e5f91f1fa6e4acf4c58bb7fd20226edb3bd',
          'SA10.56':'94a44b2b931655a2a2d23f3ec4763c8cd700934184912de019d9dc2ac0e63dce',
          'SA10.57':'610670713adb410595ca680903c9445d0130ba387da7afe9549be4970d01bbce'},
 'GC001':{'SA10.55':'921a871af5e609d812187236641270562c852222e3d3d5de4b83d406f85ef1fb',
          'SA10.56':'5f841e720cd621fbb22ed30cae8e5d05abd2f9e7a22a0ed2ec1ead2fe1535cdb',
          'SA10.57':'c51c8bac13f68802b1a7d0022eccd1eff66ae2e4b2f601a7e9b881b936eb4445'}}
ROLES=('hair','major_clothing','torso','lower_body','left_arm','right_arm')
CHECKLIST=('faceless_default_and_no_skin_plate', 'recognizable_hair_flow_and_head_shape',
           'source_costume_planes_and_distinctive_accessories',
           'anatomically_legible_both_arms_and_pose',
           'overall_silhouette_and_person_identity', 'no_unapproved_generated_or_raster_detail')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def png_sha(image):
    b=io.BytesIO();Image.fromarray(image).save(b,format='PNG');return hashlib.sha256(b.getvalue()).hexdigest()

def require_pins(name,source,svgs):
    if name not in CASES:raise ValueError('UNKNOWN_SIGNED_CASE')
    if len(svgs)!=3:raise ValueError('THREE_STAGES_REQUIRED')
    for stage,path in zip(STAGES,svgs):
        if not Path(path).is_file() or sha(path)!=VECTORS[name][stage][0]:
            raise ValueError('SHA_PINNED_SVG_CHANGED '+name+' '+stage)
    # SA10.58's independently pinned Stage57 and source originals.
    data,case,_=old.authorities(name,source,svgs[2])
    for stage,path in zip(STAGES,svgs):
        tree=ET.parse(path).getroot()
        old.previous.prior.previous.audit_default_faceless(tree)
        cost=old.previous.prior.actual_svg_vertices(tree,case)
        if cost!=VECTORS[name][stage][1] or cost>case['budget']:
            raise AssertionError('TRUE_EXPANDED_VERTEX_MISMATCH '+stage)
    return data,case

def source_owners(case,face):
    masks=[case['masks'][f'sa1041-owner-{i}'] for i in range(len(case['records']))]
    label=old.topmost_owner_masks(masks,case['records'],face)
    region={}
    for role in ROLES:
        index=next(i for i,r in enumerate(case['records']) if r['source_mask_owner']==role)
        region[role]=label==index
    return label,region

def mae(source,render,mask):
    if not np.any(mask):return None
    return round(float(np.abs(source[mask].astype(np.int16)-render[mask].astype(np.int16)).mean()),6)

def silhouette_stats(source_mask,candidate_mask):
    a=source_mask.astype(bool);b=candidate_mask.astype(bool)
    union=int(np.count_nonzero(a|b));inter=int(np.count_nonzero(a&b))
    disagree=int(np.count_nonzero(a^b))
    kernel=np.ones((3,3),np.uint8)
    sa=cv2.morphologyEx(a.astype(np.uint8),cv2.MORPH_GRADIENT,kernel).astype(bool)
    sb=cv2.morphologyEx(b.astype(np.uint8),cv2.MORPH_GRADIENT,kernel).astype(bool)
    # One-pixel tolerance is a diagnostic, not a semantic identity gate.
    nearb=cv2.dilate(sb.astype(np.uint8),kernel).astype(bool)
    neara=cv2.dilate(sa.astype(np.uint8),kernel).astype(bool)
    precision=float(np.count_nonzero(sb&neara))/max(1,int(sb.sum()))
    recall=float(np.count_nonzero(sa&nearb))/max(1,int(sa.sum()))
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    return {'source_pixels':int(a.sum()),'candidate_pixels':int(b.sum()),
            'symmetric_difference_pixels':disagree,'iou':round(inter/union,8) if union else None,
            'boundary_f1_1px_diagnostic':round(f1,8),'source_boundary_pixels':int(sa.sum()),
            'rendered_boundary_pixels':int(sb.sum())}

def output_safety(paths,roots,out):
    roots=[Path(p).resolve() for p in roots];out=Path(out).resolve()
    if roots[0]==roots[1]:raise ValueError('SOURCES_MUST_BE_SEPARATE')
    for d in [*roots,*[Path(p).resolve().parent for pair in paths for p in pair]]:
        if d==out or d in out.parents or out in d.parents:raise ValueError('SIGNED_INPUT_OUTPUT_MUST_NOT_OVERLAP')

def measure_one(name,root,svgs,out,page):
    data,case=require_pins(name,root,svgs)
    image=data['photo'];face=data['masks']['face']
    arms=data['masks']['left_arm']|data['masks']['right_arm']
    label,roles=source_owners(case,face)
    subject=label!=-1
    frames={};metrics={}
    for stage,svg_path in zip(STAGES,svgs):
        tree=ET.parse(svg_path).getroot()
        rendered=old.previous.chromium(page,tree)
        if png_sha(rendered)!=RENDER_SHA[name][stage]:raise AssertionError('ORIGINAL_CHROMIUM_PNG_CHANGED '+name+' '+stage)
        frames[stage]=rendered
        region={k:mae(image,rendered,mask) for k,mask in roles.items()}
        metrics[stage]={'expanded_vertices':VECTORS[name][stage][1],
                        'source_nonface_rgb_mae':mae(image,rendered,subject&~face),
                        'per_source_owner_rgb_mae':region,
                        'source_arm_rgb_mae':mae(image,rendered,arms)}
        Image.fromarray(rendered).save(out/f'{name.lower()}_{stage.replace(".","").lower()}_review.png')
    baseline=frames['SA10.55'];latest=frames['SA10.57']
    changed=np.any(baseline!=latest,axis=2)
    source_exact_arms=all(np.array_equal(frames[stage][arms],baseline[arms]) for stage in STAGES)
    source_exact_face=all(np.array_equal(frames[stage][face],baseline[face]) for stage in STAGES)
    if not (source_exact_arms and source_exact_face):raise AssertionError('PROTECTED_FACE_ARMS_REGRESSED')
    # Stage8 original source label-matte authority, verified against old 10.58.
    latest_tree=ET.parse(svgs[2]).getroot()
    rendered_matte=old.matte_source_svg(page,latest_tree)
    shape=silhouette_stats(subject,rendered_matte)
    if shape['iou']>=1 or shape['symmetric_difference_pixels']==0:
        raise AssertionError('EXPECTED_SOURCE_SILHOUETTE_DIFFERENCE_ABSENT_RECHECK_GATE')
    def protected_region(k):return {'source_owner':k,'source_region_pixels':int(roles[k].sum()),
                                'candidate_source_rgb_mae':metrics['SA10.57']['per_source_owner_rgb_mae'][k]}
    # User-visible comparison boards kept PRIVATE; no raw source in GitHub.
    h, w=image.shape[:2]
    img_list=[image,frames['SA10.55'],frames['SA10.56'],frames['SA10.57']]
    labels=['SIGNED ORIGINAL','SA10.55 FACELESS','SA10.56 MATERIAL','SA10.57 STRUCTURE']
    board=Image.new('RGB',(w*4,h+36),(245,245,244));pen=ImageDraw.Draw(board)
    for i,(img,title) in enumerate(zip(img_list,labels)):
        board.paste(Image.fromarray(img),(w*i,36));pen.text((w*i+6,12),title,fill=(20,24,30))
    board.save(out/f'{name.lower()}_review_strip.png')
    yy,xx=np.where(roles['hair']|roles['major_clothing']|roles['torso']);xmin=max(0,int(xx.min())-6);xmax=min(w,int(xx.max())+7);ymin=max(0,int(yy.min())-6);ymax=min(h,int(yy.max())+7)
    zoom=Image.new('RGB',(320*4,360),(247,247,245));paint=ImageDraw.Draw(zoom)
    for i,(img,title) in enumerate(zip(img_list,labels)):
        crop=Image.fromarray(img).crop((xmin,ymin,xmax,ymax)).resize((300,325),Image.Resampling.NEAREST)
        zoom.paste(crop,(i*320+10,26));paint.text((i*320+9,7),title,fill=(15,15,15))
    zoom.save(out/f'{name.lower()}_detail_strip.png')
    return {'signed_source_sha256':case['source_input_sha256'],
            'stage_sha256':{s:VECTORS[name][s][0] for s in STAGES},
            'stage_browser_png_sha256':RENDER_SHA[name],
            'source_original_stage8_ring_vertices':case['historical_stage8_vertices'],
            'historic_stage8_source_ring_budget':case['budget'],
            'historic_stage8_ring_gate':'FAIL',
            'stages':metrics,'silhouette_matte_vs_original_source':shape,
            'source_geometry_disagreement_remains':True,
            'signed_face_pixels_identical_across_stages':source_exact_face,
            'signed_arms_pixels_identical_across_stages':source_exact_arms,
            'default_faceless_pass':True,
            'source_background_unchanged_from_baseline':bool(np.array_equal(latest[~subject],baseline[~subject])),
            'face_iris_mouth_detail_should_be_visible':False,
            'hair_latest':protected_region('hair'),'garment_latest':protected_region('major_clothing'),
            'human_checklist':{x:'PENDING' for x in CHECKLIST},
            'human_identity_verdict':'PENDING',
            'source_stage8_release_verdict':'HOLD',
            'golden':'HOLD','production':'UNCHANGED'}

def evaluate(roots,stage_inputs,out,chromium='/usr/bin/chromium'):
    roots=[Path(p).resolve() for p in roots]
    inputs=[[Path(p).resolve() for p in pset] for pset in stage_inputs]
    out=Path(out).resolve();output_safety(inputs,roots,out);out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as play:
        browser=play.chromium.launch(executable_path=chromium,headless=True,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            cases={name:measure_one(name,root,svg,out,page) for name,root,svg in zip(CASES,roots,inputs)}
            version=browser.version
        finally:browser.close()
    # Shared 2-source review board is private because signed original pixels appear.
    mosaic=Image.new('RGB',(1360,752),(245,245,244))
    for ix,name in enumerate(CASES):
        mosaic.paste(Image.open(out/f'{name.lower()}_review_strip.png').convert('RGB'),(0,376*ix))
    mosaic.save(out/'sa1059_two_case_golden_review_board.png')
    summary={'stage':'SA10.59','schema':'signed-multistage-two-source-visual-golden-review-v1',
             'chromium':version,'signed_source_cases':list(CASES),
             'total_independent_signed_input_images':2,'total_chromium_stage_replays':6,
             'golden_coverage_limited_to_two_signed_images':True,
             'source_agnostic_generalization_not_evaluated':True,
             'comparison_stage_labels':list(STAGES),'cases':cases,
             'human_visual_judgments_are_not_auto_certified':True,
             'all_human_reviews':'PENDING','source_stage8_release':'HOLD',
             'full_character_golden':'HOLD','production_phase15_gate':'NOT_RUN',
             'production_deployment':'UNCHANGED',
             'next':'Human artifact review and expanded corpus, source-stage8 policy resolution before Phase15/production'}
    # Human decision template is separate from measured evidence, cannot certify automatically.
    template={'schema':'SA1059_HUMAN_REVIEW_BLANK_V1','source_image_count':2,
              'review_instructions':'Inspect the signed original, faceless SA10.55, SA10.56 and SA10.57 side by side; fill the criteria and explanatory notes manually. This form is NOT a promotion mechanism.',
              'cases':{n:{'reviewer':'','reviewed_at':'','criteria':{k:'PENDING' for k in CHECKLIST},'artistic_identity':'PENDING','notes':''} for n in CASES},
              'release_gate_reminder':'Stage8 HOLD persists. Filling this form does not deploy or override gates.'}
    (out/'sa1059_human_review_blank.json').write_text(json.dumps(template,ensure_ascii=False,indent=2)+'\n','utf-8')
    md=['# SA10.59 Human visual Golden review sheet','',
        'Decision: **HOLD** until documented human approvals and independent Stage8 release gate resolution.',
        'Two independent signed source images, not a complete production corpus.', '',
        '| Source | Signed Stage8 | Deployed budget | Source matte silhouette IoU | Source pixels differing | Human identity |',
        '|---|---|---|---|---|---|']
    for n,v in cases.items():
        last=v['stages']['SA10.57']['expanded_vertices']; cap=v['historic_stage8_source_ring_budget'];s=v['silhouette_matte_vs_original_source']
        md.append(f"| {n} | {v['source_original_stage8_ring_vertices']}/{cap} FAIL | {last}/{cap} PASS | {s['iou']:.8f} | {s['symmetric_difference_pixels']} | PENDING |")
    md.extend(['','## Review criteria (per source)','',*['- [ ] '+x.replace('_',' ') for x in CHECKLIST],
               '', '## Nonclaims','', '- Faceless feature suppression is a deliberate style constraint, not source-RGB eye fidelity.',
               '- Pixel RGB MAE, signed source masks and silhouette IoU do not certify recognizable identity.',
               '- No human approval was performed by this script. Source Stage8 policy remains unpassed.',
               '- Do not silently substitute under-budget deployed SVG cost for oversize immutable Stage8 original ring cost.',
               '- Actual production Phase15 checks and device validation have NOT run.',
               '', 'Private original comparison: `raden_review_strip.png`, `gc001_review_strip.png`, and *_detail_strip.png.'])
    (out/'sa1059_human_review_sheet.md').write_text('\n'.join(md)+'\n','utf-8')
    summary['artifact_sha256']={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    (out/'sa1059_metrics.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n','utf-8')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('raden','gc001','raden55','raden56','raden57','gc00155','gc00156','gc00157','out'):
        p.add_argument('--'+key,required=True,type=Path)
    a=p.parse_args();m=evaluate([a.raden,a.gc001],[[a.raden55,a.raden56,a.raden57],[a.gc00155,a.gc00156,a.gc00157]],a.out)
    print(json.dumps({'stage':m['stage'],'golden':m['full_character_golden'],'source_stage8':m['source_stage8_release'],
          'cases':{name:{'source_silhouette_iou':v['silhouette_matte_vs_original_source']['iou'],
                         'diff_pixels':v['silhouette_matte_vs_original_source']['symmetric_difference_pixels'],
                         'source_mae':{s:v['stages'][s]['source_nonface_rgb_mae'] for s in STAGES}} for name,v in m['cases'].items()}},indent=2))
