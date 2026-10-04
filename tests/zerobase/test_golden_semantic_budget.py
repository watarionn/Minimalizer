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


def test_generic_manifest_uses_semantics_not_case001_names_or_list_order() -> None:
    manifest = {
        "schema_version": "1.0",
        "case_id": "synthetic",
        "features": [
            {"id": "tiny_symbol", "semantic_role": "symbol", "disposition": "optional", "importance": "compressible", "palette_role": "accent", "compression_policy": "symbolic"},
            {"id": "core_b", "semantic_role": "shape_b", "disposition": "required", "importance": "identity_critical", "palette_role": "secondary", "compression_policy": "preserve"},
            {"id": "detail", "semantic_role": "detail", "disposition": "optional", "importance": "important", "palette_role": "accent", "compression_policy": "symbolic"},
            {"id": "core_a", "semantic_role": "shape_a", "disposition": "required", "importance": "identity_critical", "palette_role": "primary", "compression_policy": "preserve"},
            {"id": "noise", "semantic_role": "noise", "disposition": "forbidden", "importance": "supporting", "palette_role": "not_applicable", "compression_policy": "omit"}
        ],
        "relations": [],
        "evaluation_regions": [{"id": "identity", "feature_ids": ["core_a", "core_b", "detail", "tiny_symbol", "noise"]}]
    }
    allocation = _alloc(allocate_semantic_budget(manifest, 3))
    assert allocation["core_a"] == 1
    assert allocation["core_b"] == 1
    assert allocation["detail"] == 1
    assert allocation["tiny_symbol"] == 0
    assert allocation["noise"] == 0


def test_feature_list_reordering_does_not_change_allocation() -> None:
    manifest = _manifest()
    reversed_manifest = dict(manifest)
    reversed_manifest["features"] = list(reversed(manifest["features"]))
    first = _alloc(allocate_semantic_budget(manifest, 13))
    second = _alloc(allocate_semantic_budget(reversed_manifest, 13))
    assert first == second
