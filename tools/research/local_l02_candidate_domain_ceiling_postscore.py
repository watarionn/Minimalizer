"""Post-inference only: identify L02 garment pixels unreachable by a frozen candidate.

Never call this with human labels before a proposal is frozen. No model inference,
owner mutation, Golden approval or production promotion occurs here.
"""
import numpy as np


class CandidateCeilingHold(ValueError):
    pass


def audit_candidate_ceiling(*, class_ids, source_alpha, frozen_candidate,
                            frozen_owner, reviewed_outerwear, reviewed_labelled,
                            reviewed_arm, reviewed_underlayer):
    arrays = (class_ids, source_alpha, frozen_owner, reviewed_outerwear,
              reviewed_labelled, reviewed_arm, reviewed_underlayer)
    if any(type(x) is not np.ndarray or x.dtype != np.uint8 or x.ndim != 2
           or not x.size for x in arrays):
        raise CandidateCeilingHold('INVALID_UINT8_ARRAY')
    if any(x.shape != class_ids.shape for x in arrays):
        raise CandidateCeilingHold('SHAPE_MISMATCH')
    if type(frozen_candidate) is not np.ndarray or frozen_candidate.dtype != np.bool_ \
            or frozen_candidate.shape != class_ids.shape:
        raise CandidateCeilingHold('INVALID_CANDIDATE')
    if np.any(class_ids >= 47) or np.any(frozen_owner > 2):
        raise CandidateCeilingHold('INVALID_CLASS_OR_OWNER')
    alpha = source_alpha > 0
    if np.any(frozen_candidate & ~alpha) or np.any((frozen_owner != 0) & ~frozen_candidate):
        raise CandidateCeilingHold('SOURCE_OR_CANDIDATE_VIOLATION')
    if np.any((frozen_owner == 1) & ~np.isin(class_ids, (5, 32))) or \
       np.any((frozen_owner == 2) & ~np.isin(class_ids, (10, 32))):
        raise CandidateCeilingHold('OWNER_CLASS_CONFLICT')
    positive = reviewed_outerwear > 0
    labelled = reviewed_labelled > 0
    arm = reviewed_arm > 0
    under = reviewed_underlayer > 0
    if np.any(positive & ~labelled) or np.any((arm | under) & (positive | ~labelled)):
        raise CandidateCeilingHold('INVALID_REVIEWED_LABELS')
    owned = frozen_owner > 0
    fp = owned & labelled & ~positive
    fn = positive & ~owned
    outside = fn & ~frozen_candidate
    cls_fp, n_fp = np.unique(class_ids[fp], return_counts=True)
    cls_fn, n_fn = np.unique(class_ids[fn], return_counts=True)
    return {
        'schema': 'minimalizer/local-l02/candidate-domain-ceiling-postscore/v1',
        'reviewed_true_positive_px': int((owned & positive).sum()),
        'reviewed_known_false_positive_px': int(fp.sum()),
        'reviewed_missing_px': int(fn.sum()),
        'missing_outside_frozen_candidate_px': int(outside.sum()),
        'missing_inside_frozen_candidate_px': int((fn & frozen_candidate).sum()),
        'known_fp_arm_px': int((fp & arm).sum()),
        'known_fp_underlayer_px': int((fp & under).sum()),
        'known_fp_by_class': {str(int(k)): int(v) for k, v in zip(cls_fp, n_fp)},
        'reviewed_missing_by_class': {str(int(k)): int(v) for k, v in zip(cls_fn, n_fn)},
        'human_labels_used_for_inference': False,
        'unknown_scored_as_negative': False,
        'source_only_phase4_quality_pass': False,
        'independent_unseen_character_pass': False,
        'L02': 'HOLD', 'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
    }
