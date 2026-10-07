from __future__ import annotations

import json
from pathlib import Path

import pytest

from minimalizer_zerobase.evaluation.cross_case_regression_matrix import (
    build_cross_case_matrix,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "benchmarks" / "regression" / "sa10"
EVIDENCE = DATA / "evidence"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sa109_exact_dino_evidence_is_hash_bound_to_final_outputs():
    kyoko = _load(DATA / "Hyakuto-Kyoko.sa10.9.json")
    raden = _load(DATA / "Juufuutei-Raden_stylecal_source.sa10.9.json")
    ke = _load(EVIDENCE / "Hyakuto-Kyoko.sa10.9-semantic-retention.json")
    re = _load(EVIDENCE / "Juufuutei-Raden_stylecal_source.sa10.9-semantic-retention.json")

    for case, evidence in ((kyoko, ke), (raden, re)):
        assert evidence["source"]["sha256"] == case["source"]["sha256"]
        assert evidence["candidate"]["sha256"] == case["provenance"]["phase14_output_sha256"]
        assert evidence["production_output_changed"] is False
        assert evidence["hard_gate_override_allowed"] is False
        assert evidence["semantic_retention"]["authoritative"] is False
        assert evidence["semantic_retention"]["can_override_hard_fail"] is False
        assert case["diagnostics"]["semantic_retention"]["value"] == pytest.approx(
            evidence["semantic_retention"]["semantic_retention_score"]
        )


def test_sa109_raden_macro_gap_is_expansion_rejection_not_budget_mismatch():
    case = _load(DATA / "Juufuutei-Raden_stylecal_source.sa10.9.json")
    evidence = _load(EVIDENCE / "Juufuutei-Raden_stylecal_source.sa10.9-macro-alignment.json")
    hair = next(row for row in evidence["roles"] if row["role"] == "hair")
    clothing = next(row for row in evidence["roles"] if row["role"] == "major_clothing")

    assert evidence["aligned"] is False
    assert hair["allocated_primitives"] == 1
    assert hair["mass_candidates"] == 1
    assert hair["emitted_primitives"] == 0
    assert hair["status"] == "PRIMITIVE_GENERATION_DROP"
    assert hair["drop_details"][0]["reason"] == "EXPANSION_EXCEEDED"
    assert hair["drop_details"][0]["expansion_ratio"] == pytest.approx(1.2861805086653162)
    assert hair["drop_details"][0]["source_coverage"] == pytest.approx(0.9401305424262886)
    assert clothing["status"] == "ALIGNED"
    assert case["diagnostics"]["adaptive_complexity"]["value"] == pytest.approx(2 / 5)
    assert case["diagnostics"]["component_survival"]["status"] == "UNAVAILABLE"
    assert case["diagnostics"]["primitive_economy"]["status"] == "UNAVAILABLE"


def test_sa109_cross_case_coverage_increases_without_new_thresholds():
    artifact = build_cross_case_matrix([
        _load(DATA / "Hyakuto-Kyoko.sa10.9.json"),
        _load(DATA / "Juufuutei-Raden_stylecal_source.sa10.9.json"),
    ])
    semantic = artifact["distributions"]["semantic_retention"]
    adaptive = artifact["distributions"]["adaptive_complexity"]
    component = artifact["distributions"]["component_survival"]

    assert semantic["available_count"] == 2
    assert semantic["min"] == pytest.approx(0.7293772165390804)
    assert semantic["max"] == pytest.approx(0.8159690921150953)
    assert adaptive["available_count"] == 2
    assert adaptive["min"] == pytest.approx(0.4)
    assert adaptive["max"] == pytest.approx(0.8)
    assert component["available_count"] == 1
    assert component["unavailable_count"] == 1
    assert artifact["boundary"]["calibrated_thresholds"] is False
    assert artifact["boundary"]["aggregate_quality_score"] is False
