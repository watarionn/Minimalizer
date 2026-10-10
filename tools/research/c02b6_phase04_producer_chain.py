"""C02b6: read-only SHA-pinned Phase03->04 producer/config lineage audit.

This never selects an arm owner, rewrites source files, or authorizes a release.
The historical SA10.41 artifact lacks its Stage04 producer/config manifest;
identical image SHA and a source_evidence_refs path do not establish lineage.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

SOURCE_SHA = '75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e'
SNAPSHOT_SHA = '89286cb1e8cf2003f02ec2dbab2a80dcf3da26b902123255a9cc17767855e434'
HISTORICAL_METRICS_SHA = 'c0d4a730289024090f4a77fe61563d56de32e7e9158790a29768a546e0265cc2'
STAGE8_SHA = '7eed624b31c9a117b6d7e6e5fe9788067f00b3fc3e8889fd250c14adaaac8f08'
PARTS = ('face', 'left_arm', 'right_arm')

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def checked(path: Path, expected: str) -> bytes:
    data = Path(path).read_bytes()
    if sha(data) != expected:
        raise ValueError('SIGNED_SHA_MISMATCH')
    return data

def canonical_config_hash(config: dict) -> str:
    return sha(json.dumps(config, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode())

def audit(snapshot: Path, historical_metrics: Path, stage8: Path) -> dict:
    raw = checked(snapshot, SNAPSHOT_SHA)
    history = json.loads(checked(historical_metrics, HISTORICAL_METRICS_SHA))
    scene = json.loads(checked(stage8, STAGE8_SHA))
    with zipfile.ZipFile(__import__('io').BytesIO(raw)) as z:
        manifest = json.loads(z.read('PRIVATE_SHA_MANIFEST.json'))
        if manifest['source_sha256'] != SOURCE_SHA or manifest['promotion_authorized'] is not False:
            raise ValueError('SOURCE_AUTHORITY_MISMATCH')
        for name, expected in manifest['files'].items():
            if sha(z.read(name)) != expected:
                raise ValueError('SNAPSHOT_MEMBER_SHA_MISMATCH')
        p3 = json.loads(z.read('phase_03/stage.json'))
        p4 = json.loads(z.read('phase_04/stage.json'))
    for stage, number in ((p3, 3), (p4, 4)):
        if stage['phase'] != number or stage['source']['sha256'] != SOURCE_SHA:
            raise ValueError('STAGE_SOURCE_MISMATCH')
        if canonical_config_hash(stage['config']) != stage['config_sha256']:
            raise ValueError('CONFIG_SHA_MISMATCH')
    for name, expected in p4['inputs']['phase3'].items():
        if manifest['files']['phase_03/' + name] != expected:
            raise ValueError('PHASE03_TO_PHASE04_CHAIN_MISMATCH')
    if history['original_source_sha256'] != SOURCE_SHA or history['original_stage8_scene_sha256'] != STAGE8_SHA:
        raise ValueError('HISTORICAL_SOURCE_BINDING_MISMATCH')
    if scene['original_source_sha256'] != SOURCE_SHA:
        raise ValueError('STAGE8_SOURCE_BINDING_MISMATCH')
    references = {}
    for part in PARTS:
        matching = [p for p in scene['primitives_back_to_front'] if p.get('source_mask_owner') == part]
        if len(matching) != 1:
            raise ValueError('STAGE8_OWNER_UNIQUE_MISMATCH')
        refs = matching[0].get('source_evidence_refs', [])
        expected = 'phase04:part_masks/' + part + '.png'
        if expected not in refs:
            raise ValueError('STAGE8_OWNER_REFERENCE_MISMATCH')
        references[part] = {'source_ref': expected,
            'current_raw_mask_sha256': manifest['files']['phase_04/part_masks/' + part + '.png'],
            'historical_raw_mask_sha256': history['source_stage04_mask_sha256'][part],
            'same_raw_mask': manifest['files']['phase_04/part_masks/' + part + '.png'] == history['source_stage04_mask_sha256'][part],
            'stage8_reference_pins_mask_sha': False}
    if references['left_arm']['same_raw_mask'] or not all(references[p]['same_raw_mask'] for p in ('face', 'right_arm')):
        raise ValueError('UNEXPECTED_REVISION_RELATION')
    return {
        'schema': 'sa1060j_c02b6_producer_chain_v1',
        'source_sha256': SOURCE_SHA,
        'phase03_config_sha256': p3['config_sha256'],
        'phase04_current_config_sha256': p4['config_sha256'],
        'phase04_current_producer': p4['producer'],
        'phase04_current_producer_version': p4['producer_version'],
        'phase03_to_current_phase04_input_sha_chain_verified': True,
        'historical_sa1041_stage04_config_sha256': None,
        'historical_sa1041_stage04_producer_version': None,
        'historical_producer_config_lineage_proven': False,
        'owner_raw_sha_comparison': references,
        'source_ref_without_content_sha_is_not_lineage_proof': True,
        'left_arm_385_pixel_revision_difference': 'CONFIRMED_PREVIOUS_C02B5',
        'semantic_arm_owner_verified': False,
        'stage8_original_budget': 'HOLD',
        'human_golden': 'PENDING',
        'release_authorized': False,
        'production_changed': False,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--historical-metrics', type=Path, required=True)
    parser.add_argument('--stage8', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    protected = [args.snapshot.resolve(), args.historical_metrics.resolve(), args.stage8.resolve()]
    if args.output.resolve() in protected:
        raise ValueError('OUTPUT_MUST_NOT_OVERWRITE_SIGNED_INPUTS')
    result = audit(args.snapshot, args.historical_metrics, args.stage8)
    if args.output.exists():
        raise FileExistsError('OUTPUT_ALREADY_EXISTS')
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    main()
