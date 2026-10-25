"""Post-inference-only audit of residual known garment loss by frozen model class.

No candidate pixels are produced. Human review masks are accepted ONLY after
source-only owner proposals have been frozen; they are not inference inputs.
Unknown pixels remain unknown, and a coarse review can overlap occluding bags.
This diagnostic never authorizes a semantic owner, Golden, or release.
"""
from __future__ import annotations

import numpy as np


class ResidualTaxonomyHold(ValueError):
    pass


def audit_known_residual_taxonomy(*, source_alpha: np.ndarray,
                                  class_ids: np.ndarray,
                                  frozen_owner: np.ndarray,
                                  reviewed_outerwear: np.ndarray,
                                  reviewed_known: np.ndarray) -> dict:
    arrays = (source_alpha, class_ids, frozen_owner,
              reviewed_outerwear, reviewed_known)
    if (any(type(a) is not np.ndarray or a.ndim != 2 or a.dtype != np.uint8
            for a in arrays) or not source_alpha.size or
            any(a.shape != source_alpha.shape for a in arrays)):
        raise ResidualTaxonomyHold('INVALID_FROZEN_POSTSCORE_INPUT')
    if (np.any(class_ids >= 47) or np.any(frozen_owner > 2) or
            np.any(reviewed_outerwear > 1) or np.any(reviewed_known > 1)):
        raise ResidualTaxonomyHold('INVALID_LABEL_DOMAIN')
    alpha = source_alpha > 0
    if (np.any((frozen_owner > 0) & ~alpha) or
            np.any((reviewed_outerwear > 0) & ~alpha) or
            np.any((reviewed_outerwear > 0) & (reviewed_known == 0))):
        raise ResidualTaxonomyHold('INVALID_SOURCE_OR_REVIEW_PROVENANCE')
    positives = reviewed_outerwear > 0
    known = reviewed_known > 0
    missed = positives & (frozen_owner == 0)
    assigned = frozen_owner > 0
    known_fp = assigned & known & ~positives
    unknown_assigned = assigned & ~known
    counts = np.bincount(class_ids[missed], minlength=47)
    residual = {str(i): int(n) for i, n in enumerate(counts) if n}
    fn = int(np.count_nonzero(missed))
    class32 = int(counts[32])
    risky = sum(int(counts[i]) for i in (0, 2, 7))
    return {
        'schema': 'minimalizer/local-l02/known-residual-taxonomy-postscore/v1',
        'known_outerwear_fn': fn,
        'known_outerwear_tp': int(np.count_nonzero(positives & assigned)),
        'known_false_owner_fp': int(np.count_nonzero(known_fp)),
        'unknown_assigned_not_counted_as_fp': int(np.count_nonzero(unknown_assigned)),
        'missing_by_frozen_class': residual,
        'class32_only_max_possible_recovery': class32,
        'known_fn_remaining_even_if_all_class32_recovered': fn - class32,
        'known_fn_in_classes_0_2_7_requiring_independent_review': risky,
        'class32_only_ceiling_is_not_a_quality_pass': True,
        'class0_2_7_is_not_auto_promotable': True,
        'human_review_is_postscore_only': True,
        'occluded_accessory_may_overlap_coarse_review': True,
        'unknown_pixels_treated_as_negative': False,
        'unseen_character_quality': 'PENDING',
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
