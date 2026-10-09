"""SA10.42: source-signed SVG owner/protection raster parity, research only.

Original Stage8 OpenCV rings and signed Stage04 masks are never modified.
The pixel-cell rectangle proof is deliberately NOT a production renderer:
every rectangle vertex is counted and product complexity remains NO-GO.
"""
from __future__ import annotations
import argparse
import copy
from hashlib import sha256
import io
import json
from pathlib import Path
import shutil
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from PIL import Image

NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', 'http://www.w3.org/2000/svg')
SIGNED = {
    'Raden_source.png': 'd9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00',
    'phase8_adaptive_source_contour_research.json': 'be6001f3607466617a4c2db92cdc92ad81296a403cdeeef009ac0628dc149b5f',
    'signed_full_opencv_reference.png': '749fc372e293de4a839b13dc2196d5576e98d2f5c784d73449ca2f96ab074a92',
    'full_character_vector.svg': 'ecc48fcf20a85b584a421bbd7f485c40c1c0bab6cd536049a73a61d4d7ac97db',
    'signed_face_stage04_mask.png': 'a192ef05aa3ae2cc42e249cb311349d82dd5e4115c1aa438c7a3205ba0d4ec2f',
    'signed_left_arm_stage04_mask.png': '6872bd01fb350b5ce2b5ec09b44feaa2c46cc442aa327cccc0e8681db33b404e',
    'signed_right_arm_stage04_mask.png': '79829023fd293e16a619dbc7b84736ca3d2ac172ac442c04d35bc1a3eae13025',
}
OWNER_ORDER = ('torso', 'hair', 'right_arm', 'left_arm', 'unknown', 'face',
               'major_clothing', 'lower_body', 'head', 'accessory_or_held_object', 'neck')


def verify_inputs(root: Path) -> None:
    for name, digest in SIGNED.items():
        path = root/name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen signed input changed: '+name)


def source_ring_mask(rings: list[dict], size=(340, 340)) -> np.ndarray:
    contours = []
    for _, item in sorted(enumerate(rings), key=lambda x: (x[1]['depth'], x[0])):
        depth = item['depth']
        if not isinstance(depth, int) or depth < 0 or item['role'] != ('hole' if depth%2 else 'fill'):
            raise ValueError('Signed ring depth and fill role disagree')
        points = np.asarray(item['points'], dtype=np.float64)
        if points.ndim != 2 or points.shape[1] != 2 or not len(points) or not np.isfinite(points).all():
            raise ValueError('Invalid original ring points')
        contours.append(np.rint(points).astype(np.int32).reshape(-1, 1, 2))
    if not contours:
        raise ValueError('Signed source owner has no rings')
    raster = np.zeros(size, np.uint8)
    cv2.drawContours(raster, contours, -1, 255, thickness=cv2.FILLED, lineType=cv2.LINE_8)
    return raster > 0


