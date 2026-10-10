"""C02b7c: adversarial independence/abstention and SHA-pinned two-case replay."""
from __future__ import annotations
import os
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'research'))
sys.path.insert(0, str(Path(__file__).parent))
import c02b7c_independent_owner_evidence_gate as g

BASE = Path(os.environ.get('SA1060_C02_SIGNED_DIR', '/__private_signed_not_available__'))
PINS = g.CASE_PINS


def record(case='GC001', owner='right_arm', xy=(12, 15), family='segmentation', observer='modelA', confidence=.95, lineage_char='1'):
    return {"observer_id": observer, "observer_family": family,
            "observer_lineage_sha256": lineage_char * 64, "run_sha256": ('a' if observer=='modelA' else 'b')*64,
            "source_sha256": PINS[case]['source'], "case": case,
            "input_provenance": ["original_source_only"],
            "origin": "source_only_semantic_model", "calibrated": True,
            "owner": owner, "point": list(xy), "confidence": confidence}


def test_no_independent_observers_abstains():
    r=g.inspect('GC001',PINS['GC001']['source'],[])
    assert r['outcome']=='ABSTAIN_NO_INDEPENDENT_ANCHORS' and r['candidate']=='NONE'
    assert not r['owner_ground_truth_verified'] and not r['release_authorized']


def test_single_vision_model_abstains():
    r=g.inspect('GC001',PINS['GC001']['source'],[record()])
    assert r['low_confidence_locations']==1 and r['review_only_agreement_locations']==0


def test_two_models_same_family_abstain():
    r=g.inspect('GC001',PINS['GC001']['source'],[record(),record(family='segmentation',observer='modelB',lineage_char='2')])
    assert r['insufficient_independence_locations']==1


def test_shared_model_lineage_abstain():
    r=g.inspect('GC001',PINS['GC001']['source'],[record(),record(family='pose',observer='modelB',lineage_char='1')])
    assert r['insufficient_independence_locations']==1


def test_two_distinct_high_confidence_only_review():
    r=g.inspect('GC001',PINS['GC001']['source'],[record(),record(family='pose',observer='modelB',lineage_char='2')])
    assert r['outcome']=='REVIEW_ONLY_UNVERIFIED_INDEPENDENCE'
    assert r['review_only_agreement_locations']==1 and r['candidate']=='NONE'
    assert not r['independence_cryptographically_verified'] and not r['owner_ground_truth_verified']
    assert r['owner_mask_modifications']==0 and not r['release_authorized']



def test_one_observer_cannot_claim_independence_with_two_runs():
    a=record()
    b=record(family='pose', lineage_char='2')
    b['run_sha256']='f'*64
    r=g.inspect('GC001', PINS['GC001']['source'], [a,b])
    assert r['insufficient_independence_locations']==1
    assert r['candidate']=='NONE'

def test_conflicting_labels_never_promote():
    r=g.inspect('GC001',PINS['GC001']['source'],[record(),record(owner='hair',family='pose',observer='modelB',lineage_char='2')])
    assert r['conflicting_locations']==1 and r['review_only_agreement_locations']==0


def test_low_confidence_abstains_even_with_two_families():
    r=g.inspect('GC001',PINS['GC001']['source'],[record(),record(family='pose',observer='modelB',lineage_char='2',confidence=.5)])
    assert r['low_confidence_locations']==1


def test_wrong_case_source_and_reused_raden_anchor_fail_closed():
    r=record()
    r['case']='Raden'
    with pytest.raises(ValueError,match='SOURCE_BINDING_MISMATCH'):
        g.inspect('GC001',PINS['GC001']['source'],[r])


def test_stage8_mask_consumption_forbidden():
    r=record();r['input_provenance']=['original_source_only','stage8']
    with pytest.raises(ValueError,match='INDEPENDENCE_CLAIM_INVALID'):
        g.inspect('GC001',PINS['GC001']['source'],[r])


