import json,os,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).parent))
import c02b7a_prospective_source_binding as m
BASE=Path(os.environ.get('SA1060_C02_SIGNED_DIR','/__private_signed_not_available__'))
SNAP=BASE/'GC001_Phase03_Phase04_ReadOnlySnapshot_20261009.zip'
STAGE=BASE/'GC001_phase8_adaptive_source_contour_research.json'
@pytest.fixture(scope='module')
def binding():
    if not SNAP.exists() or not STAGE.exists():pytest.skip('private inputs missing')
    return m.propose(SNAP,STAGE)
def test_pinned_stage_inputs(binding):
    assert m.sha(SNAP.read_bytes())==m.SNAP_SHA
    assert m.sha(STAGE.read_bytes())==m.STAGE8_SHA
def test_prospective_scope_only(binding):
    assert binding['scope']=='RECOVERED_CURRENT_PHASE04_ONLY_NOT_HISTORICAL_STAGE8_PROOF'
    assert binding['historical_stage8_used_this_revision']=='UNPROVEN'
    assert binding['cryptographic_signature']=='NONE'
def test_current_raw_mask_binding(binding):
    assert len(binding['phase04_mask_raw_sha256'])==3
    assert binding['phase04_mask_raw_sha256']['left_arm']=='cb707edab78c6d0715de5fcb811f6e0595baa53c9f5c8cd3290be420ba06061d'
def test_input_chain(binding):
    assert binding['phase03_stage_sha256']=='c1485333f581e26ca75e2d425cc09f061ff06d721839777300ee73da829d460c'
    assert binding['phase04_config_sha256']=='037d8107f72e15f39c3b4dcc812471933d8edb19512e53be15a226cd5716f8b8'
def test_validates_exact_binding(binding):assert m.validate(SNAP,STAGE,binding)
def test_tamper_sidecar_rejected(binding):
    b=json.loads(json.dumps(binding));b['phase04_mask_raw_sha256']['left_arm']='0'*64
    with pytest.raises(ValueError,match='PROSPECTIVE_BINDING_MISMATCH'):m.validate(SNAP,STAGE,b)
def test_tamper_source_rejected(binding,tmp_path):
    bad=tmp_path/'bad.zip';bad.write_bytes(SNAP.read_bytes()+b'X')
    with pytest.raises(ValueError,match='SIGNED_INPUT_SHA_MISMATCH'):m.propose(bad,STAGE)
def test_no_release_claim(binding):
    assert binding['candidate_promoted'] is False
    assert binding['release_authorized'] is False and binding['production_changed'] is False
    assert binding['human_golden']=='PENDING' and binding['original_stage8_budget']=='HOLD'
def test_deterministic(binding):assert m.propose(SNAP,STAGE)==m.propose(SNAP,STAGE)==binding
