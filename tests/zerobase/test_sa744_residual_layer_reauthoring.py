import cv2
import numpy as np

from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import (
    MacroGeometryPrimitive,
)
from minimalizer_zerobase.semantic_abstraction.residual_layer_reauthoring import (
    RESIDUAL_LAYER_VERSION,
    reauthor_residual_layers,
)


def _mask(shape=(120, 120), boxes=()):
    out = np.zeros(shape, bool)
    for x0, y0, x1, y1 in boxes:
        out[y0:y1, x0:x1] = True
    return out


def _poly(x0, y0, x1, y1, role):
    return MacroGeometryPrimitive(
        semantic_part=role,
        polygon=np.array(
            [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
            dtype=np.float32,
        ),
        source_area=max(1, (x1 - x0) * (y1 - y0)),
        retained_area=max(1, (x1 - x0) * (y1 - y0)),
    )


def test_no_residual_when_coarse_geometry_covers_authority():
    masks = {
        "hair": _mask(boxes=((10, 10, 50, 50),)),
        "major_clothing": _mask(boxes=((70, 70, 110, 110),)),
    }
    base = (
        _poly(10, 10, 49, 49, "hair"),
        _poly(70, 70, 109, 109, "major_clothing"),
    )

    layers, report = reauthor_residual_layers(masks, base, global_cap=3)

    assert layers == ()
    assert report.version == RESIDUAL_LAYER_VERSION
    assert report.selected_count == 0


def test_large_missing_lobe_becomes_one_residual_layer():
    hair = _mask(
        boxes=(
            (10, 10, 50, 50),
            (60, 10, 90, 40),
        )
    )
    masks = {
        "hair": hair,
        "major_clothing": _mask(boxes=((20, 70, 100, 110),)),
    }
    base = (
        _poly(10, 10, 49, 49, "hair"),
        _poly(20, 70, 99, 109, "major_clothing"),
    )

    layers, report = reauthor_residual_layers(masks, base, global_cap=3)

    hair_layers = [layer for layer in layers if layer.semantic_part == "hair"]
    assert len(hair_layers) == 1
    assert hair_layers[0].layer_kind == "residual"
    assert report.selected_count == 1
    assert report.selected[0].authority_spill == 0


def test_tiny_residual_fragments_do_not_consume_budget():
    hair = _mask(
        boxes=(
            (10, 10, 70, 70),
            (90, 90, 92, 92),
        )
    )
    masks = {
        "hair": hair,
        "major_clothing": _mask(boxes=((10, 80, 70, 115),)),
    }
    base = (
        _poly(10, 10, 69, 69, "hair"),
        _poly(10, 80, 69, 114, "major_clothing"),
    )

    layers, report = reauthor_residual_layers(masks, base, global_cap=3)

    assert layers == ()
    assert report.selected_count == 0


def test_higher_marginal_value_wins_under_cap():
    masks = {
        "hair": _mask(
            boxes=(
                (5, 5, 45, 45),
                (55, 5, 85, 35),
            )
        ),
        "major_clothing": _mask(
            boxes=(
                (5, 70, 55, 115),
                (70, 80, 90, 100),
            )
        ),
    }
    base = (
        _poly(5, 5, 44, 44, "hair"),
        _poly(5, 70, 54, 114, "major_clothing"),
    )

    layers, report = reauthor_residual_layers(masks, base, global_cap=1)

    assert len(layers) == 1
    assert layers[0].semantic_part == "hair"
    assert report.selected[0].residual_area > 800


def test_residual_polygon_never_crosses_other_role_authority():
    hair = _mask(
        boxes=(
            (10, 10, 60, 60),
            (60, 30, 90, 55),
        )
    )
    clothing = _mask(boxes=((75, 20, 110, 70),))
    masks = {
        "hair": hair,
        "major_clothing": clothing,
    }
    base = (
        _poly(10, 10, 59, 59, "hair"),
        _poly(75, 20, 109, 69, "major_clothing"),
    )

    layers, report = reauthor_residual_layers(masks, base, global_cap=3)

    for candidate in report.selected:
        assert candidate.authority_spill == 0
        raster = np.zeros(hair.shape, np.uint8)
        cv2.fillPoly(
            raster,
            [candidate.polygon.astype(np.int32)],
            1,
        )
        if candidate.role == "hair":
            assert int((raster.astype(bool) & clothing).sum()) == 0
        else:
            assert int((raster.astype(bool) & hair).sum()) == 0


def test_global_residual_cap_is_enforced():
    masks = {
        "hair": _mask(
            boxes=(
                (5, 5, 35, 35),
                (45, 5, 75, 35),
                (85, 5, 115, 35),
            )
        ),
        "major_clothing": _mask(
            boxes=(
                (5, 75, 35, 105),
                (45, 75, 75, 105),
                (85, 75, 115, 105),
            )
        ),
    }
    base = (
        _poly(5, 5, 34, 34, "hair"),
        _poly(5, 75, 34, 104, "major_clothing"),
    )

    layers, report = reauthor_residual_layers(masks, base, global_cap=2)

    assert len(layers) == 2
    assert report.selected_count == 2


def test_repeat_and_mapping_order_are_deterministic():
    hair = _mask(
        boxes=(
            (5, 5, 45, 45),
            (55, 5, 90, 40),
        )
    )
    clothing = _mask(
        boxes=(
            (5, 70, 55, 115),
            (70, 75, 105, 110),
        )
    )
    base = (
        _poly(5, 5, 44, 44, "hair"),
        _poly(5, 70, 54, 114, "major_clothing"),
    )

    a_layers, a = reauthor_residual_layers(
        {"hair": hair, "major_clothing": clothing},
        base,
        global_cap=2,
    )
    b_layers, b = reauthor_residual_layers(
        {"major_clothing": clothing, "hair": hair},
        base,
        global_cap=2,
    )

    assert a.to_dict() == b.to_dict()
    assert [
        (
            layer.semantic_part,
            layer.component_index,
            layer.layer_kind,
            layer.source_area,
        )
        for layer in a_layers
    ] == [
        (
            layer.semantic_part,
            layer.component_index,
            layer.layer_kind,
            layer.source_area,
        )
        for layer in b_layers
    ]
