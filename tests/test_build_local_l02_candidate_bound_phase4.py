import numpy as np
import pytest

from tools.research.audit_local_l02_phase5_input import PARTS
from tools.research.build_local_l02_candidate_bound_phase4 import (
    CandidateBoundPhase4Hold,
    arbitrate_outerwear_over_arm_owners,
    integrate_candidate_masks,
)


def base_masks(shape=(6, 6)):
    masks = {part: np.zeros(shape, dtype=bool) for part in PARTS}
    masks["torso"][2:4, 1:5] = True
    masks["left_arm"][2:5, 0] = True
    masks["face"][0, 2:4] = True
    return masks


def test_known_arm_and_torso_owners_are_preserved_on_candidate_conflict():
    base = base_masks()
    candidate = np.zeros((6, 6), dtype=np.uint8)
    candidate[2:5, 0:3] = 1
    source_alpha = np.ones((6, 6), dtype=bool)
    result, stats = integrate_candidate_masks(base, candidate, source_alpha)
    assert stats["accepted_garment_pixels"] == 2
    assert stats["known_owner_conflict_pixels"] == 7
    assert result["left_arm"][2:5, 0].all()
    assert result["torso"][2:4, 1:3].all()
    assert result["major_clothing"][4, 1:3].all()
    assert not result["major_clothing"][2:4, 0:3].any()


def test_unknown_candidate_connected_to_clothing_is_promoted():
    base = base_masks()
    candidate = np.zeros((6, 6), dtype=np.uint8)
    candidate[1, 1:3] = 1
    source_alpha = np.ones((6, 6), dtype=bool)
    result, stats = integrate_candidate_masks(base, candidate, source_alpha)
    assert stats["accepted_garment_pixels"] == 2
    assert result["major_clothing"][1, 1:3].all()
    assert not result["unknown"][1, 1:3].any()


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


def test_outerwear_component_reassigns_only_connected_arm_owner_pixels():
    base = base_masks()
    outerwear = np.zeros((6, 6), dtype=bool)
    outerwear[2:5, 0:3] = True
    result, stats = arbitrate_outerwear_over_arm_owners(
        base, outerwear, np.ones((6, 6), dtype=bool)
    )
    assert stats["eligible_outerwear_components"] == 1
    assert stats["arm_owner_pixels_reassigned_to_clothing"] == 3
    assert not result["left_arm"][2:5, 0].any()
    assert result["major_clothing"][2:5, 0].all()
    assert result["torso"][2:4, 1:3].all()


def test_isolated_outerwear_arm_overlap_is_abstained():
    base = base_masks()
    outerwear = np.zeros((6, 6), dtype=bool)
    outerwear[2:5, 0] = True
    result, stats = arbitrate_outerwear_over_arm_owners(
        base, outerwear, np.ones((6, 6), dtype=bool)
    )
    assert stats["eligible_outerwear_components"] == 0
    assert stats["arm_owner_pixels_reassigned_to_clothing"] == 0
    assert result["left_arm"][2:5, 0].all()
    assert not result["major_clothing"][2:5, 0].any()
