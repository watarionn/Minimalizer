"""Verify a human-readable, candidate-bound L02 visual review form.

The reviewer writes plain text after inspecting frozen previews.  This verifier
does not load images, masks, labels, or model outputs and cannot promote Phase4;
it only authenticates that the required review fields bind to the frozen
candidate array hashes.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path


EXPECTED_CANDIDATE_SHA256 = {
    "H04": "c34cd47712d974f6f49e4f2da72704fb3028d92cbfb5e8e278ee3c96d9148b8c",
    "H06": "f21bd9733a077e1a0cebe9b8c3a251cccd25394db2f2eccaeb55209aeb63eb2b",
    "H08": "021becbb4ab5460b01ab69f7862d29a28b6593173cd5e37a010a3cbe29f75775",
}

REQUIRED_CASE_FIELDS = {
    "正衣装保持",
    "腕・手の誤ownerなし",
    "下着・別レイヤーの誤ownerなし",
    "袖の回復",
    "遮蔽の前後関係",
    "変更範囲の十分性",
}


class IndependentReviewHold(ValueError):
    """Raised when a review cannot be bound to the frozen candidate."""


def _value(lines: list[str], prefix: str) -> str:
    for line in lines:
        if line.startswith(prefix):
            value = line[len(prefix):].strip()
            if value:
                return value
    raise IndependentReviewHold(f"MISSING_FIELD:{prefix}")


def _case_value(lines: list[str], case: str, field: str) -> str:
    marker = f"{case} candidate SHA-256:"
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == marker)
    except StopIteration as exc:
        raise IndependentReviewHold(f"MISSING_CASE:{case}") from exc
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].strip().endswith("candidate SHA-256:")),
        len(lines),
    )
    if field == "candidate SHA-256":
        if start + 1 >= end:
            raise IndependentReviewHold(f"MISSING_FIELD:{case}:{field}")
        value = lines[start + 1].strip()
        if not value:
            raise IndependentReviewHold(f"MISSING_FIELD:{case}:{field}")
        return value
    return _value(lines[start + 1:end], f"{field}:")


def _yes(value: str, field: str) -> None:
    if value != "YES":
        raise IndependentReviewHold(f"REQUIRED_YES:{field}:{value}")


def verify_review_text(review_path: Path) -> dict[str, object]:
    if not isinstance(review_path, Path) or not review_path.is_file():
        raise IndependentReviewHold("REVIEW_FILE_REQUIRED")
    text = review_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines()]
    if any(len(line) > 1000 for line in lines):
        raise IndependentReviewHold("LINE_TOO_LONG")

    reviewer = _value(lines, "レビュー担当者:")
    review_datetime = _value(lines, "レビュー日時:")
    signature = _value(lines, "署名または改変検知可能な記録:")
    _yes(_value(lines, "開発側から独立している:"), "reviewer_independence")
    _yes(_value(lines, "推論前に評価ラベルを見ていない:"), "pre_inference_label_blindness")

    cases: dict[str, dict[str, str]] = {}
    for case in EXPECTED_CANDIDATE_SHA256:
        supplied_hash = _case_value(lines, case, "candidate SHA-256")
        if not re.fullmatch(r"[0-9a-f]{64}", supplied_hash):
            raise IndependentReviewHold(f"INVALID_CANDIDATE_SHA:{case}")
        if supplied_hash != EXPECTED_CANDIDATE_SHA256[case]:
            raise IndependentReviewHold(f"CANDIDATE_SHA_MISMATCH:{case}")
        values = {
            field: _case_value(lines, case, field)
            for field in REQUIRED_CASE_FIELDS
        }
        for field, value in values.items():
            _yes(value, f"{case}:{field}")
        reason = _case_value(lines, case, "理由")
        cases[case] = {"candidate_sha256": supplied_hash, **values, "理由": reason}

    overall = _value(lines, "総合判定:")
    _yes(overall, "overall_review")
    return {
        "schema": "minimalizer/local-l02/independent-visual-review-verification/v1",
        "review_file_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "reviewer": reviewer,
        "review_datetime": review_datetime,
        "signature_record": signature,
        "cases": cases,
        "review_gate": "PASS",
        "Phase4": "NOT_PROMOTED",
        "L02": "HOLD",
        "production": "NO_GO",
    }
