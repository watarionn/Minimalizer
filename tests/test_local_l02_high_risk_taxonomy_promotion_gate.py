import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
import pytest
from local_l02_high_risk_taxonomy_promotion_gate import (
    audit_taxonomy_promotion, TaxonomyPromotionHold)

def rec(**overrides):
    r={'source_only_added_by_class':{'30':849,'32':5},
       'total_added_source_pixels':854,
       'independent_specific_outerwear_supported_added_pixels':0,
       'human_unlabelled_added_pixels':5,
       'signed_source_verified':True,'frozen_model_verified':True,
       'human_labels_used_for_inference':False}
    r.update(overrides)
    return r

def test_existing_class30_class32_optin_is_not_auto_approved():
    a=audit_taxonomy_promotion(rec())
    assert a['semantic_promotion']=='NOT_AUTHORIZED_BY_THIS_AUDIT'
    assert a['L02']=='HOLD' and a['Phase4']=='FAIL'

def test_known_tp_gain_cannot_hide_large_pants_background_exposure():
    a=audit_taxonomy_promotion(rec(
       source_only_added_by_class={'0':4185,'7':8770},
       total_added_source_pixels=12955,
       independent_specific_outerwear_supported_added_pixels=1,
       human_unlabelled_added_pixels=10035))
    assert a['semantic_promotion']=='HOLD'
    assert a['high_risk_unsupported_lower_bound']==12954
    assert a['human_unlabelled_added_pixels_unknown_not_negative']==10035

def test_specific_support_only_removes_this_particular_veto():
    a=audit_taxonomy_promotion(rec(source_only_added_by_class={'7':20},
       total_added_source_pixels=20,
       independent_specific_outerwear_supported_added_pixels=20,
       human_unlabelled_added_pixels=20))
    assert a['semantic_promotion']=='NOT_AUTHORIZED_BY_THIS_AUDIT'

def test_generic_clothes_not_counted_as_independent_specific_support():
    a=audit_taxonomy_promotion(rec(source_only_added_by_class={'25':100},
       total_added_source_pixels=100,
       independent_specific_outerwear_supported_added_pixels=0,
       human_unlabelled_added_pixels=100))
    assert a['reason']=='MODEL_CLASS_0_7_25_UNSUPPORTED'

@pytest.mark.parametrize('patch',[
    {'total_added_source_pixels':855},
    {'human_unlabelled_added_pixels':855},
    {'independent_specific_outerwear_supported_added_pixels':855},
    {'signed_source_verified':False},
    {'human_labels_used_for_inference':True},
    {'source_only_added_by_class':{'7':-1}},
    {'source_only_added_by_class':{'pants':10}},
])
def test_fail_closed_on_invalid_provenance_or_counts(patch):
    with pytest.raises(TaxonomyPromotionHold):audit_taxonomy_promotion(rec(**patch))
