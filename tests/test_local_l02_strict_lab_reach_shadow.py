"""Source-free guards, not a semantic quality or unknown-character test."""
import sys
from pathlib import Path
import hashlib
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_strict_lab_reach_shadow import propose_strict_lab_reach_shadow, StrictLabReachHold

def sample():
    rgba = np.full((20, 30, 4), 125, np.uint8)
    rgba[..., 3] = 255
    cls = np.full((20, 30), 32, np.uint8)
    owner = np.zeros((20, 30), np.uint8)
    owner[10, 3] = 1; owner[10, 26] = 2
    cls[10, 3] = 5; cls[10, 26] = 10
    return rgba, cls, owner

def call(rgba, cls, owner, pin=None):
    return propose_strict_lab_reach_shadow(
        source_rgba=rgba, class_ids=cls, strict_owner=owner,
        expected_strict_owner_sha256=pin or hashlib.sha256(owner.tobytes()).hexdigest())

def test_source_only_keeps_frozen_and_never_merges():
    rgba, cls, owner = sample()
    snapshots = [x.copy() for x in (rgba, cls, owner)]
    out, meta = call(rgba, cls, owner)
    assert meta['Phase4'] == 'FAIL'
    assert meta['new_source_pixels'] > 0
    np.testing.assert_array_equal(out[owner > 0], owner[owner > 0])
    assert np.count_nonzero(out[owner == 0]) == meta['new_source_pixels']
    for a, b in zip((rgba, cls, owner), snapshots):
        np.testing.assert_array_equal(a, b)

def test_pin_mismatch_fails_closed():
    rgba, cls, owner = sample()
    with pytest.raises(StrictLabReachHold, match='STRICT_OWNER_EXTERNAL_PIN_MISMATCH'):
        call(rgba, cls, owner, '0'*64)

def test_alpha_and_owner_provenance_fail_closed():
    rgba, cls, owner = sample()
    rgba[10, 3, 3] = 0
    with pytest.raises(StrictLabReachHold, match='INVALID_STRICT_OWNER_PROVENANCE'):
        call(rgba, cls, owner)
    rgba[10, 3, 3] = 255
    cls[10, 3] = 18
    with pytest.raises(StrictLabReachHold, match='INVALID_STRICT_OWNER_PROVENANCE'):
        call(rgba, cls, owner)

def test_single_owner_noop():
    rgba, cls, owner = sample()
    owner[10, 26] = 0
    out, meta = call(rgba, cls, owner)
    np.testing.assert_array_equal(out, owner)
    assert meta['new_source_pixels'] == 0
