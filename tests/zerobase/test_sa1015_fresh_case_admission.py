from __future__ import annotations

import hashlib
import json
from pathlib import Path

from minimalizer_zerobase.evaluation.adopted_baseline_registry import (
    BaselineAdoptionRecord,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "benchmarks" / "regression" / "sa10"
TX = DATA / "transactions"
EVIDENCE = DATA / "evidence"
BASELINES = DATA / "baselines"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_sha(payload: dict) -> str:
    raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def test_sa1015_azki_adoption_is_immutable_and_separate():
    record = BaselineAdoptionRecord.from_mapping(
        _load(BASELINES / "AZKi.sa10.15-adoption.json")
    )
    assert record.case_id == "AZKi"
    assert record.review_status == "ADOPTED"
    assert record.immutable_record is True
    assert record.evaluation_baseline_allowed is True
    assert record.production_inference_allowed is False
    assert record.candidate_self_reference_forbidden is True

    visual = _load(EVIDENCE / "AZKi.sa10.15-visual-hard-gate.json")
    binding = visual["binding"]
    assert binding["adoption_transaction_id"] == record.adoption_transaction_id
    assert binding["evaluation_transaction_id"] == "sa10.15-regression-azki-20261007-v1"
    assert binding["same_transaction"] is False
    assert binding["binding_passed"] is True
    assert binding["candidate_bytes_equal_baseline"] is True


def test_sa1015_azki_all_hard_evidence_passes():
    tx = _load(TX / "AZKi.sa10.15-transaction.json")
    assert tx["pass_transaction"] is True
    assert all(tx["evidence_links"].values())
    assert len(tx["hard_evidence"]) == 8
    assert all(row["status"] == "AVAILABLE" for row in tx["hard_evidence"])
    assert all(row["passed"] is True for row in tx["hard_evidence"])

    visual = _load(EVIDENCE / "AZKi.sa10.15-visual-hard-gate.json")
    assert visual["feature_survival"]["required_signature_count"] == 10
    assert visual["feature_survival"]["missing_count"] == 0
    assert visual["feature_survival"]["passed"] is True
    assert visual["forbidden_face_detail"]["ratio"] == 0.0
    assert visual["forbidden_face_detail"]["passed"] is True


def test_sa1015_azki_diagnostics_do_not_gain_authority():
    tx = _load(TX / "AZKi.sa10.15-transaction.json")
    diagnostics = tx["diagnostics"]
    assert diagnostics["semantic_retention"]["value"] == 0.8350633040526145
    assert diagnostics["semantic_retention"]["authoritative"] is False
    assert diagnostics["semantic_retention"]["can_override_hard_fail"] is False

    case_diag = diagnostics["case_diagnostics"]
    for name in (
        "adaptive_complexity",
        "component_survival",
        "primitive_economy",
        "teacher_coverage",
        "teacher_primitive_disagreements",
    ):
        assert case_diag[name]["status"] == "UNAVAILABLE"

    actual = diagnostics["actual_emission_support"]
    assert actual["diagnostic_only"] is True
    assert actual["emission_realization_ratio"] == 0.75
    assert actual["maps_to_sa10_component_survival"] is False
    assert actual["maps_to_sa10_primitive_economy"] is False


def test_sa1015_three_case_transaction_set_is_reproducible():
    tx_set = _load(DATA / "SA10_15_transaction_set.json")
    assert tx_set["transaction_count"] == 3
    assert tx_set["pass_set"] is True
    assert tx_set["boundary"]["aggregate_quality_score"] is False
    assert tx_set["boundary"]["calibrated_thresholds"] is False
    assert tx_set["boundary"]["case_specific_production_logic"] is False
    assert {row["case_id"] for row in tx_set["transactions"]} == {
        "AZKi",
        "Hyakuto-Kyoko",
        "Juufuutei-Raden_stylecal_source",
    }
    for row in tx_set["transactions"]:
        payload = _load(ROOT / row["path"])
        assert payload["pass_transaction"] is True
        assert _canonical_sha(payload) == row["canonical_payload_sha256"]


def test_sa1015_fresh_case_repairs_are_generic_not_azki_branches():
    production_paths = (
        "minimalizer_zerobase/parts/decomposition.py",
        "minimalizer_zerobase/image_io.py",
        "minimalizer_zerobase/artifact_contract/bridge.py",
        "minimalizer_zerobase/importance/artifacts.py",
        "minimalizer_zerobase/palette/artifacts.py",
        "minimalizer_zerobase/geometrization/artifacts.py",
        "minimalizer_zerobase/composition/artifacts.py",
        "tools/run_zerobase_phase9.py",
        "tools/run_zerobase_phase12.py",
    )
    for relative in production_paths:
        content = (ROOT / relative).read_text(encoding="utf-8")
        assert "AZKi" not in content
