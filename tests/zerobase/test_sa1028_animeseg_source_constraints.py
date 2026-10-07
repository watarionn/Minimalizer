import numpy as np

from minimalizer_zerobase.simplification.animeseg_source_constraints import (
    CLASS_RGB, build_source_constraints, source_bound_detail_groups,
)


def test_animeseg_classes_are_clipped_by_source_alpha():
    source = np.zeros((2, 3, 4), dtype=np.uint8)
    source[..., 3] = [[255, 0, 255], [255, 255, 0]]
    mask = np.zeros((2, 3, 3), dtype=np.uint8)
    mask[0, 0] = CLASS_RGB[4]
    mask[0, 1] = CLASS_RGB[4]
    mask[1, 0] = CLASS_RGB[3]
    mask[1, 2] = (7, 8, 9)
    result = build_source_constraints(source, mask)
    assert result["classes"]["left_eye"]["raw_pixels"] == 2
    assert result["classes"]["left_eye"]["source_clipped_pixels"] == 1
    assert result["classes"]["left_eye"]["alpha_removed_pixels"] == 1
    assert result["unknown_rgb_pixels"] == 1
    assert result["authority"] is False


def test_invalid_shape_fails_closed():
    source = np.zeros((2, 2, 3), dtype=np.uint8)
    mask = np.zeros((2, 2, 3), dtype=np.uint8)
    try:
        build_source_constraints(source, mask)
    except ValueError as exc:
        assert "HxWx4" in str(exc)
    else:
        raise AssertionError("invalid source shape must fail")


def test_detail_groups_are_source_colored_and_source_alpha_bound():
    source = np.zeros((8, 8, 4), dtype=np.uint8)
    source[..., :3] = (10, 20, 30)
    source[..., 3] = 255
    source[2:5, 2:5, :3] = (200, 100, 50)
    source[2, 2, 3] = 0
    mask = np.zeros((8, 8, 3), dtype=np.uint8)
    mask[2:5, 2:5] = CLASS_RGB[4]
    constraints = build_source_constraints(source, mask)
    groups = source_bound_detail_groups(constraints, source, minimum_pixels=3)
    assert len(groups) == 1
    assert groups[0]["part"] == "face"
    assert groups[0]["color"] == (200, 100, 50)
    assert not groups[0]["mask"][2, 2]  # transparent source pixel is excluded
