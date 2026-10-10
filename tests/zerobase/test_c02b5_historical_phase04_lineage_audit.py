import json,sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/research'))
import c02b5_historical_phase04_lineage_audit as a
BASE=Path(__import__('os').environ.get('SA1060_C02_SIGNED_DIR','/__signed_c02_not_available__'))
SOURCE=BASE/'GC001_source.png'
SCENE=BASE/'GC001_phase8_adaptive_source_contour_research.json'
SNAP=BASE/'GC001_Phase03_Phase04_ReadOnlySnapshot_20261009.zip'

@pytest.fixture(scope='module')
def result(tmp_path_factory):
    if not all(p.exists() for p in [SOURCE,SCENE,SNAP]+[BASE/f'GC001_historical_{p}_stage04_mask.png' for p in ('right_arm','left_arm','face')]):
        pytest.skip('Private signed C02 inputs unavailable')
    return a.run(SOURCE,SCENE,SNAP,BASE,tmp_path_factory.mktemp('c02b5_signed')/'fresh')

def test_historical_sha_pins(result):
    for part,sha in a.HISTORICAL_SHA.items():
        assert a.sha((BASE/f'GC001_historical_{part}_stage04_mask.png').read_bytes())==sha

def test_snapshot_sha_pin(result):
    assert a.sha(SNAP.read_bytes())==a.SNAP_SHA

def test_stage8_source_pin(result):
    assert a.sha(SCENE.read_bytes())==a.PINS['GC001']['stage8']

def test_historical_current_left_385_subset(result):
    x=result['parts']['left_arm']['historical_vs_current']
    assert (x['a_pixels'],x['b_pixels'],x['xor_pixels'])==(2715,2330,385)
    assert (x['a_only_pixels'],x['b_only_pixels'])==(385,0)

def test_stage8_historical_left_5(result):
    x=result['parts']['left_arm']['historical_vs_stage8']
    assert (x['a_pixels'],x['b_pixels'],x['xor_pixels'])==(2715,2718,5)
    assert (x['a_only_pixels'],x['b_only_pixels'])==(1,4)

def test_stage8_current_left_390(result):
    x=result['parts']['left_arm']['current_vs_stage8']
    assert (x['a_pixels'],x['b_pixels'],x['xor_pixels'])==(2330,2718,390)
    assert (x['a_only_pixels'],x['b_only_pixels'])==(1,389)

def test_right_arm_same_revision_stage8_24(result):
    p=result['parts']['right_arm']
    assert p['historical_vs_current']['xor_pixels']==0
    assert p['historical_vs_stage8']['xor_pixels']==24
    assert p['current_vs_stage8']['xor_pixels']==24

def test_face_unchanged_all(result):
    p=result['parts']['face']
    assert all(p[k]['xor_pixels']==0 for k in ('historical_vs_current','historical_vs_stage8','current_vs_stage8'))

def test_no_semantic_or_production_promotion(result):
    assert result['historical_pixel_similarity_is_not_proof_of_identical_producer_or_config']
    assert result['source_mask_semantic_quality']=='NOT_PROVEN'
    assert result['release_authorized'] is False
    assert result['production_changed'] is False
    assert result['original_stage8_budget']=='HOLD'

def test_source_refs_present(result):
    for part in ('right_arm','left_arm','face'):
        assert result['parts'][part]['stage8_source_ref']==[f'phase04:part_masks/{part}.png']

def test_tamper_historical_rejected(result, tmp_path):
    f=tmp_path/'GC001_historical_left_arm_stage04_mask.png';f.write_bytes((BASE/f.name).read_bytes()+b' ')
    with pytest.raises(ValueError,match='HISTORICAL_MASK_SHA_FAIL'):
        a.read_historical(tmp_path,'left_arm')

def test_tamper_snapshot_rejected(result, tmp_path):
    f=tmp_path/'bad.zip';f.write_bytes(SNAP.read_bytes()+b' ')
    with pytest.raises(ValueError,match='CURRENT_SNAPSHOT_SHA_FAIL'):
        a.read_current(f,'left_arm')

def test_mask_partition_synthetic():
    x=np.array([[True,True,False],[False,False,True]])
    y=np.array([[True,False,True],[False,False,True]])
    d=a.support_distance(x,y)
    assert (d['a_pixels'],d['b_pixels'],d['xor_pixels'],d['a_only_pixels'],d['b_only_pixels'])==(3,3,2,1,1)

def test_no_input_overwrite(result):
    with pytest.raises(ValueError,match='OUTPUT_MUST_NOT_OVERWRITE_SIGNED_INPUTS'):
        a.run(SOURCE,SCENE,SNAP,BASE,SOURCE)

def test_deterministic_source_revision_readonly(result, tmp_path):
    first=a.run(SOURCE,SCENE,SNAP,BASE,tmp_path/'fresh')
    second=a.run(SOURCE,SCENE,SNAP,BASE,tmp_path/'another')
    assert first==result==second
    import hashlib
    for f in (tmp_path/'fresh').iterdir():
        assert hashlib.sha256(f.read_bytes()).hexdigest()==hashlib.sha256((tmp_path/'another'/f.name).read_bytes()).hexdigest()
