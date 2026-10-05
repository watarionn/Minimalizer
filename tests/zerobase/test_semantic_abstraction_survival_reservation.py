import numpy as np

from minimalizer_zerobase.semantic_abstraction.survival_reservation import (
    reserve_semantic_survival_signatures,
)


def _fixture():
    rgb = np.full((64, 64, 3), (170, 150, 130), np.uint8)
    torso = np.zeros((64, 64), bool)
    torso[12:48, 16:48] = True
    rgb[20:26, 22:30] = (20, 40, 45)
    rgb[34:40, 34:42] = (75, 145, 210)
    return rgb, {"torso": torso}


def test_reservation_is_deterministic_and_source_supported():
    rgb, masks = _fixture()
    a = reserve_semantic_survival_signatures(rgb, masks)
    b = reserve_semantic_survival_signatures(rgb, masks)
    assert [(x.part_id, x.color, x.area_ratio, x.cx, x.cy) for x in a] == [
        (x.part_id, x.color, x.area_ratio, x.cx, x.cy) for x in b
    ]
    assert a
    for row in a:
        assert np.any(row.mask)
        assert row.part_id == "torso"
        assert np.all(masks[row.part_id][row.mask])


def test_small_high_contrast_signature_can_outrank_large_flat_mass():
    rgb, masks = _fixture()
    rows = reserve_semantic_survival_signatures(rgb, masks, max_reservations=2)
    colors = {row.color for row in rows}
    assert (20, 40, 45) in colors
    assert (75, 145, 210) in colors


def test_reservation_budget_is_hard_bounded():
    rgb, masks = _fixture()
    assert len(reserve_semantic_survival_signatures(rgb, masks, max_reservations=1)) <= 1


def test_mask_shape_mismatch_fails_closed():
    rgb, masks = _fixture()
    masks["bad"] = np.ones((10, 10), bool)
    try:
        reserve_semantic_survival_signatures(rgb, masks)
    except ValueError as exc:
        assert "shape mismatch" in str(exc)
    else:
        raise AssertionError("expected ValueError")
