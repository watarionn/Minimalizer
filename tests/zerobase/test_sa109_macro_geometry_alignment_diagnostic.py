from __future__ import annotations

import numpy as np
import pytest

from minimalizer_zerobase.evaluation.macro_geometry_alignment_diagnostic import (
    classify_macro_alignment,
    diagnose_macro_geometry_alignment,
)


def _mask(shape=(120, 120), boxes=()):
    out = np.zeros(shape, bool)
    for x0, y0, x1, y1 in boxes:
        out[y0:y1, x0:x1] = True
    return out


def test_alignment_classifier_distinguishes_three_contract_states():
    assert classify_macro_alignment(
        allocated_primitives=2,
        mass_candidates=2,
        emitted_primitives=2,
    ) == "ALIGNED"
    assert classify_macro_alignment(
        allocated_primitives=2,
        mass_candidates=1,
        emitted_primitives=1,
    ) == "BUDGET_MASS_GAP"
    assert classify_macro_alignment(
        allocated_primitives=2,
        mass_candidates=2,
        emitted_primitives=1,
    ) == "PRIMITIVE_GENERATION_DROP"


def test_impossible_alignment_counts_fail_closed():
    with pytest.raises(ValueError):
        classify_macro_alignment(
            allocated_primitives=1,
            mass_candidates=2,
            emitted_primitives=1,
        )
    with pytest.raises(ValueError):
        classify_macro_alignment(
            allocated_primitives=2,
            mass_candidates=1,
            emitted_primitives=2,
        )


def test_regular_source_is_aligned():
    hair = _mask(boxes=((10, 10, 50, 50),))
    clothing = _mask(
        boxes=(
            (65, 10, 110, 35),
            (65, 45, 110, 70),
            (65, 80, 110, 110),
        )
    )
    report = diagnose_macro_geometry_alignment(
        hair_mask=hair,
        clothing_mask=clothing,
        global_primitive_budget=5,
    )
    assert report.aligned is True
    assert all(role.status == "ALIGNED" for role in report.roles)
    assert report.authoritative is False
