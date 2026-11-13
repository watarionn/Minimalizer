"""Component-level source-only owner arbitration for Lane A L02.

This module is deliberately a new owner-reconstruction layer.  It does not
read a frozen owner array, human labels, or review JSON, and it never edits an
existing owner pixel-by-pixel.  Candidate garment instances and independent
body/underlayer evidence are authenticated, grouped by contact components, and
either accepted as whole instances or moved to ``unknown`` as whole contact
components.

The result is research-only.  It is not a Phase4 promotion and carries an
explicit fail-closed promotion state.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import cv2
import numpy as np


class ComponentOwnerSolverHold(ValueError):
    """Raised when authenticated source-only evidence is not safe to solve."""


ROLE_ARM = "arm"
ROLE_UNDERLAYER = "underlayer"
ROLE_OUTERWEAR = "outerwear"
ALLOWED_ROLES = frozenset({ROLE_ARM, ROLE_UNDERLAYER, ROLE_OUTERWEAR})


@dataclass(frozen=True)
class ContactDecision:
    contact_id: int
    area: int
    instance_ids: tuple[int, ...]
    arm_pixels: int
    underlayer_pixels: int
    overlap_pixels: int
    decision: str


@dataclass(frozen=True)
class ComponentOwnerResult:
    owner: np.ndarray
    unknown: np.ndarray
    accepted_instances: tuple[int, ...]
    decisions: tuple[ContactDecision, ...]
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


def _require_sha(array: np.ndarray, expected: str, error: str) -> None:
    if type(expected) is not str or len(expected) != 64 or _sha256(array) != expected:
        raise ComponentOwnerSolverHold(error)


def _validate_bool_mask(mask: np.ndarray, shape: tuple[int, int], error: str) -> None:
    if (
        type(mask) is not np.ndarray
        or mask.dtype != np.bool_
        or mask.ndim != 2
        or mask.shape != shape
    ):
        raise ComponentOwnerSolverHold(error)


def _validate_instance_masks(
    instance_masks: np.ndarray, source_alpha: np.ndarray
) -> None:
    if (
        type(instance_masks) is not np.ndarray
        or instance_masks.dtype != np.bool_
        or instance_masks.ndim != 3
        or instance_masks.shape[1:] != source_alpha.shape
    ):
        raise ComponentOwnerSolverHold("INVALID_GARMENT_INSTANCES")
    if np.any(instance_masks & ~source_alpha[None, :, :]):
        raise ComponentOwnerSolverHold("INSTANCE_OUTSIDE_SOURCE_ALPHA")


def _contact_labels(instance_masks: np.ndarray) -> tuple[np.ndarray, int]:
    union = np.any(instance_masks, axis=0).astype(np.uint8)
    count, labels = cv2.connectedComponents(union, connectivity=8)
    return labels, count - 1


def solve_component_owners(
    *,
    source_alpha: np.ndarray,
    instance_masks: np.ndarray,
    instance_masks_sha256: str,
    role_masks: tuple[tuple[str, np.ndarray, str, str], ...],
    occlusion_edges: tuple[tuple[int, int], ...] = (),
) -> ComponentOwnerResult:
    """Solve whole contact components from authenticated source-only evidence.

    ``instance_masks`` are fresh garment proposals, not an existing owner map.
    ``role_masks`` entries are ``(role, mask, sha256, observer_id)``.  A
    contact component is accepted only when it contains exactly one instance,
    has no arm/underlayer evidence, and has no unresolved overlap.  Otherwise
    the complete component is unknown; the solver never trims only the
    conflicting pixels.

    Occlusion edges are provenance-only relationships for this first solver
    stage.  They are validated and retained by the result contract through the
    contact grouping, but they cannot authorize an owner on their own.
    """
    _validate_bool_mask(source_alpha, source_alpha.shape, "INVALID_SOURCE_ALPHA")
    if not isinstance(occlusion_edges, tuple):
        raise ComponentOwnerSolverHold("INVALID_OCCLUSION_EDGES")
    for edge in occlusion_edges:
        if (
            not isinstance(edge, tuple)
            or len(edge) != 2
            or type(edge[0]) is not int
            or type(edge[1]) is not int
            or edge[0] < 0
            or edge[1] < 0
            or edge[0] >= instance_masks.shape[0]
            or edge[1] >= instance_masks.shape[0]
            or edge[0] == edge[1]
        ):
            raise ComponentOwnerSolverHold("INVALID_OCCLUSION_EDGES")
    _validate_instance_masks(instance_masks, source_alpha)
    _require_sha(instance_masks, instance_masks_sha256, "INSTANCE_MASK_SHA_MISMATCH")

    if not isinstance(role_masks, tuple) or not role_masks:
        raise ComponentOwnerSolverHold("ROLE_EVIDENCE_REQUIRED")
    role_by_name: dict[str, np.ndarray] = {}
    observer_ids: set[str] = set()
    for entry in role_masks:
        if not isinstance(entry, tuple) or len(entry) != 4:
            raise ComponentOwnerSolverHold("INVALID_ROLE_MASK_ENTRY")
        role, mask, expected_sha, observer_id = entry
        if (
            role not in ALLOWED_ROLES
            or role in role_by_name
            or type(observer_id) is not str
            or not observer_id
            or observer_id in observer_ids
        ):
            raise ComponentOwnerSolverHold("INVALID_ROLE_MASK_ENTRY")
        _validate_bool_mask(mask, source_alpha.shape, "INVALID_ROLE_MASK")
        _require_sha(mask.astype(np.uint8), expected_sha, "ROLE_MASK_SHA_MISMATCH")
        if np.any(mask & ~source_alpha):
            raise ComponentOwnerSolverHold("ROLE_MASK_OUTSIDE_SOURCE_ALPHA")
        role_by_name[role] = mask
        observer_ids.add(observer_id)

    arm = role_by_name.get(ROLE_ARM, np.zeros_like(source_alpha))
    underlayer = role_by_name.get(ROLE_UNDERLAYER, np.zeros_like(source_alpha))
    labels, contact_count = _contact_labels(instance_masks)
    owner = np.zeros(source_alpha.shape, dtype=np.uint16)
    accepted: list[int] = []
    instance_owner_ids: dict[int, int] = {}
    decisions: list[ContactDecision] = []
    next_owner_id = 1

    for contact_id in range(1, contact_count + 1):
        contact = labels == contact_id
        area = int(contact.sum())
        contained = tuple(
            int(index)
            for index, mask in enumerate(instance_masks)
            if np.any(mask & contact)
        )
        overlap = np.zeros_like(contact)
        for left, right in occlusion_edges:
            overlap |= instance_masks[left] & instance_masks[right] & contact

        arm_pixels = int(np.count_nonzero(contact & arm))
        underlayer_pixels = int(np.count_nonzero(contact & underlayer))
        overlap_pixels = int(overlap.sum())
        safe = (
            len(contained) == 1
            and arm_pixels == 0
            and underlayer_pixels == 0
            and overlap_pixels == 0
        )
        if safe:
            instance_id = contained[0]
            owner_id = instance_owner_ids.setdefault(instance_id, next_owner_id)
            if owner_id == next_owner_id:
                next_owner_id += 1
                accepted.append(instance_id)
            owner[instance_masks[instance_id] & contact] = owner_id
            decision = "ACCEPT_WHOLE_INSTANCE"
        else:
            decision = "ABSTAIN_WHOLE_CONTACT_COMPONENT"
        decisions.append(
            ContactDecision(
                contact_id=contact_id,
                area=area,
                instance_ids=contained,
                arm_pixels=arm_pixels,
                underlayer_pixels=underlayer_pixels,
                overlap_pixels=overlap_pixels,
                decision=decision,
            )
        )

    unknown = source_alpha & (owner == 0)
    if np.any(owner[~source_alpha] != 0) or np.any(owner > np.iinfo(np.uint16).max):
        raise ComponentOwnerSolverHold("OWNER_OUTSIDE_SOURCE_ALPHA")
    if np.any((owner != 0) & unknown):
        raise ComponentOwnerSolverHold("OWNER_UNKNOWN_OVERLAP")
    return ComponentOwnerResult(
        owner=owner,
        unknown=unknown,
        accepted_instances=tuple(accepted),
        decisions=tuple(decisions),
    )

