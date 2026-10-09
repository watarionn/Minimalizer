"""SA10.50 signed source-observed color boundaries, source-only SVG research.

Use the real RGB original to observe, NOT to embed or generate pixels. Existing
champions remain immutable. Double-gate geometry and original RGB separately.
Never present a flat-face comparison as proof of identity or a prototype as
production-ready. All emitted color polygons, masks and references are counted.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2,numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1043_boundary_compaction as edge
import sa1044_shared_geometry as shared
import sa1047_two_case_visible_optimizer as opt
import sa1049_source_detail_dual_gate as dual

NS=edge.NS
CHAMPION_HASH={
 'Raden':'8a2ea697b81e8d1c6ee1ac35e8a1b2264932b1091dcd6cc06f25c35ae5bd3345',
 'GC001':'e20afd2588a55bbaf74d5c567bc5a33165ed3aedd29734f5fc7a6b084116a61f'}
CHAMPION_VERTEX={'Raden':1409,'GC001':1883}
CHAMPION_FLAT_RGB={'Raden':882,'GC001':1871}
PALETTE_POLICY={
 'face': {'k':4,'min_area':7,'epsilon':1.4},
 'hair': {'k':3,'min_area':18,'epsilon':2.0},
 'major_clothing': {'k':3,'min_area':16,'epsilon':1.8},
 'lower_body': {'k':3,'min_area':18,'epsilon':2.0},
 'torso': {'k':3,'min_area':20,'epsilon':2.0},
}
ROLES_TO_TEST=('hair','major_clothing','lower_body','torso')


def source_medoid(values:np.ndarray)->tuple[int,int,int]:
    if not len(values):raise ValueError('empty source observed region')
    median=np.median(values.astype(np.float64),axis=0)
    delta=np.abs(values.astype(np.float64)-median).sum(axis=1)
    return tuple(int(x) for x in values[int(np.argmin(delta))])


def observe_palette(photo:np.ndarray,mask:np.ndarray,policy:dict):
    """Deterministic source-only k-means in LAB; output color must be an actual RGB pixel."""
    if photo.shape!=(340,340,3) or mask.shape!=(340,340) or mask.dtype!=bool:
        raise ValueError('Only 340x340 signed source observations')
    if not 0<policy['k']<=8 or policy['epsilon']<0 or policy['min_area']<1:
        raise ValueError('Unsafe/unbounded source palette policy')
    softened=cv2.GaussianBlur(photo,(3,3),0.65)
    samples=cv2.cvtColor(softened,cv2.COLOR_RGB2LAB)[mask].astype(np.float32)
    cv2.setRNGSeed(1050)
    _,indices,_=cv2.kmeans(samples,policy['k'],None,
        (cv2.TERM_CRITERIA_MAX_ITER+cv2.TERM_CRITERIA_EPS,30,0.05),5,cv2.KMEANS_PP_CENTERS)
    labels=np.full(mask.shape,-1,np.int16);labels[mask]=indices.ravel()
    counts=np.bincount(indices.ravel(),minlength=policy['k'])
    order=sorted(range(policy['k']),key=lambda n:(-counts[n],n))
    palette={idx:source_medoid(photo[mask][indices.ravel()==idx]) for idx in order}
    if any(not np.any(np.all(photo[mask]==np.asarray(color),axis=1)) for color in palette.values()):
        raise AssertionError('Some paint color not evidenced by the source pixels')
    details=[];pixels_retained=0
    for idx in order[1:]:
        binary=(labels==idx).astype(np.uint8)
        n,number,stats,_=cv2.connectedComponentsWithStats(binary,8)
        clean=np.zeros_like(binary)
        for x in range(1,n):
            if stats[x,cv2.CC_STAT_AREA]>=policy['min_area']:
                clean[number==x]=1
        contours,_=cv2.findContours(clean,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
        paths=[];vertices=0
        for ct in contours:
            points=cv2.approxPolyDP(ct,policy['epsilon'],True).reshape(-1,2)
            if len(points)<3:continue
            paths.append('M '+' L '.join(f'{int(x)} {int(y)}' for x,y in points)+' Z')
            vertices+=len(points)
        if paths:
            pixels_retained+=int(clean.sum())
            details.append({'cluster':int(idx),'rgb':palette[idx], 'path':' '.join(paths),
                 'vertices':int(vertices),'source_cluster_pixels':int(counts[idx]),
                 'source_connected_pixels':int(clean.sum())})
    return {'base_rgb':palette[order[0]],'details':details,
            'source_colors':{str(i):palette[i] for i in order},
            'source_palette_clusters':policy['k'],'source_kept_nonbase_pixels':pixels_retained}


def hex_rgb(rgb):return '#'+''.join(f'{int(c):02x}' for c in rgb)

def rgb_mae(a,b,mask):return round(float(np.abs(a[mask].astype(np.int16)-b[mask]).mean()),6)

def changed_pixels(a,b,mask):return int(np.count_nonzero(np.any(a!=b,axis=2)&mask))


def safe_metrics(data):
    """Strip source-traced path geometry from GitHub-friendly public metrics."""
    if isinstance(data,dict):return {k:safe_metrics(v) for k,v in data.items() if k!='path'}
    if isinstance(data,list):return [safe_metrics(v) for v in data]
    return data


def load_signed(name,root,champion):
    # Source and older champion must both be immutable, independent authorities.
    data=dual.load_case(name,root)
    case=opt.load_case(name,root)
    if hashlib.sha256(champion.read_bytes()).hexdigest()!=CHAMPION_HASH[name]:
        raise ValueError('CHAMPION_SHA_MISMATCH '+name)
    svg=ET.parse(champion).getroot()
    base_count=opt.count_svg(svg,case['overlay_vertices'])['expanded_deployed_vertices']
    historical_trim=sum(4 for n in svg.iter(NS+'rect') if n.get('data-sa1045-protected-trim')=='1')
    if base_count+historical_trim!=CHAMPION_VERTEX[name]:
        raise ValueError('CHAMPION_BUDGET_MISMATCH '+name)
    return data,case,svg


def make_face(scene,photo,face_mask):
    out=copy.deepcopy(scene)
    x=observe_palette(photo,face_mask,PALETTE_POLICY['face'])
    guard=[n for n in out if n.get('mask')=='url(#sa1041-original-face-guard)']
    if len(guard)!=1 or len(guard[0])!=1:raise ValueError('No original signed face guard')
    old=guard[0][0].get('fill')
    guard[0][0].set('fill',hex_rgb(x['base_rgb']))
    layer=ET.SubElement(out,NS+'g',{'mask':'url(#sa1041-original-face-guard)',
        'data-sa1050-evidence':'original-source-face-color-boundaries'})
    for detail in x['details']:
        ET.SubElement(layer,NS+'path',{'d':detail['path'], 'fill':hex_rgb(detail['rgb']),
                       'fill-rule':'evenodd','data-sa1050-source-cluster':str(detail['cluster'])})
    # A *second* actual paint reference to the face mask costs an expanded copy.
    face_mask_id='sa1041-original-face-guard'
    mask=next(n for n in out.iter(NS+'mask') if n.get('id')==face_mask_id)
    reused_mask_vertices=sum(shared.path_vertices(n.get('d','')) for n in mask if n.tag==NS+'path')
    x.update({'old_flat_face_color':old,'new_extra_path_vertices':sum(d['vertices'] for d in x['details']),
        'new_mask_reference_vertex_occurrences':reused_mask_vertices,
        'new_expanded_vertices':sum(d['vertices'] for d in x['details'])+reused_mask_vertices})
    return out,x


def make_owner_color_candidate(scene,case,photo,role,visible):
    """Non-generative detail is painted inside the EXISTING signed-z owner group.

    Existing source-owner mask clips color boundaries; later owner paint still
    occludes them. For all geometry the source pixel must belong to visible owner.
    """
    idx=next(i for i,p in enumerate(case['records']) if p['source_mask_owner']==role)
    name=f'sa1041-owner-{idx}'
    data=observe_palette(photo,visible[name],PALETTE_POLICY[role])
    out=copy.deepcopy(scene)
    owners=[n for n in out if n.get('data-owner-index')==str(idx)]
    if len(owners)!=1 or owners[0].get('mask')!=f'url(#{name})':
        raise ValueError('Original source owner was reordered')
    owner=owners[0]
    if not len(owner) or owner[0].tag!=NS+'rect':
        raise ValueError('Source owner not an opaque color rect')
    # Source-observed color regions live atop the owner fill and below original
    # Stage9/37 color planes so existing semantic color source priority wins.
    owner[0].set('fill',hex_rgb(data['base_rgb']))
    for number,item in enumerate(data['details']):
        owner.insert(1+number,ET.Element(NS+'path',{'d':item['path'],
            'fill':hex_rgb(item['rgb']),'fill-rule':'evenodd',
            'data-sa1050-evidence':'original-source-'+role+'-'+str(item['cluster'])}))
    data['new_expanded_vertices']=sum(d['vertices'] for d in data['details'])
    data['new_extra_path_vertices']=data['new_expanded_vertices']
    return out,data


def evaluate_case(name,root,champion,out,page):
    evidence,case,base_svg=load_signed(name,root,champion)
    photo=evidence['photo'];face=evidence['masks']['face'];render=edge.chromium_rgb
    initial=render(page,ET.tostring(base_svg,encoding='unicode'))
    expected=edge.metrics(case['original'],initial,case['signed'])
    if expected['full_rgb_mismatch']!=CHAMPION_FLAT_RGB[name]:
        raise AssertionError('Source championship browser parity changed')
    # a facial study, in original-source color space, independent of flat RGB.
    face_svg,facemeta=make_face(base_svg,photo,face)
    face_png=render(page,ET.tostring(face_svg,encoding='unicode'))
    if changed_pixels(face_png,initial,~face):
        raise AssertionError('Face-color vector prototype repainted outside original face')
    if rgb_mae(face_png,photo,face)>=rgb_mae(initial,photo,face):
        raise AssertionError('Source face feature study did not improve actual-source MAE')
    visible,_=opt.visible_ownership(case)
    working=face_svg;working_img=face_png
    parts={};gate_mask=np.logical_or.reduce([case['signed'][k] for k in ('left_arm','right_arm')])
    foreground=np.logical_or.reduce([*visible.values(),face]);main_mae=rgb_mae(working_img,photo,foreground)
    for role in ROLES_TO_TEST:
        candidate,meta=make_owner_color_candidate(working,case,photo,role,visible)
        observation=render(page,ET.tostring(candidate,encoding='unicode'))
        owner_name=next(i for i,p in enumerate(case['records']) if p['source_mask_owner']==role)
        owner_mask=visible[f'sa1041-owner-{owner_name}']
        local_before=rgb_mae(working_img,photo,owner_mask)
        local_after=rgb_mae(observation,photo,owner_mask)
        all_after=rgb_mae(observation,photo,foreground)
        has_arm_new_error=changed_pixels(observation,initial,gate_mask)
        # Account candidate even if rejected. Accept only an independently
        # source-improving, composition-safe application.
        accept=(all_after<main_mae and local_after<local_before and has_arm_new_error==0)
        meta.update({'mae_before_owner':local_before,'mae_after_owner':local_after,
          'mae_before_foreground':main_mae,'mae_after_foreground':all_after,
          'final_arm_rgb_changed_vs_champion':has_arm_new_error,
          'accepted':bool(accept),'role_source_pixels':int(owner_mask.sum())})
        parts[role]=meta
        if accept:
            working,working_img=candidate,observation;main_mae=all_after
    if changed_pixels(working_img,initial,gate_mask):
        raise AssertionError('Arm-protected composite changed')
    if changed_pixels(working_img,face_png,face):
        raise AssertionError('Hair/clothing observables repainted signed facial region')
    # Existing budget is 1409/1883. Every added source-derived path is counted.
    accepted=sum(m['new_expanded_vertices'] for m in parts.values() if m['accepted'])
    expanded=CHAMPION_VERTEX[name]+facemeta['new_expanded_vertices']+accepted
    total_paths=sum(1 for n in working.iter() if n.get('data-sa1050-evidence'))
    if total_paths<2:raise AssertionError('No actual source-derived SVG detail produced')
    pref=name.lower()
    for suffix,node in [('face_detail',face_svg),('face_hair_clothes_detail',working)]:
        (out/f'{pref}_{suffix}.svg').write_text(ET.tostring(node,encoding='unicode'),'utf-8')
    Image.fromarray(initial).save(out/f'{pref}_champion_flat.png')
    Image.fromarray(face_png).save(out/f'{pref}_face_detail.png')
    Image.fromarray(working_img).save(out/f'{pref}_face_hair_clothes_detail.png')
    Image.fromarray(photo).save(out/f'{pref}_original_private.png')
    localface=case['signed']['face']
    return {'case':name,'signed_source_sha':case['source_input_sha256'],
      'chromium_original_champion_parity':expected,'signed_source_original_vs_svg_face':{
        'face_pixels':int(localface.sum()),
        'face_mae_champion':rgb_mae(initial,photo,localface),
        'face_mae_source_color_prototype':rgb_mae(working_img,photo,localface),
        'face_changed_pixels_vs_original_champion':changed_pixels(working_img,initial,localface)},
      'original_source_foreground_mae_champion':rgb_mae(initial,photo,foreground),
      'original_source_foreground_mae_prototype':rgb_mae(working_img,photo,foreground),
      'face_detail':safe_metrics(facemeta),'material_details':safe_metrics(parts),
      'added_actual_path_count':total_paths,'expanded_vertex_count_champion':CHAMPION_VERTEX[name],
      'expanded_vertex_count_prototype':expanded,'hard_budget':case['budget'],
      'budget_pass':expanded<=case['budget'],
      'original_signed_face_geometry_changed':False,
      'protected_arm_champion_rgb_unchanged':changed_pixels(working_img,initial,gate_mask)==0,
      'legacy_flat_face_rgb_zero_not_claimed':True,
      'historical_source_ring_budget_pass':False,
      'production_promotion_authorized':False,'golden_pass':False}


def evaluate(raden_root:Path,gc001_root:Path,champion_raden:Path,champion_gc001:Path,out:Path,chromium='/usr/bin/chromium'):
    roots=[raden_root.resolve(),gc001_root.resolve()];out=out.resolve()
    if len(set(roots))<2 or any(out==p or out in p.parents or p in out.parents for p in roots):
        raise ValueError('Signed source and output directory must be separate')
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pl:
        browser=pl.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            cases=[evaluate_case(n,p,c,out,page) for n,p,c in zip(('Raden','GC001'),roots,(champion_raden,champion_gc001))]
            chrome=browser.version
        finally:browser.close()
    board=Image.new('RGB',(340*4,380*2),(246,246,242));draw=ImageDraw.Draw(board)
    for row,name in enumerate(('raden','gc001')):
        for col,(caption,suf) in enumerate((('SIGNED ORIGINAL','original_private'),('PREVIOUS CHAMPION','champion_flat'),
                            ('ORIGINAL FACE COLORS','face_detail'),('FACE / HAIR / CLOTHES','face_hair_clothes_detail'))):
            image=np.asarray(Image.open(out/f'{name}_{suf}.png').convert('RGB'))
            board.paste(Image.fromarray(image),(col*340,row*380+40))
            draw.text((col*340+8,row*380+13),f'{name.upper()}: {caption}',fill=(22,22,28))
    board.save(out/'sa1050_two_case_source_detail_board.png')
    # Keep only the private comparison board, never duplicate original source PNGs.
    for case_name in ('raden','gc001'):
        (out/f'{case_name}_original_private.png').unlink()
    report={'stage':'SA10.50','schema':'signed-source-observed-svg-color-boundaries-v1',
      'chromium':chrome,'source_RGB_details_from_original_only':True,
      'kmeans_medoids_are_real_source_pixels':True,
      'no_generation_or_embedded_bitmaps':True,
      'source_signed_masks_not_overwritten':True,
      'source_color_vs_flat_legacy_gate_separated':True,
      'cases':{n['case']:n for n in cases},
      'both_signed_arms_stable':all(n['protected_arm_champion_rgb_unchanged'] for n in cases),
      'two_case_deployed_svg_budget':all(n['budget_pass'] for n in cases),
      'human_visual_review':'PENDING','full_character_golden':'HOLD','production_deployment':'UNCHANGED'}
    all_artifacts=sorted(p.name for p in out.iterdir() if p.is_file())
    report['artifact_sha256']={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in all_artifacts}
    (out/'sa1050_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raden',type=Path,required=True);p.add_argument('--gc001',type=Path,required=True)
    p.add_argument('--raden-svg',type=Path,required=True);p.add_argument('--gc001-svg',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=evaluate(a.raden,a.gc001,a.raden_svg,a.gc001_svg,a.out)
    print(json.dumps({'stage':r['stage'],'cases':{k:{'face':v['signed_source_original_vs_svg_face'],
        'foreground_champion':v['original_source_foreground_mae_champion'],
        'foreground_prototype':v['original_source_foreground_mae_prototype'],
        'vertices':v['expanded_vertex_count_prototype'],'budget':v['hard_budget'],
        'budget_pass':v['budget_pass'],
        'applied_regions':[k for k,z in v['material_details'].items() if z['accepted']]}
        for k,v in r['cases'].items()}},indent=2))
