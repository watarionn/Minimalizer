"""SA10.57: source-signed faceless owner-boundary guard and vertex-neutral material edge search.

Research only. No new anatomy or pixels. Stage04 face, both arms, source owner masks,
owner ordering, and outer silhouette band are exact compositor guards. Adjust only
existing SA10.56 source-observed material contour coordinates, under true budgets.
"""
from __future__ import annotations
import argparse,copy,hashlib,io,json,re,sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import cv2
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1056_faceless_material_reallocation as prior

NS=prior.NS
CASES=('Raden','GC001')
BASE_SHA={'Raden':'18474c41978f257ebf605040de4cfe2c532f6cc5f171b69089d8f48d921d349d',
          'GC001':'858080f4a738f41cade641fa24bf6414726f2bc9ce1b364f02400d9e0f37ed7e'}
CHROMIUM_SHA={'Raden':'94a44b2b931655a2a2d23f3ec4763c8cd700934184912de019d9dc2ac0e63dce',
              'GC001':'5f841e720cd621fbb22ed30cae8e5d05abd2f9e7a22a0ed2ec1ead2fe1535cdb'}
BASE_VERT={'Raden':1409,'GC001':1873}
DIRS=((-1,0),(1,0),(0,-1),(0,1))
RE_CORD=re.compile(r'(-?\d+)\s+(-?\d+)')
ROLE_ORDER=('hair','major_clothing','torso','lower_body')


def signed_case(name,root,svg_path):
    if name not in CASES:raise ValueError('Unknown signed test case')
    if prior.sign(svg_path)!=BASE_SHA[name]:raise ValueError('SA1056_SIGNED_SVG_SHA_MISMATCH')
    data=prior.previous.previous.prev.last.prior.prior.dual.load_case(name,root)
    case=prior.previous.previous.prev.last.prior.prior.opt.load_case(name,root)
    svg=ET.parse(svg_path).getroot()
    prior.previous.audit_default_faceless(svg)
    if prior.actual_svg_vertices(svg,case)!=BASE_VERT[name]:raise ValueError('SA1056_DEPLOYED_VERTEX_COUNT_MISMATCH')
    return data,case,svg


def inventory(svg):
    """Exact immutable signed geometry except coordinates of SA10.56 source-only paths."""
    paths=[]
    for n in svg.iter(NS+'path'):
        if n.get('data-sa1056-material'):
            coords=RE_CORD.findall(n.get('d',''))
            paths.append((n.get('data-sa1056-material'),n.get('fill'),len(coords),
                prior.previous.previous.prev.last.prior.prior.shared.path_vertices(n.get('d',''))))
    return {'protected':prior.protected_inventory(svg),'material_paths':paths,
            'background_and_owner_order':tuple(n.get('data-owner-index') for n in svg if n.get('data-owner-index') is not None),
            'owner_masks':tuple(ET.tostring(m,encoding='unicode') for m in svg.iter(NS+'mask'))}


def owner_topology(case,visible):
    """Signed owner-mask adjacency evidence, not a claim about correct segmentation."""
    roles={f'sa1041-owner-{i}':p['source_mask_owner'] for i,p in enumerate(case['records'])}
    keys=sorted(visible)
    coverage=np.zeros(next(iter(visible.values())).shape,dtype=np.uint8)
    for k in keys:coverage+=visible[k].astype(np.uint8)
    if np.any(coverage>1):raise AssertionError('VISIBLE_SOURCE_OWNER_OVERLAP')
    ker=np.ones((3,3),np.uint8);adj=[]
    for i,a in enumerate(keys):
        aa=cv2.dilate(visible[a].astype(np.uint8),ker).astype(bool)
        for b in keys[i+1:]:
            if np.any(aa & visible[b]):adj.append([roles[a],roles[b]])
    return {'owner_count':len(keys),'role_pixel_counts':{roles[k]:int(visible[k].sum()) for k in keys},
            'source_visible_owner_overlap_pixels':int(np.count_nonzero(coverage>1)),
            'adjacency_pairs':adj}


def guard_masks(data,case):
    face=data['masks']['face'];arms=data['masks']['left_arm']|data['masks']['right_arm']
    visible,foreground=prior.foreground_masks(case,face)
    # Two-pixel perimeter of the *signed* source-visible silhouette cannot change.
    ker=np.ones((3,3),np.uint8)
    erosion=cv2.erode(foreground.astype(np.uint8),ker,iterations=2).astype(bool)
    dilated=cv2.dilate(foreground.astype(np.uint8),ker,iterations=2).astype(bool)
    perimeter=dilated&~erosion
    # Signed source part-to-part interfaces likewise must stay visually identical.
    internal=np.zeros_like(face)
    keys=sorted(visible)
    for i,a in enumerate(keys):
        expand=cv2.dilate(visible[a].astype(np.uint8),ker,iterations=1).astype(bool)
        for b in keys[i+1:]:internal|=expand & visible[b]
    # This guard conservatively freezes interfaces rather than claiming to repair them.
    frozen=face|arms|(~foreground)|perimeter|internal
    return visible,foreground,frozen,{'perimeter_pixel_count':int(perimeter.sum()),'interface_pixel_count':int(internal.sum()),
             'faceless_signed_face_pixels':int(face.sum()),'signed_arms_pixels':int(arms.sum())}


