"""Synthetic contract tests, not signed-character quality evidence."""
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_atr_dual_head_disagreement_research import (
    ATRHeadAuditHold, audit_atr_head_disagreement,
)


def case():
    raw = np.array([[16, 16, 14], [4, 0, 0]], dtype=np.uint8)
    refined = np.array([[16, 4, 15], [4, 0, 0]], dtype=np.uint8)
    alpha = np.array([[255, 255, 255], [255, 0, 0]], dtype=np.uint8)
    return dict(raw_ids=raw, refined_ids=refined, source_alpha=alpha)


def test_disagreement_is_postscore_free_and_does_not_mutate():
    x = case(); before = {k:v.copy() for k,v in x.items()}
    r = audit_atr_head_disagreement(**x)
    assert r['counts']['head_disagreement_px'] == 2
    assert r['counts']['bag_raw_only_px'] == 1
    assert r['counts']['upper_clothes_refined_only_px'] == 1
    assert r['counts']['left_arm_raw_only_px'] == 1
    assert r['counts']['right_arm_refined_only_px'] == 1
    assert r['head_selection_authorized'] is False
    assert r['owner_modified'] is False and r['Phase4'] == 'FAIL'
    assert all(np.array_equal(before[k],v) for k,v in x.items())
    assert not any(isinstance(v,np.ndarray) for v in r.values())


@pytest.mark.parametrize('field', ['raw_ids','refined_ids'])
def test_bad_taxonomy_rejected(field):
    x=case(); x[field][0,0]=18
    with pytest.raises(ATRHeadAuditHold, match='TAXONOMY'):
        audit_atr_head_disagreement(**x)


@pytest.mark.parametrize('field', ['raw_ids','refined_ids'])
def test_outside_alpha_rejected(field):
    x=case(); x[field][1,1]=16
    with pytest.raises(ATRHeadAuditHold, match='OUTSIDE_SOURCE_ALPHA'):
        audit_atr_head_disagreement(**x)


def test_malformed_shape_and_alpha_rejected():
    x=case();x['refined_ids']=np.zeros((2,2),np.uint8)
    with pytest.raises(ATRHeadAuditHold, match='INVALID_ATR_HEAD'):
        audit_atr_head_disagreement(**x)
    x=case();x['source_alpha']=x['source_alpha'].astype(bool)
    with pytest.raises(ATRHeadAuditHold, match='INVALID_ATR_HEAD'):
        audit_atr_head_disagreement(**x)


def test_opaque_without_predictions_is_not_negative_evidence():
    x=case();x['raw_ids'][:]=0;x['refined_ids'][:]=0
    r=audit_atr_head_disagreement(**x)
    assert r['counts']['head_disagreement_px']==0
    assert r['counts']['opaque_px']==4
    assert r['unknown_treated_as_negative'] is False
