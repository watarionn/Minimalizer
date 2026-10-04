from __future__ import annotations

import json
from pathlib import Path

import pytest

from minimalizer_zerobase.golden_comparison.geometry_grammar import (
    GeometryGrammarError,
    build_geometry_plan,
    validate_authorized_fit,
)
from minimalizer_zerobase.golden_comparison.semantic_budget import allocate_semantic_budget
from minimalizer_zerobase.golden_comparison.semantic_manifest import load_semantic_manifest

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "benchmarks" / "golden" / "cases" / "GC001_IMG_1205.semantic.json"


def _manifest() -> dict:
    return load_semantic_manifest(CASE)


def _plan(budget: int = 11) -> dict:
    manifest = _manifest()
    return build_geometry_plan(manifest, allocate_semantic_budget(manifest, budget))


def test_gc001_plan_uses_category_grammar_not_coordinates() -> None:
    plan = _plan()
    raw = json.dumps(plan, sort_keys=True)
    assert '"x"' not in raw
    assert '"y"' not in raw
    assert '"points"' not in raw
    assert '"bbox"' not in raw
    assert '"polygon"' in raw


def test_gc001_category_grammar_assigns_semantic_families() -> None:
    plan = _plan(11)
    by_feature = {}
    for primitive in plan["primitives"]:
        by_feature.setdefault(primitive["feature_id"], []).append(primitive["primitive_kind"])
    assert by_feature["orange_hair"][0] == "bezier_silhouette"
    assert by_feature["goggles"][0] == "ring"
    assert by_feature["green_necktie"][0] == "trapezoid"
    assert by_feature["navy_white_uniform"][0] == "trapezoid"
    assert by_feature["hair_ornament"][0] == "polygon"
    assert by_feature["badges"][0] == "ring"
    assert by_feature["armband"][0] == "ribbon"
    assert "facial_details" not in by_feature


def test_plan_is_deterministic() -> None:
    assert json.dumps(_plan(17), sort_keys=True) == json.dumps(_plan(17), sort_keys=True)


def test_case_mismatch_fails_closed() -> None:
    manifest = _manifest()
    budget = allocate_semantic_budget(manifest, 8)
    budget["case_id"] = "other"
    with pytest.raises(GeometryGrammarError, match="case_id"):
        build_geometry_plan(manifest, budget)


def test_unknown_budget_feature_fails_closed() -> None:
    manifest = _manifest()
    budget = allocate_semantic_budget(manifest, 8)
    budget["allocations"][0]["feature_id"] = "unknown"
    with pytest.raises(GeometryGrammarError, match="unknown feature"):
        build_geometry_plan(manifest, budget)


def test_vtracer_requires_authorized_semantic_mask() -> None:
    with pytest.raises(GeometryGrammarError, match="authorized semantic mask"):
        validate_authorized_fit(
            _plan(), feature_id="goggles", primitive_kind="ring",
            mask_authorized=False, fitter="vtracer"
        )


def test_vtracer_cannot_choose_unplanned_semantics_or_geometry() -> None:
    plan = _plan()
    with pytest.raises(GeometryGrammarError, match="no authorized primitive budget"):
        validate_authorized_fit(
            plan, feature_id="facial_details", primitive_kind="ellipse",
            mask_authorized=True, fitter="vtracer"
        )
    with pytest.raises(GeometryGrammarError, match="outside authorized grammar"):
        validate_authorized_fit(
            plan, feature_id="goggles", primitive_kind="polygon",
            mask_authorized=True, fitter="vtracer"
        )


def test_authorized_vtracer_fit_remains_non_authoritative() -> None:
    report = validate_authorized_fit(
        _plan(), feature_id="goggles", primitive_kind="ring",
        mask_authorized=True, fitter="vtracer"
    )
    assert report["semantic_authority"] == "manifest"
    assert report["fitter_may_decide_semantics"] is False


def test_generic_unknown_role_uses_deterministic_fallback_grammar() -> None:
    manifest = {
        "schema_version": "1.0",
        "case_id": "synthetic-geometry",
        "features": [
            {"id": "core", "semantic_role": "novel_core", "disposition": "required", "importance": "identity_critical", "palette_role": "primary", "compression_policy": "preserve"}
        ],
        "relations": [],
        "evaluation_regions": [{"id": "identity", "feature_ids": ["core"]}]
    }
    plan = build_geometry_plan(manifest, allocate_semantic_budget(manifest, 2))
    assert [row["primitive_kind"] for row in plan["primitives"]] == ["polygon", "ellipse"]
