"""C02b5 read-only reconciliation of two signed Phase04 revisions and Stage8.

Only establishes pixel support/provenance consistency; never assigns semantic
ownership or authorizes rendering, source edits or production release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from io import BytesIO
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from c02b4_alpha_owner_authority_audit import PINS, SNAP_SHA, read_source, read_scene, owner_mask, sha

HISTORICAL_SHA = {
    'right_arm': '4900beccaf0ca4a9ca33600339df77976a4500f1db932fcb240a41907b935b91',
    'left_arm': '49986981c02f472a888e1717205799c254b16c1bca7ef96beba2dc6b4f696b5f',
    'face': 'b4812364eaec7da9930a18ae85270d6612555d3fb3d80283efcf69b03aa6a72f',
}
PARTS=('right_arm','left_arm','face')

def signed_mask(data: bytes) -> np.ndarray:
    arr=np.asarray(Image.open(BytesIO(data)).convert('L'))
    if arr.shape!=(340,340) or not np.isin(arr,(0,255)).all():
        raise ValueError('SIGNED_MASK_BINARY_FAIL')
    return arr!=0

def read_historical(folder: Path, part: str) -> np.ndarray:
    raw=(Path(folder)/f'GC001_historical_{part}_stage04_mask.png').read_bytes()
    if sha(raw)!=HISTORICAL_SHA[part]:
        raise ValueError('HISTORICAL_MASK_SHA_FAIL')
    return signed_mask(raw)

def read_current(snapshot: Path, part: str) -> np.ndarray:
    raw=Path(snapshot).read_bytes()
    if sha(raw)!=SNAP_SHA:
        raise ValueError('CURRENT_SNAPSHOT_SHA_FAIL')
    with zipfile.ZipFile(BytesIO(raw)) as z:
        m=json.loads(z.read('PRIVATE_SHA_MANIFEST.json'))
        if m['source_sha256']!=PINS['GC001']['source'] or m['promotion_authorized'] is not False:
            raise ValueError('CURRENT_SNAPSHOT_AUTHORITY_FAIL')
        for name,digest in m['files'].items():
            if sha(z.read(name))!=digest:
                raise ValueError('CURRENT_SNAPSHOT_MEMBER_SHA_FAIL')
        return signed_mask(z.read(f'phase_04/part_masks/{part}.png'))

def support_distance(a: np.ndarray, b: np.ndarray) -> dict:
    return {'a_pixels':int(a.sum()),'b_pixels':int(b.sum()),
            'xor_pixels':int(np.count_nonzero(a^b)),
            'a_only_pixels':int(np.count_nonzero(a&~b)),
            'b_only_pixels':int(np.count_nonzero(b&~a))}

def run(source: Path, scene: Path, snapshot: Path, historical: Path, output: Path):
    paths=[Path(x).resolve() for x in (source,scene,snapshot)]
    historical=Path(historical).resolve()
    output=Path(output).resolve()
    if (any(output==p or output in p.parents or p in output.parents for p in paths)
            or output==historical or output in historical.parents):
        raise ValueError('OUTPUT_MUST_NOT_OVERWRITE_SIGNED_INPUTS')
    if output.exists() and any(output.iterdir()):
        raise ValueError('OUTPUT_NOT_EMPTY')
    rgba=read_source(source,'GC001')
    s8=read_scene(scene,'GC001')
    masks={}
    metrics={}
    for part in PARTS:
        h=read_historical(historical,part)
        c=read_current(snapshot,part)
        s=owner_mask(s8,part)
        masks[part]={'historical':h,'current':c,'stage8':s}
        metrics[part]={
            'historical_vs_current':support_distance(h,c),
            'historical_vs_stage8':support_distance(h,s),
            'current_vs_stage8':support_distance(c,s),
            'stage8_source_ref':next(p['source_evidence_refs'] for p in s8['primitives_back_to_front'] if p['source_mask_owner']==part),
        }
    result={'schema':'minimalizer-c02b5-signed-phase04-revision-lineage-v1',
            'original_source_sha256':PINS['GC001']['source'],
            'stage8_source_ring_sha256':PINS['GC001']['stage8'],
            'current_phase03_phase04_snapshot_sha256':SNAP_SHA,
            'historical_reencoded_stage04_mask_sha256':HISTORICAL_SHA,
            'parts':metrics,
            'finding':'STAGE8_LEFT_ARM_RASTER_CLOSE_TO_HISTORICAL_PHASE04_NOT_CURRENT_REVISION',
            'historical_pixel_similarity_is_not_proof_of_identical_producer_or_config':True,
            'source_mask_semantic_quality':'NOT_PROVEN',
            'candidate_promoted':False,'original_stage8_budget':'HOLD',
            'human_golden':'PENDING','release_authorized':False,'production_changed':False}
    output.mkdir(parents=True,exist_ok=True)
    # Private comparison board: original source plus three SHA-bound overlays.
    alpha=rgba[:,:,3:4].astype(float)/255
    base=np.clip(rgba[:,:,:3].astype(float)*alpha+(1-alpha)*247,0,255).astype(np.uint8)
    imgs=[base]
    h,c,s=(masks['left_arm'][k] for k in ('historical','current','stage8'))
    for mask,col in [(h,(245,40,150)),(c,(40,140,245)),(s,(45,190,80))]:
        v=base.astype(float)
        v[mask]=v[mask]*.55+np.array(col)*.45
        imgs.append(v.astype(np.uint8))
    board=Image.new('RGB',(1360,380),(246,246,246));draw=ImageDraw.Draw(board)
    for i,(im,title) in enumerate(zip(imgs,['SOURCE','HISTORICAL PHASE04 LEFT','CURRENT PHASE04 LEFT','SIGNED STAGE8 LEFT'])):
        board.paste(Image.fromarray(im),(340*i,35));draw.text((340*i+8,10),title,fill=(20,20,20))
    board.save(output/'GC001_PHASE04_REVISION_LINEAGE_PRIVATE.png')
    (output/'C02B5_PHASE04_REVISION_LINEAGE_PRIVATE.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('source','scene','snapshot','historical','output'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(run(a.source,a.scene,a.snapshot,a.historical,a.output),indent=2))
