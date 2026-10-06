import numpy as np
import pytest

from minimalizer_zerobase.semantic_abstraction.layer_occlusion_evidence import (
    LayerRelation,
    observe_layer_occlusion,
)


def _mask(boxes=()):
    out = np.zeros((80, 80), bool)
    for x0, y0, x1, y1 in boxes:
        out[y0:y1, x0:x1] = True
    return out


def _relation(report, a, b):
    key = tuple(sorted((a, b)))
    return next(
        row
        for row in report.relations
        if (row.role_a, row.role_b) == key
    )


def test_overlap_is_observed_without_inventing_direction():
    report = observe_layer_occlusion(
        {
            "hair": _mask(((10, 10, 45, 45),)),
            "head": _mask(((30, 25, 60, 60),)),
        }
    )
    row = _relation(report, "hair", "head")

    assert row.relation is LayerRelation.OVERLAP
    assert row.overlap_pixels > 0
    assert row.front_role is None
    assert row.back_role is None
    assert row.direction_source == "unavailable"
    assert row.authoritative is False


def test_existing_canonical_z_order_can_be_observed_not_changed():
    report = observe_layer_occlusion(
        {
            "hair": _mask(((10, 10, 45, 45),)),
            "head": _mask(((30, 25, 60, 60),)),
        },
        role_z_order={"hair": 10, "head": 20},
    )
    row = _relation(report, "hair", "head")

    assert row.front_role == "head"
    assert row.back_role == "hair"
    assert row.direction_source == "canonical_z_order_observation"
    assert report.production_output_changed is False
    assert report.authoritative is False


def test_touching_masks_are_not_promoted_to_overlap():
    report = observe_layer_occlusion(
        {
            "left_arm": _mask(((10, 10, 30, 30),)),
            "torso": _mask(((30, 10, 50, 30),)),
        }
    )
    row = _relation(report, "left_arm", "torso")

    assert row.relation is LayerRelation.TOUCHING
    assert row.overlap_pixels == 0
    assert row.boundary_contact_pixels > 0


def test_disjoint_masks_remain_explicitly_disjoint():
    report = observe_layer_occlusion(
        {
            "hair": _mask(((5, 5, 20, 20),)),
            "lower_body": _mask(((55, 55, 75, 75),)),
        },
        role_z_order={"hair": 5, "lower_body": 50},
    )
    row = _relation(report, "hair", "lower_body")

    assert row.relation is LayerRelation.DISJOINT
    assert row.front_role is None
    assert row.direction_source == "not_applicable"


def test_equal_z_order_is_ambiguous_not_invented():
    report = observe_layer_occlusion(
        {
            "left_arm": _mask(((10, 10, 40, 40),)),
            "torso": _mask(((25, 25, 60, 60),)),
        },
        role_z_order={"left_arm": 10, "torso": 10},
    )
    row = _relation(report, "left_arm", "torso")

    assert row.relation is LayerRelation.OVERLAP
    assert row.front_role is None
    assert row.back_role is None
    assert row.direction_source == "ambiguous_equal_canonical_z_order"


def test_partial_z_order_is_recorded_as_partial():
    report = observe_layer_occlusion(
        {
            "hair": _mask(((10, 10, 45, 45),)),
            "head": _mask(((30, 25, 60, 60),)),
        },
        role_z_order={"head": 20},
    )
    row = _relation(report, "hair", "head")

    assert row.front_role is None
    assert row.direction_source == "partial_canonical_z_order"


def test_mapping_order_does_not_change_report():
    hair = _mask(((10, 10, 45, 45),))
    head = _mask(((30, 25, 60, 60),))
    torso = _mask(((20, 50, 55, 75),))

    a = observe_layer_occlusion(
        {"hair": hair, "head": head, "torso": torso},
        role_z_order={"hair": 5, "head": 10, "torso": 15},
    )
    b = observe_layer_occlusion(
        {"torso": torso, "head": head, "hair": hair},
        role_z_order={"torso": 15, "head": 10, "hair": 5},
    )

    assert a.to_dict() == b.to_dict()


def test_shape_mismatch_fails_closed():
    with pytest.raises(ValueError, match="shape mismatch"):
        observe_layer_occlusion(
            {
                "hair": np.zeros((20, 20), bool),
                "head": np.zeros((30, 20), bool),
            }
        )


def test_unknown_z_order_role_fails_closed():
    with pytest.raises(ValueError, match="unknown roles"):
        observe_layer_occlusion(
            {"hair": _mask(((5, 5, 20, 20),))},
            role_z_order={"invented": 1},
        )
