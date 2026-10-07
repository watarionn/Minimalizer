from __future__ import annotations

import json
from pathlib import Path

import pytest

from minimalizer_zerobase.evaluation.adopted_baseline_registry import (
    BaselineAdoptionRecord,
)
from minimalizer_zerobase.evaluation.cross_case_regression_matrix import (
    build_cross_case_matrix,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "benchmarks" / "regression" / "sa10"
EVIDENCE = DATA / "evidence"
BASELINES = DATA / "baselines"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sa1012_adoption_records_are_explicit_and_evaluation_only():
    for name in ("Hyakuto-Kyoko", "Juufuutei-Raden_stylecal_source"):
        payload = _load(BASELINES / f"{name}.sa10.12-adoption.json")
        record = BaselineAdoptionRecord.from_mapping(payload)
        assert record.review_status == "ADOPTED"
        assert record.reviewer == "Rinka"
        assert record.review_evidence
        assert record.immutable_record is True
        assert record.evaluation_baseline_allowed is True
        assert record.production_inference_allowed is False
        assert record.candidate_self_reference_forbidden is True


@pytest.mark.parametrize(
    "name,required_count,face_ratio",
    [
        ("Hyakuto-Kyoko", 17, 0.058444259567387684),
        ("Juufuutei-Raden_stylecal_source", 9, 0.012738853503184714),
    ],
)
def test_sa1012_visual_hard_gate_is_fresh_and_separate(
    name: str,
    required_count: int,
    face_ratio: float,
):
    feature = _load(EVIDENCE / f"{name}.sa10.12-feature-survival.json")
    face = _load(EVIDENCE / f"{name}.sa10.12-forbidden-face-detail.json")
    hard = _load(EVIDENCE / f"{name}.sa10.12-hard-evidence.json")

    for payload in (feature, face):
        binding = payload["binding"]
        assert binding["binding_passed"] is True
        assert binding["same_transaction"] is False
        assert binding["candidate_self_reference_forbidden"] is True
        assert binding["candidate_bytes_equal_baseline"] is True
        assert binding["production_inference_allowed"] is False

    assert feature["report"]["status"] == "AVAILABLE"
    assert feature["report"]["passed"] is True
    assert feature["report"]["required_signature_count"] == required_count
    assert feature["report"]["missing_count"] == 0

    assert face["report"]["status"] == "AVAILABLE"
    assert face["report"]["passed"] is False
    assert face["report"]["ratio"] == pytest.approx(face_ratio)
    assert face["max_forbidden_face_ratio"] == 0.0

    assert hard["hard_evidence"]["feature_survival"]["passed"] is True
    assert hard["hard_evidence"]["forbidden_face_detail"]["passed"] is False
    assert hard["hard_evidence"]["anatomy"]["passed"] is True
    assert hard["hard_evidence"]["topology"]["passed"] is True
    assert hard["hard_evidence"]["source_authority"]["passed"] is True
    assert hard["boundary"]["candidate_used_as_own_baseline"] is False
    assert hard["boundary"]["aggregate_quality_score"] is False
    assert hard["boundary"]["new_quality_thresholds"] is False


def test_sa1012_cross_case_matrix_exposes_face_hard_failures():
    artifact = build_cross_case_matrix([
        _load(DATA / "Hyakuto-Kyoko.sa10.12.json"),
        _load(DATA / "Juufuutei-Raden_stylecal_source.sa10.12.json"),
    ])
    for case in artifact["cases"]:
        hard = {row["name"]: row for row in case["hard_evidence"]}
        assert hard["feature_survival"]["status"] == "AVAILABLE"
        assert hard["feature_survival"]["passed"] is True
        assert hard["forbidden_face_detail"]["status"] == "AVAILABLE"
        assert hard["forbidden_face_detail"]["passed"] is False
        assert hard["anatomy"]["passed"] is True
        assert hard["topology"]["passed"] is True
        assert hard["source_authority"]["passed"] is True

    assert artifact["boundary"]["aggregate_quality_score"] is False
    assert artifact["boundary"]["calibrated_thresholds"] is False


def test_sa1012_teacher_evidence_remains_unavailable():
    for name in ("Hyakuto-Kyoko", "Juufuutei-Raden_stylecal_source"):
        case = _load(DATA / f"{name}.sa10.12.json")
        assert case["diagnostics"]["teacher_coverage"]["status"] == "UNAVAILABLE"
        assert case["diagnostics"]["teacher_primitive_disagreements"]["status"] == "UNAVAILABLE"
