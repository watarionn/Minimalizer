"""SA10.49 signed original-identity vs Stage37 flat reference audit tests."""
from pathlib import Path
import os, sys, json, hashlib
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import sa1049_source_detail_dual_gate as s

@pytest.fixture
def inputs():
    a=os.environ.get('SA1049_RADEN_ROOT');b=os.environ.get('SA1049_GC001_ROOT')
    if not a or not b: pytest.skip('Private SHA-authorized test images not distributed')
    return Path(a),Path(b)

def test_case_authority_signature(inputs):
    for name,root in zip(s.CASES,inputs):
        case=s.load_case(name,root)
        assert case['photo'].shape==(340,340,3)
        assert case['frozen'].shape==(340,340,3)

def test_detail_never_equal_flat_face(inputs):
    for name,root in zip(s.CASES,inputs):
        a=s.audit(s.load_case(name,root))
        assert not a['all_face_fidelity_and_flat_face_gate_simultaneously_satisfiable']
        assert a['face']['frozen_distinct_rgb_colors']==1
        assert a['face']['source_distinct_rgb_colors']>1000

def test_frozen_analytical_counts(inputs):
    expected={'Raden':{'face':4047,'left_arm':10419,'right_arm':9844},
              'GC001':{'face':4936,'left_arm':2715,'right_arm':6486}}
    for name,root in zip(s.CASES,inputs):
        measured=s.audit(s.load_case(name,root))
        assert {k:measured[k]['source_vs_flat_rgb_mismatch'] for k in s.ROLES}==expected[name]

def test_fails_closed_on_modified_source(inputs,tmp_path):
    root=inputs[1]
    from shutil import copy2
    for name in s.CASES['GC001']['root_required']:copy2(root/name,tmp_path/name)
    (tmp_path/'GC001_source.png').write_bytes((tmp_path/'GC001_source.png').read_bytes()+b'corruption')
    with pytest.raises(ValueError,match='SIGNED_SOURCE_HASH_MISMATCH'):s.load_case('GC001',tmp_path)

def test_no_input_overwrite(inputs):
    with pytest.raises(ValueError,match='distinct'):s.evaluate(inputs[0],inputs[1],inputs[1])

def test_identity_source_audit_and_outputs(inputs,tmp_path):
    r=s.evaluate(*inputs,tmp_path)
    assert r['production_deployment']=='UNCHANGED' and r['full_character_golden']=='HOLD'
    assert r['new_facial_anatomy_synthesized'] is False and r['svg_modified'] is False
    assert all(c['source_fidelity_and_flat_face_parity_are_mutually_exclusive'] for c in r['cases'].values())
    assert (tmp_path/'two_case_source_vs_flat_authority.png').exists()
    assert hashlib.sha256((tmp_path/'two_case_source_vs_flat_authority.png').read_bytes()).hexdigest()==r['asset_sha256']['two_case_source_vs_flat_authority.png']
