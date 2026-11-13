from __future__ import annotations

import hashlib

import numpy as np
import pytest

from tools.research.local_l02_fashionpedia_outerwear_reconstruction import (
    FIXED_CONFIDENCE_THRESHOLD,
    FashionpediaOuterwearHold,
    reconstruct_outerwear_owner,
)


def _sha(value: np.ndarray) -> str:
    return hashlib.sha256(value.tobytes(order="C")).hexdigest()


def test_reconstructs_fresh_owner_from_main_garment_and_keeps_sleeves_diagnostic() -> None:
    alpha = np.ones((12, 14), dtype=bool)
    masks = np.zeros((4, 12, 14), dtype=bool)
    masks[0, 2:7, 3:7] = True  # jacket
    masks[1, 4:6, 7:10] = True  # sleeve touching jacket
    masks[1, 10:11, 12:13] = True  # detached detector artifact in same instance
    masks[2, 9:11, 1:3] = True  # unrelated sleeve: must remain unknown
    masks[3, 0:2, 0:2] = True  # shirt: not outerwear
    result = reconstruct_outerwear_owner(
        source_alpha=alpha,
        detection_masks=masks,
        class_ids=np.array([4, 31, 31, 1], dtype=np.int64),
        confidences=np.array([0.9, 0.8, 0.8, 0.9], dtype=np.float32),
    )

    assert result.selected_main_instances == 1
    assert result.selected_sleeve_instances == 2
    assert result.attached_sleeve_pixels == 0
    assert set(np.unique(result.owner)) == {0, 1}
    assert int(np.count_nonzero(result.owner)) == 20
    assert not result.observed[4:6, 7:10].any()
    assert result.unknown[4:6, 7:10].all()
    assert result.unknown[9:11, 1:3].all()


def test_rejects_case_specific_threshold() -> None:
    alpha = np.ones((3, 3), dtype=bool)
    masks = np.ones((1, 3, 3), dtype=bool)
    with pytest.raises(FashionpediaOuterwearHold, match="CASE_SPECIFIC_THRESHOLD_FORBIDDEN"):
        reconstruct_outerwear_owner(
            source_alpha=alpha,
            detection_masks=masks,
            class_ids=np.array([4], dtype=np.int64),
            confidences=np.array([0.9], dtype=np.float32),
            confidence_threshold=0.5,
        )


def test_output_is_alpha_bounded_and_unknown_is_not_negative() -> None:
    alpha = np.zeros((8, 8), dtype=bool)
    alpha[1:7, 1:7] = True
    masks = np.zeros((1, 8, 8), dtype=bool)
    masks[0, 0:4, 0:4] = True
    result = reconstruct_outerwear_owner(
        source_alpha=alpha,
        detection_masks=masks,
        class_ids=np.array([9], dtype=np.int64),
        confidences=np.array([FIXED_CONFIDENCE_THRESHOLD], dtype=np.float32),
    )

    assert not result.owner[~alpha].any()
    assert np.array_equal(result.unknown | result.observed, alpha)
    assert not np.logical_and(result.unknown, result.observed).any()


def test_rejects_non_boolean_detection_masks() -> None:
    alpha = np.ones((4, 4), dtype=bool)
    with pytest.raises(FashionpediaOuterwearHold, match="INVALID_DETECTION_MASKS"):
        reconstruct_outerwear_owner(
            source_alpha=alpha,
            detection_masks=np.ones((1, 4, 4), dtype=np.uint8),
            class_ids=np.array([4], dtype=np.int64),
            confidences=np.array([0.9], dtype=np.float32),
        )
