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
