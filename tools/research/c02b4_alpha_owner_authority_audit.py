"""Read-only C02b4: source alpha versus border-connected RGB owner evidence.

Never modifies source, Stage04, Stage08, or any release artifacts. Alpha says
whether a source pixel is visible, NOT which semantic part owns that pixel.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from io import BytesIO
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

PINS = {
    'GC001': {
        'source': '75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e',
        'stage8': '7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08',
    },
    'Raden': {
        'source': 'd9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00',
        'stage8': 'be6001f3607466617a4c2db92cdc92ad81296a403cdeeef009ac0628dc149b5f',
    },
}
SNAP_SHA = '89286cb1e8cf2003f02ec2dbab2a80dcf3da26b902123255a9cc17767855e434'
PARTS = ('right_arm', 'left_arm', 'hair', 'major_clothing', 'face')

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def pinned_bytes(path: Path, expected: str) -> bytes:
    raw = Path(path).read_bytes()
    if sha(raw) != expected:
        raise ValueError('SIGNED_INPUT_SHA_FAIL')
    return raw

def read_source(path: Path, case: str) -> np.ndarray:
    raw = pinned_bytes(path, PINS[case]['source'])
    rgba = np.asarray(Image.open(BytesIO(raw)).convert('RGBA'))
    if rgba.shape != (340, 340, 4):
        raise ValueError('SOURCE_CANVAS_FAIL')
    return rgba

def read_scene(path: Path, case: str) -> dict:
    data = json.loads(pinned_bytes(path, PINS[case]['stage8']))
    if (data.get('original_source_sha256') != PINS[case]['source']
            or data.get('research_only') is not True
            or data.get('production_authorized') is not False
            or data.get('no_new_material_or_owner') is not True):
        raise ValueError('SIGNED_STAGE8_PROVENANCE_FAIL')
    return data

def border_rgb_observer(rgba: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int], int]:
    """Exact 4-connected opaque-border RGB match, never background truth."""
    rgb, alpha = rgba[:, :, :3], rgba[:, :, 3]
    edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    edge_a = np.concatenate([alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1]])
    opaque = edge[edge_a == 255]
    if len(opaque) < 200:
        raise ValueError('BORDER_RGB_UNSUPPORTED')
    colors, counts = np.unique(opaque, axis=0, return_counts=True)
    ix = int(np.argmax(counts))
    if counts[ix] < 200:
        raise ValueError('BORDER_RGB_AMBIGUOUS')
    color = colors[ix]
    exact = np.all(rgb == color, axis=2).astype(np.uint8)
    _, labels = cv2.connectedComponents(exact, connectivity=4)
    border = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    border = border[border != 0]
    return np.isin(labels, border) & (labels != 0), tuple(map(int, color)), int(counts[ix])

def owner_mask(scene: dict, part: str) -> np.ndarray:
    records = [p for p in scene['primitives_back_to_front'] if p.get('source_mask_owner') == part]
    if len(records) != 1:
        raise ValueError('OWNER_NOT_UNIQUE:' + part)
    contours = []
    for ring in sorted(records[0]['parameters']['rings'], key=lambda r: int(r['depth'])):
        depth = int(ring['depth'])
        if ring['role'] != ('fill' if depth % 2 == 0 else 'hole'):
            raise ValueError('RING_ROLE_DEPTH_MISMATCH')
        pts = np.asarray(ring['points'], dtype=float)
        if pts.ndim != 2 or pts.shape[1] != 2 or not len(pts) or not np.isfinite(pts).all():
            raise ValueError('BAD_RING_POINTS')
        contours.append(np.rint(pts).astype(np.int32).reshape(-1, 1, 2))
    canvas = np.zeros((340, 340), np.uint8)
    cv2.drawContours(canvas, contours, -1, 255, thickness=cv2.FILLED, lineType=cv2.LINE_8)
    return canvas != 0

def evidence(mask: np.ndarray, rgba: np.ndarray, connected_rgb: np.ndarray) -> dict:
    alpha = rgba[:, :, 3]
    overlap = mask & connected_rgb
    return {
        'owner_pixels': int(mask.sum()),
        'owner_on_alpha_zero': int(np.count_nonzero(mask & (alpha == 0))),
        'owner_on_alpha_partial': int(np.count_nonzero(mask & (alpha > 0) & (alpha < 255))),
        'owner_on_alpha_opaque': int(np.count_nonzero(mask & (alpha == 255))),
        'owner_on_border_connected_rgb': int(overlap.sum()),
        'rgb_overlap_alpha_zero': int(np.count_nonzero(overlap & (alpha == 0))),
        'rgb_overlap_alpha_partial': int(np.count_nonzero(overlap & (alpha > 0) & (alpha < 255))),
        'rgb_overlap_alpha_opaque': int(np.count_nonzero(overlap & (alpha == 255))),
    }

def phase04_mask_from_signed_zip(snapshot: Path, name: str) -> np.ndarray:
    with zipfile.ZipFile(BytesIO(pinned_bytes(snapshot, SNAP_SHA))) as z:
        manifest = json.loads(z.read('PRIVATE_SHA_MANIFEST.json'))
        if manifest['source_sha256'] != PINS['GC001']['source'] or manifest['promotion_authorized'] is not False:
            raise ValueError('SNAPSHOT_PROVENANCE_FAIL')
        for n, h in manifest['files'].items():
            if sha(z.read(n)) != h:
                raise ValueError('SNAPSHOT_MEMBER_SHA_FAIL')
        b = z.read('phase_04/part_masks/' + name + '.png')
    a = np.asarray(Image.open(BytesIO(b)).convert('L'))
    if a.shape != (340, 340) or not np.isin(a, (0, 255)).all():
        raise ValueError('SIGNED_MASK_NOT_BINARY')
    return a > 0

def case_audit(case: str, source: Path, scene: Path, snapshot: Path | None = None):
    rgba = read_source(source, case)
    s8 = read_scene(scene, case)
    rgb_mask, color, n = border_rgb_observer(rgba)
    owners = {part: owner_mask(s8, part) for part in PARTS}
    result = {
        'case': case,
        'source_sha256': PINS[case]['source'],
        'stage8_sha256': PINS[case]['stage8'],
        'opaque_border_rgb_anchor': color,
        'opaque_border_anchor_count': n,
        'source_alpha_zero_pixels': int(np.count_nonzero(rgba[:, :, 3] == 0)),
        'border_connected_rgb_pixels': int(rgb_mask.sum()),
        'stage8_owner_evidence': {part: evidence(owners[part], rgba, rgb_mask) for part in PARTS},
        'source_alpha_is_semantic_owner_ground_truth': False,
        'border_rgb_is_background_ground_truth': False,
        'proposed_owner_mutation': 'NONE',
    }
    if snapshot is not None:
        if case != 'GC001':
            raise ValueError('SNAPSHOT_CASE_MISMATCH')
        diff = {}
        for part in PARTS:
            current = phase04_mask_from_signed_zip(snapshot, part)
            historical = owners[part]
            diff[part] = {
                'current_phase04_pixels': int(current.sum()),
                'stage8_owner_pixels': int(historical.sum()),
                'stage8_only_pixels': int(np.count_nonzero(historical & ~current)),
                'phase04_only_pixels': int(np.count_nonzero(current & ~historical)),
                'xor_pixels': int(np.count_nonzero(current ^ historical)),
                'not_a_causal_attribution': True,
            }
        result['phase04_to_stage8_lineage_observation'] = diff
        result['phase04_snapshot_sha256'] = SNAP_SHA
    return result, rgba, owners, rgb_mask

def review_board(case: str, rgba: np.ndarray, owners: dict, rgb_mask: np.ndarray, out: Path) -> None:
    # Only private review evidence. Never place the original pixels in GitHub.
    rgb = rgba[:, :, :3].astype(np.float32)
    alpha = rgba[:, :, 3:4].astype(np.float32) / 255
    white = np.clip(rgb * alpha + 247 * (1 - alpha), 0, 255).astype(np.uint8)
    panels = [white]
    for part, color in [('right_arm', (255, 60, 135)), ('left_arm', (45, 100, 245))]:
        v = white.astype(np.float32)
        v[owners[part]] = v[owners[part]] * .55 + np.array(color) * .45
        panels.append(v.astype(np.uint8))
    v = white.astype(np.float32)
    intersect = (owners['right_arm'] | owners['left_arm']) & rgb_mask
    v[intersect] = v[intersect] * .4 + np.array((255, 0, 0)) * .6
    panels.append(v.astype(np.uint8))
    im = Image.new('RGB', (340 * 4, 380), (245, 245, 245))
    draw = ImageDraw.Draw(im)
    for i, (panel, label) in enumerate(zip(panels, ['SIGNED SOURCE', 'STAGE8 RIGHT ARM', 'STAGE8 LEFT ARM', 'ARM / BORDER RGB'])):
        im.paste(Image.fromarray(panel, 'RGB'), (i * 340, 35))
        draw.text((i * 340 + 5, 9), label, fill=(20, 20, 20))
    im.save(out / (case + '_alpha_rgb_owner_review_PRIVATE.png'))

def run(gc_source, gc_scene, raden_source, raden_scene, gc_snapshot, output: Path):
    inputs = [Path(x).resolve() for x in [gc_source, gc_scene, raden_source, raden_scene, gc_snapshot]]
    output = Path(output).resolve()
    if any(output == p or output in p.parents or p in output.parents for p in inputs):
        raise ValueError('OUTPUT_MUST_NOT_OVERWRITE_INPUTS')
    if output.exists() and any(output.iterdir()):
        raise ValueError('OUTPUT_NOT_EMPTY')
    g, gi, gm, gb = case_audit('GC001', gc_source, gc_scene, gc_snapshot)
    r, ri, rm, rb = case_audit('Raden', raden_source, raden_scene)
    result = {
        'schema': 'minimalizer_c02b4_alpha_rgb_owner_evidence_v1',
        'status': 'RESEARCH_ONLY_C02_HOLD',
        'independent_cases': [g, r],
        'finding': 'OPAQUE_RGB_BORDER_MATCH_CANNOT_BE_REMOVED_AS_BACKGROUND_FROM_COLOR_ALONE',
        'original_stage8_ring_budget': 'HOLD',
        'human_golden': 'PENDING',
        'approved18_78': 'NOT_RUN',
        'chromium': 'NOT_RUN',
        'release_authorized': False,
        'production_changed': False,
    }
    output.mkdir(parents=True, exist_ok=False) if not output.exists() else None
    review_board('GC001', gi, gm, gb, output)
    review_board('Raden', ri, rm, rb, output)
    (output / 'C02B4_ALPHA_RGB_OWNER_PRIVATE.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for k in ('gc_source', 'gc_scene', 'raden_source', 'raden_scene', 'gc_snapshot', 'output'):
        p.add_argument('--' + k.replace('_','-'), required=True, type=Path)
    a=p.parse_args()
    report=run(a.gc_source, a.gc_scene, a.raden_source, a.raden_scene, a.gc_snapshot, a.output)
    print(json.dumps(report, indent=2, ensure_ascii=False))
