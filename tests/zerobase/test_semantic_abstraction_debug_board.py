from __future__ import annotations

from minimalizer_zerobase.semantic_abstraction.debug_board import (
    canonical_debug_json,
    render_semantic_debug_svg,
)
from minimalizer_zerobase.semantic_abstraction.ir import (
    AbstractionPlan,
    AbstractionPolicy,
    SemanticPart,
)


def _plan(order: tuple[str, ...]) -> AbstractionPlan:
    return AbstractionPlan(
        parts=tuple(
            SemanticPart(
                id=item,
                category=item,
                bbox=(0.1, 0.2, 0.5, 0.8),
                importance=0.75,
                abstraction_policy=AbstractionPolicy.PRESERVE,
            )
            for item in order
        )
    )


def test_debug_json_is_reorder_invariant() -> None:
    assert canonical_debug_json(_plan(("b", "a"))) == canonical_debug_json(_plan(("a", "b")))


def test_debug_svg_is_reorder_invariant() -> None:
    assert render_semantic_debug_svg(_plan(("b", "a")), width=100, height=200) == render_semantic_debug_svg(
        _plan(("a", "b")), width=100, height=200
    )


def test_debug_svg_exposes_policy_importance_and_part() -> None:
    svg = render_semantic_debug_svg(_plan(("arm",)), width=100, height=200)
    assert 'data-part="arm"' in svg
    assert 'data-policy="preserve"' in svg
    assert "0.750" in svg
    assert "PRESERVE" in svg


def test_debug_board_rejects_invalid_dimensions() -> None:
    try:
        render_semantic_debug_svg(_plan(("a",)), width=0, height=100)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected ValueError")
