from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "benchmarks" / "regression" / "sa10"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_sha(payload: dict) -> str:
    raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def test_sa1016_five_case_transaction_set_is_reproducible():
    tx_set = _load(DATA / "SA10_16_transaction_set.json")
    assert tx_set["artifact_version"] == "sa10.16-set-v1"
    assert tx_set["transaction_count"] == 5
    assert tx_set["pass_set"] is True
    assert tx_set["boundary"]["aggregate_quality_score"] is False
    assert tx_set["boundary"]["calibrated_thresholds"] is False
    assert tx_set["boundary"]["case_specific_production_logic"] is False

    expected = {
        "AZKi",
        "Hyakuto-Kyoko",
        "Juufuutei-Raden_stylecal_source",
        "Nekomata-Okayu",
        "Hoshimachi-Suisei",
    }
    assert {row["case_id"] for row in tx_set["transactions"]} == expected

    for row in tx_set["transactions"]:
        payload = _load(ROOT / row["path"])
        assert payload["pass_transaction"] is True
        assert _canonical_sha(payload) == row["canonical_payload_sha256"]


def test_sa1016_admitted_fresh_cases_keep_all_hard_gates_visible():
    for case_id in ("Nekomata-Okayu", "Hoshimachi-Suisei"):
        tx = _load(DATA / "transactions" / f"{case_id}.sa10.16-transaction.json")
        assert tx["pass_transaction"] is True
        assert len(tx["hard_evidence"]) == 8
        assert all(row["status"] == "AVAILABLE" for row in tx["hard_evidence"])
        assert all(row["passed"] is True for row in tx["hard_evidence"])
        assert all(tx["evidence_links"].values())
        assert tx["boundary"]["aggregate_quality_score"] is False
        assert tx["boundary"]["diagnostics_can_override_hard_fail"] is False

        diagnostics = tx["diagnostics"]["case_diagnostics"]
        assert diagnostics["teacher_coverage"]["status"] == "UNAVAILABLE"
        assert diagnostics["teacher_primitive_disagreements"]["status"] == "UNAVAILABLE"
        assert diagnostics["component_survival"]["status"] == "UNAVAILABLE"
        assert diagnostics["primitive_economy"]["status"] == "UNAVAILABLE"

        actual = tx["diagnostics"]["actual_emission_support"]
        assert actual["diagnostic_only"] is True
        assert actual["maps_to_sa10_component_survival"] is False
        assert actual["maps_to_sa10_primitive_economy"] is False


def test_sa1016_taxonomy_preserves_failed_cases_and_categories():
    taxonomy = _load(DATA / "SA10_16_failure_taxonomy.json")
    assert taxonomy["screened_case_count"] == 8
    by_case = {row["case_id"]: row for row in taxonomy["screened_cases"]}

    assert by_case["Fuwawa-Abyssgard"]["phase13_first_bad_stage"] == "07"
    assert by_case["Fuwawa-Abyssgard"]["admitted"] is False

    for case_id in ("La-Darknesss", "Kaela-Kovalskia"):
        failures = by_case[case_id]["failures"]
        assert any(item["code"] == "fragmentation_penalty" for item in failures)
        assert by_case[case_id]["admitted"] is False

    ouro_failures = by_case["Ouro-Kronii"]["failures"]
    assert ouro_failures == [
        {
            "category": "topology_anatomy",
            "stage": "sa10_hard_evidence",
            "code": "missing_required_relation",
            "relation": "neck:attached_to:face",
        }
    ]

    fubuki_failures = by_case["Shirakami-Fubuki"]["failures"]
    assert fubuki_failures[0]["code"] == "missing_visible_part"
    assert fubuki_failures[0]["part"] == "neck"

    tokino_failures = by_case["Tokino-Sora"]["failures"]
    assert tokino_failures[0]["code"] == "major_color_mass_consistency"

    summary = taxonomy["category_summary"]
    assert summary["runtime_environment_blockers"]["count"] == 0
    assert summary["unicode_path_io"]["count"] == 0
    assert summary["forbidden_face_detail"]["count"] == 0
    assert summary["provenance_source_authority"]["count"] == 0
    assert summary["phase14_visual_machine"]["clusters"]["fragmentation_penalty"] == [
        "Fuwawa-Abyssgard",
        "La-Darknesss",
        "Kaela-Kovalskia",
    ]


def test_sa1016_failed_cases_are_not_adopted_or_in_pass_set():
    taxonomy = _load(DATA / "SA10_16_failure_taxonomy.json")
    failed = {
        row["case_id"]
        for row in taxonomy["screened_cases"]
        if row["admitted"] is False
    }
    tx_set = _load(DATA / "SA10_16_transaction_set.json")
    admitted = {row["case_id"] for row in tx_set["transactions"]}

    assert failed.isdisjoint(admitted)
    for case_id in failed:
        assert not (DATA / "baselines" / f"{case_id}.sa10.16-adoption.json").exists()


def test_sa1016_failure_evidence_paths_exist_and_boundaries_hold():
    taxonomy = _load(DATA / "SA10_16_failure_taxonomy.json")
    for row in taxonomy["screened_cases"]:
        for rel in row.get("evidence", []):
            assert (ROOT / rel).is_file()

    boundary = taxonomy["boundaries"]
    assert boundary["aggregate_quality_score"] is False
    assert boundary["threshold_calibration"] is False
    assert boundary["diagnostics_can_override_hard_fail"] is False
    assert boundary["case_specific_production_logic"] is False
    assert boundary["production_code_changed_in_sa1016"] is False
    assert boundary["failures_preserved_before_repair"] is True
    assert boundary["failed_cases_not_adopted"] is True
