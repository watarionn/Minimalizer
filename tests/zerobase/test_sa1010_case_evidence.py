from __future__ import annotations
import json
from pathlib import Path
import pytest
from minimalizer_zerobase.evaluation.cross_case_regression_matrix import build_cross_case_matrix

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/"benchmarks"/"regression"/"sa10"
E=DATA/"evidence"
def load(p): return json.loads(p.read_text(encoding="utf-8"))

def test_sa1010_corrects_semantic_retention_to_production_candidate():
    cases=[
        ("Hyakuto-Kyoko",0.7709177748262631,"9faec9556f98d21465301f16e2fe674b1ee930f373b2dd6d2ddcb82116d5ab7b"),
        ("Juufuutei-Raden_stylecal_source",0.914517616858495,"9911795a0a87a0d227c9b43a86bec8497ca47e6cce60c1ef048027e3fb527c1d"),
    ]
    for name,score,sha in cases:
        case=load(DATA/f"{name}.sa10.10.json")
        evidence=load(E/f"{name}.sa10.10-semantic-retention.json")
        assert evidence["candidate"]["path"]=="12_final.png"
        assert evidence["candidate"]["sha256"]==sha
        assert case["diagnostics"]["semantic_retention"]["value"]==pytest.approx(score)
        assert evidence["semantic_retention"]["semantic_retention_score"]==pytest.approx(score)

def test_sa1010_hard_evidence_is_independent_of_phase14_pass():
    for name in ("Hyakuto-Kyoko","Juufuutei-Raden_stylecal_source"):
        case=load(DATA/f"{name}.sa10.10.json")
        hard=load(E/f"{name}.sa10.10-hard-evidence.json")
        assert hard["hard_evidence"]["source_authority"]=={"status":"AVAILABLE","passed":True}
        assert hard["hard_evidence"]["anatomy"]=={"status":"AVAILABLE","passed":False}
        assert hard["hard_evidence"]["topology"]=={"status":"AVAILABLE","passed":False}
        assert hard["hard_evidence"]["feature_survival"]["status"]=="UNAVAILABLE"
        assert hard["hard_evidence"]["forbidden_face_detail"]["status"]=="UNAVAILABLE"
        assert hard["boundary"]["phase14_metrics_reused_as_hard_evidence"] is False
        assert hard["boundary"]["candidate_used_as_own_baseline"] is False
        assert case["hard_evidence"]["source_authority"]["passed"] is True
        assert case["hard_evidence"]["anatomy"]["passed"] is False
        assert case["hard_evidence"]["topology"]["passed"] is False

def test_sa1010_actual_emission_is_context_only():
    raden=load(E/"Juufuutei-Raden_stylecal_source.sa10.10-hard-evidence.json")
    actual=raden["actual_emission_support"]
    assert actual["emission_realization_ratio"]==pytest.approx(0.5)
    assert actual["actual_component_representation_ratio"]==pytest.approx(0.5)
    assert actual["actual_primitive_support_ratio"]==pytest.approx(1.0)
    assert actual["maps_to_sa10_component_survival"] is False
    assert actual["maps_to_sa10_primitive_economy"] is False

def test_sa1010_matrix_preserves_hard_failures_without_thresholds():
    artifact=build_cross_case_matrix([
        load(DATA/"Hyakuto-Kyoko.sa10.10.json"),
        load(DATA/"Juufuutei-Raden_stylecal_source.sa10.10.json"),
    ])
    for case in artifact["cases"]:
        hard={x["name"]:x for x in case["hard_evidence"]}
        assert hard["source_authority"]["passed"] is True
        assert hard["anatomy"]["passed"] is False
        assert hard["topology"]["passed"] is False
    assert artifact["boundary"]["aggregate_quality_score"] is False
    assert artifact["boundary"]["calibrated_thresholds"] is False
