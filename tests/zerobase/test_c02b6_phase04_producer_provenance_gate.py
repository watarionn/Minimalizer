"""Synthetic security and optional real signed C02b6 provenance replay."""
from pathlib import Path
import sys,os,json
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/research'))
import c02b6_phase04_producer_provenance_gate as a
BASE=Path(os.getenv('SA1060_C02_SIGNED_DIR','/__signed_c02_not_available__'))
SOURCE=BASE/'GC001_source.png';SNAP=BASE/'GC001_Phase03_Phase04_ReadOnlySnapshot_20261009.zip';STAGE=BASE/'GC001_phase8_adaptive_source_contour_research.json'
@pytest.fixture(scope='module')
def real():
    if not all(x.exists() for x in (SOURCE,SNAP,STAGE)):pytest.skip('Signed original fixtures absent')
    return a.analyze(SOURCE,SNAP,STAGE)

def test_digest_is_sha256():
    assert a.sha(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'

def test_source_pin_fails_first(tmp_path):
    p=tmp_path/'wrong.png';p.write_bytes(b'no')
    with pytest.raises(ValueError,match='SOURCE_SHA_FAIL'):a.analyze(p,BASE/'missing.zip',STAGE)

def test_source_chain_verified(real):
    assert real['phase03_to_phase04_sha_chain']=='VERIFIED'
    assert real['signed_phase03_stage_sha256']==a.PHASE3_STAGE_SHA
    assert real['signed_phase04_stage_sha256']==a.PHASE4_STAGE_SHA

def test_exact_historical_authority_not_claimed(real):
    assert real['stage8_phase04_ref_mode']=='PATH_ONLY_NO_ORIGINAL_MASK_DIGEST'
    assert real['stage8_exact_phase04_revision']=='UNPROVEN'
    assert real['historical_stage04_producer_config']=='NOT_RECOVERED'
    assert set(real['stage8_missing_source_mask_sha256'])==set(a.PARTS)

def test_no_source_mutation_or_promotion(real):
    assert real['signed_originals_modified'] is False
    assert real['release_authorized'] is False and real['production_changed'] is False
    assert real['source_semantic_arm_correctness']=='UNPROVEN'

def test_sha_determinism(real):
    assert real==a.analyze(SOURCE,SNAP,STAGE)

def test_modified_original_rejected(real,tmp_path):
    f=tmp_path/'wrong_source.png';f.write_bytes(SOURCE.read_bytes()+b' ')
    with pytest.raises(ValueError,match='SOURCE_SHA_FAIL'):a.analyze(f,SNAP,STAGE)

def test_modified_snapshot_rejected(real,tmp_path):
    f=tmp_path/'wrong_snapshot.zip';f.write_bytes(SNAP.read_bytes()+b' ')
    with pytest.raises(ValueError,match='SNAPSHOT_SHA_FAIL'):a.analyze(SOURCE,f,STAGE)

def test_modified_stage8_rejected(real,tmp_path):
    f=tmp_path/'wrong_stage8.json';f.write_bytes(STAGE.read_bytes()+b' ')
    with pytest.raises(ValueError,match='STAGE8_SHA_FAIL'):a.analyze(SOURCE,SNAP,f)
