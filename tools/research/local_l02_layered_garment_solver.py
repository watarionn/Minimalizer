"""Whole-image, source-only layered garment reconstruction for Lane A.

This is a new candidate generator, not a patch over an existing owner map.
It combines fresh Fashionpedia garment-part instances with fresh body/limb
evidence.  A sleeve instance that is geometrically attached to an outerwear
body is interpreted as garment-over-body occlusion; arm evidence does not
automatically erase that sleeve.  Disconnected or ambiguous sleeve
components remain unknown.  Underlayer evidence is retained as a separate
diagnostic and never treated as a negative observation.

The solver has no input for frozen owners, human masks, review JSON, or
case-specific thresholds.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import cv2
import numpy as np


class LayeredGarmentSolverHold(ValueError):
    """Raised when source-only evidence cannot be authenticated."""


OUTERWEAR_CLASS_IDS = frozenset({3, 4, 5, 9, 12})
UNDERLAYER_CLASS_IDS = frozenset({0, 1, 2})
SLEEVE_CLASS_ID = 31
FIXED_CONFIDENCE_THRESHOLD = 0.30
FIXED_CONTACT_RADIUS_PX = 12
FIXED_MIN_SLEEVE_COMPONENT_AREA = 32


@dataclass(frozen=True)
class SleeveDecision:
    detection_id: int
    component_id: int
    area: int
    arm_overlap_pixels: int
    body_contact_pixels: int
    associated_outerwear: int | None
    decision: str


@dataclass(frozen=True)
class LayeredGarmentResult:
    owner: np.ndarray
    unknown: np.ndarray
    outerwear_observed: np.ndarray
    underlayer_observed: np.ndarray
    sleeve_decisions: tuple[SleeveDecision, ...]
    source_only: bool = True
    human_labels_used: bool = False
    frozen_owner_used: bool = False
    unknown_not_treated_as_negative: bool = True
    owner_promotion_authorized: bool = False
    quality: str = "UNASSESSED"
    phase4: str = "FAIL"
    l02: str = "HOLD"
    production: str = "NO_GO"


def _sha256(array: np.ndarray) -> str:
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def _require_bool(mask: np.ndarray, shape: tuple[int, int], label: str) -> None:
    if type(mask) is not np.ndarray or mask.dtype != np.bool_ or mask.shape != shape:
        raise LayeredGarmentSolverHold(label)


def _component_masks(mask: np.ndarray) -> list[tuple[int, np.ndarray]]:
    count, labels = cv2.connectedComponents(mask.astype(np.uint8), connectivity=8)
    return [
        (component_id, labels == component_id)
        for component_id in range(1, count)
    ]


def _disk_dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1)
    )
    return cv2.dilate(mask.astype(np.uint8), kernel, iterations=1).astype(bool)


def solve_layered_garment(
    *,
    source_alpha: np.ndarray,
    detection_masks: np.ndarray,
    detection_classes: np.ndarray,
    detection_confidences: np.ndarray,
    arm_mask: np.ndarray,
    detection_masks_sha256: str,
    arm_mask_sha256: str,
) -> LayeredGarmentResult:
    """Reconstruct a fresh outerwear owner from authenticated observations."""
    if (
        type(source_alpha) is not np.ndarray
        or source_alpha.dtype != np.bool_
        or source_alpha.ndim != 2
        or not source_alpha.size
    ):
        raise LayeredGarmentSolverHold("INVALID_SOURCE_ALPHA")
    shape = source_alpha.shape
    _require_bool(arm_mask, shape, "INVALID_ARM_MASK")
    if np.any(arm_mask & ~source_alpha):
        raise LayeredGarmentSolverHold("ARM_OUTSIDE_SOURCE_ALPHA")
    if type(detection_masks) is not np.ndarray or detection_masks.dtype != np.bool_ or detection_masks.ndim != 3 or detection_masks.shape[1:] != shape:
        raise LayeredGarmentSolverHold("INVALID_DETECTION_MASKS")
    if type(detection_classes) is not np.ndarray or detection_classes.ndim != 1 or detection_classes.shape[0] != detection_masks.shape[0] or detection_classes.dtype.kind not in "iu" or np.any(detection_classes < 0) or np.any(detection_classes >= 46):
        raise LayeredGarmentSolverHold("INVALID_DETECTION_CLASSES")
    if type(detection_confidences) is not np.ndarray or detection_confidences.ndim != 1 or detection_confidences.shape[0] != detection_masks.shape[0] or detection_confidences.dtype.kind not in "fc" or not np.isfinite(detection_confidences).all() or np.any(detection_confidences < 0) or np.any(detection_confidences > 1):
        raise LayeredGarmentSolverHold("INVALID_DETECTION_CONFIDENCES")
    if type(detection_masks_sha256) is not str or _sha256(detection_masks.astype(np.uint8)) != detection_masks_sha256:
        raise LayeredGarmentSolverHold("DETECTION_MASK_SHA_MISMATCH")
    if type(arm_mask_sha256) is not str or _sha256(arm_mask.astype(np.uint8)) != arm_mask_sha256:
        raise LayeredGarmentSolverHold("ARM_MASK_SHA_MISMATCH")

    selected = detection_confidences >= FIXED_CONFIDENCE_THRESHOLD
    main_indices = [
        int(i) for i in range(detection_masks.shape[0])
        if selected[i] and int(detection_classes[i]) in OUTERWEAR_CLASS_IDS
    ]
    underlayer_indices = [
        int(i) for i in range(detection_masks.shape[0])
        if selected[i] and int(detection_classes[i]) in UNDERLAYER_CLASS_IDS
    ]
    sleeve_indices = [
        int(i) for i in range(detection_masks.shape[0])
        if selected[i] and int(detection_classes[i]) == SLEEVE_CLASS_ID
    ]

    main_indices.sort(key=lambda i: float(detection_confidences[i]), reverse=True)
    main_masks = [detection_masks[i] & source_alpha for i in main_indices]
    main_dilated = [_disk_dilate(mask, FIXED_CONTACT_RADIUS_PX) for mask in main_masks]
    underlayer_observed = np.zeros(shape, dtype=bool)
    for index in underlayer_indices:
        underlayer_observed |= detection_masks[index] & source_alpha

    owner = np.zeros(shape, dtype=np.uint16)
    outerwear_observed = np.zeros(shape, dtype=bool)
    claimed = np.zeros(shape, dtype=bool)
    for owner_id, mask in enumerate(main_masks, start=1):
        visible = mask & ~claimed
        owner[visible] = owner_id
        claimed |= visible
        outerwear_observed |= mask

    decisions: list[SleeveDecision] = []
    for detection_id in sleeve_indices:
        sleeve = detection_masks[detection_id] & source_alpha
        for component_id, component in _component_masks(sleeve):
            area = int(component.sum())
            if area < FIXED_MIN_SLEEVE_COMPONENT_AREA:
                decisions.append(SleeveDecision(detection_id, component_id, area, int((component & arm_mask).sum()), 0, None, "ABSTAIN_SMALL_COMPONENT"))
                continue
            contacts = [int(i) for i, dilated in enumerate(main_dilated) if np.any(component & dilated)]
            arm_overlap = int((component & arm_mask).sum())
            contact_pixels = int(sum(np.count_nonzero(component & main_dilated[i]) for i in contacts))
            if len(contacts) != 1:
                decisions.append(SleeveDecision(detection_id, component_id, area, arm_overlap, contact_pixels, None, "ABSTAIN_AMBIGUOUS_OUTERWEAR_CONTACT"))
                continue
            associated = contacts[0]
            if arm_overlap == area:
                decisions.append(SleeveDecision(detection_id, component_id, area, arm_overlap, contact_pixels, associated, "ABSTAIN_ALL_ARM_EVIDENCE"))
                continue
            attached = component & ~claimed
            owner[attached] = associated + 1
            claimed |= attached
            outerwear_observed |= component
            decisions.append(SleeveDecision(detection_id, component_id, area, arm_overlap, contact_pixels, associated, "ACCEPT_GARMENT_OVER_ARM_OCCLUSION"))

    owner[~source_alpha] = 0
    unknown = source_alpha & (owner == 0)
    if np.any(owner & ~source_alpha):
        raise LayeredGarmentSolverHold("OWNER_OUTSIDE_SOURCE_ALPHA")
    if np.any((owner != 0) & unknown):
        raise LayeredGarmentSolverHold("OWNER_UNKNOWN_OVERLAP")
    return LayeredGarmentResult(
        owner=owner,
        unknown=unknown,
        outerwear_observed=outerwear_observed,
        underlayer_observed=underlayer_observed,
        sleeve_decisions=tuple(decisions),
    )
