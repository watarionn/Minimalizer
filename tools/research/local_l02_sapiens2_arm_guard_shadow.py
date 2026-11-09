"""Source-only Sapiens2 arm-owner guard for L02 research candidates.

This module is intentionally a shadow-stage helper.  Sapiens2 explicit arm
classes may authorize conservative owner removal from an existing candidate;
garment classes, absent classes, and every unlisted class remain abstentions.
No human label, review mask, or threshold fitted to a reviewed case is accepted.
"""
from __future__ import annotations

import hashlib
import io
import re

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from tools.research.local_l02_class32_topology_palette_shadow import (
    SourceOnlyAbstentionHold,
    _components4,
    _components8,
    _enclosed_owner_voids,
    _frozen_cross_owner_contact8,
    _safe_to_remove,
)

MAX_PIXELS = 16_000_000
SAPIENS2_ARM_CLASSES = (5, 6, 7, 10, 14, 15, 16, 20)
SAPIENS2_GARMENT_CLASSES = (1, 12, 13, 23)


def _sha(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def _validate_inputs(*, source_bytes: bytes, expected_source_sha256: str,
                     sapiens_classes: np.ndarray,
                     expected_sapiens_sha256: str,
                     frozen_owner: np.ndarray,
                     candidate_owner: np.ndarray) -> np.ndarray:
    if (type(source_bytes) is not bytes or not source_bytes or
            not isinstance(expected_source_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", expected_source_sha256) is None or
            hashlib.sha256(source_bytes).hexdigest() != expected_source_sha256):
        raise SourceOnlyAbstentionHold("SIGNED_SOURCE_SHA_MISMATCH")
    arrays = (sapiens_classes, frozen_owner, candidate_owner)
    if any(type(a) is not np.ndarray or a.ndim != 2 for a in arrays):
        raise SourceOnlyAbstentionHold("INVALID_OWNER_OBSERVER_ARRAY")
    if (sapiens_classes.dtype != np.uint8 or frozen_owner.dtype != np.uint8 or
            candidate_owner.dtype != np.uint8 or
            sapiens_classes.size == 0 or sapiens_classes.size > MAX_PIXELS or
            not (sapiens_classes.shape == frozen_owner.shape == candidate_owner.shape)):
        raise SourceOnlyAbstentionHold("INVALID_OWNER_OBSERVER_ARRAY")
    if (np.any(sapiens_classes >= 29) or np.any(frozen_owner > 2) or
            np.any(candidate_owner > 2)):
        raise SourceOnlyAbstentionHold("INVALID_OWNER_OBSERVER_TAXONOMY")
    if (not isinstance(expected_sapiens_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", expected_sapiens_sha256) is None or
            _sha(sapiens_classes) != expected_sapiens_sha256):
        raise SourceOnlyAbstentionHold("SAPIENS2_CLASS_ARRAY_SHA_MISMATCH")
    if np.any((candidate_owner > 0) & (frozen_owner == 0)):
        raise SourceOnlyAbstentionHold("CANDIDATE_OWNER_PROMOTION")
    try:
        with Image.open(io.BytesIO(source_bytes)) as image:
            rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise SourceOnlyAbstentionHold("INVALID_SIGNED_SOURCE") from exc
    if rgba.shape[:2] != sapiens_classes.shape:
        raise SourceOnlyAbstentionHold("SOURCE_OBSERVER_SHAPE_MISMATCH")
    opaque = rgba[:, :, 3] > 0
    if np.any((frozen_owner > 0) & ~opaque) or np.any((candidate_owner > 0) & ~opaque):
        raise SourceOnlyAbstentionHold("OWNER_OUTSIDE_SIGNED_ALPHA")
    return opaque


def _assert_topology(before: np.ndarray, after: np.ndarray) -> None:
    for owner_id in (1, 2):
        before_mask, after_mask = before == owner_id, after == owner_id
        if (_components4(before_mask) != _components4(after_mask) or
                _components8(before_mask) != _components8(after_mask) or
                _enclosed_owner_voids(before_mask, 4) != _enclosed_owner_voids(after_mask, 4) or
                _enclosed_owner_voids(before_mask, 8) != _enclosed_owner_voids(after_mask, 8)):
            raise SourceOnlyAbstentionHold("SAPIENS2_OWNER_TOPOLOGY_FAIL")


def remove_sapiens2_arm_owner(*, source_bytes: bytes,
        expected_source_sha256: str, sapiens_classes: np.ndarray,
        expected_sapiens_sha256: str, frozen_owner: np.ndarray,
        candidate_owner: np.ndarray,
        eligible_mask: np.ndarray | None = None) -> tuple[np.ndarray, dict]:
    """Remove only conservative explicit-arm pixels from an existing candidate."""
    opaque = _validate_inputs(
        source_bytes=source_bytes, expected_source_sha256=expected_source_sha256,
        sapiens_classes=sapiens_classes,
        expected_sapiens_sha256=expected_sapiens_sha256,
        frozen_owner=frozen_owner, candidate_owner=candidate_owner)
    if eligible_mask is None:
        eligible_mask = np.ones(candidate_owner.shape, dtype=bool)
    if (type(eligible_mask) is not np.ndarray or eligible_mask.dtype != np.bool_ or
            eligible_mask.shape != candidate_owner.shape):
        raise SourceOnlyAbstentionHold("INVALID_SAPIENS2_ELIGIBILITY_MASK")
    protected = _frozen_cross_owner_contact8(frozen_owner)
    selected = (
        np.isin(sapiens_classes, SAPIENS2_ARM_CLASSES) &
        ~np.isin(sapiens_classes, SAPIENS2_GARMENT_CLASSES) &
        (candidate_owner > 0) & (frozen_owner > 0) &
        ~protected & opaque & eligible_mask)
    result = candidate_owner.copy()
    removed = 0
    for owner_id in (1, 2):
        for y, x in np.argwhere(selected & (result == owner_id)):
            if _safe_to_remove(result == owner_id, int(y), int(x)):
                result[y, x] = 0
                removed += 1
    if (np.any(result > candidate_owner) or
            np.any((candidate_owner > 0) & (frozen_owner == 0)) or
            np.any((result > 0) & ~opaque)):
        raise SourceOnlyAbstentionHold("SAPIENS2_OWNER_POSTCONDITION_FAIL")
    _assert_topology(candidate_owner, result)
    return result, {
        "schema": "minimalizer/local-l02/sapiens2-arm-guard-shadow/v1",
        "sapiens2_arm_classes": list(SAPIENS2_ARM_CLASSES),
        "sapiens2_garment_classes_protected": list(SAPIENS2_GARMENT_CLASSES),
        "selected_explicit_arm_px": int(selected.sum()),
        "removed_explicit_arm_px": removed,
        "sapiens2_class_array_sha256": expected_sapiens_sha256,
        "source_sha256": expected_source_sha256,
        "human_labels_used": False,
        "unknown_not_treated_as_negative": True,
        "owner_promotions": 0,
        "candidate_only": True,
        "quality": "UNASSESSED",
        "L02": "HOLD",
        "Phase4": "FAIL",
        "Phase5": "NO_GO",
    }


def veto_sapiens2_arm_evidence(*, positive_evidence: np.ndarray,
        sapiens_classes: np.ndarray, expected_sapiens_sha256: str) -> tuple[np.ndarray, dict]:
    """Veto explicit arms before a positive evidence map reaches owner assignment."""
    if (type(positive_evidence) is not np.ndarray or
            positive_evidence.dtype != np.bool_ or positive_evidence.ndim != 2 or
            type(sapiens_classes) is not np.ndarray or
            sapiens_classes.dtype != np.uint8 or
            positive_evidence.shape != sapiens_classes.shape or
            expected_sapiens_sha256 != _sha(sapiens_classes)):
        raise SourceOnlyAbstentionHold("SAPIENS2_ARM_VETO_INPUT_MISMATCH")
    arm = np.isin(sapiens_classes, SAPIENS2_ARM_CLASSES)
    protected = positive_evidence & arm
    result = positive_evidence & ~arm
    return result, {
        "schema": "minimalizer/local-l02/sapiens2-arm-veto-shadow/v1",
        "sapiens2_class_array_sha256": expected_sapiens_sha256,
        "positive_input_px": int(positive_evidence.sum()),
        "explicit_arm_veto_px": int(protected.sum()),
        "positive_output_px": int(result.sum()),
        "human_labels_used": False,
        "unknown_not_treated_as_negative": True,
        "candidate_only": True,
    }