def merged_pixel_rectangles(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    binary = np.asarray(mask)
    if binary.ndim != 2 or binary.dtype != np.bool_:
        raise ValueError('Original source mask must be binary')
    active, rects = {}, []
    for y, row in enumerate(binary):
        run_ends = np.flatnonzero(np.diff(np.r_[False, row, False].astype(np.int8)))
        following = {}
        for x0, x1 in zip(run_ends[::2], run_ends[1::2]):
            key = (int(x0), int(x1))
            following[key] = active.get(key, y)
        for (x0, x1), start in active.items():
            if (x0, x1) not in following:
                rects.append((x0, start, x1-x0, y-start))
        active = following
    for (x0, x1), start in active.items():
        rects.append((x0, start, x1-x0, binary.shape[0]-start))
    return rects


def replace_signed_mask(root: ET.Element, mask_id: str, pixels: np.ndarray, inverse=False) -> int:
    nodes = [el for el in root.iter(NS+'mask') if el.get('id') == mask_id]
    if len(nodes) != 1 or pixels.ndim != 2 or not np.any(pixels):
        raise ValueError('Exactly one signed mask with nonempty geometry required')
    node = nodes[0]
    height, width = pixels.shape
    if node.get('width') != str(width) or node.get('height') != str(height):
        raise ValueError('Original SVG viewport differs from signed mask')
    for el in list(node):
        node.remove(el)
    ET.SubElement(node, NS+'rect', {'x':'0', 'y':'0', 'width':str(width),
        'height':str(height), 'fill':'#ffffff' if inverse else '#000000'})
    rects = merged_pixel_rectangles(pixels)
    for x, y, w, h in rects:
        ET.SubElement(node, NS+'rect', {'x':str(x), 'y':str(y),
            'width':str(w), 'height':str(h),
            'fill':'#000000' if inverse else '#ffffff',
            'shape-rendering':'crispEdges'})
    return len(rects)


def isolated_svg(original: ET.Element, mask_id: str) -> ET.Element:
    root = copy.deepcopy(original)
    for el in list(root):
        if el.tag != NS+'defs':
            root.remove(el)
    width, height = root.get('width'), root.get('height')
    ET.SubElement(root, NS+'rect', {'width':width,'height':height,'fill':'#ffffff'})
    ET.SubElement(root, NS+'rect', {'width':width,'height':height,
        'fill':'#000000','mask':f'url(#{mask_id})'})
    return root


def browser_png(page, element: ET.Element) -> np.ndarray:
    svg = ET.tostring(element, encoding='unicode')
    if any(token in svg for token in ('<image', 'data:image', 'base64,', '<foreignObject')):
        raise ValueError('Raster embedding and external objects are prohibited')
    page.set_content('<style>html,body{margin:0;padding:0}svg{display:block}</style>'+svg)
    return np.asarray(Image.open(io.BytesIO(page.locator('svg').screenshot())).convert('RGB')).copy()


def rgb_mismatches(expected: np.ndarray, actual: np.ndarray, role_masks: dict) -> dict:
    if expected.shape != actual.shape:
        raise ValueError('Source reference and real browser canvas differ')
    mismatched = np.any(expected != actual, axis=2)
    return {'full_scene': int(mismatched.sum()),
        'protected_parts': {role:int(np.count_nonzero(mismatched & region))
            for role, region in role_masks.items()},
        'rgb_mae':round(float(np.mean(np.abs(expected.astype(np.int16)-actual.astype(np.int16)))),6)}


def evaluate(root: Path, output: Path, chromium: str|None=None) -> dict:
    from playwright.sync_api import sync_playwright
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents or output in root.parents:
        raise ValueError('Never overwrite original signed input authorities')
    verify_inputs(root)
    scene = json.loads((root/'phase8_adaptive_source_contour_research.json').read_text('utf-8'))
    if scene.get('original_source_sha256') != SIGNED['Raden_source.png']:
        raise ValueError('Stage8 image provenance differs')
    owners = scene['primitives_back_to_front']
    if len(owners) != 11 or tuple(x['source_mask_owner'] for x in owners) != OWNER_ORDER:
        raise ValueError('Source owner order or count changed')
    svg = ET.parse(root/'full_character_vector.svg').getroot()
    if any(node.tag in (NS+'image', NS+'foreignObject') for node in svg.iter()):
        raise ValueError('Original SVG embeds raster or external object')
    masks = {name:np.asarray(Image.open(root/f'signed_{name}_stage04_mask.png').convert('L'))>0
             for name in ('face','left_arm','right_arm')}
    reference = np.asarray(Image.open(root/'signed_full_opencv_reference.png').convert('RGB'))
    source = np.asarray(Image.open(root/'Raden_source.png').convert('RGBA'))
    if source.shape[:2] != (340,340) or reference.shape != (340,340,3) or any(m.shape != (340,340) for m in masks.values()):
        raise ValueError('Original source width/height incorrect')
    protected = masks['face'] | masks['left_arm'] | masks['right_arm']
    exact_owners = {name:source_ring_mask(record['parameters']['rings'])
                    for name, record in ((p['source_mask_owner'],p) for p in owners)}
    repairs = [
        ('sa1041-original-face-guard',masks['face'],False),
        ('sa1041-protected-clear',protected,True),
        ('sa1041-owner-2',exact_owners['right_arm'],False),
        ('sa1041-owner-3',exact_owners['left_arm'],False),
    ]
    modified = copy.deepcopy(svg)
    counts = {mask_id:replace_signed_mask(modified,mask_id,mask,inverse)
              for mask_id,mask,inverse in repairs}
    output.mkdir(parents=True, exist_ok=True)
    (output/'repaired_research.svg').write_text(ET.tostring(modified,encoding='unicode'),'utf-8')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
            executable_path=chromium or shutil.which('chromium') or shutil.which('google-chrome'),
            args=['--no-sandbox','--disable-gpu'])
        try:
            page = browser.new_page(viewport={'width':340,'height':340},device_scale_factor=1)
            before, after = browser_png(page,svg), browser_png(page,modified)
            binary = {}
            for mask_id,mask,inverse in repairs:
                old = browser_png(page,isolated_svg(svg,mask_id))[...,0]<128
                new = browser_png(page,isolated_svg(modified,mask_id))[...,0]<128
                expected = ~mask if inverse else mask
                binary[mask_id] = {
                    'before':int(np.count_nonzero(old!=expected)),
                    'after':int(np.count_nonzero(new!=expected)),
                    'source_run_rectangles':counts[mask_id],
                    'rectangle_vertices':4*counts[mask_id],
                }
            version=browser.version
        finally:
            browser.close()
    baseline=rgb_mismatches(reference,before,masks)
    repaired=rgb_mismatches(reference,after,masks)
    if any(v['after'] for v in binary.values()) or any(repaired['protected_parts'].values()) or repaired['full_scene']>=baseline['full_scene']:
        raise AssertionError('Research-only source-protected pixel parity gate FAILED')
    Image.fromarray(before).save(output/'before_full_scene.png')
    Image.fromarray(after).save(output/'after_full_scene.png')
    comparison=np.full((384,1020,3),245,np.uint8)
    for i,im in enumerate((reference,before,after)):comparison[44:,i*340:(i+1)*340]=im
    for i,title in enumerate(('SIGNED OPENCV','OLD CHROME SVG','EXACT MASK PROBE')):
        cv2.putText(comparison,title,(i*340+5,28),cv2.FONT_HERSHEY_SIMPLEX,.47,(20,20,20),1,cv2.LINE_AA)
    Image.fromarray(comparison).save(output/'before_after_comparison.png')
    source_vertices=sum(len(r['points']) for p in owners for r in p['parameters']['rings'])
    report={
        'status':'PROTECTED_SOURCE_MASK_PARITY_RESEARCH_PASS','case':'Juufuutei-Raden_stylecal_source',
        'chromium_version':version,'signed_input_sha256':SIGNED,
        'baseline':baseline,'repaired':repaired,'mask_binary_raster_probes':binary,
        'original_source_ring_vertices':source_vertices,'original_vertex_budget':1412,
        'research_pixel_cell_vertices':4*sum(counts.values()),
        'original_vertex_budget_pass':source_vertices<=1412,
        'full_character_browser_parity_pass':False,'full_character_golden_pass':False,
        'production_changed':False,'generative_fill_used':False,
        'source_original_modified':False,
        'requires_budget_preserving_contour_compaction':True,
        'next':'Find lower-vertex exact source contour strategy; isolate hair and unknown owner; retest full character.',
    }
    report['output_sha256']={f.name:sha256(f.read_bytes()).hexdigest()
                             for f in sorted(output.iterdir()) if f.suffix in ('.png','.svg')}
    (output/'sa1042_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    return report


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--chromium')
    args=parser.parse_args()
    print(json.dumps(evaluate(args.root,args.out,args.chromium),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
