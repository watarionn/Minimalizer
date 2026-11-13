import numpy as np
import pytest

from tools.research.local_l02_anime_bodypart_owner_solver import (
    AnimeBodypartOwnerHold,
    build_anime_bodypart_owner_candidate,
)


def _inputs():
    logits = np.full((19, 4, 5), -1.0, dtype=np.float32)
    classes = np.zeros((4, 5), dtype=np.uint8)
    alpha = np.ones((4, 5), dtype=bool)
    return logits, classes, alpha


def test_handwear_is_promoted_only_outside_independent_arm_observation():
    logits, classes, alpha = _inputs()
    logits[11, 1, 1] = 1.0  # topwear
    logits[12, 1, 2] = 1.0  # sleeve/handwear, not observed as arm
    logits[12, 1, 3] = 1.0  # handwear observed as arm
    classes[1, 3] = 6

    result = build_anime_bodypart_owner_candidate(
        see_through_logits=logits,
        sapiens_class_ids=classes,
        source_alpha=alpha,
    )

    assert result.owner[1, 1] == 1
    assert result.owner[1, 2] == 1
    assert result.owner[1, 3] == 0
    assert result.unknown[1, 3]
    assert result.source_only
    assert result.unknown_not_treated_as_negative
    assert not result.owner_promotion_authorized


def test_transparent_pixels_are_never_promoted():
    logits, classes, alpha = _inputs()
    logits[11, 0, 0] = 2.0
    alpha[0, 0] = False

    result = build_anime_bodypart_owner_candidate(
        see_through_logits=logits,
        sapiens_class_ids=classes,
        source_alpha=alpha,
    )

    assert result.owner[0, 0] == 0
    assert not result.unknown[0, 0]


def test_mismatched_observers_fail_closed():
    logits, classes, alpha = _inputs()
    with pytest.raises(AnimeBodypartOwnerHold, match="OBSERVATION_SHAPE_MISMATCH"):
        build_anime_bodypart_owner_candidate(
            see_through_logits=logits,
            sapiens_class_ids=classes[:3],
            source_alpha=alpha,
        )
