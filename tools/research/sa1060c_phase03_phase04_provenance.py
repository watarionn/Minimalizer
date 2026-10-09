"""C02a: source-SHA pinned Phase03->Phase04 owner authority and history audit.

Does not change any saved stage, semantic mask, source image or SVG. Source RGB
exact-match connectivity is a *risk witness*, not an anatomy oracle. The
historical signed left arm and current Phase04 raw stage are distinct versions.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, zipfile
from pathlib import Path
from io import BytesIO
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sa1060b_first_bad_stage_audit as c01

SOURCE_SHA = c01.GC_SHA['GC001_source.png']
STAGE3_MASK_SHA = 'af694550c7e4d60524aed51df997ebd03ebb1f40cef7425aa975590245c2e7c7'
CURRENT_STAGE4_SHA = {'right_arm': '8829b6865a50abee2fac820cfe250c35e3089a8f5eb4c3754b633a7d1327ac58',
                       'left_arm': 'cb707edab78c6d0715de5fcb811f6e0595baa53c9f5c8cd3290be420ba06061d',
                       'face': 'e1c4665e07e236b1667af6741a9b25480ea350243de2289c2ff6fbc018f4b293',
                       'hair': 'cc6ac8dff96ffcca1840e42339ad2ac26cea6d6f4d9dab5054dce304c229221f',
                       'major_clothing': '046e5b015548cb4e5a8adc0b790ff2c0b2dc0d6278cc3d7b30f73e7aa37fe778'}
HISTORICAL_STAGE04_LEFT_SHA = '303e52490b7ff9f04079682345e1822ac0cba90775df98b1ce7f23a7a0f95130'
SNAPSHOT_SHA = '89286cb1e8cf2003f02ec2dbab2a80dcf3da26b902123255a9cc17767855e434'
ROLES = ('right_arm','left_arm','face','hair','major_clothing')

def sha(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()

def read_mask(raw: bytes) -> np.ndarray:
    im = np.asarray(Image.open(BytesIO(raw)).convert('L'))
    if im.shape != (340,340) or not np.isin(im, (0,255)).all():
        raise ValueError('PHASE3_4_MASK_NOT_PINNED_BINARY')
    return im > 0

def validate_archive(snapshot: Path, *, require_pin:bool=True) -> tuple[dict,dict,dict,dict]:
    data = snapshot.read_bytes()
    if require_pin and sha(data) != SNAPSHOT_SHA:
        raise ValueError('PHASE03_04_PRIVATE_ZIP_SHA_MISMATCH')
    with zipfile.ZipFile(BytesIO(data)) as z:
        names = z.namelist()
        if len(set(names)) != len(names) or 'PRIVATE_SHA_MANIFEST.json' not in names:
            raise ValueError('INVALID_SNAPSHOT_MEMBER_SET')
        manifest = json.loads(z.read('PRIVATE_SHA_MANIFEST.json'))
        if manifest['source_sha256'] != SOURCE_SHA or manifest['promotion_authorized'] is not False:
            raise ValueError('SOURCE_BINDING_OR_RELEASE_STATUS_INVALID')
        if set(manifest['files']) != set(names)-{'PRIVATE_SHA_MANIFEST.json'} or len(manifest['files'])!=19:
            raise ValueError('SNAPSHOT_MANIFEST_INCOMPLETE')
        blobs = {}
        for name,digest in manifest['files'].items():
            if name.startswith('/') or '..' in Path(name).parts:
                raise ValueError('PRIVATE_SNAPSHOT_PATH_TRAVERSAL')
            b=z.read(name)
            if sha(b)!=digest:raise ValueError('SNAPSHOT_MEMBER_SHA_MISMATCH:'+name)
            blobs[name]=b
        stages={n:json.loads(blobs[f'phase_0{n}/stage.json']) for n in (3,4)}
        for stage_no,stage in stages.items():
            if stage['source']['sha256']!=SOURCE_SHA or stage['phase']!=stage_no:
                raise ValueError('STAGE_ORIGINAL_SOURCE_PROVENANCE_DRIFT')
            for rel,expected in stage['outputs'].items():
                path=f'phase_0{stage_no}/{rel}'
                if path in blobs and sha(blobs[path])!=expected:
                    raise ValueError('STAGE_OUTPUT_SHA_MISMATCH:'+path)
        if stages[4]['inputs']['phase3']['03_subject_mask.png']!=STAGE3_MASK_SHA:
            raise ValueError('PHASE04_TO_PHASE03_SOURCE_BINDING_MISMATCH')
        if sha(blobs['phase_03/03_subject_mask.png'])!=STAGE3_MASK_SHA:
            raise ValueError('PHASE03_ORIGINAL_MASK_CHANGED')
        for role,digest in CURRENT_STAGE4_SHA.items():
            if sha(blobs[f'phase_04/part_masks/{role}.png'])!=digest:
                raise ValueError('CURRENT_PHASE04_ROLE_PIN_FAILED:'+role)
        return stages,blobs,manifest,{'snapshot_zip_sha':sha(data),'member_count':len(blobs)}

def assert_role_history(raw:dict,signed:dict) -> dict:
    result={}
    for role in ('right_arm','left_arm','face'):
        before,after=raw[role],signed[role]
        if before.shape!=(340,340) or after.shape!=before.shape:
            raise ValueError('HISTORICAL_MASK_SHAPE_MISMATCH')
        result[role]={
            'current_phase04_pixels':int(before.sum()),
            'historical_sa1041_signed_pixels':int(after.sum()),
            'historical_extra_pixels':int(np.count_nonzero(after & ~before)),
            'historical_missing_pixels':int(np.count_nonzero(before & ~after)),
            'raster_xor':int(np.count_nonzero(before ^ after))}
    if result['right_arm']['raster_xor'] or result['face']['raster_xor']:
        raise ValueError('EXPECTED_SHARED_RIGHT_ARM_OR_FACE_CHANGED')
    return result

def analyze(source: Path, signed_root: Path, snapshot: Path, output: Path)->dict:
    for input_path in (source,snapshot):
        if output.resolve() == input_path.resolve() or input_path.resolve() in output.resolve().parents:
            raise ValueError('OUTPUT_MUST_NOT_OVERWRITE_FROZEN_INPUT')
    if signed_root.resolve()==output.resolve() or signed_root.resolve() in output.resolve().parents:
        raise ValueError('OUTPUT_INSIDE_SIGNED_AUTHORITY')
    if output.exists() and any(output.iterdir()):
        raise ValueError('OUTPUT_DIRECTORY_NOT_EMPTY')
    stages,blobs,manifest,snapshot_metadata=validate_archive(snapshot)
    if c01.digest(source)!=SOURCE_SHA:
        raise ValueError('ORIGINAL_RGB_SOURCE_SHA_MISMATCH')
    c01.signed_check(signed_root,c01.GC_SHA)
    rgba=np.asarray(Image.open(source).convert('RGBA'))
    photo,alpha=rgba[...,:3],rgba[...,3]
    p3=read_mask(blobs['phase_03/03_subject_mask.png'])
    masks={role:read_mask(blobs[f'phase_04/part_masks/{role}.png']) for role in ROLES}
    signed={role:c01.mask_at(signed_root,'gc001_'+{'right_arm':'right','left_arm':'left','face':'face'}[role]+'.png') for role in ('right_arm','left_arm','face')}
    history=assert_role_history(masks,signed)
    connected,obs=c01.source_connected_background(photo,alpha)
    if any(np.count_nonzero(m & ~p3) for m in masks.values()):
        raise ValueError('PHASE04_ROLE_ESCAPED_PHASE03_SUBJECT')
    overlap=lambda m: {'pixels':int(m.sum()),'exact_border_connected_rgb_overlap':int(np.count_nonzero(m&connected)),
                       'fully_opaque_intersection':int(np.count_nonzero(m&connected&(alpha==255)))}
    metrics={'phase03_subject':overlap(p3), 'phase04_roles':{k:overlap(v) for k,v in masks.items()},
             'historical_sa1041_vs_current':history}
    # A real risk was already present at P03, but RGB equality alone never proves anatomy.
    if(metrics['phase03_subject']['exact_border_connected_rgb_overlap']!=648
       or metrics['phase04_roles']['right_arm']['exact_border_connected_rgb_overlap']!=533
       or metrics['phase04_roles']['hair']['exact_border_connected_rgb_overlap']!=31
       or metrics['historical_sa1041_vs_current']['left_arm']['raster_xor']!=385):
        raise ValueError('PINNED_STAGE03_04_SOURCE_OBSERVATION_DRIFT')
    output.mkdir(parents=True,exist_ok=True)
    board=Image.new('RGB',(340*4,383),(245,245,242));pen=ImageDraw.Draw(board)
    def ov(mask,color):
        canvas=photo.astype(np.float32).copy()
        canvas[mask]=.55*canvas[mask]+.45*np.asarray(color,dtype=np.float32)
        return Image.fromarray(np.clip(canvas,0,255).astype('uint8'))
    panels=[('SOURCE',Image.fromarray(photo)),('PHASE03 SUBJECT',ov(p3,(92,205,133))),
            ('CURRENT PHASE04 RIGHT ARM',ov(masks['right_arm'],(255,45,145))),
            ('HISTORICAL LEFT MASK DELTA',ov(signed['left_arm']&~masks['left_arm'],(65,85,248)))]
    for i,(title,panel) in enumerate(panels):board.paste(panel,(340*i,43));pen.text((340*i+8,12),title,fill=(12,12,12))
    board.save(output/'gc001_p03_p04_history_private_board.png')
    report={'schema':'sa1060c-c02a-original-phase3-to-phase4-provenance-v1','stage':'C02a','status':'RESEARCH_DIAGNOSIS_COMPLETE_RELEASE_HOLD',
            'phase03_first_checked_source_background_intersection':True,
            'source_connected_rgb_is_not_anatomy_truth':True,
            'phase03_algorithm_root_cause':'NOT_ESTABLISHED','phase04_algorithm_root_cause':'NOT_ESTABLISHED',
            'historical_left_stage4_mask_exact_parity':False,
            'historical_source_sha256':SOURCE_SHA,'phase03_mask_sha256':STAGE3_MASK_SHA,
            'phase04_current_mask_sha256':CURRENT_STAGE4_SHA,
            'phase04_sa1041_signed_source_left_raw_sha256':HISTORICAL_STAGE04_LEFT_SHA,
            'snapshot':snapshot_metadata,'metrics':metrics,'source_observer':obs,
            'artistic_golden':'PENDING','original_stage8_budget':'HOLD','release_authorized':False,
            'production_changed':False,'private_board_filename':'gc001_p03_p04_history_private_board.png'}
    (output/'c02a_private_replay.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    public={k:report[k] for k in ('schema','stage','status','phase03_first_checked_source_background_intersection','source_connected_rgb_is_not_anatomy_truth','phase03_algorithm_root_cause','phase04_algorithm_root_cause','historical_left_stage4_mask_exact_parity','artistic_golden','original_stage8_budget','release_authorized','production_changed')}
    public['measurements']={'phase03_source_background_connected_exact_rgb_pixels':648,
           'phase04_right_arm_overlap_pixels':533, 'phase04_hair_overlap_pixels':31,
           'current_phase04_left_arm_pixels':history['left_arm']['current_phase04_pixels'],
           'historical_sa1041_left_arm_pixels':history['left_arm']['historical_sa1041_signed_pixels'],
           'historical_left_arm_extra_pixels':385,
           'phase03_source_binding_verified':True,'phase04_source_binding_verified':True}
    (output/'c02a_public_numeric.json').write_text(json.dumps(public,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--signed-root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();r=analyze(a.source,a.signed_root,a.snapshot,a.out)
    print(json.dumps({'stage':r['stage'],'p03_overlap':r['metrics']['phase03_subject']['exact_border_connected_rgb_overlap'],
                      'p04_right_overlap':r['metrics']['phase04_roles']['right_arm']['exact_border_connected_rgb_overlap'],
                      'left_signed_xor':r['metrics']['historical_sa1041_vs_current']['left_arm']['raster_xor'],
                      'promotion':r['release_authorized']}))

if __name__=='__main__': main()
