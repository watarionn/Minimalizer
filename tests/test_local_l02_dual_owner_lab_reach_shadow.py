"""Fail-closed provenance and source-only owner protection, no private inputs."""
import hashlib
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_dual_owner_lab_reach_shadow import (
    DualOwnerLabReachHold, propose_dual_owner_lab_reach_shadow,
)


def fixture():
    rgba = np.zeros((64, 64, 4), dtype=np.uint8)
    rgba[..., :3] = (120, 80, 130)
    rgba[..., 3] = 255
    cls = np.full((64, 64), 32, dtype=np.uint8)
    owner = np.zeros((64, 64), dtype=np.uint8)
    owner[15:30, 8:18] = 1
    owner[15:30, 48:58] = 2
    return rgba, cls, owner


def digest(owner):
    return hashlib.sha256(owner.tobytes(order='C')).hexdigest()


def run(rgba, cls, owner, pin):
    return propose_dual_owner_lab_reach_shadow(
        source_rgba=rgba, class_ids=cls, composed_owner=owner,
        expected_composed_owner_sha256=pin)


def test_owner_pin_is_mandatory_and_must_be_external():
    rgba, cls, owner = fixture()
    with pytest.raises(DualOwnerLabReachHold, match='MISSING_OR_INVALID_COMPOSED_OWNER_PIN'):
        run(rgba, cls, owner, '')
    with pytest.raises(DualOwnerLabReachHold, match='COMPOSED_OWNER_SHA_MISMATCH'):
        run(rgba, cls, owner, '0'*64)


def test_signed_stage_mismatch_is_rejected_before_candidate():
    rgba, cls, owner = fixture()
    pinned = digest(owner)
    owner[1, 1] = 1
    with pytest.raises(DualOwnerLabReachHold, match='COMPOSED_OWNER_SHA_MISMATCH'):
        run(rgba, cls, owner, pinned)


def test_source_alpha_and_owner_immutability():
    rgba, cls, owner = fixture()
    candidate, receipt = run(rgba, cls, owner, digest(owner))
    assert receipt['verified_composed_owner_sha256'] == digest(owner)
    assert receipt['semantic_owner_authorized'] is False
    assert receipt['Phase4'] == 'FAIL'
    assert np.array_equal(candidate[owner>0], owner[owner>0])
    assert np.all(candidate[(owner==0)&(candidate>0)] > 0)
    assert np.all(cls[(owner==0)&(candidate>0)] == 32)
    assert np.all(rgba[...,3][candidate>0] == 255)


def test_alpha_escape_fails_closed():
    rgba, cls, owner = fixture()
    rgba[20, 10, 3] = 0
    with pytest.raises(DualOwnerLabReachHold, match='INVALID_FROZEN_OWNER_PROVENANCE'):
        run(rgba, cls, owner, digest(owner))


def test_unrecognized_owner_class_fails_closed():
    rgba, cls, owner = fixture()
    cls[20, 10] = 1
    with pytest.raises(DualOwnerLabReachHold, match='INVALID_FROZEN_OWNER_PROVENANCE'):
        run(rgba, cls, owner, digest(owner))


def test_single_owner_abstains_even_with_valid_pin():
    rgba, cls, owner = fixture()
    owner[owner==1] = 0
    out, receipt = run(rgba, cls, owner, digest(owner))
    assert np.array_equal(out, owner)
    assert receipt['dual_owner_domain'] is False
    assert receipt['new_source_pixels'] == 0


def test_current_main_owner_and_contact_audits_are_attached():
    rgba, cls, owner = fixture()
    result, receipt = run(rgba, cls, owner, digest(owner))
    transition = receipt['frozen_owner_transition_audit']
    contacts = receipt['cross_owner_contact_audit']
    assert transition['schema'] == 'minimalizer/local-l02/frozen-owner-transition-audit/v1'
    assert transition['frozen_owner_pixels_modified'] == 0
    assert transition['newly_assigned_pixels'] == receipt['new_source_pixels']
    assert contacts['schema'] == 'minimalizer/local-l02/cross-owner-contact-edge-gate/v1'
    assert contacts['new_cross_owner_4_edges'] == 0
    assert contacts['new_cross_owner_diagonal_edges'] == 0
    assert receipt['Phase4'] == 'FAIL'
    assert np.array_equal(result[owner > 0], owner[owner > 0])


def test_main_frozen_owner_contract_rejection_is_not_suppressed(monkeypatch):
    import local_l02_dual_owner_lab_reach_shadow as shadow
    rgba, cls, owner = fixture()

    def reject(**kwargs):
        raise shadow.FrozenOwnerTransitionHold('FORCED_FROZEN_OWNER_NEGATIVE')

    monkeypatch.setattr(shadow, 'audit_frozen_owner_transition', reject)
    with pytest.raises(DualOwnerLabReachHold, match='MAIN_OWNER_CONTRACT_HOLD:FORCED_FROZEN_OWNER_NEGATIVE'):
        run(rgba, cls, owner, digest(owner))


def test_main_cross_owner_contract_rejection_is_not_suppressed(monkeypatch):
    import local_l02_dual_owner_lab_reach_shadow as shadow
    rgba, cls, owner = fixture()

    def reject(**kwargs):
        raise shadow.CrossOwnerContactHold('FORCED_CONTACT_NEGATIVE')

    monkeypatch.setattr(shadow, 'verify_no_new_cross_owner_contacts', reject)
    with pytest.raises(DualOwnerLabReachHold, match='MAIN_OWNER_CONTRACT_HOLD:FORCED_CONTACT_NEGATIVE'):
        run(rgba, cls, owner, digest(owner))
