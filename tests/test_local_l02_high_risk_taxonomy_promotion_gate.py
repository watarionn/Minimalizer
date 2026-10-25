import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
import pytest
from local_l02_high_risk_taxonomy_promotion_gate import (
    audit_taxonomy_promotion, TaxonomyPromotionHold)


def rec(**overrides):
    r = {'source_only_added_by_class': {'30': 849, '32': 5},
         'total_added_source_pixels': 854,
         'independent_specific_outerwear_supported_added_pixels': 0,
         'human_unlabelled_added_pixels': 5,
         'signed_source_verified': True, 'frozen_model_verified': True,
         'human_labels_used_for_inference': False}
    r.update(overrides)
    return r


def test_existing_class30_class32_optin_is_not_auto_approved():
    a = audit_taxonomy_promotion(rec())
    assert a['semantic_promotion'] == 'NOT_AUTHORIZED_BY_THIS_AUDIT'
    assert a['L02'] == 'HOLD' and a['Phase4'] == 'FAIL'


def test_signed_h06_pants_background_exposure_still_blocked():
    a = audit_taxonomy_promotion(rec(
        source_only_added_by_class={'0': 4185, '7': 8770},
        total_added_source_pixels=12955,
        independent_specific_outerwear_supported_added_pixels=1,
        independent_specific_outerwear_verified=True,
        human_unlabelled_added_pixels=10035))
    assert a['semantic_promotion'] == 'HOLD'
    assert a['high_risk_unsupported_lower_bound'] == 12954
    assert a['high_risk_unsupported_or_unverified_pixels'] == 12955
    assert a['human_unlabelled_added_pixels_unknown_not_negative'] == 10035


def test_global_support_on_safe_class_cannot_cancel_risky_class_veto():
    a = audit_taxonomy_promotion(rec(
        source_only_added_by_class={'7': 20, '30': 20},
        total_added_source_pixels=40,
        independent_specific_outerwear_supported_added_pixels=20,
        independent_specific_outerwear_verified=True,
        human_unlabelled_added_pixels=40,
        independent_specific_outerwear_supported_added_by_class={'30': 20},
        class_intersection_verified=True))
    assert a['semantic_promotion'] == 'HOLD'
    assert a['high_risk_unsupported_lower_bound'] == 0
    assert a['high_risk_unsupported_or_unverified_pixels'] == 20
    assert a['reason'] == 'MODEL_CLASS_0_7_25_UNSUPPORTED'


def test_missing_intersection_must_hold_even_if_global_support_covers_risk():
    a = audit_taxonomy_promotion(rec(
        source_only_added_by_class={'7': 20, '30': 20},
        total_added_source_pixels=40,
        independent_specific_outerwear_supported_added_pixels=20,
        independent_specific_outerwear_verified=True,
        human_unlabelled_added_pixels=40))
    assert a['semantic_promotion'] == 'HOLD'
    assert a['reason'] == 'CLASS_SUPPORT_INTERSECTION_MISSING'


def test_verified_same_class_intersection_only_removes_specific_veto():
    a = audit_taxonomy_promotion(rec(
        source_only_added_by_class={'7': 20}, total_added_source_pixels=20,
        independent_specific_outerwear_supported_added_pixels=20,
        independent_specific_outerwear_verified=True,
        human_unlabelled_added_pixels=20,
        independent_specific_outerwear_supported_added_by_class={'7': 20},
        class_intersection_verified=True))
    assert a['semantic_promotion'] == 'NOT_AUTHORIZED_BY_THIS_AUDIT'
    assert a['high_risk_unsupported_or_unverified_pixels'] == 0
    assert a['Phase4'] == 'FAIL'


def test_partial_same_class_intersection_remains_hold():
    a = audit_taxonomy_promotion(rec(
        source_only_added_by_class={'7': 20}, total_added_source_pixels=20,
        independent_specific_outerwear_supported_added_pixels=19,
        independent_specific_outerwear_verified=True,
        human_unlabelled_added_pixels=20,
        independent_specific_outerwear_supported_added_by_class={'7': 19},
        class_intersection_verified=True))
    assert a['semantic_promotion'] == 'HOLD'
    assert a['high_risk_unsupported_or_unverified_pixels'] == 1


def test_generic_clothes_not_independent_specific_support():
    a = audit_taxonomy_promotion(rec(source_only_added_by_class={'25': 100},
        total_added_source_pixels=100, human_unlabelled_added_pixels=100))
    assert a['reason'] == 'MODEL_CLASS_0_7_25_UNSUPPORTED'


@pytest.mark.parametrize('patch', [
    {'total_added_source_pixels': 855},
    {'human_unlabelled_added_pixels': 855},
    {'independent_specific_outerwear_supported_added_pixels': 855},
    {'signed_source_verified': False},
    {'human_labels_used_for_inference': True},
    {'source_only_added_by_class': {'7': -1}},
    {'source_only_added_by_class': {'pants': 10}},
    {'independent_specific_outerwear_supported_added_pixels': 1},
    {'class_intersection_verified': True},
    {'independent_specific_outerwear_supported_added_by_class': {'7': 1}},
    {'independent_specific_outerwear_supported_added_by_class': {'30': 1},
     'class_intersection_verified': True},
    {'source_only_added_by_class': {'7': 10, '30': 10},
     'total_added_source_pixels': 20,
     'independent_specific_outerwear_supported_added_pixels': 20,
     'independent_specific_outerwear_verified': True,
     'independent_specific_outerwear_supported_added_by_class': {'7': 21},
     'class_intersection_verified': True},
])
def test_fail_closed_on_invalid_provenance_or_counts(patch):
    with pytest.raises(TaxonomyPromotionHold):
        audit_taxonomy_promotion(rec(**patch))

def test_signed_h06_bag_observer_overlap_does_not_clear_accessory_veto():
    # Source-only class25 bag and garment-specific observer overlap 6,586px.
    # The visible signed RGB is a handbag; a reviewed coat polygon overlaps it.
    # Postscore labels are NOT semantic proof and are never gate inputs.
    a = audit_taxonomy_promotion(rec(
        source_only_added_by_class={'25': 6586},
        total_added_source_pixels=6586,
        independent_specific_outerwear_supported_added_pixels=6586,
        independent_specific_outerwear_verified=True,
        human_unlabelled_added_pixels=0,
        independent_specific_outerwear_supported_added_by_class={'25': 6586},
        class_intersection_verified=True))
    assert a['semantic_promotion'] == 'HOLD'
    assert a['reason'] == 'MODEL_CLASS_25_ACCESSORY_CONFLICT'
    assert a['class25_accessory_conflict_pixels'] == 6586
    assert a['high_risk_unsupported_or_unverified_pixels'] == 0
    assert a['Phase4'] == 'FAIL'


def test_accessory_conflict_is_not_cleared_by_safe_class_support():
    a = audit_taxonomy_promotion(rec(
        source_only_added_by_class={'25': 12, '30': 20},
        total_added_source_pixels=32,
        independent_specific_outerwear_supported_added_pixels=32,
        independent_specific_outerwear_verified=True,
        human_unlabelled_added_pixels=32,
        independent_specific_outerwear_supported_added_by_class={'25': 12, '30': 20},
        class_intersection_verified=True))
    assert a['reason'] == 'MODEL_CLASS_25_ACCESSORY_CONFLICT'
    assert a['semantic_promotion'] == 'HOLD'
    assert a['class25_accessory_conflict_pixels'] == 12

