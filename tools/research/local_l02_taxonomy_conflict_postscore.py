"""Research-only postscore audit of frozen SegFormer fashion taxonomy conflicts.

Never import this from owner inference: the reviewed masks are post-inference
only, and a model-vs-human disagreement is not a corrected human label.
No pixels, coordinates, source SHA or private assets are returned.
"""
from __future__ import annotations
import numpy as np

class TaxonomyConflictHold(ValueError):
    pass

# Pinned sayeed99/segformer-b2-fashion taxonomy. No model-specific inference
# is performed here; only disagreement between frozen prediction and review.
CLASS_LABELS = {0: 'everything_else', 7: 'pants', 25: 'bag_wallet',
                30: 'lapel', 32: 'sleeve'}


def audit_postscore_taxonomy(*, class_ids: np.ndarray, frozen_owner: np.ndarray,
                             source_alpha: np.ndarray, reviewed_outerwear: np.ndarray,
                             reviewed_known_negative: np.ndarray) -> dict:
    arrays = (class_ids, frozen_owner, source_alpha)
    if any(type(x) is not np.ndarray or x.dtype != np.uint8 or x.ndim != 2 or not x.size for x in arrays):
        raise TaxonomyConflictHold('INVALID_SOURCE_ONLY_ARRAYS')
    if any(x.shape != class_ids.shape for x in (*arrays, reviewed_outerwear, reviewed_known_negative)):
        raise TaxonomyConflictHold('SHAPE_MISMATCH')
    if any(type(x) is not np.ndarray or x.dtype != np.bool_ for x in (reviewed_outerwear, reviewed_known_negative)):
        raise TaxonomyConflictHold('INVALID_POSTSCORE_MASKS')
    if np.any(class_ids >= 47) or np.any(frozen_owner > 2):
        raise TaxonomyConflictHold('INVALID_MODEL_OR_OWNER_CLASS')
    opaque = source_alpha > 0
    if np.any((frozen_owner > 0) & ~opaque):
        raise TaxonomyConflictHold('OWNER_OUTSIDE_SOURCE')
    if np.any((reviewed_outerwear | reviewed_known_negative) & ~opaque):
        raise TaxonomyConflictHold('POSTSCORE_OUTSIDE_SOURCE')
    if np.any(reviewed_outerwear & reviewed_known_negative):
        raise TaxonomyConflictHold('OVERLAPPING_HUMAN_LABELS')
    missing = reviewed_outerwear & (frozen_owner == 0)
    known_fp = reviewed_known_negative & (frozen_owner > 0)
    unknown = opaque & ~(reviewed_outerwear | reviewed_known_negative)
    class_rows = {}
    for cid in (0, 7, 25, 30, 32):
        mask = class_ids == cid
        class_rows[str(cid)] = {
            'model_label': CLASS_LABELS[cid],
            'reviewed_outerwear_missing_px': int(np.count_nonzero(mask & missing)),
            'known_negative_wrong_owner_px': int(np.count_nonzero(mask & known_fp)),
            'unknown_unscored_px': int(np.count_nonzero(mask & unknown)),
        }
    bag_conflict = class_rows['25']['reviewed_outerwear_missing_px']
    return {
        'schema': 'minimalizer/local-l02/taxonomy-conflict-postscore/v1',
        'reviewed_outerwear_missing_total_px': int(np.count_nonzero(missing)),
        'reviewed_outerwear_missing_by_class': class_rows,
        'bag_wallet_vs_outerwear_review_conflict_px': bag_conflict,
        'bag_wallet_review_status': 'REVIEW_REQUIRED' if bag_conflict else 'NO_OBSERVED_CONFLICT',
        'reviewed_masks_modified': False,
        'raw_known_FN_metric_modified': False,
        'human_annotations_used_for_inference': False,
        'unknown_treated_as_negative': False,
        'known_character_only': True,
        'unseen_character_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
