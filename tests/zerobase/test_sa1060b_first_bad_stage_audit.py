"""Synthetic and pinned-real GC001/Raden Stage04 owner lineage checks."""
from pathlib import Path
import importlib.util
import json
import os

import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[2]/'tools/research/sa1060b_first_bad_stage_audit.py'
if not SCRIPT.is_file():
    SCRIPT = Path(__file__).with_name('sa1060b_first_bad_stage_audit.py')
spec = importlib.util.spec_from_file_location('sa1060b_first_bad_stage_audit', SCRIPT)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


def synthetic(bg=(125, 32, 50)):
    photo = np.full((340, 340, 3), bg, np.uint8)
    alpha = np.full((340, 340), 255, np.uint8)
    return photo, alpha


def test_exact_border_connected_rgb_only():
    photo, alpha = synthetic()
    photo[80:110, 80:110] = (30, 60, 90)
    photo[85:90, 85:90] = (125,32,50)
    region, details = s.source_connected_background(photo,alpha)
    assert details['dominant_border_exact_rgb'] == [125,32,50]
    assert region[1,1] and not region[80,80]
    assert not region[86,86]  # Same RGB but disconnected, never blindly delete.


def test_partial_alpha_is_not_auto_deleted_from_candidate():
    photo, alpha = synthetic()
    alpha[0,0]=128
    mask=np.zeros((340,340),bool)
    mask[0,0]=True; mask[0,1]=True
    sample={'right_arm':mask,'left_arm':np.zeros_like(mask),'face':np.zeros_like(mask)}
    result,connected,candidate=s.diagnose(photo,alpha,sample,None)
    assert result['source_background_connected_intersection']['right_arm']==2
    assert result['fully_opaque_source_background_intersection']['right_arm']==1
    assert candidate[0,0] and not candidate[0,1]
    assert result['right_arm_candidate']['partially_transparent_exact_rgb_overlap_not_auto_removed']==1


def test_fails_closed_when_border_anchor_uncertain():
    photo=np.random.default_rng(11).integers(0,256,(340,340,3),dtype=np.uint8)
    _,alpha=synthetic()
    with pytest.raises(ValueError,match='BACKGROUND_RGB_ANCHOR_AMBIGUOUS'):
        s.source_connected_background(photo,alpha)


def test_empty_or_transparent_border_rejected():
    photo,alpha=synthetic();alpha[:]=0
    with pytest.raises(ValueError,match='NO_OPAQUE_BORDER_RGB_ANCHOR'):
        s.source_connected_background(photo,alpha)


def test_no_source_image_or_masks_cannot_fake_pins(tmp_path):
    with pytest.raises(ValueError,match='SIGNED_SOURCE_CHANGED_OR_MISSING'):
        s.signed_check(tmp_path,s.GC_SHA)


def test_outputs_cannot_overlap_signed_input(tmp_path):
    with pytest.raises(ValueError,match='SIGNED_INPUT_OUTPUT_NOT_SEPARATE'):
        s.run(tmp_path,tmp_path/'raden',tmp_path/'phase8.json',tmp_path/'results')


def test_wrong_stage8_role_or_polarity_rejected():
    with pytest.raises(ValueError,match='STAGE8_ROLE_NOT_UNIQUE'):
        s.ring_raster([],'right_arm')
    bad=[{'source_mask_owner':'right_arm','parameters':{'rings':[{'depth':0,'role':'hole','points':[[0,0],[2,0],[0,2]]}]}}]
    with pytest.raises(ValueError,match='STAGE8_RING_POLARITY_MISMATCH'):
        s.ring_raster(bad,'right_arm')


def test_sanitized_never_has_trace_or_private_keys():
    dummy={k:'HOLD' for k in ('stage','schema','first_demonstrable_bad_stage','origin_prior_to_phase04',
       'phase05_phase06_causal_path','source_background_color_semantic_authority','golden_human_review',
       'historic_stage8_ring_gate','phase15','production','next')}
    dummy['candidate_promotion_authorized']=False
    dummy['gc001']={'phase04_mask_pixels':{'right_arm':6486},'source_background_connected_intersection':{'right_arm':533},
                    'stage8':{},'right_arm_candidate':{'removed_from_signed_original':520,
                      'source_mask_connected_components_before':{'components':1},'candidate_components_after':{'components':1}}}
    dummy['raden_independent_control']={'phase04_mask_pixels':{'right_arm':9870},
                                        'source_background_connected_intersection':{'right_arm':3}}
    dummy['private_artifact_sha256']={'secret_source.png':'fake'}
    out=s.sanitized(dummy)
    assert not out['candidate_promotion_authorized']
    assert 'private_artifact_sha256' not in out
    assert 'points' not in json.dumps(out) and 'secret_source.png' not in json.dumps(out)


@pytest.fixture
def real_inputs():
    gc,ra,stage=[os.getenv(k) for k in ('SA1060B_GC_DIR','SA1060B_RADEN_DIR','SA1060B_STAGE8')]
    if not all((gc,ra,stage)):
        pytest.skip('Private signed sources not supplied')
    return Path(gc),Path(ra),Path(stage)


def test_pinned_real_phase04_stage8_first_bad_stage(real_inputs):
    gc,ra,stage=real_inputs
    s.signed_check(gc,s.GC_SHA);s.signed_check(ra,s.RADEN_SHA)
    assert s.digest(stage)==s.STAGE8_SHA
    photo,alpha=s.source_rgb(gc,'GC001_source.png')
    masks={role:s.mask_at(gc,'gc001_'+{'right_arm':'right','left_arm':'left','face':'face'}[role]+'.png') for role in s.ROLES}
    report,connected,candidate=s.diagnose(photo,alpha,masks,json.loads(stage.read_text()))
    assert report['source_background_connected_intersection']=={'right_arm':533,'left_arm':0,'face':0}
    assert report['fully_opaque_source_background_intersection']['right_arm']==520
    assert report['stage8']['right_arm']['source_background_connected_intersection']==533
    assert report['stage8']['right_arm']['xor_pixels_vs_signed_stage04']==24
    assert report['stage8']['left_arm']['xor_pixels_vs_signed_stage04']==5
    assert report['stage8']['face']['xor_pixels_vs_signed_stage04']==0
    assert candidate.sum()==masks['right_arm'].sum()-520
    assert not np.any(candidate&~masks['right_arm'])
    assert report['right_arm_candidate']['candidate_components_after']['components']==1


def test_private_replay_and_independent_control(real_inputs,tmp_path):
    gc,ra,stage=real_inputs
    info=s.run(gc,ra,stage,tmp_path/'new')
    assert info['first_demonstrable_bad_stage']=='PHASE04_SIGNED_RIGHT_ARM_MASK'
    assert info['origin_prior_to_phase04']=='NOT_ESTABLISHED'
    assert info['phase05_phase06_causal_path']=='NOT_INDIVIDUALLY_REPLAYED'
    assert not info['candidate_promotion_authorized'] and info['production']=='UNCHANGED'
    assert info['raden_independent_control']['source_background_connected_intersection']=={
        'right_arm':3,'left_arm':7,'face':0}
    assert (tmp_path/'new/gc001_phase04_stage8_diagnostic2_private.png').is_file()
    assert (tmp_path/'new/gc001_right_arm_phase04_candidate_v1_PRIVATE.png').is_file()
    # read only inputs remain exact-pinned after full experiment.
    s.signed_check(gc,s.GC_SHA);s.signed_check(ra,s.RADEN_SHA)
