"""Source-only L02 fail-closed cross-owner edge preservation gate.

An owner component may remain connected while new jacket/coat adjacency
silently changes occlusion. This verifier observes only owner arrays, never
human labels or coordinates. It is not a semantic Phase4 PASS.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage
from local_l02_frozen_owner_transition_audit import (
    audit_frozen_owner_transition, FrozenOwnerTransitionHold,
)


class CrossOwnerContactHold(ValueError):
    pass


def verify_no_new_cross_owner_contacts(*, before: np.ndarray,
                                       after: np.ndarray) -> dict:
    """Reject new 4- or diagonal 8-neighbour jacket/coat adjacency edges."""
    if (type(before) is not np.ndarray or type(after) is not np.ndarray or
            before.dtype != np.uint8 or after.dtype != np.uint8 or
            before.ndim != 2 or after.shape != before.shape or not before.size):
        raise CrossOwnerContactHold('INVALID_OWNER_ARRAYS')
    if np.any(before > 2) or np.any(after > 2):
        raise CrossOwnerContactHold('INVALID_OWNER_DOMAIN')
    counts = {'4': 0, 'diagonal': 0}
    h, w = before.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == dx == 0 or abs(dy) >= h or abs(dx) >= w:
                continue
            a_y = slice(max(0, -dy), h - max(0, dy))
            b_y = slice(max(0, dy), h - max(0, -dy))
            a_x = slice(max(0, -dx), w - max(0, dx))
            b_x = slice(max(0, dx), w - max(0, -dx))
            b1, b2 = before[a_y, a_x], before[b_y, b_x]
            a1, a2 = after[a_y, a_x], after[b_y, b_x]
            old = ((b1 == 1) & (b2 == 2)) | ((b1 == 2) & (b2 == 1))
            new = ((a1 == 1) & (a2 == 2)) | ((a1 == 2) & (a2 == 1))
            n = int(np.count_nonzero(new & ~old))
            if n:
                counts['4' if dy == 0 or dx == 0 else 'diagonal'] += n
    if counts['4'] or counts['diagonal']:
        raise CrossOwnerContactHold('NEW_CROSS_OWNER_CONTACT_EDGE')
    return {
        'schema': 'minimalizer/local-l02/cross-owner-contact-edge-gate/v1',
        'new_cross_owner_4_edges': 0,
        'new_cross_owner_diagonal_edges': 0,
        'human_annotations_used_for_inference': False,
        'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
    }


def prune_new_cross_owner_additions(*, before: np.ndarray,
                                    proposed: np.ndarray,
                                    allowed_abstentions: np.ndarray | None = None) -> tuple[np.ndarray, dict]:
    """Prune newly added contact edges, not frozen owners.

    Earlier vetoes must be passed as an exact allowed_abstentions mask.
    A separate topology check must run afterward: pruning can disconnect
    proposed new pixels. The merged frozen-owner auditor is authoritative
    for all frozen owner deletion counts.
    """
    if (type(before) is not np.ndarray or type(proposed) is not np.ndarray or
            before.dtype != np.uint8 or proposed.dtype != np.uint8 or
            before.ndim != 2 or before.shape != proposed.shape or not before.size or
            np.any(before > 2) or np.any(proposed > 2)):
        raise CrossOwnerContactHold('INVALID_OWNER_ARRAYS')
    if allowed_abstentions is None:
        allowed_abstentions = np.zeros(before.shape, dtype=bool)
    elif (type(allowed_abstentions) is not np.ndarray or
          allowed_abstentions.dtype != np.bool_ or
          allowed_abstentions.shape != before.shape):
        raise CrossOwnerContactHold('INVALID_ALLOWED_ABSTENTION_MASK')
    if np.any(allowed_abstentions & (before == 0)):
        raise CrossOwnerContactHold('ABSTENTION_MASK_OUTSIDE_FROZEN_OWNER')
    if np.any((before > 0) & (proposed > 0) & (proposed != before)):
        raise CrossOwnerContactHold('FROZEN_OWNER_REASSIGNMENT_NOT_REPAIRABLE')
    erased = (before > 0) & (proposed == 0)
    if np.any(erased & ~allowed_abstentions):
        raise CrossOwnerContactHold('UNAUTHORIZED_FROZEN_OWNER_ERASURE')
    h, w = before.shape
    to_remove = np.zeros(before.shape, dtype=bool)
    new_4_edges = 0
    new_diagonal_edges = 0
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        sy = slice(max(0, -dy), h - max(0, dy))
        ty = slice(max(0, dy), h - max(0, -dy))
        sx = slice(max(0, -dx), w - max(0, dx))
        tx = slice(max(0, dx), w - max(0, -dx))
        b1, b2 = before[sy, sx], before[ty, tx]
        a1, a2 = proposed[sy, sx], proposed[ty, tx]
        old = ((b1 == 1) & (b2 == 2)) | ((b1 == 2) & (b2 == 1))
        new = ((a1 == 1) & (a2 == 2)) | ((a1 == 2) & (a2 == 1))
        conflict = new & ~old
        n = int(np.count_nonzero(conflict))
        if dx == 0 or dy == 0:
            new_4_edges += n
        else:
            new_diagonal_edges += n
        if not n:
            continue
        first_added = (b1 == 0) & (a1 > 0)
        second_added = (b2 == 0) & (a2 > 0)
        if np.any(conflict & ~first_added & ~second_added):
            raise CrossOwnerContactHold('UNREPAIRABLE_NEW_CROSS_OWNER_CONTACT')
        to_remove[sy, sx] |= conflict & first_added
        to_remove[ty, tx] |= conflict & second_added
    out = proposed.copy()
    out[to_remove] = 0
    orphan_removed = 0
    if np.any(to_remove):
        st4 = ndimage.generate_binary_structure(2, 1)
        for owner_id in (1, 2):
            seeds = (before == owner_id) & (out == owner_id)
            mask = out == owner_id
            reachable = ndimage.binary_propagation(seeds, structure=st4, mask=mask)
            orphan = mask & ~reachable & (before == 0)
            orphan_removed += int(np.count_nonzero(orphan))
            out[orphan] = 0
    verify_no_new_cross_owner_contacts(before=before, after=out)
    try:
        transition = audit_frozen_owner_transition(
            before=before, after=out, allowed_abstentions=allowed_abstentions,
        )
    except FrozenOwnerTransitionHold as exc:
        raise CrossOwnerContactHold('FROZEN_OWNER_TRANSITION_HOLD:' + str(exc)) from exc
    return out, {
        'schema': 'minimalizer/local-l02/cross-owner-contact-addition-prune/v1',
        'new_cross_owner_4_edges_blocked': new_4_edges,
        'new_cross_owner_diagonal_edges_blocked': new_diagonal_edges,
        'newly_added_owner_pixels_removed': int(np.count_nonzero(to_remove)),
        'detached_added_owner_pixels_removed': orphan_removed,
        'frozen_owner_pixels_modified_by_repair': 0,
        'preapproved_frozen_owner_abstentions': transition['preapproved_frozen_owner_abstentions'],
        'frozen_owner_pixels_modified': transition['frozen_owner_pixels_modified'],
        'frozen_owner_transition_audit': transition,
        'human_annotations_used_for_inference': False,
        'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
    }