def test_mask_colored_threshold_origin_forbidden():
    r=record();r['origin']='canny'
    with pytest.raises(ValueError,match='INDEPENDENCE_CLAIM_INVALID'):
        g.inspect('GC001',PINS['GC001']['source'],[r])


def test_nan_and_boolean_confidence_forbidden():
    for val in (float('nan'),True,float('inf'),-1,1.1):
        r=record();r['confidence']=val
        with pytest.raises(ValueError,match='CONFIDENCE_INVALID'):
            g.inspect('GC001',PINS['GC001']['source'],[r])


def test_out_of_bounds_or_nonint_point_forbidden():
    for xy in ([340,1],[-1,0],[5.0,2],[True,2],[1],[1,2,3]):
        r=record();r['point']=xy
        with pytest.raises(ValueError,match='POINT_INVALID'):
            g.inspect('GC001',PINS['GC001']['source'],[r])


def test_duplicate_same_run_same_pixel_forbidden():
    r=record()
    with pytest.raises(ValueError,match='DUPLICATE_OBSERVER_LOCATION'):
        g.inspect('GC001',PINS['GC001']['source'],[r,r])


def test_unknown_owner_and_extra_fields_forbidden():
    r=record();r['owner']='eye'
    with pytest.raises(ValueError,match='UNKNOWN_OWNER'):
        g.inspect('GC001',PINS['GC001']['source'],[r])
    r=record();r['claimed_pixel_truth']=True
    with pytest.raises(ValueError,match='SCHEMA_FAIL_CLOSED'):
        g.inspect('GC001',PINS['GC001']['source'],[r])


def test_missing_case_or_improper_payload_forbidden():
    with pytest.raises(ValueError,match='TARGET_CASE_SHA_MISMATCH'):
        g.inspect('Raden',PINS['GC001']['source'],[])
    with pytest.raises(ValueError,match='OBSERVATIONS_MUST_BE_LIST'):
        g.inspect('GC001',PINS['GC001']['source'],{})
    with pytest.raises(ValueError,match='BOTH_SIGNED_CASES_REQUIRED'):
        g.run_private({'GC001':(Path('x'),Path('y'))})


@pytest.fixture(scope='module')
def signed():
    files={k:(BASE/f'{k}_source.png',BASE/f'{k}_phase8_adaptive_source_contour_research.json') for k in ('GC001','Raden')}
    if not all(p.exists() for pair in files.values() for p in pair):
        pytest.skip('private SHA-pinned GC001 and Raden missing')
    return files


def test_two_sha_pinned_originals_abstain_without_independent_semantics(signed):
    r=g.run_private(signed)
    assert [x['case'] for x in r['cases']]==['GC001','Raden']
    assert all(x['outcome']=='ABSTAIN_NO_INDEPENDENT_ANCHORS' and x['observer_claims']==0 for x in r['cases'])
    assert not r['semantic_model_executed'] and not r['release_authorized'] and not r['deployment_verified']
    assert r==g.run_private(signed)


def test_tampered_source_fails_closed(signed, tmp_path):
    path=tmp_path/'bad.png'
    path.write_bytes(signed['GC001'][0].read_bytes()+b'\0')
    bad=dict(signed);bad['GC001']=(path,signed['GC001'][1])
    with pytest.raises(ValueError,match='SIGNED_SOURCE_OR_SCENE_SHA_MISMATCH'):
        g.run_private(bad)


def test_tampered_scene_fails_closed(signed,tmp_path):
    path=tmp_path/'bad.json'
    path.write_bytes(signed['Raden'][1].read_bytes()+b' ')
    bad=dict(signed);bad['Raden']=(signed['Raden'][0],path)
    with pytest.raises(ValueError,match='SIGNED_SOURCE_OR_SCENE_SHA_MISMATCH'):
        g.run_private(bad)


def test_merged_real_source_rejects_any_cross_case_submissions(signed):
    subs={'GC001':[record(case='Raden')],'Raden':[]}
    with pytest.raises(ValueError,match='SOURCE_BINDING_MISMATCH'):
        g.run_private(signed,subs)
