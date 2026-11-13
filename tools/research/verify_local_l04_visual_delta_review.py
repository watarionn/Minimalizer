"""Read back a focused L04 delta review without promoting a candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from .verify_local_l04_visual_review import (
        VisualReviewHold,
        _load_audit,
        _line_value,
        _answer,
    )
except ImportError:  # pragma: no cover - direct CLI execution
    from verify_local_l04_visual_review import (  # type: ignore
        VisualReviewHold,
        _load_audit,
        _line_value,
        _answer,
    )


ANSWER_RE = re.compile(r"^(?:回答:\s*)?(はい|いいえ|保留)")


def _delta_answer(lines: list[str], number: int) -> str:
    marker = f"{number}. "
    for index, line in enumerate(lines):
        if line.startswith(marker):
            for candidate in lines[index + 1 : index + 5]:
                if candidate.startswith("回答:"):
                    return _answer(candidate)
    raise VisualReviewHold(f"MISSING_DELTA_ANSWER:{number}")


def _baseline(package: Path) -> dict[str, Any]:
    path = package / "BASELINE_REVIEW_BINDING.json"
    if not path.is_file():
        raise VisualReviewHold("BASELINE_BINDING_MISSING")
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "minimalizer/local-l04/visual-delta-baseline-binding/v1":
        raise VisualReviewHold("BASELINE_BINDING_SCHEMA")
    expected = {"H04": [3], "H06": [1, 6], "H08": []}
    actual = {
        case: list(value.get("baseline_cases", {}).get(case, {}).get("failed_question_numbers", []))
        for case in expected
    }
    if actual != expected or value.get("baseline_review_gate") != "HOLD":
        raise VisualReviewHold("BASELINE_BINDING_NOT_EXPECTED_V5")
    if value.get("carried_forward_accepted_case") != "H08":
        raise VisualReviewHold("BASELINE_CARRY_FORWARD_INVALID")
    return value


def readback_delta_review(review_path: Path, package: Path) -> dict[str, Any]:
    if not review_path.is_file():
        raise VisualReviewHold("REVIEW_FILE_REQUIRED")
    lines = [line.strip() for line in review_path.read_text(encoding="utf-8").splitlines()]
    current_sha = _line_value(lines, "今回レビュー対象三点セットreceipt SHA-256（書き換え禁止）:").lower()
    actual_sha = hashlib.sha256((package / "L04_CANDIDATE_TRIPLE_RECEIPT.json").read_bytes()).hexdigest()
    if current_sha != actual_sha:
        raise VisualReviewHold("REVIEW_BINDING_MISMATCH")
    baseline = _baseline(package)
    if _line_value(lines, "前回v5レビュー対象receipt SHA-256（固定）:").lower() != str(baseline["baseline_receipt_sha256"]).lower():
        raise VisualReviewHold("BASELINE_REVIEW_BINDING_MISMATCH")
    reviewer = _line_value(lines, "確認者名:")
    affiliation = _line_value(lines, "所属・立場（開発側との関係）:")
    independent = _answer(_line_value(lines, "開発側から独立している:"))
    reviewed_at = _line_value(lines, "確認日時（JST）:")
    browser = _line_value(lines, "使用端末・ブラウザ:")
    candidate_audit, delivery_audit = _load_audit(package)
    answers = [_delta_answer(lines, number) for number in range(1, 5)]
    overall = _answer(_line_value(lines, "差分4項目をすべて視覚的に受入できる:"))
    lineage = _answer(_line_value(lines, "今回のreceiptの数値来歴と実物表示を照合した:"))
    independence = _answer(_line_value(lines, "独立性を確認した:"))
    passed = (
        all(answer == "はい" for answer in answers)
        and overall == "はい"
        and lineage == "はい"
        and independent == "はい"
        and independence == "はい"
    )
    return {
        "schema": "minimalizer/local-l04/independent-visual-delta-review-readback/v1",
        "review_file_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "review_binding_receipt_sha256": actual_sha,
        "baseline_review_carried_forward": True,
        "baseline_receipt_sha256": baseline["baseline_receipt_sha256"],
        "reviewer": reviewer,
        "affiliation": affiliation,
        "reviewer_independent": independent == "はい",
        "reviewed_at_jst": reviewed_at,
        "browser": browser,
        "candidate_numerical_audit": "PASS",
        "b_delivery_audit": "PASS",
        "delta_answers": answers,
        "overall_answer": overall,
        "lineage_answer": lineage,
        "independence_answer": independence,
        "review_gate": "PASS" if passed else "HOLD",
        "L04_formal": "PASS" if passed else "HOLD",
        "Golden": "PASS" if passed else "HOLD",
        "production": "NO_GO",
        "release_authorized": False,
        "candidate_audit_schema": candidate_audit.get("schema"),
        "delivery_audit_schema": delivery_audit.get("schema"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="L04差分視覚確認票をfail-closedで読み戻す")
    parser.add_argument("review", type=Path)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = readback_delta_review(args.review, args.package)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
