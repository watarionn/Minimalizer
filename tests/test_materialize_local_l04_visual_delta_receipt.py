import hashlib
import json
from pathlib import Path

import pytest

from tools.research.materialize_local_l04_visual_delta_receipt import (
    DeltaReceiptHold,
    materialize_delta_receipt,
)
from tools.research.prepare_local_l04_visual_delta_review_kit import prepare


def _make_package(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    (source / "sources").mkdir(parents=True)
    cases = []
    for case in ("H04", "H06", "H08"):
        (source / "sources" / f"{case}.png").write_bytes(b"source-" + case.encode())
        (source / case).mkdir()
        (source / case / "expanded_stage8.svg").write_text("<svg/>", encoding="utf-8")
        cases.append({
            "case": case,
            "source_sha256": f"{case.lower():0<64}",
            "stage8_json_sha256": f"{case.lower():1<64}",
            "expanded_svg_sha256": f"{case.lower():2<64}",
        })
    (source / "L04_CANDIDATE_TRIPLE_RECEIPT.json").write_text(
        json.dumps({
            "schema": "minimalizer/local-l04/candidate-triple-receipt/v1",
            "cases": cases,
            "L04_formal": "HOLD",
            "Golden": "HOLD",
            "production": "NO_GO",
        }), encoding="utf-8"
    )
    (source / "L04_CANDIDATE_TRIPLE_AUDIT.json").write_text(json.dumps({
        "schema": "minimalizer/local-l04/candidate-triple-audit/v1",
        "numerical_handoff_eligible": True,
        "failures": [],
        "cases": {item["case"]: {**item, "failures": []} for item in cases},
    }), encoding="utf-8")
    (source / "B_L04_DELIVERY_AUDIT.json").write_text(json.dumps({
        "schema": "minimalizer/local-l04/candidate-b-delivery-audit/v1",
        "B_L04_delivery": "PASS",
        "failures": [],
    }), encoding="utf-8")

    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "L04_CANDIDATE_TRIPLE_RECEIPT.json").write_text(
        json.dumps({
            "schema": "minimalizer/local-l04/candidate-triple-receipt/v1",
            "baseline": "v5",
            "cases": [{"case": case} for case in ("H04", "H06", "H08")],
        }), encoding="utf-8"
    )
    baseline_review = tmp_path / "baseline-review.json"
    baseline_review.write_text(json.dumps({
        "schema": "minimalizer/local-l04/independent-visual-review-readback/v1",
        "review_file_sha256": "form",
        "review_gate": "HOLD",
        "L04_formal": "HOLD",
        "cases": {
            "H04": {"failed_question_numbers": [3]},
            "H06": {"failed_question_numbers": [1, 6]},
            "H08": {"failed_question_numbers": []},
        },
    }), encoding="utf-8")
    destination = tmp_path / "package"
    prepare(source, destination, baseline / "L04_CANDIDATE_TRIPLE_RECEIPT.json", baseline_review)

    receipt_path = destination / "L04_CANDIDATE_TRIPLE_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["cases"][2]["candidate_sha256"] = "8daafac9aabac48635d73b393a8220dd64f88b3a2ef6d7c06ae76b52b049f091"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    (destination / "authority").mkdir()
    (destination / "authority" / "H08_OWNER_AUTHORITY_RECEIPT.json").write_text(json.dumps({
        "schema": "minimalizer/local-l02/h08-owner-authority/v1",
        "case": "H08",
        "frozen_owner_sha256": "43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52",
        "source_sha256": cases[2]["source_sha256"],
        "prediction_sha256": "8daafac9aabac48635d73b393a8220dd64f88b3a2ef6d7c06ae76b52b049f091",
        "owner_promotion_authorized": True,
        "authority_receipt_verified": True,
        "bound_to_case": True,
        "bound_to_source_sha": True,
        "bound_to_prediction_sha": True,
        "bound_to_observer_sha": True,
        "owner_promotion_explicitly_approved": True,
        "unknown_not_promoted": True,
        "human_labels_not_used_for_inference": True,
        "production_not_authorized": True,
        "golden": "HOLD",
        "production": "NO_GO",
    }), encoding="utf-8")
    return destination, baseline_review


def _review_text(package: Path, baseline_sha: str) -> Path:
    receipt_sha = hashlib.sha256((package / "L04_CANDIDATE_TRIPLE_RECEIPT.json").read_bytes()).hexdigest()
    text = "\n".join([
        "今回レビュー対象三点セットreceipt SHA-256（書き換え禁止）: " + receipt_sha,
        "前回v5レビュー対象receipt SHA-256（固定）: " + baseline_sha,
        "確認者名: reviewer",
        "所属・立場（開発側との関係）: independent",
        "開発側から独立している: はい",
        "確認日時（JST）: 2026-11-13 12:00",
        "使用端末・ブラウザ: Chrome",
        "1. H04: x", "回答: はい", "2. H06: x", "回答: はい",
        "3. H06: x", "回答: はい", "4. H08: x", "回答: はい",
        "差分4項目をすべて視覚的に受入できる: はい",
        "今回のreceiptの数値来歴と実物表示を照合した: はい",
        "独立性を確認した: はい",
    ]) + "\n"
    path = package / "review.txt"
    path.write_text(text, encoding="utf-8")
    return path


def test_materialize_requires_delta_pass_and_binds_authority(tmp_path: Path) -> None:
    package, _ = _make_package(tmp_path)
    baseline_sha = hashlib.sha256(
        (tmp_path / "baseline" / "L04_CANDIDATE_TRIPLE_RECEIPT.json").read_bytes()
    ).hexdigest()
    review = _review_text(package, baseline_sha)
    result = materialize_delta_receipt(review, package)
    assert result["receipt_created"] is True
    assert result["L04_formal"] == "PASS"
    assert result["Golden"] == "PASS"
    assert result["production"] == "NO_GO"


def test_materialize_rejects_missing_authority(tmp_path: Path) -> None:
    package, _ = _make_package(tmp_path)
    (package / "authority" / "H08_OWNER_AUTHORITY_RECEIPT.json").unlink()
    baseline_sha = hashlib.sha256(
        (tmp_path / "baseline" / "L04_CANDIDATE_TRIPLE_RECEIPT.json").read_bytes()
    ).hexdigest()
    review = _review_text(package, baseline_sha)
    with pytest.raises(DeltaReceiptHold, match="MISSING_FILE"):
        materialize_delta_receipt(review, package)
