"""C02b7b static checks and fail-closed signed GC001/Raden replay."""
import os,sys,json,hashlib
from pathlib import Path
import pytest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/research'))
sys.path.insert(0,str(Path(__file__).parent))
import c02b7b_source_boundary_owner_observer as s
BASE=Path(os.environ.get('SA1060_C02_SIGNED_DIR','/__private_input_missing__'))
FILES=[BASE/'GC001_source.png',BASE/'GC001_phase8_adaptive_source_contour_research.json',
       BASE/'Raden_source.png',BASE/'Raden_phase8_adaptive_source_contour_research.json',
       BASE/'GC001_Phase03_Phase04_ReadOnlySnapshot_20261009.zip',BASE]
@pytest.fixture
def signed():
    if not all(x.exists() for x in FILES[:5]) or not (BASE/'GC001_historical_left_arm_stage04_mask.png').exists():
        pytest.skip('private signed fixtures missing')
    return FILES

def test_bad_border_mask_rejected():
    with pytest.raises(ValueError,match='MASK_BOOL_SHAPE_REQUIRED'):s.border(np.zeros((340,340),np.uint8))

def test_empty_border_has_zero_pixels():
    assert not s.border(np.zeros((340,340),bool)).any()

def test_source_shape_fail_closed():
    with pytest.raises(ValueError,match='SOURCE_RGBA_SHAPE_REQUIRED'):s.edge_cue(np.zeros((2,2,4),np.uint8))

def test_synthetic_observation_is_non_authoritative():
    a=np.zeros((340,340),bool);a[20:30,40:50]=True
    b=np.zeros_like(a);b[25:35,45:55]=True
    r=np.ones((340,340,4),np.uint8)*255;e=np.zeros_like(a)
    m=s.inspect_owner(a,b,r,e)
    assert m['pixels']==100 and m['overlap_with_other_declared_owners_pixels']==25
    assert m['border_without_source_canny_pixels']==36
    assert not m['source_boundary_is_anatomical_truth'] and not m['raster_core_is_semantic_truth']

def test_unknown_case_fail_closed():
    with pytest.raises(ValueError,match='UNKNOWN_CASE'):
        s.inspect_case('OTHER',Path('/missing'),Path('/missing'))

def test_signed_cases_deterministic_and_no_mutation(signed):
    a=s.run(*signed);b=s.run(*signed)
    assert a==b and len(a['cases'])==2
    assert a['candidate']=='NONE' and not a['release_authorized'] and not a['production_changed']
    assert a['cases'][0]['GC001_lineage_differences']['left_arm']['historical_stage8_xor']==5
    assert a['cases'][0]['GC001_lineage_differences']['left_arm']['current_stage8_xor']==390
    assert a['cases'][1]['GC001_lineage_differences']=='NOT_AVAILABLE'
    assert all(not c['suitable_for_owner_mutation'] for c in a['cases'])

def test_signed_source_tamper_fails_closed(signed,tmp_path):
    p=tmp_path/'bad.png';p.write_bytes(signed[0].read_bytes()+b'X')
    with pytest.raises(ValueError,match='SIGNED_INPUT_SHA_FAIL'):s.run(p,*signed[1:])

def test_signed_scene_tamper_fails_closed(signed,tmp_path):
    p=tmp_path/'bad.json';p.write_bytes(signed[3].read_bytes()+b'X')
    x=list(signed);x[3]=p
    with pytest.raises(ValueError,match='SIGNED_INPUT_SHA_FAIL'):s.run(*x)

def test_reject_raden_revision_substitution(signed):
    with pytest.raises(ValueError,match='RADEN_GC001_LINEAGE_INPUTS_FORBIDDEN'):
        s.inspect_case('Raden', signed[2], signed[3], signed[4], signed[5])