def feature_roi(photo,owner):
    gray=cv2.cvtColor(photo,cv2.COLOR_RGB2GRAY)
    dx=cv2.Sobel(gray,cv2.CV_32F,1,0,ksize=3)
    dy=cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3)
    strength=cv2.magnitude(dx,dy)
    return (strength>128)&owner,strength


def select_vertices(svg,role,allowed,photo,limit=4):
    node=next((p for p in svg.iter(NS+'path') if p.get('data-sa1056-material')==role),None)
    if node is None:raise ValueError('Missing signed observed material path '+role)
    _,gradient=feature_roi(photo,allowed)
    tuples=[]
    for i,m in enumerate(RE_CORD.finditer(node.get('d',''))):
        x,y=int(m[1]),int(m[2]); x0=max(0,x-2);x1=min(340,x+3);y0=max(0,y-2);y1=min(340,y+3)
        if y0>=y1 or x0>=x1 or not allowed[y0:y1,x0:x1].any():continue
        grad=float(np.max(gradient[y0:y1,x0:x1]*allowed[y0:y1,x0:x1]))
        tuples.append((-grad,i,x,y))
    return node,sorted(tuples)[:limit]


def png_sha(img):
    buf=io.BytesIO();Image.fromarray(img).save(buf,format='PNG');return hashlib.sha256(buf.getvalue()).hexdigest()


def chromium(page,svg):return prior.actual_chromium(page,svg)


def run_case(name,source,svg_file,out,page):
    data,case,svg=signed_case(name,source,svg_file)
    original=chromium(page,svg)
    if png_sha(original)!=CHROMIUM_SHA[name]:raise AssertionError('SIGNED_SA1056_CHROMIUM_REPLAY_CHANGED')
    photo=data['photo'];visible,fg,frozen,guard=guard_masks(data,case)
    topo=owner_topology(case,visible)
    initial_inventory=inventory(svg)
    start_global=prior.score(original,photo,fg)
    current=original;overall=start_global;accepted=[];trials=0
    for role in ROLE_ORDER:
        idx=next(i for i,p in enumerate(case['records']) if p['source_mask_owner']==role)
        owner=visible[f'sa1041-owner-{idx}']
        can_update=owner&~frozen
        if not np.any(can_update):continue
        # The signed unmodified owner is the source measurement authority.
        source_edge,grad=feature_roi(photo,owner)
        starting_edge=prior.score(current,photo,source_edge) if np.any(source_edge) else None
        start_owner=prior.score(current,photo,owner)
        node,vertices=select_vertices(svg,role,can_update,photo,limit=5)
        for _,vertex_index,x,y in vertices:
            old=node.get('d','');matches=list(RE_CORD.finditer(old))
            if vertex_index>=len(matches):raise AssertionError('Material SVG unexpectedly changed')
            match=matches[vertex_index];cx,cy=int(match[1]),int(match[2]);winner=None
            for dx,dy in DIRS:
                node.set('d',old[:match.start()]+f'{cx+dx} {cy+dy}'+old[match.end():])
                frame=chromium(page,svg);trials+=1
                if not np.array_equal(frame[frozen],original[frozen]):continue
                gain=prior.score(frame,photo,fg)
                if gain>=overall-1e-8:continue
                own=prior.score(frame,photo,owner)
                if own>=prior.score(current,photo,owner)-1e-8:continue
                edge=prior.score(frame,photo,source_edge) if starting_edge is not None else None
                if edge is not None and edge>prior.score(current,photo,source_edge)+1e-7:continue
                rank=(gain,own,dx,dy)
                if winner is None or rank<winner[0]:winner=(rank,node.get('d'),frame,own,edge,dx,dy)
            if winner is None:node.set('d',old)
            else:
                _,path,current,owner_score,edge_score,dx,dy=winner
                node.set('d',path);overall=prior.score(current,photo,fg)
                accepted.append({'role':role,'vertex_ordinal':vertex_index,'delta':[dx,dy],
                  'global_source_mae_after':round(overall,6),'owner_mae_after':round(owner_score,6),
                  'source_edge_mae_after':round(edge_score,6) if edge_score is not None else None})
    result=chromium(page,svg)
    if not np.array_equal(result,current):raise AssertionError('CHROMIUM_NONDETERMINISM')
    if not np.array_equal(result[frozen],original[frozen]):raise AssertionError('SIGNED_EXTERNAL_OR_PART_BOUNDARY_CHANGED')
    if inventory(svg)!=initial_inventory:raise AssertionError('MASK_PALETTE_SHAPE_OR_VERTEX_INVENTORY_CHANGED')
    prior.previous.audit_default_faceless(svg)
    verts=prior.actual_svg_vertices(svg,case)
    if verts!=BASE_VERT[name] or verts>prior.CAP[name]:raise AssertionError('VERTEX_BUDGET_OR_TOPOLOGY_CHANGED')
    if overall>start_global+1e-8:raise AssertionError('PHOTO_SOURCE_FIDELITY_REGRESSED')
    k=name.lower();Image.fromarray(original).save(out/f'{k}_sa1056_baseline.png');Image.fromarray(result).save(out/f'{k}_structure_guarded.png')
    (out/f'{k}_structure_guarded.svg').write_text(ET.tostring(svg,encoding='unicode'),'utf-8')
    return {'case':name,'signed_input_sha256':case['source_input_sha256'],'input_svg_sha256':prior.sign(svg_file),
       'baseline_render_sha256':CHROMIUM_SHA[name],'expanded_vertices':verts,'budget':prior.CAP[name],
       'source_visible_foreground_rgb_mae_before':round(start_global,6),
       'source_visible_foreground_rgb_mae_after':round(overall,6),
       'source_owner_topology':topo,'protected_pixels':guard,'candidate_chromium_renders':trials,
       'accepted_existing_vertex_moves':accepted,'fully_protected_pixel_changes':0,
       'masks_face_arms_and_source_role_colors_unchanged':True,'standard_face_microfeatures_off':True,
       'outer_silhouette_edge_pixel_changes':0,'owner_interface_pixel_changes':0,
       'silhouette_source_identity_certified':False,'historical_stage8_source_ring_gate':'FAIL',
       'human_visual_review':'PENDING','golden':'HOLD','production':'UNCHANGED'}


