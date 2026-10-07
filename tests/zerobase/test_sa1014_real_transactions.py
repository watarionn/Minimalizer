from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "benchmarks" / "regression" / "sa10"
TX = DATA / "transactions"
EVIDENCE = DATA / "evidence"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sa1014_real_transactions_bind_all_hard_evidence():
    expected = {
        "Hyakuto-Kyoko": (
            "84022e48e13ed7a80f8e3425d085d311e3ab7c86fcb28278ba079e182a33646a",
            "sa10.14-regression-hyakuto-kyoko-20261007-v1",
        ),
        "Juufuutei-Raden_stylecal_source": (
            "576a7baa1cf2dcf1a3254fb7daecefb1f5520dc8833294924077ba8ef98ab4b5",
            "sa10.14-regression-juufuutei-raden-20261007-v1",
        ),
    }
    for case_id, (candidate_sha, transaction_id) in expected.items():
        payload = _load(TX / f"{case_id}.sa10.14-transaction.json")
        assert payload["artifact_version"] == "sa10.14-v1"
        assert payload["transaction_id"] == transaction_id
        assert payload["candidate_sha256"] == candidate_sha
        assert payload["pass_transaction"] is True
        assert all(payload["evidence_links"].values())
        assert len(payload["hard_evidence"]) == 8
        assert all(row["status"] == "AVAILABLE" for row in payload["hard_evidence"])
        assert all(row["passed"] is True for row in payload["hard_evidence"])
        assert payload["boundary"]["aggregate_quality_score"] is False
        assert payload["boundary"]["diagnostics_can_override_hard_fail"] is False
        assert payload["boundary"]["new_quality_thresholds"] is False


def test_sa1014_visual_gate_is_bound_to_same_transaction_id():
    pairs = (
        ("Hyakuto-Kyoko", "sa10.14-regression-hyakuto-kyoko-20261007-v1"),
        (
            "Juufuutei-Raden_stylecal_source",
            "sa10.14-regression-juufuutei-raden-20261007-v1",
        ),
    )
    for case_id, transaction_id in pairs:
        gate = _load(EVIDENCE / f"{case_id}.sa10.14-visual-hard-gate.json")
        assert gate["binding"]["evaluation_transaction_id"] == transaction_id
        assert gate["binding"]["binding_passed"] is True
        assert gate["binding"]["same_transaction"] is False
        assert gate["binding"]["production_inference_allowed"] is False
        assert gate["canonical_hard_gate"]["pass_gate"] is True


def test_sa1014_teacher_and_raden_emission_boundaries_remain_explicit():
    kyoko = _load(TX / "Hyakuto-Kyoko.sa10.14-transaction.json")
    raden = _load(
        TX / "Juufuutei-Raden_stylecal_source.sa10.14-transaction.json"
    )

    for payload in (kyoko, raden):
        case_diag = payload["diagnostics"]["case_diagnostics"]
        assert case_diag["teacher_coverage"]["status"] == "UNAVAILABLE"
        assert (
            case_diag["teacher_primitive_disagreements"]["status"]
            == "UNAVAILABLE"
        )
        assert payload["diagnostics"]["semantic_retention"]["authoritative"] is False
        assert (
            payload["diagnostics"]["semantic_retention"][
                "can_override_hard_fail"
            ]
            is False
        )

    raden_case = raden["diagnostics"]["case_diagnostics"]
    assert raden_case["component_survival"]["status"] == "UNAVAILABLE"
    assert raden_case["primitive_economy"]["status"] == "UNAVAILABLE"
    actual = raden["diagnostics"]["actual_emission_support"]
    assert actual["diagnostic_only"] is True
    assert actual["emission_realization_ratio"] == 0.5
    assert actual["maps_to_sa10_component_survival"] is False
    assert actual["maps_to_sa10_primitive_economy"] is False
