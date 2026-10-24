"""Source-free, fail-closed audit of high-risk garment-owner additions.

Counts are from frozen, signed-source model observations, never human labels.
Unknown human pixels are neither negatives nor evidence of garment ownership.
A global independent-model overlap count cannot establish that its support
covers *the same* high-risk model-class pixels: require verified intersections.
This module never authorizes semantic promotion or production release.
"""
from __future__ import annotations
from collections.abc import Mapping

class TaxonomyPromotionHold(ValueError):
    pass

RISK_CLASSES = (0, 7, 25)


def _valid_counts(value, reason):
    if not isinstance(value, Mapping) or any(
            type(k) is not str or not k.isdigit() or type(v) is not int or v < 0
            for k, v in value.items()):
        raise TaxonomyPromotionHold(reason)
    return value


def audit_taxonomy_promotion(record: Mapping) -> dict:
    if not isinstance(record, Mapping):
        raise TaxonomyPromotionHold('INVALID_RECORD')
    counts = _valid_counts(record.get('source_only_added_by_class'),
                           'MISSING_OR_INVALID_MODEL_TAXONOMY_COUNTS')
    total = record.get('total_added_source_pixels')
    independent = record.get('independent_specific_outerwear_supported_added_pixels')
    unknown = record.get('human_unlabelled_added_pixels')
    if (any(type(v) is not int or v < 0 for v in (total, independent, unknown)) or
            sum(counts.values()) != total or independent > total or unknown > total):
        raise TaxonomyPromotionHold('INVALID_ADDITION_ACCOUNTING')
    if record.get('signed_source_verified') is not True or record.get('frozen_model_verified') is not True:
        raise TaxonomyPromotionHold('UNVERIFIED_SOURCE_OR_MODEL')
    if record.get('human_labels_used_for_inference') is not False:
        raise TaxonomyPromotionHold('HUMAN_LABEL_LEAKAGE')
    if independent and record.get('independent_specific_outerwear_verified') is not True:
        raise TaxonomyPromotionHold('UNVERIFIED_INDEPENDENT_OUTERWEAR')

    risky = sum(counts.get(str(k), 0) for k in RISK_CLASSES)
    support = record.get('independent_specific_outerwear_supported_added_by_class')
    intersection_verified = record.get('class_intersection_verified') is True
    # Without a class-by-class intersection, global independent support might
    # be entirely on *safe* classes. It must never cancel a risky-class veto.
    if support is not None:
        support = _valid_counts(support, 'INVALID_CLASS_INTERSECTION_COUNTS')
        if (any(k not in counts or v > counts[k] for k, v in support.items()) or
                sum(support.values()) != independent):
            raise TaxonomyPromotionHold('INVALID_CLASS_INTERSECTION_ACCOUNTING')
        if not intersection_verified:
            raise TaxonomyPromotionHold('UNVERIFIED_CLASS_INTERSECTION')
    elif intersection_verified:
        raise TaxonomyPromotionHold('MISSING_CLASS_INTERSECTION_COUNTS')

    proven_risky_support = (sum(support.get(str(k), 0) for k in RISK_CLASSES)
                            if support is not None and intersection_verified else 0)
    unsupported = risky - proven_risky_support
    missing_intersection = bool(risky and independent and support is None)
    hold = unsupported > 0
    return {
        'schema': 'minimalizer/local-l02/high-risk-taxonomy-promotion-gate/v2',
        'high_risk_added_pixels': risky,
        'high_risk_verified_independent_supported_pixels': proven_risky_support,
        'high_risk_unsupported_or_unverified_pixels': unsupported,
        # This remains a valid *mathematical* lower bound for legacy consumers;
        # it is NOT a substitute for intersection verification.
        'high_risk_unsupported_lower_bound': max(0, risky - independent),
        'class_intersection_verified': bool(support is not None and intersection_verified),
        'human_unlabelled_added_pixels_unknown_not_negative': unknown,
        'semantic_promotion': 'HOLD' if hold else 'NOT_AUTHORIZED_BY_THIS_AUDIT',
        'reason': ('CLASS_SUPPORT_INTERSECTION_MISSING' if missing_intersection else
                   'MODEL_CLASS_0_7_25_UNSUPPORTED' if hold else
                   'FURTHER_SEMANTIC_REVIEW_REQUIRED'),
        'known_case_frontier_is_not_semantic_pass': True,
        'unknown_pixels_treated_as_negative': False,
        'L02': 'HOLD', 'Phase4': 'FAIL', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
