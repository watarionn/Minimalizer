"""SA10.43 independent browser raster vs SVG vertex-budget Pareto research.

No source image embedding, no generative fill, no deployed renderer edits.
Stage04 / 08 / 41 signed artifacts are immutable and validated by SHA.
All path coordinate occurrences (including masks and structural support) count
against the original unchanged 1,412-vertex hard ceiling.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', 'http://www.w3.org/2000/svg')
SIZE = (340, 340)
BUDGET = 1412
EXTRAS = 12  # signed Raden Stage9 plane vertices; Stage37 apparel = 0
EPSILONS = (0.5, 0.75, 1.0, 1.25, 1.5)
SHA = {
    'Raden_source.png': 'd9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00',
    'phase8_adaptive_source_contour_research.json': 'be6001f3607466617a4c2db92cdc92ad81296a403cdeeef009ac0628dc149b5f',
    'signed_full_opencv_reference.png': '749fc372e293de4a839b13dc2196d5576e98d2f5c784d73449ca2f96ab074a92',
    'full_character_vector.svg': 'ecc48fcf20a85b584a421bbd7f485c40c1c0bab6cd536049a73a61d4d7ac97db',
    'signed_face_stage04_mask.png': 'a192ef05aa3ae2cc42e249cb311349d82dd5e4115c1aa438c7a3205ba0d4ec2f',
    'signed_left_arm_stage04_mask.png': '6872bd01fb350b5ce2b5ec09b44feaa2c46cc442aa327cccc0e8681db33b404e',
    'signed_right_arm_stage04_mask.png': '79829023fd293e16a619dbc7b84736ca3d2ac172ac442c04d35bc1a3eae13025',
}
ORDER = ('torso', 'hair', 'right_arm', 'left_arm', 'unknown', 'face',
         'major_clothing', 'lower_body', 'head', 'accessory_or_held_object', 'neck')
DIRECTION = ((1, 0), (0, 1), (-1, 0), (0, -1))
TURN_RANK = (1, 0, 3, 2)  # right, straight, left, back


def frozen(root: Path) -> None:
    for filename, expected in SHA.items():
        path = root / filename
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Missing / altered signed authority: ' + filename)


def source_ring_mask(rings: list[dict]) -> np.ndarray:
    if not rings:
        raise ValueError('Source geometry must have rings')
    contours = []
    for i, r in sorted(enumerate(rings), key=lambda it: (it[1]['depth'], it[0])):
        depth = r['depth']
        pts = np.asarray(r['points'], dtype=np.float64)
        if not isinstance(depth, int) or depth < 0 or r['role'] != ('hole' if depth % 2 else 'fill'):
            raise ValueError('Source ring hierarchy invalid')
        if pts.ndim != 2 or pts.shape[1] != 2 or not len(pts) or not np.isfinite(pts).all():
            raise ValueError('Invalid source contour')
        contours.append(np.rint(pts).astype(np.int32).reshape(-1, 1, 2))
    bitmap = np.zeros(SIZE[::-1], np.uint8)
    cv2.drawContours(bitmap, contours, -1, 255, cv2.FILLED, lineType=cv2.LINE_8)
    return bitmap > 0


def pixel_edge_loops(pixels: np.ndarray) -> list[list[tuple[int, int]]]:
    """Deterministic directed pixel-square boundary; right-turn tie for diagonal contacts.

    A topological loop owns a literal visible pixel union. Pixel-edge locations
    are derived from frozen source masks; no image colors are reconstructed.
    """
    mask = np.asarray(pixels)
    if mask.shape != SIZE[::-1] or mask.dtype != bool:
        raise ValueError('Signed mask must be 340x340 binary')
    h, w = mask.shape
    graph = defaultdict(list)
    def add(a, b):
        graph[a].append(b)
    for y, x in np.argwhere(mask):
        x, y = int(x), int(y)
        if y == 0 or not mask[y-1, x]: add((x,y),(x+1,y))
        if x == w-1 or not mask[y,x+1]: add((x+1,y),(x+1,y+1))
        if y == h-1 or not mask[y+1,x]: add((x+1,y+1),(x,y+1))
        if x == 0 or not mask[y,x-1]: add((x,y+1),(x,y))
    n_edges = sum(len(v) for v in graph.values())
    loops = []
    while graph:
        start = min(graph)
        here = start
        prev = None
        pts = [here]
        for _ in range(n_edges + 1):
            choices = graph[here]
            if prev is None:
                end = min(choices)
            else:
                prior = DIRECTION.index((here[0]-prev[0], here[1]-prev[1]))
                def rank(other):
                    current = DIRECTION.index((other[0]-here[0],other[1]-here[1]))
                    return TURN_RANK.index((current-prior)%4), other
                end = min(choices, key=rank)
            choices.remove(end)
            if not choices:
                del graph[here]
            prev, here = here, end
            pts.append(here)
            if here == start:
                break
        else:
            raise AssertionError('Source pixel-edge loop failed to close')
        points = pts[:-1]
        turns = []
        for i, point in enumerate(points):
            a = points[i-1]
            b = points[(i+1)%len(points)]
            if (point[0]-a[0],point[1]-a[1]) != (b[0]-point[0],b[1]-point[1]):
                turns.append(point)
        if len(turns) < 4:
            raise AssertionError('Closed source boundary lost square corners')
        loops.append(turns)
    return loops


def boundary_path(loops: list[list[tuple[int,int]]], epsilon: float) -> tuple[str,int]:
    if epsilon not in EPSILONS:
        raise ValueError('Unreviewed boundary approximation')
    segments = []
    total = 0
    for loop in loops:
        points = np.asarray(loop,np.float32)
        if epsilon:
            approximate = cv2.approxPolyDP(points.reshape(-1,1,2),epsilon,True).reshape(-1,2)
            if len(approximate) >= 3:
                points = approximate
        if len(points) < 3:
            raise AssertionError('Contour collapsed')
        total += len(points)
        segments.append('M ' + ' L '.join(f'{int(x)} {int(y)}' for x,y in points) + ' Z')
    return ' '.join(segments), total


def replace_svg_mask(root: ET.Element, ident: str, data: str, *, inverse=False) -> None:
    masks = [node for node in root.iter(NS+'mask') if node.get('id') == ident]
    if len(masks) != 1:
        raise ValueError('Expected one source-named SVG mask: '+ident)
    mask = masks[0]
    if mask.get('width') != '340' or mask.get('height') != '340':
        raise ValueError('Wrong protected SVG canvas')
    for el in list(mask):
        mask.remove(el)
    ET.SubElement(mask, NS+'rect', {'width':'340','height':'340',
        'fill':'#ffffff' if inverse else '#000000'})
    ET.SubElement(mask, NS+'path', {'d':data,'fill':'#000000' if inverse else '#ffffff',
        'fill-rule':'evenodd','shape-rendering':'crispEdges'})


def isolated_svg(root: ET.Element, ident: str) -> str:
    sample = copy.deepcopy(root)
    for child in list(sample):
        if child.tag != NS+'defs':sample.remove(child)
    ET.SubElement(sample,NS+'rect',{'width':'340','height':'340','fill':'#ffffff'})
    ET.SubElement(sample,NS+'rect',{'width':'340','height':'340','fill':'#000000',
        'mask':'url(#'+ident+')'})
    return ET.tostring(sample,encoding='unicode')


def chromium_rgb(page, svg: str) -> np.ndarray:
    if any(x in svg for x in ('<image','data:image','base64,','<foreignObject')):
        raise ValueError('No raster embedding or foreign objects')
    page.set_content('<style>html,body{margin:0;padding:0}svg{display:block}</style>'+svg)
    return np.asarray(Image.open(io.BytesIO(page.locator('svg').screenshot())).convert('RGB')).copy()


def metrics(a: np.ndarray, b: np.ndarray, roles: dict[str,np.ndarray]):
    diff = np.any(a!=b,axis=2)
    return {'full_rgb_mismatch':int(diff.sum()),
       'source_signed_protected':{k:int((diff & roles[k]).sum()) for k in ('face','left_arm','right_arm')},
       'rgb_mae':round(float(np.abs(a.astype(np.int16)-b.astype(np.int16)).mean()),6)}


def choose_budgeted(measured: dict, limit: int) -> dict:
    """Exploratory exact finite knapsack; weighted errors are not a release gate."""
    weights = {key:(20 if key in ('sa1041-original-face-guard', 'sa1041-protected-clear',
               'sa1041-owner-2','sa1041-owner-3','sa1041-owner-5')
               else 4 if key=='sa1041-owner-1' else 2) for key in measured}
    dp = {0:(0,())}
    for ident, options in measured.items():
        updated = {}
        for current_cost,(score,selection) in dp.items():
            for opt in options:
                cost = current_cost+opt['vertices']
                if cost>limit: continue
                trial = (score + weights[ident]*opt['binary_pixel_mismatch'], selection+(opt['epsilon'],))
                if cost not in updated or (trial[0],trial[1]) < (updated[cost][0],updated[cost][1]):
                    updated[cost]=trial
        if not updated: raise ValueError('No SVG mask combination fits original hard ceiling')
        dp = updated
    cost,(score,selected) = min(dp.items(),key=lambda x:(x[1][0],x[0],x[1][1]))
    return {'chosen_epsilons':dict(zip(measured,selected)),'mask_vertices':cost,
            'weighted_binary_error_score':score,
            'weights':weights,'decision':'EXPLORATORY_ONLY_NOT_SOURCE_EXACT'}


def run(input_root: Path, output: Path, chromium='/usr/bin/chromium') -> dict:
    input_root,output = input_root.resolve(),output.resolve()
    if input_root == output or input_root in output.parents or output in input_root.parents:
        raise ValueError('Do not overwrite signed source artifacts')
    frozen(input_root)
    scene = json.loads((input_root/'phase8_adaptive_source_contour_research.json').read_text('utf-8'))
    if scene.get('original_source_sha256') != SHA['Raden_source.png']:
        raise ValueError('Incorrect original source authority')
    owners=scene['primitives_back_to_front']
    if len(owners)!=11 or tuple(x['source_mask_owner'] for x in owners)!=ORDER:
        raise ValueError('Source z-order changed')
    root=ET.parse(input_root/'full_character_vector.svg').getroot()
    masks={f'sa1041-owner-{i}':source_ring_mask(p['parameters']['rings']) for i,p in enumerate(owners)}
    signed={key:np.asarray(Image.open(input_root/f'signed_{key}_stage04_mask.png').convert('L'))>0
           for key in ('face','left_arm','right_arm')}
    masks['sa1041-original-face-guard']=signed['face']
    masks['sa1041-protected-clear']=signed['face']|signed['left_arm']|signed['right_arm']
    reference=np.asarray(Image.open(input_root/'signed_full_opencv_reference.png').convert('RGB'))
    if reference.shape!=(340,340,3) or any(x.shape != (340,340) for x in masks.values()):
        raise ValueError('Source width and height changed')
    original_vertices=sum(len(r['points']) for part in owners for r in part['parameters']['rings'])
    if original_vertices!=2370:
        raise ValueError('Historical source contour count unexpectedly changed')
    vector={ident:pixel_edge_loops(mask) for ident,mask in masks.items()}
    versions={ident:{eps:boundary_path(loops,eps) for eps in EPSILONS} for ident,loops in vector.items()}
    output.mkdir(parents=True,exist_ok=True)
    measured={}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu'])
        try:
            page=browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            for ident,opts in versions.items():
                measured[ident]=[]
                for epsilon,(path,vertices) in opts.items():
                    temporary=copy.deepcopy(root)
                    inverse=ident=='sa1041-protected-clear'
                    replace_svg_mask(temporary,ident,path,inverse=inverse)
                    rgb=chromium_rgb(page,isolated_svg(temporary,ident))
                    expected=(~masks[ident] if inverse else masks[ident])
                    mismatch=int(np.count_nonzero((rgb[...,0]<128)!=expected))
                    measured[ident].append({'epsilon':epsilon,'vertices':vertices,
                                            'binary_pixel_mismatch':mismatch})
                    if epsilon==0.5 and mismatch:
                        raise AssertionError('Even original pixel-boundary path is not pixel-exact: '+ident)
            selected=choose_budgeted(measured,BUDGET-EXTRAS)
            proposals={
                'source_exact':{ident:0.5 for ident in masks},
                'budget_weighted':selected['chosen_epsilons'],
                'uniform_epsilon_1':{ident:1.0 for ident in masks},
            }
            results={}
            before=chromium_rgb(page,ET.tostring(root,encoding='unicode'))
            Image.fromarray(before).save(output/'original_chromium.png')
            results['original']={'metrics':metrics(reference,before,signed),
                 'geometry_vertices':original_vertices,
                 'total_vertex_occurrences':original_vertices+EXTRAS+484+110,
                 'under_original_budget':False}
            for candidate,choice in proposals.items():
                trial=copy.deepcopy(root)
                used=0
                binary_errors=0
                for ident,epsilon in choice.items():
                    path,verts=versions[ident][epsilon]
                    used+=verts
                    binary_errors+=next(x['binary_pixel_mismatch'] for x in measured[ident] if x['epsilon']==epsilon)
                    replace_svg_mask(trial,ident,path,inverse=(ident=='sa1041-protected-clear'))
                xml=ET.tostring(trial,encoding='unicode')
                (output/f'{candidate}.svg').write_text(xml,'utf-8')
                rgb=chromium_rgb(page,xml)
                Image.fromarray(rgb).save(output/f'{candidate}.png')
                results[candidate]={
                    'metrics':metrics(reference,rgb,signed),
                    'all_owner_and_protected_binary_mismatches':binary_errors,
                    'mask_vertex_occurrences':used,
                    'stage9_vertices':EXTRAS,
                    'total_vertex_occurrences':used+EXTRAS,
                    'under_original_budget':used+EXTRAS<=BUDGET,
                    'epsilons':choice,
                }
            chrome_version=browser.version
        finally:
            browser.close()
    # Stage8 source owner budget already fails, even if rebuilt SVG mask subpaths pass.
    # Reconstructed geometry must never be misrepresented as product golden.
    if results['source_exact']['all_owner_and_protected_binary_mismatches'] or results['source_exact']['under_original_budget']:
        raise AssertionError('Exact source mask / strict budget gate invalid')
    if not results['budget_weighted']['under_original_budget']:
        raise AssertionError('Weighted research candidate exceeded budget')
    panels=[('OPENCV SIGNED',reference),('SVG SA10.41',before)]
    for name in ('source_exact','budget_weighted','uniform_epsilon_1'):
        panels.append((name.upper(),np.asarray(Image.open(output/f'{name}.png').convert('RGB'))))
    art=Image.new('RGB',(340*len(panels),380),(245,245,243))
    pen=ImageDraw.Draw(art)
    for i,(name,im) in enumerate(panels):
        art.paste(Image.fromarray(im),(i*340,40))
        pen.text((i*340+10,12),name,fill=(25,25,25))
    art.save(output/'sa1043_five_way.png')
    report={
        'stage':'SA10.43','case':'Juufuutei-Raden_stylecal_source',
        'schema':'sa1043-independent-pixel-edge-svg-budget-pareto-v1',
        'status':'SOURCE_EXACT_BROWSER_PARITY_PASS_BUDGET_AND_GOLDEN_HOLD',
        'original_source_sha256':SHA,'chromium_version':chrome_version,
        'original_budget_limit':BUDGET,'original_source_ring_vertices':original_vertices,
        'all_masks_have_true_browser_pixel_exact_mode':True,
        'per_mask_epsilon_sweep':measured,
        'budget_candidate_selection':selected,'research_candidates':results,
        'face_and_both_arms_protection_require_zero_binary_mismatch':True,
        'full_character_golden_pass':False,'production_changed':False,
        'source_generation_used':False,'no_raster_svg_embedding':True,
        'global_silhouette_full_source_certified':False,
        'next':'Seek shared topological geometry / alternate vertex accounting only with explicit governance; focus on source owned budget-constrained positive cases, no promotion',
    }
    report['output_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest()
           for f in sorted(output.glob('*')) if f.suffix.lower() in ('.png','.svg')}
    (output/'sa1043_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--chromium',default='/usr/bin/chromium')
    a=ap.parse_args()
    report=run(a.root,a.out,a.chromium)
    print(json.dumps({'status':report['status'],'candidates':{k:{'geometry':v['total_vertex_occurrences'],
      'rgb_mismatch':v['metrics']['full_rgb_mismatch'],'protected':v['metrics']['source_signed_protected'],
      'mask_binary_mismatches':v.get('all_owner_and_protected_binary_mismatches')}
      for k,v in report['research_candidates'].items()}},indent=2))

if __name__=='__main__':main()
