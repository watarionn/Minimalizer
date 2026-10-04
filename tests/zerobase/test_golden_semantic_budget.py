from __future__ import annotations

import json
from pathlib import Path

import pytest

from minimalizer_zerobase.golden_comparison.semantic_budget import (
    SemanticBudgetError,
    allocate_semantic_budget,
)
from minimalizer_zerobase.golden_comparison.semantic_manifest import load_semantic_manifest

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "benchmarks" / "golden" / "cases" / "GC001_IMG_1205.semantic.json"


def _manifest() -> dict:
    return load_semantic_manifest(CASE)


def _alloc(report: dict) -> dict[str, int]:
    return {row["feature_id"]: row["allocated_primitives"] for row in report["allocations"]}


def test_required_minimum_is_reserved_before_optional_features() -> None:
    report = allocate_semantic_budget(_manifest(), 4)
    allocation = _alloc(report)
    assert report["required_minimum"] == 4
    assert all(allocation[key] == 1 for key in ("orange_hair", "goggles", "green_necktie", "navy_white_uniform"))
    assert allocation["hair_ornament"] == 0
    assert allocation["badges"] == 0
    assert allocation["armband"] == 0


def test_insufficient_budget_fails_instead_of_sacrificing_required_identity() -> None:
    with pytest.raises(SemanticBudgetError, match="cannot satisfy required minimum 4"):
        allocate_semantic_budget(_manifest(), 3)


def test_forbidden_feature_never_receives_budget() -> None:
    report = allocate_semantic_budget(_manifest(), 20)
    assert _alloc(report)["facial_details"] == 0


def test_important_optional_is_funded_before_compressible_optional() -> None:
    allocation = _alloc(allocate_semantic_budget(_manifest(), 5))
    assert allocation["hair_ornament"] == 1
    assert allocation["badges"] == 0
    assert allocation["armband"] == 0


def test_compressible_optional_features_are_stable_by_feature_id() -> None:
    allocation = _alloc(allocate_semantic_budget(_manifest(), 7))
    assert allocation["armband"] == 1
    assert allocation["badges"] == 1


def test_extra_budget_cycles_by_semantic_priority_not_pixel_area() -> None:
    report = allocate_semantic_budget(_manifest(), 11)
    allocation = _alloc(report)
    required = ["orange_hair", "goggles", "green_necktie", "navy_white_uniform"]
    assert all(allocation[key] >= 2 for key in required)
    assert allocation["facial_details"] == 0


def test_budgeter_is_deterministic() -> None:
    first = allocate_semantic_budget(_manifest(), 17)
    second = allocate_semantic_budget(_manifest(), 17)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


@pytest.mark.parametrize("bad_budget", [-1, 1.5, True])
def test_invalid_budget_is_rejected(bad_budget) -> None:
    with pytest.raises(SemanticBudgetError):
        allocate_semantic_budget(_manifest(), bad_budget)
