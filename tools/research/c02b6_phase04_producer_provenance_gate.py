"""Fail-closed signed Phase03->04->Stage8 authority check. Never changes assets."""
from __future__ import annotations
import hashlib
import json
import zipfile
from pathlib import Path
from io import BytesIO

SOURCE_SHA = '75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e'
SNAP_SHA = '89286cb1e8cf2003f02ec2dbab2a80dcf3da26b902123255a9cc17767855e434'
STAGE8_SHA = '7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08'
PHASE3_STAGE_SHA = 'c1485333f581e26ca75e2d425cc09f061ff06d721839777300ee73da829d460c'
PHASE4_STAGE_SHA = '7a73dc4ae03fd4a5d5789a7d0bc8e0103f480cb3ae44a88badc28f06db56ff0e'
PARTS = ('left_arm','right_arm','face')

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def analyze(source:Path,snapshot:Path,stage8:Path)->dict:
    if sha(Path(source).read_bytes())!=SOURCE_SHA: raise ValueError('SOURCE_SHA_FAIL')
    snap=Path(snapshot).read_bytes()
    if sha(snap)!=SNAP_SHA: raise ValueError('SNAPSHOT_SHA_FAIL')
    stage_bytes=Path(stage8).read_bytes()
    if sha(stage_bytes)!=STAGE8_SHA: raise ValueError('STAGE8_SHA_FAIL')
    with zipfile.ZipFile(BytesIO(snap)) as z:
        manifest=json.loads(z.read('PRIVATE_SHA_MANIFEST.json'))
        if manifest.get('source_sha256')!=SOURCE_SHA or manifest.get('promotion_authorized') is not False:
            raise ValueError('SNAPSHOT_AUTHORITY_FAIL')
        for name,expected in manifest['files'].items():
            if sha(z.read(name))!=expected: raise ValueError('MEMBER_SHA_FAIL')
        p3raw=z.read('phase_03/stage.json');p4raw=z.read('phase_04/stage.json')
        if sha(p3raw)!=PHASE3_STAGE_SHA or sha(p4raw)!=PHASE4_STAGE_SHA:
            raise ValueError('SIGNED_STAGE_SHA_FAIL')
        p3=json.loads(p3raw);p4=json.loads(p4raw)
        if p3['source']['sha256']!=SOURCE_SHA or p4['source']['sha256']!=SOURCE_SHA:
            raise ValueError('STAGE_SOURCE_SHA_FAIL')
        if p3['producer']!='minimalizer-zerobase2-phase3' or p4['producer']!='minimalizer-zerobase2-phase4':
            raise ValueError('PRODUCER_FAIL')
        for key in ('03_subject_mask.png','03_subject_overlay.png'):
            if p4['inputs']['phase3'][key]!=sha(z.read('phase_03/'+key)):
                raise ValueError('P03_TO_P04_INPUT_FAIL')
        if p4['inputs']['phase3']['stage.json']!=sha(p3raw):
            raise ValueError('P03_STAGE_CHAIN_FAIL')
        archived=set(z.namelist())
        unavailable=[]
        for name,digest in p4['outputs'].items():
            member='phase_04/'+name
            if member not in archived:
                unavailable.append(name)
                continue
            if sha(z.read(member))!=digest: raise ValueError('P04_OUTPUT_SHA_FAIL')
        mask_shas={part:p4['outputs']['part_masks/'+part+'.png'] for part in PARTS}
    s=json.loads(stage_bytes)
    if s.get('original_source_sha256')!=SOURCE_SHA or s.get('research_only') is not True or s.get('production_authorized') is not False:
        raise ValueError('STAGE8_AUTHORITY_FAIL')
    missing=[]
    for part in PARTS:
        rec=[x for x in s['primitives_back_to_front'] if x.get('source_mask_owner')==part]
        if len(rec)!=1: raise ValueError('STAGE8_OWNER_NOT_UNIQUE')
        x=rec[0]
        if x.get('source_evidence_refs')!=['phase04:part_masks/'+part+'.png'] or x.get('source_mask_replay') is not True:
            raise ValueError('STAGE8_REF_MISMATCH')
        # A path string is not an input content hash. Never use raster similarity as authority.
        if not any(x.get(k)==mask_shas[part] for k in ('source_mask_sha256','source_evidence_sha256','source_artifact_sha256')):
            missing.append(part)
    return {
        'schema':'c02b6-phase04-to-stage8-input-sha-lineage-v1',
        'signed_source_sha256':SOURCE_SHA,'signed_phase03_stage_sha256':PHASE3_STAGE_SHA,
        'signed_phase04_stage_sha256':PHASE4_STAGE_SHA,
        'phase03_config_sha256':p3['config_sha256'],'phase04_config_sha256':p4['config_sha256'],
        'phase03_producer':p3['producer'],'phase04_producer':p4['producer'],
        'phase03_to_phase04_sha_chain':'VERIFIED',
        'phase04_declared_outputs_not_in_private_snapshot':unavailable,
        'phase04_mask_sha256':mask_shas,
        'stage8_phase04_ref_mode':'PATH_ONLY_NO_ORIGINAL_MASK_DIGEST',
        'stage8_missing_source_mask_sha256':missing,
        'stage8_exact_phase04_revision':'UNPROVEN',
        'historical_stage04_producer_config':'NOT_RECOVERED',
        'historic_left_385_pixel_difference':'KNOWN_FROM_C02B5_NOT_CAUSALLY_EXPLAINED',
        'source_semantic_arm_correctness':'UNPROVEN',
        'stage':'C02b6','status':'PROVENANCE_GAP_CONFIRMED_RESEARCH_COMPLETE_C02_HOLD',
        'signed_originals_modified':False,'human_golden':'PENDING',
        'release_authorized':False,'production_changed':False,
    }

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    for n in ('source','snapshot','stage8','output'):p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();result=analyze(a.source,a.snapshot,a.stage8)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
