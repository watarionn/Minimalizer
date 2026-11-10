"""Regression: approved deletion must never be reported as zero loss."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_frozen_owner_transition_audit import (
    audit_frozen_owner_transition, FrozenOwnerTransitionHold,
)


def test_approved_deletion_is_counted_and_phase4_remains_fail():
    old = np.zeros((5, 5), np.uint8)
    old[2, 1:4] = 1
    new = old.copy()
    new[2, 3] = 0
    allowed = np.zeros(old.shape, bool)
    allowed[2, 3] = True
    receipt = audit_frozen_owner_transition(before=old, after=new,
                                            allowed_abstentions=allowed)
    assert receipt['frozen_owner_pixels_modified'] == 1
    assert receipt['preapproved_frozen_owner_abstentions'] == 1
    assert receipt['Phase4'] == 'FAIL'


def test_unapproved_deletion_and_owner_swap_fail_closed():
    old = np.zeros((5, 5), np.uint8)
    old[2, 2] = 1
    new = old.copy()
    new[2, 2] = 0
    with pytest.raises(FrozenOwnerTransitionHold, match='UNAPPROVED'):
        audit_frozen_owner_transition(before=old, after=new)
    new[2, 2] = 2
    with pytest.raises(FrozenOwnerTransitionHold, match='REASSIGNED'):
        audit_frozen_owner_transition(before=old, after=new)


def test_source_only_addition_does_not_count_as_frozen_loss():
    old = np.zeros((5, 5), np.uint8)
    old[2, 1] = 1
    new = old.copy()
    new[2, 2] = 1
    receipt = audit_frozen_owner_transition(before=old, after=new)
    assert receipt['frozen_owner_pixels_modified'] == 0
    assert receipt['newly_assigned_pixels'] == 1
    assert receipt['semantic_quality_pass'] is False


def test_malformed_inputs_rejected():
    old = np.zeros((2, 2), np.uint8)
    with pytest.raises(FrozenOwnerTransitionHold):
        audit_frozen_owner_transition(before=old, after=old.astype(bool))
    with pytest.raises(FrozenOwnerTransitionHold):
        audit_frozen_owner_transition(before=old, after=old,
                                      allowed_abstentions=np.ones((2, 2), bool))
