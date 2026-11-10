from __future__ import annotations

import hashlib

import numpy as np
import pytest

from tools.research.local_l02_component_owner_solver import (
    ComponentOwnerSolverHold,
    solve_component_owners,
)


def _sha(array: np.ndarray) -> str:
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def _source_alpha() -> np.ndarray:
    alpha = np.ones((10, 12), dtype=bool)
    alpha[[0, -1], :] = False
    alpha[:, [0, -1]] = False
    return alpha


def _roles(alpha: np.ndarray, *, arm=None, underlayer=None):
    arm_mask = np.zeros_like(alpha) if arm is None else arm
    under_mask = np.zeros_like(alpha) if underlayer is None else underlayer
    return (
        ("arm", arm_mask, _sha(arm_mask.astype(np.uint8)), "arm-observer"),
        (
            "underlayer",
            under_mask,
            _sha(under_mask.astype(np.uint8)),
            "underlayer-observer",
        ),
    )


def test_accepts_a_whole_unconflicted_instance_and_preserves_unknown():
    alpha = _source_alpha()
    instances = np.zeros((1, *alpha.shape), dtype=bool)
    instances[0, 2:5, 3:7] = True

    result = solve_component_owners(
        source_alpha=alpha,
        instance_masks=instances,
        instance_masks_sha256=_sha(instances),
        role_masks=_roles(alpha),
    )

    assert result.accepted_instances == (0,)
    assert result.decisions[0].decision == "ACCEPT_WHOLE_INSTANCE"
    assert np.all(result.owner[2:5, 3:7] == 1)
    assert int(result.unknown.sum()) == int(alpha.sum()) - 12
    assert result.source_only is True
    assert result.owner_promotion_authorized is False


def test_arm_conflict_abstains_the_whole_contact_component_not_just_overlap():
    alpha = _source_alpha()
    instances = np.zeros((1, *alpha.shape), dtype=bool)
    instances[0, 2:6, 3:8] = True
    arm = np.zeros_like(alpha)
    arm[3, 3] = True

    result = solve_component_owners(
        source_alpha=alpha,
        instance_masks=instances,
        instance_masks_sha256=_sha(instances),
        role_masks=_roles(alpha, arm=arm),
    )

    assert result.accepted_instances == ()
    assert result.decisions[0].decision == "ABSTAIN_WHOLE_CONTACT_COMPONENT"
    assert not np.any(result.owner)
    assert np.all(result.unknown[2:6, 3:8])


def test_overlapping_instances_are_not_resolved_by_pixel_priority():
    alpha = _source_alpha()
    instances = np.zeros((2, *alpha.shape), dtype=bool)
    instances[0, 2:6, 3:7] = True
    instances[1, 4:8, 5:9] = True

    result = solve_component_owners(
        source_alpha=alpha,
        instance_masks=instances,
        instance_masks_sha256=_sha(instances),
        role_masks=_roles(alpha),
        occlusion_edges=((0, 1),),
    )

    assert result.accepted_instances == ()
    assert result.decisions[0].decision == "ABSTAIN_WHOLE_CONTACT_COMPONENT"
    assert not np.any(result.owner)
    assert np.all(result.unknown[2:8, 3:9])


def test_rejects_instance_or_role_evidence_outside_source_alpha():
    alpha = _source_alpha()
    instances = np.zeros((1, *alpha.shape), dtype=bool)
    instances[0, 0, 1] = True
    with pytest.raises(ComponentOwnerSolverHold, match="INSTANCE_OUTSIDE_SOURCE_ALPHA"):
        solve_component_owners(
            source_alpha=alpha,
            instance_masks=instances,
            instance_masks_sha256=_sha(instances),
            role_masks=_roles(alpha),
        )

