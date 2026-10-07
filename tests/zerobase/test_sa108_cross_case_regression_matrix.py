from __future__ import annotations

import json
from pathlib import Path

import pytest

from minimalizer_zerobase.evaluation.cross_case_regression_matrix import (
    DIAGNOSTIC_NAMES,
    build_cross_case_matrix,
)


ROOT = Path(__file__).resolve().parents[2]


def _case(name: str) -> dict:
    return json.loads(
        (ROOT / "benchmarks" / "regression" / "sa10" / name).read_text(encoding="utf-8")
    )


def test_cross_case_matrix_preserves_available_and_unavailable_evidence():
    artifact = build_cross_case_matrix([
        _case("Hyakuto-Kyoko.sa10.8.json"),
        _case("Juufuutei-Raden_stylecal_source.sa10.8.json"),
    ])
    assert artifact["case_count"] == 2
    by_case = {row["case_id"]: row for row in artifact["cases"]}
    kyoko = {row["name"]: row for row in by_case["Hyakuto-Kyoko"]["diagnostics"]}
    raden = {
        row["name"]: row
        for row in by_case["Juufuutei-Raden_stylecal_source"]["diagnostics"]
    }
    assert kyoko["adaptive_complexity"]["value"] == pytest.approx(0.8)
    assert kyoko["component_survival"]["value"] == pytest.approx(4 / 7)
    assert kyoko["primitive_economy"]["value"] == pytest.approx(1.0)
    assert kyoko["semantic_retention"]["status"] == "UNAVAILABLE"
    assert all(raden[name]["status"] == "UNAVAILABLE" for name in DIAGNOSTIC_NAMES)


def test_cross_case_matrix_has_no_aggregate_score_or_calibrated_thresholds():
    artifact = build_cross_case_matrix([
        _case("Hyakuto-Kyoko.sa10.8.json"),
        _case("Juufuutei-Raden_stylecal_source.sa10.8.json"),
    ])
    assert artifact["boundary"] == {
        "aggregate_quality_score": False,
        "calibrated_thresholds": False,
        "gc001_threshold_derivation": False,
        "hard_failures_individually_visible": True,
        "unavailable_evidence_preserved": True,
    }
    assert "score" not in artifact


def test_hard_categories_remain_individually_visible():
    artifact = build_cross_case_matrix([
        _case("Hyakuto-Kyoko.sa10.8.json"),
        _case("Juufuutei-Raden_stylecal_source.sa10.8.json"),
    ])
    for case in artifact["cases"]:
        hard = {row["name"]: row for row in case["hard_evidence"]}
        assert hard["feature_survival"]["status"] == "UNAVAILABLE"
        assert hard["forbidden_face_detail"]["status"] == "UNAVAILABLE"
        assert hard["anatomy"]["status"] == "UNAVAILABLE"
        assert hard["topology"]["status"] == "UNAVAILABLE"
        assert hard["source_authority"]["status"] == "UNAVAILABLE"
        assert hard["phase14_machine"]["passed"] is True
        assert hard["phase14_human_visual"]["passed"] is True
        assert hard["determinism"]["passed"] is True


def test_duplicate_case_id_fails_closed():
    kyoko = _case("Hyakuto-Kyoko.sa10.8.json")
    with pytest.raises(ValueError):
        build_cross_case_matrix([kyoko, kyoko])
