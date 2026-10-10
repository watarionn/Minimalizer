"""C02b6: deterministic source authority checks; real inputs remain private."""
import hashlib
import json
import os
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/research'))
import c02b6_phase04_producer_chain as m

BASE = Path(os.environ.get('SA1060_C02_SIGNED_DIR', '/__signed_c02_not_available__'))
SNAP = BASE / 'GC001_Phase03_Phase04_ReadOnlySnapshot_20261009.zip'
HIST = BASE / 'full_character_svg_metrics.json'
SCENE = BASE / 'GC001_phase8_adaptive_source_contour_research.json'

@pytest.fixture(scope='module')
def signed():
    if not all(p.is_file() for p in (SNAP, HIST, SCENE)):
        pytest.skip('private signed inputs unavailable')
    return m.audit(SNAP, HIST, SCENE)

def test_config_canonical_hash_order_independent():
    a = {'a': 1, 'b': 'hello'}
    assert m.canonical_config_hash(a) == m.canonical_config_hash({'b': 'hello', 'a': 1})

def test_checked_rejects_tampering(tmp_path):
    f = tmp_path / 'altered.json'
    f.write_bytes(b'not signed')
    with pytest.raises(ValueError, match='SIGNED_SHA_MISMATCH'):
        m.checked(f, m.HISTORICAL_METRICS_SHA)

def test_real_current_phase03_phase04_sha_chain(signed):
    assert signed['phase03_to_current_phase04_input_sha_chain_verified']
    assert signed['phase03_config_sha256'] == '0984eed6a1967847a60b32365c193ab75c6014ebafab6211b4a2424f4996c05e'
    assert signed['phase04_current_config_sha256'] == '037d8107f72e15f39c3b4dcc812471933d8edb19512e53be15a226cd5716f8b8'

def test_historical_config_unavailable_not_invented(signed):
    assert signed['historical_sa1041_stage04_config_sha256'] is None
    assert signed['historical_producer_config_lineage_proven'] is False

def test_left_arm_revision_mismatch(signed):
    owners = signed['owner_raw_sha_comparison']
    assert owners['left_arm']['same_raw_mask'] is False
    assert owners['right_arm']['same_raw_mask'] is True
    assert owners['face']['same_raw_mask'] is True

def test_source_refs_do_not_pin_sha(signed):
    assert all(not r['stage8_reference_pins_mask_sha'] for r in signed['owner_raw_sha_comparison'].values())

def test_no_artistic_or_release_promotion(signed):
    assert signed['semantic_arm_owner_verified'] is False
    assert signed['stage8_original_budget'] == 'HOLD'
    assert signed['human_golden'] == 'PENDING'
    assert signed['release_authorized'] is False
    assert signed['production_changed'] is False

def test_two_runs_identical(signed):
    assert m.audit(SNAP, HIST, SCENE) == signed
    assert m.audit(SNAP, HIST, SCENE) == signed

def test_source_files_unchanged(signed):
    assert m.sha(SNAP.read_bytes()) == m.SNAPSHOT_SHA
    assert m.sha(HIST.read_bytes()) == m.HISTORICAL_METRICS_SHA
    assert m.sha(SCENE.read_bytes()) == m.STAGE8_SHA
