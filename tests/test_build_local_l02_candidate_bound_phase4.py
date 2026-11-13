import numpy as np
import pytest

from tools.research.audit_local_l02_phase5_input import PARTS
from tools.research.build_local_l02_candidate_bound_phase4 import (
    CandidateBoundPhase4Hold,
    integrate_candidate_masks,
)


def base_masks(shape=(6, 6)):
    masks = {part: np.zeros(shape, dtype=bool) for part in PARTS}
    masks["torso"][2:4, 1:5] = True
    masks["left_arm"][2:5, 0] = True
    masks["face"][0, 2:4] = True
    return masks


def test_connected_garment_component_takes_exclusive_arm_owner():
    base = base_masks()
    candidate = np.zeros((6, 6), dtype=np.uint8)
    candidate[2:5, 0:3] = 1
    source_alpha = np.ones((6, 6), dtype=bool)
    result, stats = integrate_candidate_masks(base, candidate, source_alpha)
    assert stats["accepted_garment_pixels"] == 9
    assert result["major_clothing"][2:5, 0:3].all()
    assert not result["left_arm"][2:5, 0].any()


def test_disconnected_candidate_becomes_unknown():
    base = base_masks()
    candidate = np.zeros((6, 6), dtype=np.uint8)
    candidate[5, 5] = 1
    result, stats = integrate_candidate_masks(base, candidate, np.ones((6, 6), dtype=bool))
    assert stats["accepted_garment_pixels"] == 0
    assert result["unknown"][5, 5]
    assert not result["major_clothing"][5, 5]


def test_protected_face_is_not_overwritten():
    base = base_masks()
    candidate = np.zeros((6, 6), dtype=np.uint8)
    candidate[0, 2:4] = 1
    result, stats = integrate_candidate_masks(base, candidate, np.ones((6, 6), dtype=bool))
    assert stats["protected_candidate_pixels"] == 2
    assert result["face"][0, 2:4].all()
    assert not result["major_clothing"][0, 2:4].any()


def test_invalid_owner_and_alpha_outside_fail_closed():
    base = base_masks()
    source_alpha = np.ones((6, 6), dtype=bool)
    invalid = np.zeros((6, 6), dtype=np.uint8)
    invalid[2, 2] = 3
    with pytest.raises(CandidateBoundPhase4Hold, match="OWNER_VALUE"):
        integrate_candidate_masks(base, invalid, source_alpha)
    outside = np.zeros((6, 6), dtype=np.uint8)
    outside[5, 5] = 1
    source_alpha[5, 5] = False
    with pytest.raises(CandidateBoundPhase4Hold, match="OUTSIDE_SOURCE_ALPHA"):
        integrate_candidate_masks(base, outside, source_alpha)
