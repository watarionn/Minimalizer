"""Source-free, post-inference-only audit of suspected bag/outerwear occlusion.

This module NEVER changes a pixel owner, an annotation, a Golden, or an
inference input. Model class 25 is evidence of a bag, not a ground-truth mask.
Human reviewed masks may be supplied ONLY after all model/owner outputs freeze.
"""
from __future__ import annotations

import numpy as np

BAG_CLASS_ID = 25  # SegFormer-B2 Fashion label: bag / purse


class BagOcclusionAuditHold(ValueError):
    """Invalid inputs must not produce a seemingly valid quality receipt."""


def audit_bag_occlusion_postscore(*, class_ids: np.ndarray, owner: np.ndarray,
                                   opaque: np.ndarray, known_outerwear: np.ndarray,
                                   known_non_outerwear: np.ndarray,
                                   garment_owner_id: int,
                                   independent_outerwear: np.ndarray | None = None) -> dict:
    """Return aggregate-only disagreement counts, without masks or coordinates.

    Contract: class_ids, owner and optional independent_outerwear are FROZEN
    source-only predictions. Human masks are evaluation-only, never inputs to
    candidate generation. The caller is responsible for enforcing this order.
    """
    if not isinstance(garment_owner_id, int) or type(garment_owner_id) is not int or not 1 <= garment_owner_id <= 254:
        raise BagOcclusionAuditHold('INVALID_GARMENT_OWNER_ID')
    if (type(class_ids) is not np.ndarray or class_ids.dtype != np.uint8 or
            class_ids.ndim != 2 or not class_ids.size or
            class_ids.size > 16_000_000 or type(owner) is not np.ndarray or
            owner.dtype != np.uint8 or owner.shape != class_ids.shape):
        raise BagOcclusionAuditHold('INVALID_FROZEN_MODEL_OR_OWNER')
    for name, mask in [('opaque', opaque), ('known_outerwear', known_outerwear),
                       ('known_non_outerwear', known_non_outerwear)]:
        if (type(mask) is not np.ndarray or mask.shape != class_ids.shape or
                mask.dtype not in (np.bool_, np.uint8) or
                (mask.dtype == np.uint8 and np.any(mask > 1))):
            raise BagOcclusionAuditHold('INVALID_' + name.upper())
    if independent_outerwear is not None and (
            type(independent_outerwear) is not np.ndarray or
            independent_outerwear.shape != class_ids.shape or
            independent_outerwear.dtype not in (np.bool_, np.uint8) or
            (independent_outerwear.dtype == np.uint8 and np.any(independent_outerwear > 1))):
        raise BagOcclusionAuditHold('INVALID_INDEPENDENT_OBSERVER')
    visible = opaque.astype(bool)
    positive = known_outerwear.astype(bool)
    negative = known_non_outerwear.astype(bool)
    if (np.any(positive & negative) or np.any((positive | negative) & ~visible) or
            np.any((owner != 0) & ~visible)):
        raise BagOcclusionAuditHold('INVALID_REVIEW_OR_SOURCE_DOMAIN')
    # Class 25 is a tentative bag prediction, not permission to relabel.
    bag = (class_ids == BAG_CLASS_ID) & visible
    independent = independent_outerwear.astype(bool) if independent_outerwear is not None else None
    # Independent model positives outside the signed source-alpha domain are
    # invalid provenance, not silent negatives or harmless ignored pixels.
    if independent is not None and np.any(independent & ~visible):
        raise BagOcclusionAuditHold('INDEPENDENT_OBSERVER_OUTSIDE_SOURCE_ALPHA')
    counts = {
        'bag_class25_visible_px': int(np.count_nonzero(bag)),
        'bag_class25_reviewed_outerwear_conflict_px': int(np.count_nonzero(bag & positive)),
        'bag_class25_reviewed_non_outerwear_px': int(np.count_nonzero(bag & negative)),
        'bag_class25_unknown_px': int(np.count_nonzero(bag & ~(positive | negative))),
        'bag_class25_on_garment_owner_px': int(np.count_nonzero(bag & (owner == garment_owner_id))),
        'bag_class25_unowned_px': int(np.count_nonzero(bag & (owner == 0))),
        'bag_class25_other_owner_px': int(np.count_nonzero(bag & (owner != 0) & (owner != garment_owner_id))),
    }
    if independent is not None:
        counts.update({
            'bag_class25_independent_outerwear_overlap_px': int(np.count_nonzero(bag & independent)),
            'bag_class25_independent_outerwear_reviewed_conflict_px': int(np.count_nonzero(bag & independent & positive)),
            'bag_class25_independent_outerwear_reviewed_non_outerwear_px': int(np.count_nonzero(bag & independent & negative)),
            'bag_class25_independent_outerwear_unknown_px': int(np.count_nonzero(bag & independent & ~(positive | negative))),
        })
    # Fail closed even under `python -O`, which disables bare assert statements.
    if (counts['bag_class25_reviewed_outerwear_conflict_px'] +
            counts['bag_class25_reviewed_non_outerwear_px'] +
            counts['bag_class25_unknown_px'] != counts['bag_class25_visible_px']):
        raise BagOcclusionAuditHold('REVIEW_PARTITION_INVARIANT')
    if (counts['bag_class25_on_garment_owner_px'] +
            counts['bag_class25_unowned_px'] +
            counts['bag_class25_other_owner_px'] != counts['bag_class25_visible_px']):
        raise BagOcclusionAuditHold('OWNER_PARTITION_INVARIANT')
    if independent is not None and (
            counts['bag_class25_independent_outerwear_reviewed_conflict_px'] +
            counts['bag_class25_independent_outerwear_reviewed_non_outerwear_px'] +
            counts['bag_class25_independent_outerwear_unknown_px'] !=
            counts['bag_class25_independent_outerwear_overlap_px']):
        raise BagOcclusionAuditHold('INDEPENDENT_PARTITION_INVARIANT')
    return {
        'schema': 'minimalizer/local-l02/bag-occlusion-postscore/v1',
        'bag_class25_is_ground_truth': False,
        'reviewed_labels_unchanged': True,
        'owner_modified': False,
        'inference_uses_human_annotations': False,
        'unknown_treated_as_negative': False,
        'metric_override_allowed': False,
        'quality': 'UNASSESSED',
        'L02': 'HOLD', 'Phase4': 'FAIL', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
        'counts': counts,
    }
