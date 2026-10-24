"""Source-only Lane A audit for changes to a frozen owner assignment.

This is a verifier, never an inference input. It must run before any
postscore/quality promotion. It does not establish semantic Phase4 PASS.
"""
from __future__ import annotations
import numpy as np


class FrozenOwnerTransitionHold(ValueError):
    pass


def audit_frozen_owner_transition(*, before: np.ndarray, after: np.ndarray,
                                  allowed_abstentions: np.ndarray | None = None) -> dict:
    """Account for all frozen-owner deletions, including approved abstentions.

    Allowed abstentions authorize only zeroing exactly those old owner pixels.
    No existing owner may be reassigned to a different nonzero owner.
    """
    if (type(before) is not np.ndarray or type(after) is not np.ndarray or
            before.dtype != np.uint8 or after.dtype != np.uint8 or
            before.ndim != 2 or before.shape != after.shape or before.size == 0 or
            np.any(before > 2) or np.any(after > 2)):
        raise FrozenOwnerTransitionHold('INVALID_OWNER_ARRAYS')
    if allowed_abstentions is None:
        allowed_abstentions = np.zeros(before.shape, dtype=bool)
    elif (type(allowed_abstentions) is not np.ndarray or
          allowed_abstentions.dtype != np.bool_ or
          allowed_abstentions.shape != before.shape):
        raise FrozenOwnerTransitionHold('INVALID_ALLOWED_ABSTENTIONS')
    if np.any(allowed_abstentions & (before == 0)):
        raise FrozenOwnerTransitionHold('ABSTENTION_OUTSIDE_FROZEN_OWNER')
    reassigned = (before > 0) & (after > 0) & (before != after)
    if np.any(reassigned):
        raise FrozenOwnerTransitionHold('FROZEN_OWNER_REASSIGNED')
    erased = (before > 0) & (after == 0)
    if np.any(erased & ~allowed_abstentions):
        raise FrozenOwnerTransitionHold('UNAPPROVED_FROZEN_OWNER_ERASURE')
    n_erased = int(np.count_nonzero(erased))
    return {
        'schema': 'minimalizer/local-l02/frozen-owner-transition-audit/v1',
        'frozen_owner_pixels_modified': n_erased,
        'preapproved_frozen_owner_abstentions': n_erased,
        'newly_assigned_pixels': int(np.count_nonzero((before == 0) & (after > 0))),
        'frozen_owner_reassignments': 0,
        'human_annotations_used_for_inference': False,
        'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
    }
