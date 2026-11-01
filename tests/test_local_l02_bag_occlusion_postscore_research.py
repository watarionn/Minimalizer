"""Synthetic contract tests only; not signed-character quality PASS."""
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_bag_occlusion_postscore_research import audit_bag_occlusion_postscore, BagOcclusionAuditHold


def fixture():
    # 25 on 3 pixels; one human outerwear conflict, one explicit negative,
    # one unknown. No model-derived bag pixels are promoted to garment.
    c = np.array([[25, 25, 25], [32, 0, 0]], np.uint8)
    owner = np.array([[0, 2, 1], [2, 0, 0]], np.uint8)
    opaque = np.array([[1, 1, 1], [1, 0, 0]], np.uint8)
    pos = np.array([[1, 0, 0], [1, 0, 0]], np.uint8)
    neg = np.array([[0, 1, 0], [0, 0, 0]], np.uint8)
    ind = np.array([[1, 1, 1], [0, 0, 0]], np.uint8)
    return dict(class_ids=c, owner=owner, opaque=opaque,
                known_outerwear=pos, known_non_outerwear=neg,
                garment_owner_id=2, independent_outerwear=ind)


def test_postscore_only_and_partition_no_mutation():
    x=fixture(); originals={k:v.copy() for k,v in x.items() if isinstance(v,np.ndarray)}
    r=audit_bag_occlusion_postscore(**x); c=r['counts']
    assert (c['bag_class25_visible_px'], c['bag_class25_reviewed_outerwear_conflict_px'],
            c['bag_class25_reviewed_non_outerwear_px'], c['bag_class25_unknown_px'])==(3,1,1,1)
    assert (c['bag_class25_on_garment_owner_px'],c['bag_class25_unowned_px'],c['bag_class25_other_owner_px'])==(1,1,1)
    assert (c['bag_class25_independent_outerwear_overlap_px'],c['bag_class25_independent_outerwear_reviewed_conflict_px'],c['bag_class25_independent_outerwear_reviewed_non_outerwear_px'],c['bag_class25_independent_outerwear_unknown_px'])==(3,1,1,1)
    assert r['metric_override_allowed'] is False and r['owner_modified'] is False
    assert r['Phase4']=='FAIL' and r['L02']=='HOLD' and r['production']=='NO_GO'
    assert all(np.array_equal(x[k],v) for k,v in originals.items())
    assert not any(isinstance(v,np.ndarray) for v in r.values())


def test_optional_independent_observer_not_imputed():
    x=fixture();x['independent_outerwear']=None
    r=audit_bag_occlusion_postscore(**x)
    assert all('independent' not in k for k in r['counts'])


@pytest.mark.parametrize('field', ['opaque','known_outerwear','known_non_outerwear','independent_outerwear'])
def test_invalid_mask_rejected(field):
    x=fixture();x[field]=np.full((2,3),2,np.uint8)
    with pytest.raises(BagOcclusionAuditHold):audit_bag_occlusion_postscore(**x)


def test_overlap_known_labels_rejected():
    x=fixture();x['known_non_outerwear'][0,0]=1
    with pytest.raises(BagOcclusionAuditHold,match='INVALID_REVIEW_OR_SOURCE_DOMAIN'):
        audit_bag_occlusion_postscore(**x)


def test_human_labels_outside_alpha_rejected():
    x=fixture();x['known_outerwear'][1,1]=1
    with pytest.raises(BagOcclusionAuditHold,match='INVALID_REVIEW_OR_SOURCE_DOMAIN'):
        audit_bag_occlusion_postscore(**x)


def test_owner_outside_alpha_rejected():
    x=fixture();x['owner'][1,1]=2
    with pytest.raises(BagOcclusionAuditHold,match='INVALID_REVIEW_OR_SOURCE_DOMAIN'):
        audit_bag_occlusion_postscore(**x)


def test_bad_owner_and_source_rejected():
    x=fixture();x['garment_owner_id']=0
    with pytest.raises(BagOcclusionAuditHold,match='INVALID_GARMENT_OWNER_ID'):
        audit_bag_occlusion_postscore(**x)
    x=fixture();x['class_ids']=x['class_ids'].astype(np.int16)
    with pytest.raises(BagOcclusionAuditHold,match='INVALID_FROZEN_MODEL_OR_OWNER'):
        audit_bag_occlusion_postscore(**x)


def test_independent_positive_outside_source_alpha_is_not_silently_ignored():
    x = fixture()
    # The signed source is transparent here; the independent model must not
    # supply positive pixels outside it, even if bag metrics would ignore them.
    x['independent_outerwear'][1, 1] = 1
    with pytest.raises(BagOcclusionAuditHold, match='INDEPENDENT_OBSERVER_OUTSIDE_SOURCE_ALPHA'):
        audit_bag_occlusion_postscore(**x)
