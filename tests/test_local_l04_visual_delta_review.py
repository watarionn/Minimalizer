import json
from pathlib import Path

import pytest

from tools.research.prepare_local_l04_visual_delta_review_kit import prepare
from tools.research.verify_local_l04_visual_delta_review import VisualReviewHold, readback_delta_review


def _package(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "source"
    (source / "sources").mkdir(parents=True)
    for case in ("H04", "H06", "H08"):
        (source / "sources" / f"{case}.png").write_bytes(b"source")
        (source / case).mkdir()
        (source / case / "expanded_stage8.svg").write_text("<svg/>", encoding="utf-8")
    (source / "L04_CANDIDATE_TRIPLE_RECEIPT.json").write_text(
        json.dumps({"schema": "minimalizer/local-l04/candidate-triple-receipt/v1", "cases": [{"case": c} for c in ("H04", "H06", "H08")] }),
        encoding="utf-8",
    )
    (source / "L04_CANDIDATE_TRIPLE_AUDIT.json").write_text(
        json.dumps({"numerical_handoff_eligible": True, "failures": [], "schema": "candidate"}), encoding="utf-8"
    )
    (source / "B_L04_DELIVERY_AUDIT.json").write_text(
        json.dumps({"B_L04_delivery": "PASS", "failures": [], "schema": "delivery"}), encoding="utf-8"
    )
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "L04_CANDIDATE_TRIPLE_RECEIPT.json").write_text(
        json.dumps({"schema": "minimalizer/local-l04/candidate-triple-receipt/v1", "baseline": "v5", "cases": [{"case": c} for c in ("H04", "H06", "H08")] }),
        encoding="utf-8",
    )
    review = tmp_path / "baseline-review.json"
    review.write_text(json.dumps({
        "schema": "minimalizer/local-l04/independent-visual-review-readback/v1",
        "review_file_sha256": "baseline-form",
        "review_gate": "HOLD",
        "L04_formal": "HOLD",
        "cases": {
            "H04": {"failed_question_numbers": [3]},
            "H06": {"failed_question_numbers": [1, 6]},
            "H08": {"failed_question_numbers": []},
        },
    }), encoding="utf-8")
    return source, baseline / "L04_CANDIDATE_TRIPLE_RECEIPT.json", review


def test_delta_kit_carries_baseline_and_uses_four_questions(tmp_path: Path) -> None:
    source, baseline_receipt, baseline_review = _package(tmp_path)
    destination = tmp_path / "delta"
    result = prepare(source, destination, baseline_receipt, baseline_review)
    assert result["delta_questions"] == 4
    assert (destination / "BASELINE_REVIEW_BINDING.json").exists()
    assert "差分4項目" in (destination / "L04差分独立視覚確認票.txt").read_text(encoding="utf-8")


def test_delta_readback_requires_current_receipt(tmp_path: Path) -> None:
    source, baseline_receipt, baseline_review = _package(tmp_path)
    destination = tmp_path / "delta"
    prepare(source, destination, baseline_receipt, baseline_review)
    review = destination / "L04差分独立視覚確認票.txt"
    review.write_text(review.read_text(encoding="utf-8").replace("回答: \n", "回答: はい\n"), encoding="utf-8")
    with pytest.raises(VisualReviewHold, match="MISSING_FIELD"):
        readback_delta_review(review, destination)
