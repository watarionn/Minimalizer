"""C02b4 read-only synthetic and independently signed two-case tests."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/research'))
import c02b4_alpha_owner_authority_audit as a

ROOT = Path(__import__('os').environ.get('SA1060_C02_SIGNED_DIR','/__signed_c02_not_available__'))
GC = ROOT / 'GC001_source.png'
GS = ROOT / 'GC001_phase8_adaptive_source_contour_research.json'
RA = ROOT / 'Raden_source.png'
RS = ROOT / 'Raden_phase8_adaptive_source_contour_research.json'
SNAP = ROOT / 'GC001_Phase03_Phase04_ReadOnlySnapshot_20261009.zip'

@pytest.fixture(scope='module')
def real():
    if not all(p.exists() for p in (GC,GS,RA,RS,SNAP)):
        pytest.skip('Private signed C02 inputs unavailable')
    return a.case_audit('GC001', GC, GS, SNAP), a.case_audit('Raden', RA, RS)

def test_pinned_sources_and_scenes(real):
    for case, src, scene in [('GC001', GC, GS), ('Raden', RA, RS)]:
        assert a.sha(src.read_bytes()) == a.PINS[case]['source']
        assert a.sha(scene.read_bytes()) == a.PINS[case]['stage8']

def test_signed_scene_guard(real):
    for row in real:
        assert row[0]['source_alpha_is_semantic_owner_ground_truth'] is False
        assert row[0]['border_rgb_is_background_ground_truth'] is False
        assert row[0]['proposed_owner_mutation'] == 'NONE'

def test_gc_right_rgb_alpha_categories(real):
    m = real[0][0]['stage8_owner_evidence']['right_arm']
    assert m['owner_pixels'] == 6510
    assert (m['owner_on_alpha_zero'], m['owner_on_alpha_partial']) == (3, 38)
    assert (m['rgb_overlap_alpha_zero'], m['rgb_overlap_alpha_partial'], m['rgb_overlap_alpha_opaque']) == (0, 13, 520)
    assert m['owner_on_border_connected_rgb'] == 533

def test_raden_arm_independent_control(real):
    right = real[1][0]['stage8_owner_evidence']['right_arm']
    left = real[1][0]['stage8_owner_evidence']['left_arm']
    assert (right['owner_pixels'], left['owner_pixels']) == (9872, 10419)
    assert (right['owner_on_border_connected_rgb'], left['owner_on_border_connected_rgb']) == (2, 7)
    assert (left['owner_on_alpha_zero'], left['owner_on_alpha_partial']) == (74, 38)

def test_gc_stage04_stage08_lineage_not_silently_aliased(real):
    d = real[0][0]['phase04_to_stage8_lineage_observation']
    assert (d['right_arm']['xor_pixels'], d['left_arm']['xor_pixels'], d['face']['xor_pixels']) == (24, 390, 0)
    assert d['left_arm']['stage8_only_pixels'] == 389
    assert d['left_arm']['phase04_only_pixels'] == 1
    assert all(x['not_a_causal_attribution'] for x in d.values())

def test_rgba_synthetic_not_semantic():
    rgba=np.zeros((340,340,4),np.uint8)
    rgba[:,:,:3]=(10,20,30);rgba[:,:,3]=255
    owner=np.zeros((340,340),bool);owner[4:8,4:8]=True
    rgb, color, n = a.border_rgb_observer(rgba)
    assert color==(10,20,30) and n>=200
    e=a.evidence(owner,rgba,rgb)
    assert e['owner_on_border_connected_rgb']==16
    assert e['rgb_overlap_alpha_opaque']==16
    assert e['rgb_overlap_alpha_zero']==0
    # No decision to remove any pixels follows from opaque/color match.

def test_mask_alpha_categories_partition():
    rgba=np.zeros((340,340,4),np.uint8)
    rgba[0,0,3]=0;rgba[0,1,3]=128;rgba[0,2,3]=255
    mask=np.zeros((340,340),bool);mask[0,:3]=True
    rgb=np.zeros_like(mask);rgb[0,:3]=True
    e=a.evidence(mask,rgba,rgb)
    assert [e['rgb_overlap_alpha_zero'],e['rgb_overlap_alpha_partial'],e['rgb_overlap_alpha_opaque']]==[1,1,1]

def test_role_depth_mismatch_rejected():
    scene={'primitives_back_to_front':[{'source_mask_owner':'right_arm','parameters':{'rings':[{'depth':1,'role':'fill','points':[[0,0],[2,0],[0,2]]}]}}]}
    with pytest.raises(ValueError,match='RING_ROLE_DEPTH_MISMATCH'):
        a.owner_mask(scene,'right_arm')

def test_bad_source_rejected(real, tmp_path):
    f=tmp_path/'bad.png';f.write_bytes(GC.read_bytes()+b'X')
    with pytest.raises(ValueError,match='SIGNED_INPUT_SHA_FAIL'):
        a.read_source(f,'GC001')

def test_bad_scene_rejected(real, tmp_path):
    f=tmp_path/'bad.json';f.write_bytes(GS.read_bytes()+b' ')
    with pytest.raises(ValueError,match='SIGNED_INPUT_SHA_FAIL'):
        a.read_scene(f,'GC001')

def test_bad_snapshot_rejected(real, tmp_path):
    f=tmp_path/'bad.zip';f.write_bytes(SNAP.read_bytes()+b'X')
    with pytest.raises(ValueError,match='SIGNED_INPUT_SHA_FAIL'):
        a.phase04_mask_from_signed_zip(f,'right_arm')

def test_snapshot_wrong_case_rejected(real):
    with pytest.raises(ValueError,match='SNAPSHOT_CASE_MISMATCH'):
        a.case_audit('Raden',RA,RS,SNAP)

def test_deterministic_real_two_case_readonly(real):
    g=a.case_audit('GC001',GC,GS,SNAP)[0]
    r=a.case_audit('Raden',RA,RS)[0]
    assert json.dumps([g,r],sort_keys=True)==json.dumps([real[0][0],real[1][0]],sort_keys=True)

def test_output_source_separation(real):
    with pytest.raises(ValueError,match='OUTPUT_MUST_NOT_OVERWRITE_INPUTS'):
        a.run(GC,GS,RA,RS,SNAP,GC)

def test_no_promotion_or_image_in_public_report():
    data=json.loads((Path(__file__).resolve().parents[2]/'docs/research/evidence/sa1060h_c02b4_alpha_rgb_public_20261010.json').read_text())
    assert data['release_authorized'] is False
    assert data['production_changed'] is False
    assert data['visual_golden']=='PENDING'
    assert data['source_stage8_original_budget']=='HOLD'
    assert not any(k in data for k in ('original_image_base64','source_pixels','approved_golden'))
