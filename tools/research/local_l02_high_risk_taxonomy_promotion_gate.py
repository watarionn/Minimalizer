"""Source-free audit of high-risk garment-owner additions from frozen models.

This does NOT score human labels or treat unknown pixels as negatives. It blocks
promotion of pants/bag/background model classes based solely on RGB proximity
when independent garment-specific support is insufficient. Known-case frontier
numbers remain diagnostics, never semantic PASS or unseen generalization.
"""
from __future__ import annotations
from collections.abc import Mapping

class TaxonomyPromotionHold(ValueError):
    pass

RISK_CLASSES = (0, 7, 25)

def audit_taxonomy_promotion(record: Mapping) -> dict:
    if not isinstance(record, Mapping):
        raise TaxonomyPromotionHold('INVALID_RECORD')
    counts = record.get('source_only_added_by_class')
    if not isinstance(counts, Mapping):
        raise TaxonomyPromotionHold('MISSING_MODEL_TAXONOMY_COUNTS')
    if any(type(k) is not str or not k.isdigit() or type(v) is not int or v < 0
           for k,v in counts.items()):
        raise TaxonomyPromotionHold('INVALID_MODEL_TAXONOMY_COUNTS')
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
    risky = sum(counts.get(str(k),0) for k in RISK_CLASSES)
    unsupported_lower_bound = max(0, risky - independent)
    # Independent support is a necessary, never sufficient, condition. A
    # generic-clothes observer does not count as garment-specific evidence.
    hold = unsupported_lower_bound > 0
    return {
        'schema':'minimalizer/local-l02/high-risk-taxonomy-promotion-gate/v1',
        'high_risk_added_pixels':risky,
        'high_risk_unsupported_lower_bound':unsupported_lower_bound,
        'human_unlabelled_added_pixels_unknown_not_negative':unknown,
        'semantic_promotion':'HOLD' if hold else 'NOT_AUTHORIZED_BY_THIS_AUDIT',
        'reason':'MODEL_CLASS_0_7_25_UNSUPPORTED' if hold else 'FURTHER_SEMANTIC_REVIEW_REQUIRED',
        'known_case_frontier_is_not_semantic_pass':True,
        'unknown_pixels_treated_as_negative':False,
        'L02':'HOLD','Phase4':'FAIL','L03':'NO_GO','Golden':'HOLD','production':'NO_GO',
    }
