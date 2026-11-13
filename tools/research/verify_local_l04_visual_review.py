"""Read back a human L04 visual review without fabricating a PASS.

The reviewer answers a plain Japanese text form.  This tool binds the answer
to the frozen candidate-triple audit, records every failed item, and keeps
formal L04/Golden/production closed when even one case is not accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


CASES = ("H04", "H06", "H08")
QUESTION_COUNT = 6
# The case rows include ``回答:`` while the top-level fields are already
# stripped by ``_line_value``.  Accept both forms so the readback is strict
# about the answer value without depending on which field supplied it.
ANSWER_RE = re.compile(r"^(?:回答:\s*)?(はい|いいえ|保留)")
CHECKBOX_ANSWER_RE = re.compile(r"\[([^\]]*)\]\s*(はい|いいえ|保留)")


class VisualReviewHold(ValueError):
    pass


def _line_value(lines: list[str], prefix: str) -> str:
    for line in lines:
        if line.startswith(prefix):
            value = line[len(prefix):].strip()
            if value:
                return value
    raise VisualReviewHold(f"MISSING_FIELD:{prefix}")


def _answer(value: str) -> str:
    match = ANSWER_RE.match(value)
    if match:
        return match.group(1)
    options = CHECKBOX_ANSWER_RE.findall(value)
    selected = [answer for marker, answer in options if marker.strip()]
    if len(selected) == 1:
        return selected[0]
    raise VisualReviewHold(f"INVALID_ANSWER:{value}")


def _case_block(lines: list[str], case: str) -> list[str]:
    marker = f"## {case}"
    try:
        start = lines.index(marker) + 1
    except ValueError as exc:
        raise VisualReviewHold(f"MISSING_CASE:{case}") from exc
    end = len(lines)
    for other in (*CASES, "全体回答"):
        if other == case:
            continue
        candidate = f"## {other}" if other in CASES else f"## {other}"
        if candidate in lines:
            candidate_index = lines.index(candidate)
            if candidate_index > start:
                end = min(end, candidate_index)
    return lines[start:end]


def _load_audit(package: Path) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    candidate_path = package / "L04_CANDIDATE_TRIPLE_AUDIT.json"
    delivery_path = package / "B_L04_DELIVERY_AUDIT.json"
    # Older preparation runs called the same candidate audit
    # ``candidate_audit.json``.  Accept that exact fallback only when the
    # content still passes the same numerical gate; never infer PASS from a
    # missing or differently named audit.
    if not candidate_path.is_file():
        candidate_path = package / "candidate_audit.json"
    if not candidate_path.is_file() or not delivery_path.is_file():
        raise VisualReviewHold("PACKAGE_AUDIT_MISSING")
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    delivery = json.loads(delivery_path.read_text(encoding="utf-8"))
    if candidate.get("numerical_handoff_eligible") is not True or candidate.get("failures") != []:
        raise VisualReviewHold("CANDIDATE_NUMERICAL_AUDIT_NOT_READY")
    if delivery.get("B_L04_delivery") != "PASS" or delivery.get("failures") != []:
        raise VisualReviewHold("B_DELIVERY_AUDIT_NOT_READY")
    return candidate, delivery


def readback_review(review_path: Path, package: Path) -> dict[str, Any]:
    if not review_path.is_file():
        raise VisualReviewHold("REVIEW_FILE_REQUIRED")
    lines = [line.strip() for line in review_path.read_text(encoding="utf-8").splitlines()]
    bound_receipt_sha = _line_value(lines, "レビュー対象三点セットreceipt SHA-256（書き換え禁止）:")
    actual_receipt_sha = hashlib.sha256(
        (package / "L04_CANDIDATE_TRIPLE_RECEIPT.json").read_bytes()
    ).hexdigest()
    if bound_receipt_sha.lower() != actual_receipt_sha:
        raise VisualReviewHold("REVIEW_BINDING_MISMATCH")
    reviewer = _line_value(lines, "確認者名:")
    affiliation = _line_value(lines, "所属・立場（開発側との関係）:")
    independent = _answer(_line_value(lines, "開発側から独立している:"))
    reviewed_at = _line_value(lines, "確認日時（JST）:")
    browser = _line_value(lines, "使用端末・ブラウザ:")
    candidate_audit, delivery_audit = _load_audit(package)
    cases: dict[str, dict[str, Any]] = {}
    for case in CASES:
        answers = [_answer(line) for line in _case_block(lines, case) if line.startswith("回答:")]
        if len(answers) != QUESTION_COUNT:
            raise VisualReviewHold(f"ANSWER_COUNT:{case}:{len(answers)}")
        failed = [index + 1 for index, answer in enumerate(answers) if answer != "はい"]
        cases[case] = {
            "answers": answers,
            "failed_question_numbers": failed,
            "accepted": not failed,
        }
    overall = _answer(_line_value(lines, "三例すべてを視覚的に受入できる:"))
    lineage = _answer(_line_value(lines, "数値来歴と実物表示を照合した:"))
    independent_readback = _answer(_line_value(lines, "独立性を確認した:"))
    all_cases_accepted = all(item["accepted"] for item in cases.values())
    review_pass = (
        independent == "はい"
        and independent_readback == "はい"
        and lineage == "はい"
        and overall == "はい"
        and all_cases_accepted
    )
    return {
        "schema": "minimalizer/local-l04/independent-visual-review-readback/v1",
        "review_file_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "review_binding_receipt_sha256": actual_receipt_sha,
        "reviewer": reviewer,
        "affiliation": affiliation,
        "reviewer_independent": independent == "はい",
        "reviewed_at_jst": reviewed_at,
        "browser": browser,
        "candidate_numerical_audit": "PASS",
        "b_delivery_audit": "PASS",
        "cases": cases,
        "overall_answer": overall,
        "lineage_answer": lineage,
        "independence_answer": independent_readback,
        "overall_consistent": overall == "はい" and all_cases_accepted,
        "review_gate": "PASS" if review_pass else "HOLD",
        "failure_reasons": {
            case: data["failed_question_numbers"]
            for case, data in cases.items()
            if data["failed_question_numbers"]
        },
        "L04_formal": "PASS" if review_pass else "HOLD",
        "Golden": "PASS" if review_pass else "HOLD",
        "production": "NO_GO",
        "release_authorized": False,
        "candidate_audit_schema": candidate_audit.get("schema"),
        "delivery_audit_schema": delivery_audit.get("schema"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="L04独立視覚確認票をfail-closedで読み戻す")
    parser.add_argument("review", type=Path)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = readback_review(args.review, args.package)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
