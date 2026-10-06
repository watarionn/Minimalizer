import json

import numpy as np
import pytest

from minimalizer_zerobase.semantic_abstraction.adaptive_primitive_budget import (
    ADAPTIVE_PRIMITIVE_BUDGET_VERSION,
    allocate_adaptive_primitive_budget,
)
from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import (
    reauthor_macro_geometry_with_budget,
)


def _mask(shape=(160, 160), boxes=()):
    out = np.zeros(shape, bool)
    for x0, y0, x1, y1 in boxes:
        out[y0:y1, x0:x1] = True
    return out


def _allocate(role_masks, cap=5):
    return allocate_adaptive_primitive_budget(
        role_masks,
        global_cap=cap,
        minimums={"hair": 1, "major_clothing": 1},
        maximums={"hair": 3, "major_clothing": 3},
    )


def test_simple_roles_receive_only_required_minimum():
    report = _allocate(
        {
            "hair": _mask(boxes=((10, 10, 70, 70),)),
            "major_clothing": _mask(boxes=((80, 80, 145, 145),)),
        }
    )

    assert report.version == ADAPTIVE_PRIMITIVE_BUDGET_VERSION
    assert report.for_role("hair") == 1
    assert report.for_role("major_clothing") == 1
    assert report.allocated_total == 2
    assert report.unallocated == 3


def test_complex_source_supported_role_receives_more_budget():
    report = _allocate(
        {
            "hair": _mask(boxes=((10, 10, 70, 70),)),
            "major_clothing": _mask(
                boxes=(
                    (85, 10, 145, 50),
                    (85, 65, 145, 105),
                    (85, 120, 145, 155),
                )
            ),
        }
    )

    assert report.for_role("hair") == 1
    assert report.for_role("major_clothing") == 3
    clothing = next(
        row for row in report.entries
        if row.role == "major_clothing"
    )
    assert clothing.major_component_count == 3
    assert clothing.contour_vertices >= 12
    assert clothing.complexity_score > 0


def test_required_minimum_cannot_be_starved_by_optional_complexity():
    report = _allocate(
        {
            "hair": _mask(
                boxes=(
                    (5, 5, 50, 50),
                    (5, 65, 50, 110),
                    (5, 120, 50, 155),
                )
            ),
            "major_clothing": _mask(
                boxes=(
                    (90, 5, 150, 50),
                    (90, 65, 150, 110),
                    (90, 120, 150, 155),
                )
            ),
        },
        cap=2,
    )

    assert report.for_role("hair") == 1
    assert report.for_role("major_clothing") == 1
    assert report.allocated_total == 2


def test_global_cap_is_enforced_across_roles():
    report = _allocate(
        {
            "hair": _mask(
                boxes=(
                    (5, 5, 45, 45),
                    (5, 60, 45, 100),
                    (5, 115, 45, 155),
                )
            ),
            "major_clothing": _mask(
                boxes=(
                    (75, 5, 155, 45),
                    (75, 60, 155, 100),
                    (75, 115, 155, 155),
                )
            ),
        },
        cap=5,
    )

    assert report.allocated_total == 5
    assert sum(row.allocated_primitives for row in report.entries) == 5
    assert report.for_role("major_clothing") == 3
    assert report.for_role("hair") == 2


def test_mapping_order_does_not_change_budget():
    hair = _mask(
        boxes=(
            (5, 5, 50, 50),
            (5, 65, 50, 110),
        )
    )
    clothing = _mask(
        boxes=(
            (90, 5, 150, 50),
            (90, 65, 150, 110),
            (90, 120, 150, 155),
        )
    )
    a = _allocate({"hair": hair, "major_clothing": clothing})
    b = _allocate({"major_clothing": clothing, "hair": hair})
    assert a.to_dict() == b.to_dict()


def test_repeat_allocation_is_byte_deterministic():
    masks = {
        "hair": _mask(
            boxes=(
                (5, 5, 50, 50),
                (5, 65, 50, 110),
            )
        ),
        "major_clothing": _mask(
            boxes=(
                (90, 5, 150, 50),
                (90, 65, 150, 110),
            )
        ),
    }
    a = _allocate(masks)
    b = _allocate(masks)
    assert json.dumps(a.to_dict(), sort_keys=True) == json.dumps(
        b.to_dict(),
        sort_keys=True,
    )


def test_micro_fragments_do_not_inflate_demand():
    hair = _mask(
        boxes=(
            (10, 10, 80, 80),
            (120, 120, 122, 122),
            (130, 130, 132, 132),
        )
    )
    clothing = _mask(boxes=((85, 10, 150, 100),))
    report = _allocate({"hair": hair, "major_clothing": clothing})

    assert report.for_role("hair") == 1
    hair_row = next(row for row in report.entries if row.role == "hair")
    assert hair_row.major_component_count == 1


def test_cap_below_required_minimum_fails_closed():
    with pytest.raises(ValueError, match="cannot satisfy required minimum 2"):
        _allocate(
            {
                "hair": _mask(boxes=((10, 10, 80, 80),)),
                "major_clothing": _mask(boxes=((85, 10, 150, 100),)),
            },
            cap=1,
        )


def test_macro_reauthoring_consumes_adaptive_allocation():
    hair = _mask(boxes=((10, 10, 70, 70),))
    clothing = _mask(
        boxes=(
            (85, 10, 145, 50),
            (85, 65, 145, 105),
            (85, 120, 145, 155),
        )
    )

    primitives, budget = reauthor_macro_geometry_with_budget(
        hair_mask=hair,
        clothing_mask=clothing,
        global_primitive_budget=5,
    )

    assert budget.for_role("hair") == 1
    assert budget.for_role("major_clothing") == 3
    assert sum(p.semantic_part == "hair" for p in primitives) == 1
    assert sum(
        p.semantic_part == "major_clothing"
        for p in primitives
    ) == 3
