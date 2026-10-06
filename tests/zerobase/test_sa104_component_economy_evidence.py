from __future__ import annotations

import pytest

from minimalizer_zerobase.evaluation.component_economy_evidence import (
    build_component_economy_evidence,
)
from minimalizer_zerobase.semantic_abstraction.adaptive_primitive_budget import (
    AdaptivePrimitiveBudget,
    AdaptivePrimitiveBudgetEntry,
)


def _entry(role, components, primitives):
    return AdaptivePrimitiveBudgetEntry(
        role=role,
        required_minimum=1,
        hard_maximum=3,
        source_area=100,
        major_component_count=components,
        major_component_areas=tuple(range(components, 0, -1)),
        contour_vertices=10,
        complexity_score=1.0,
        allocated_primitives=primitives,
        reasons=(),
    )


def _budget():
    return AdaptivePrimitiveBudget(
        global_cap=5,
        allocated_total=4,
        unallocated=1,
        entries=(
            _entry("hair", 1, 1),
            _entry("major_clothing", 8, 3),
        ),
    )


def test_gc001_role_frame_requires_explicit_counts():
    evidence = build_component_economy_evidence(
        _budget(),
        represented_components={"hair": 1, "major_clothing": 3},
        source_supported_primitives={"hair": 1, "major_clothing": 3},
    )
    assert evidence.source_components == 9
    assert evidence.represented_components == 4
    assert evidence.component_survival_ratio == pytest.approx(4 / 9)
    assert evidence.emitted_primitives == 4
    assert evidence.source_supported_primitives == 4
    assert evidence.primitive_economy_ratio == 1.0
    assert evidence.authoritative is False


def test_missing_role_evidence_fails_closed():
    with pytest.raises(ValueError):
        build_component_economy_evidence(
            _budget(),
            represented_components={"hair": 1},
            source_supported_primitives={"hair": 1, "major_clothing": 3},
        )


def test_impossible_component_count_fails_closed():
    with pytest.raises(ValueError):
        build_component_economy_evidence(
            _budget(),
            represented_components={"hair": 2, "major_clothing": 3},
            source_supported_primitives={"hair": 1, "major_clothing": 3},
        )


def test_impossible_primitive_support_fails_closed():
    with pytest.raises(ValueError):
        build_component_economy_evidence(
            _budget(),
            represented_components={"hair": 1, "major_clothing": 3},
            source_supported_primitives={"hair": 2, "major_clothing": 3},
        )
