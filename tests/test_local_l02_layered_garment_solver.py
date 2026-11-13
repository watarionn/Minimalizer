import hashlib

import numpy as np

from tools.research.local_l02_layered_garment_solver import solve_layered_garment


def sha(mask: np.ndarray) -> str:
    return hashlib.sha256(mask.astype(np.uint8).tobytes(order="C")).hexdigest()


def test_attached_sleeve_is_kept_as_garment_over_arm():
    alpha = np.ones((32, 32), dtype=bool)
    masks = np.zeros((2, 32, 32), dtype=bool)
    masks[0, 8:24, 8:20] = True  # jacket body
    masks[1, 12:20, 18:28] = True  # attached sleeve
    arm = np.zeros_like(alpha)
    arm[14:18, 22:27] = True
    result = solve_layered_garment(
        source_alpha=alpha,
        detection_masks=masks,
        detection_classes=np.array([4, 31], dtype=np.int64),
        detection_confidences=np.array([0.9, 0.9], dtype=np.float32),
        arm_mask=arm,
        detection_masks_sha256=sha(masks),
        arm_mask_sha256=sha(arm),
    )
    assert result.owner[15, 24] == 1
    assert result.sleeve_decisions[0].decision == "ACCEPT_GARMENT_OVER_ARM_OCCLUSION"


def test_disconnected_sleeve_stays_unknown():
    alpha = np.ones((32, 32), dtype=bool)
    masks = np.zeros((2, 32, 32), dtype=bool)
    masks[0, 8:16, 8:16] = True
    masks[1, 24:29, 24:29] = True
    arm = np.zeros_like(alpha)
    result = solve_layered_garment(
        source_alpha=alpha,
        detection_masks=masks,
        detection_classes=np.array([4, 31], dtype=np.int64),
        detection_confidences=np.array([0.9, 0.9], dtype=np.float32),
        arm_mask=arm,
        detection_masks_sha256=sha(masks),
        arm_mask_sha256=sha(arm),
    )
    assert result.owner[25, 25] == 0
    assert result.unknown[25, 25]


def test_underlayer_is_observed_but_never_negative():
    alpha = np.ones((20, 20), dtype=bool)
    masks = np.zeros((2, 20, 20), dtype=bool)
    masks[0, 4:12, 4:12] = True
    masks[1, 10:16, 10:16] = True
    arm = np.zeros_like(alpha)
    result = solve_layered_garment(
        source_alpha=alpha,
        detection_masks=masks,
        detection_classes=np.array([4, 0], dtype=np.int64),
        detection_confidences=np.array([0.9, 0.9], dtype=np.float32),
        arm_mask=arm,
        detection_masks_sha256=sha(masks),
        arm_mask_sha256=sha(arm),
    )
    assert result.underlayer_observed[12, 12]
    assert result.owner[12, 12] == 0
    assert result.unknown[12, 12]