def evaluate(raden_root,gc_root,raden_svg,gc_svg,out,chromium_binary='/usr/bin/chromium'):
    roots=[Path(raden_root).resolve(),Path(gc_root).resolve()]
    bases=[Path(raden_svg).resolve(),Path(gc_svg).resolve()];out=Path(out).resolve()
    if roots[0]==roots[1] or any(out==r or out in r.parents or r in out.parents for r in roots):raise ValueError('SIGNED_INPUT_OUTPUT_NOT_SEPARATE')
    if any(out==s or out in s.parents or s in out.parents for s in bases):raise ValueError('SIGNED_SVG_MUST_NOT_BE_OVERWRITTEN')
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pl:
        browser=pl.chromium.launch(executable_path=chromium_binary,headless=True,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            cases=[run_case(n,r,s,out,page) for n,r,s in zip(CASES,roots,bases)]
            browser_version=browser.version
        finally:browser.close()
    board=Image.new('RGB',(1020,760),(246,246,244));d=ImageDraw.Draw(board)
    for row,name in enumerate(CASES):
        original=Image.open(roots[row]/prior.ORIGINAL_SOURCE[name]).convert('RGB')
        before=Image.open(out/f'{name.lower()}_sa1056_baseline.png').convert('RGB')
        after=Image.open(out/f'{name.lower()}_structure_guarded.png').convert('RGB')
        for col,(image,heading) in enumerate(((original,'SIGNED ORIGINAL'),(before,'SA10.56'),(after,'SA10.57 STRUCTURE-GUARDED'))):
            board.paste(image,(340*col,380*row+40));d.text((340*col+6,380*row+12),f'{name} / {heading}',fill=(20,20,20))
    board.save(out/'sa1057_two_case_structure_board.png')
    report={'stage':'SA10.57','schema':'signed-visible-structure-vertex-neutral-faceless-gate-v1',
        'chromium':browser_version,'cases':{a['case']:a for a in cases},
        'two_case_signed_masks_source_owner_adjacency_preserved':True,
        'two_case_outer_silhouette_and_arm_pixel_exact':True,
        'two_case_faceless_default_and_vertex_budget_pass':True,
        'any_source_edge_improvement':any(a['accepted_existing_vertex_moves'] for a in cases),
        'historical_stage8_source_ring_gate':'FAIL','full_character_golden':'HOLD',
        'human_visual_review':'PENDING','production_deployment':'UNCHANGED'}
    report['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()}
    (out/'sa1057_metrics.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n','utf-8')
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for field in ('raden','gc001','raden_svg','gc001_svg','out'):ap.add_argument('--'+field.replace('_','-'),type=Path,required=True)
    a=ap.parse_args()
    rep=evaluate(a.raden,a.gc001,a.raden_svg,a.gc001_svg,a.out)
    for n,v in rep['cases'].items():print(n,v['source_visible_foreground_rgb_mae_before'],v['source_visible_foreground_rgb_mae_after'],len(v['accepted_existing_vertex_moves']),v['candidate_chromium_renders'])
