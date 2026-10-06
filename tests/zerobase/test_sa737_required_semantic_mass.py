import numpy as np
import pytest

from minimalizer_zerobase.semantic_abstraction.required_semantic_mass import (
    MAX_EXPANSION_RATIO,
    MIN_SOURCE_COVERAGE,
    reserve_required_semantic_masses,
)


def test_reserves_bounded_contrasting_torso_and_arm_masses():
    image = np.full((60, 60, 3), [180, 100, 80], dtype=np.uint8)
    torso = np.zeros((60, 60), dtype=bool)
    torso[10:45, 18:42] = True
    arm = np.zeros((60, 60), dtype=bool)
    arm[20:50, 5:15] = True

    image[18:30, 24:36] = [20, 20, 20]
    image[31:40, 24:36] = [150, 190, 20]
    image[28:44, 6:14] = [15, 45, 55]

    rows = reserve_required_semantic_masses(
        image,
        {"torso": torso, "right_arm": arm},
        role_cluster_counts={"torso": 3, "right_arm": 2},
    )
    assert rows
    assert {row.role for row in rows} <= {"torso", "right_arm"}
    assert any(row.role == "torso" for row in rows)
    assert any(row.role == "right_arm" for row in rows)
    assert all(row.source_coverage >= MIN_SOURCE_COVERAGE for row in rows)
    assert all(row.expansion_ratio <= MAX_EXPANSION_RATIO for row in rows)
    assert all(row.outside_role_pixels == 0 for row in rows)


def test_face_and_head_reservation_is_forbidden():
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    mask = np.ones((20, 20), dtype=bool)
    with pytest.raises(ValueError, match="forbidden"):
        reserve_required_semantic_masses(
            image,
            {"face": mask},
            role_cluster_counts={"face": 2},
        )


def test_deterministic():
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    torso = np.zeros((40, 40), dtype=bool)
    torso[5:35, 8:32] = True
    image[torso] = [160, 90, 70]
    image[10:20, 10:20] = [20, 20, 20]
    image[22:30, 20:30] = [150, 180, 20]
    a = reserve_required_semantic_masses(
        image, {"torso": torso}, role_cluster_counts={"torso": 3}
    )
    b = reserve_required_semantic_masses(
        image, {"torso": torso}, role_cluster_counts={"torso": 3}
    )
    assert a == b
