"""Post-inference-only L02 owner exclusivity audit. Never an inference input.

Human masks are evaluation labels only, never model prompts, pixel selection,
weights, thresholds, or Phase4 owner authority. Unknown and occluded pixels
remain unknown. This module cannot grant semantic, Golden or production PASS.
"""
from __future__ import annotations

import hashlib
import numpy as np

CATEGORIES = ("outerwear", "arm_skin", "hair", "underlayer", "other_known_negative")


class OwnerPartitionHold(ValueError):
    pass


def audit_owner_partition(*, alpha: np.ndarray, known_masks: dict[str, np.ndarray],
                          unknown: np.ndarray, occluded_unknown: np.ndarray,
                          prediction: np.ndarray) -> dict:
    """Audit independent, human-reviewed postscore labels against a prediction.

    The caller must separately authenticate original source and prediction
    digests. This routine is NOT an independent-label provenance verifier.
    """
    if not isinstance(alpha, np.ndarray) or alpha.ndim != 2 or alpha.dtype != np.bool_:
        raise OwnerPartitionHold("INVALID_ALPHA")
    if type(known_masks) is not dict or set(known_masks) != set(CATEGORIES):
        raise OwnerPartitionHold("INVALID_OWNER_CATEGORIES")
    for name, mask in list(known_masks.items()) + [
        ("unknown", unknown), ("occluded_unknown", occluded_unknown),
        ("prediction", prediction),
    ]:
        if not isinstance(mask, np.ndarray) or mask.dtype != np.bool_ or mask.shape != alpha.shape:
            raise OwnerPartitionHold("INVALID_MASK:" + name)
        if np.any(mask & ~alpha):
            raise OwnerPartitionHold("MASK_OUTSIDE_ORIGINAL_ALPHA:" + name)

    owner_count = np.zeros(alpha.shape, dtype=np.uint8)
    for name in CATEGORIES:
        owner_count += known_masks[name].astype(np.uint8)
    if np.any(owner_count > 1):
        raise OwnerPartitionHold("NONEXCLUSIVE_KNOWN_OWNER_LABELS")
    expected_unknown = alpha & (owner_count == 0)
    if not np.array_equal(unknown, expected_unknown):
        raise OwnerPartitionHold("UNKNOWN_MUST_EQUAL_UNLABELLED_ALPHA")
    if np.any(occluded_unknown & ~unknown):
        raise OwnerPartitionHold("OCCLUSION_UNKNOWN_RELABELED_KNOWN")

    outer = known_masks["outerwear"]
    known_negative = alpha & (owner_count == 1) & ~outer
    tp = int(np.count_nonzero(prediction & outer))
    fp = int(np.count_nonzero(prediction & known_negative))
    fn = int(np.count_nonzero(~prediction & outer))
    result = {
        "tp_known_outerwear": tp,
        "fp_known_non_outerwear": fp,
        "fn_known_outerwear": fn,
        "known_only_iou": round(tp / max(1, tp + fp + fn), 6),
        "known_arm_fp_pixels": int(np.count_nonzero(prediction & known_masks["arm_skin"])),
        "known_hair_fp_pixels": int(np.count_nonzero(prediction & known_masks["hair"])),
        "known_underlayer_fp_pixels": int(np.count_nonzero(prediction & known_masks["underlayer"])),
        "known_other_fp_pixels": int(np.count_nonzero(prediction & known_masks["other_known_negative"])),
        "unknown_predicted_pixels": int(np.count_nonzero(prediction & unknown)),
        "occluded_unknown_predicted_pixels": int(np.count_nonzero(prediction & occluded_unknown)),
        "prediction_sha256": hashlib.sha256(prediction.tobytes()).hexdigest(),
        "manual_labels_used_in_inference": False,
        "independent_holdout_proven": False,
        "exclusive_owner_model_proven": False,
        "semantic_quality_pass": False,
        "L02": "HOLD", "L03": "NO_GO", "Golden": "HOLD", "production": "NO_GO",
    }
    protected = ("known_arm_fp_pixels", "known_hair_fp_pixels",
                 "known_underlayer_fp_pixels", "known_other_fp_pixels")
    if sum(result[k] for k in protected) != fp:
        raise OwnerPartitionHold("NEGATIVE_OWNER_PARTITION_MISMATCH")
    return result
