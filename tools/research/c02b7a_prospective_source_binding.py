"""Prospective SHA binding sidecar for recovered current Phase04 and Stage8.

Fail-closed research contract only. NEVER retroactively claims Stage8 used this
Phase04 revision, nor overwrites any source/scene, nor promotes a candidate.
"""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

SOURCE_SHA = '75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e'
SNAP_SHA = '89286cb1e8cf2003f02ec2dbab2a80dcf3da26b902123255a9cc17767855e434'
STAGE8_SHA = '7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08'
P4_STAGE_SHA = '7a73dc4ae03fd4a5d5789a7d0bc8e0103f480cb3ae44a88badc28f06db56ff0e'
PARTS = ('face','left_arm','right_arm')

def sha(b): return hashlib.sha256(b).hexdigest()

def load(snapshot, stage8):
    sb=Path(snapshot).read_bytes();eb=Path(stage8).read_bytes()
    if sha(sb)!=SNAP_SHA or sha(eb)!=STAGE8_SHA:raise ValueError('SIGNED_INPUT_SHA_MISMATCH')
    scene=json.loads(eb)
    if scene.get('original_source_sha256')!=SOURCE_SHA or scene.get('production_authorized') is not False:
        raise ValueError('STAGE8_AUTHORITY_MISMATCH')
    with zipfile.ZipFile(io.BytesIO(sb)) as z:
        manifest=json.loads(z.read('PRIVATE_SHA_MANIFEST.json'))
        if manifest.get('source_sha256')!=SOURCE_SHA or manifest.get('promotion_authorized') is not False:
            raise ValueError('SNAPSHOT_AUTHORITY_MISMATCH')
        for path,digest in manifest['files'].items():
            if sha(z.read(path))!=digest:raise ValueError('SNAPSHOT_MEMBER_SHA_MISMATCH')
        if manifest['files']['phase_04/stage.json'] != P4_STAGE_SHA:
            raise ValueError('PHASE04_STAGE_SHA_MISMATCH')
        p4=json.loads(z.read('phase_04/stage.json'))
        p3=json.loads(z.read('phase_03/stage.json'))
    for p in (p3,p4):
        canonical=json.dumps(p['config'],sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
        if sha(canonical)!=p['config_sha256'] or p['source']['sha256']!=SOURCE_SHA:
            raise ValueError('CONFIG_OR_SOURCE_SHA_MISMATCH')
    for name,digest in p4['inputs']['phase3'].items():
        if manifest['files']['phase_03/'+name]!=digest:
            raise ValueError('PHASE03_INPUT_SHA_MISMATCH')
    owners={}
    for part in PARTS:
        records=[p for p in scene['primitives_back_to_front'] if p.get('source_mask_owner')==part]
        if len(records)!=1 or records[0].get('source_evidence_refs')!=['phase04:part_masks/'+part+'.png']:
            raise ValueError('STAGE8_OWNER_REFERENCE_MISMATCH')
        owners[part]=manifest['files']['phase_04/part_masks/'+part+'.png']
    return p3,p4,owners

def propose(snapshot,stage8):
    p3,p4,owners=load(snapshot,stage8)
    return {'schema':'sa1060k_prospective_stage8_input_binding_v1',
        'scope':'RECOVERED_CURRENT_PHASE04_ONLY_NOT_HISTORICAL_STAGE8_PROOF',
        'source_sha256':SOURCE_SHA,'source_stage8_scene_sha256':STAGE8_SHA,
        'phase03_stage_sha256':p4['inputs']['phase3']['stage.json'],
        'phase03_config_sha256':p3['config_sha256'],
        'phase04_stage_sha256':P4_STAGE_SHA,
        'phase04_config_sha256':p4['config_sha256'],
        'phase04_mask_raw_sha256':owners,
        'historical_stage8_used_this_revision':'UNPROVEN',
        'semantic_owner_quality':'UNPROVEN',
        'cryptographic_signature':'NONE',
        'prospective_only':True,'candidate_promoted':False,
        'human_golden':'PENDING','original_stage8_budget':'HOLD',
        'release_authorized':False,'production_changed':False}

def validate(snapshot,stage8,sidecar):
    expected=propose(snapshot,stage8)
    if sidecar!=expected:raise ValueError('PROSPECTIVE_BINDING_MISMATCH')
    if sidecar['historical_stage8_used_this_revision']!='UNPROVEN' or sidecar['cryptographic_signature']!='NONE':
        raise ValueError('UNAUTHORIZED_HISTORICAL_OR_SIGNATURE_CLAIM')
    return True

def main():
    p=argparse.ArgumentParser()
    for x in ('snapshot','stage8','output'):p.add_argument('--'+x,required=True,type=Path)
    a=p.parse_args()
    if a.output.resolve() in (a.snapshot.resolve(),a.stage8.resolve()):
        raise ValueError('OUTPUT_MUST_NOT_OVERWRITE_SIGNED_INPUT')
    if a.output.exists():raise FileExistsError('OUTPUT_ALREADY_EXISTS')
    result=propose(a.snapshot,a.stage8)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':main()
