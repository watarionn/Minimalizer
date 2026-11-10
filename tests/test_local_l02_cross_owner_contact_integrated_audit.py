"""Source-free Lane A contract for the merged PR #421 deletion auditor."""
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_cross_owner_contact_gate import (
    CrossOwnerContactHold, prune_new_cross_owner_additions,
    verify_no_new_cross_owner_contacts,
)


def test_preapproved_frozen_owner_erasure_is_counted_not_hidden():
    before = np.zeros((9, 9), np.uint8)
    before[4, 1:5] = 1
    before[7, 7] = 2
    proposed = before.copy()
    proposed[4, 4] = 0
    allowed = np.zeros(before.shape, bool)
    allowed[4, 4] = True
    result, receipt = prune_new_cross_owner_additions(
        before=before, proposed=proposed, allowed_abstentions=allowed,
    )
    assert np.array_equal(result, proposed)
    assert receipt['frozen_owner_pixels_modified'] == 1
    assert receipt['frozen_owner_pixels_modified_by_repair'] == 0
    assert receipt['preapproved_frozen_owner_abstentions'] == 1
    assert receipt['frozen_owner_transition_audit']['Phase4'] == 'FAIL'
    assert receipt['L02'] == 'HOLD'


def test_unapproved_deletion_and_owner_reassignment_fail_closed():
    before = np.zeros((7, 7), np.uint8)
    before[3, 2] = 1
    proposed = before.copy()
    proposed[3, 2] = 0
    with pytest.raises(CrossOwnerContactHold, match='UNAUTHORIZED_FROZEN_OWNER_ERASURE'):
        prune_new_cross_owner_additions(before=before, proposed=proposed)
    proposed[3, 2] = 2
    with pytest.raises(CrossOwnerContactHold, match='FROZEN_OWNER_REASSIGNMENT'):
        prune_new_cross_owner_additions(before=before, proposed=proposed)


def test_contact_repair_removes_additions_without_erasing_frozen():
    before = np.zeros((9, 9), np.uint8)
    before[4, 1] = 1
    before[4, 6] = 2
    proposed = before.copy()
    proposed[4, 2:4] = 1
    proposed[4, 4:6] = 2
    repaired, receipt = prune_new_cross_owner_additions(before=before, proposed=proposed)
    assert repaired[4, 1] == 1 and repaired[4, 6] == 2
    assert receipt['frozen_owner_pixels_modified'] == 0
    assert receipt['newly_added_owner_pixels_removed'] >= 1
    verify_no_new_cross_owner_contacts(before=before, after=repaired)


def test_invalid_approval_masks_rejected():
    before = np.zeros((3, 3), np.uint8)
    before[1, 1] = 1
    with pytest.raises(CrossOwnerContactHold, match='INVALID_ALLOWED_ABSTENTION_MASK'):
        prune_new_cross_owner_additions(
            before=before, proposed=before, allowed_abstentions=np.ones((3, 3), np.uint8))
    with pytest.raises(CrossOwnerContactHold, match='ABSTENTION_MASK_OUTSIDE_FROZEN_OWNER'):
        prune_new_cross_owner_additions(
            before=before, proposed=before, allowed_abstentions=np.ones((3, 3), bool))


def test_8_neighbour_diagonal_contact_is_not_silently_accepted():
    before = np.zeros((5, 5), np.uint8)
    before[1, 1] = 1
    before[3, 3] = 2
    proposed = before.copy()
    proposed[2, 2] = 1
    repaired, receipt = prune_new_cross_owner_additions(before=before, proposed=proposed)
    assert repaired[2, 2] == 0
    assert receipt['new_cross_owner_diagonal_edges_blocked'] > 0


def test_original_arrays_not_mutated():
    before = np.zeros((5, 5), np.uint8)
    before[2, 1] = 1
    before[2, 3] = 2
    proposed = before.copy()
    proposed[2, 2] = 1
    original = proposed.copy()
    prune_new_cross_owner_additions(before=before, proposed=proposed)
    assert np.array_equal(proposed, original)
