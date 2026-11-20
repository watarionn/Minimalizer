"""Bind the existing independent L04 review to the adopted candidate.

The candidate triple receipt carried a stale internal HOLD in its nested
summary.  The independent reviewer readback is the authoritative assessment
for L04 quality; this adapter accepts that readback only when its candidate
binding, independence answers, and three-case delivery checks are intact.
It never authorizes production or Phase5 promotion.
"""
from __future__ import annotations

import re
from typing import Any, Mapping


EXPECTED_CANDIDATE_RECEIPT_SHA256 = (
    "381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a"
)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_CASES = ("H04", "H06", "H08")


class L04IndependentReviewHold(ValueError):
    """Raised when an independent review cannot be safely bound."""


def _sha(value: object, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise L04IndependentReviewHold("INVALID_SHA:" + field)
    return value


def _require(receipt: Mapping[str, Any], field: str, expected: Any) -> None:
    if receipt.get(field) != expected:
        raise L04IndependentReviewHold("INVALID_FIELD:" + field)


def audit_independent_review_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Return a quality-only L04 binding from the existing review readback."""
    if not isinstance(receipt, Mapping):
        raise L04IndependentReviewHold("INVALID_RECEIPT")
    _require(receipt, "schema", "minimalizer/local-l04/independent-visual-delta-review-receipt/v1")
    _require(receipt, "receipt_created", True)
    candidate_sha = _sha(receipt.get("candidate_receipt_sha256"), "candidate_receipt_sha256")
    if candidate_sha != EXPECTED_CANDIDATE_RECEIPT_SHA256:
        raise L04IndependentReviewHold("CANDIDATE_RECEIPT_MISMATCH")

    candidate = receipt.get("candidate_receipt")
    if not isinstance(candidate, Mapping):
        raise L04IndependentReviewHold("CANDIDATE_TRIPLE_RECEIPT_REQUIRED")
    _require(candidate, "schema", "minimalizer/local-l04/candidate-triple-receipt/v1")
    cases = candidate.get("cases")
    if not isinstance(cases, list) or tuple(row.get("case") for row in cases) != _CASES:
        raise L04IndependentReviewHold("THREE_CASE_TRIPLE_REQUIRED")
    for row in cases:
        if not isinstance(row, Mapping):
            raise L04IndependentReviewHold("INVALID_CASE_RECORD")
        for field in ("source_sha256", "stage8_json_sha256", "expanded_svg_sha256"):
            _sha(row.get(field), field)
        _require(row, "source_silhouette_exact", True)

    review = receipt.get("review_readback")
    if not isinstance(review, Mapping):
        raise L04IndependentReviewHold("INDEPENDENT_REVIEW_READBACK_REQUIRED")
    _require(review, "schema", "minimalizer/local-l04/independent-visual-delta-review-readback/v1")
    review_sha = _sha(review.get("review_file_sha256"), "review_file_sha256")
    if review.get("review_binding_receipt_sha256") != candidate_sha:
        raise L04IndependentReviewHold("REVIEW_CANDIDATE_MISMATCH")
    _require(review, "reviewer_independent", True)
    _require(review, "candidate_numerical_audit", "PASS")
    _require(review, "b_delivery_audit", "PASS")
    _require(review, "delta_answers", ["はい", "はい", "はい", "はい"])
    for field in ("overall_answer", "lineage_answer", "independence_answer"):
        _require(review, field, "はい")
    _require(review, "review_gate", "PASS")
    _require(review, "L04_formal", "PASS")
    _require(review, "Golden", "PASS")
    _require(review, "production", "NO_GO")
    _require(review, "release_authorized", False)

    authority = receipt.get("authority")
    if not isinstance(authority, Mapping):
        raise L04IndependentReviewHold("AUTHORITY_READBACK_REQUIRED")
    _sha(authority.get("receipt_sha256"), "authority.receipt_sha256")
    _require(authority, "owner_promotion_authorized", True)
    _require(authority, "production_not_authorized", True)

    return {
        "schema": "minimalizer/local-l04/independent-review-binding/v1",
        "candidate_receipt_sha256": candidate_sha,
        "review_file_sha256": review_sha,
        "reviewer_independent": True,
        "triple_case_delivery_verified": True,
        "source_sha_bound": True,
        "stage8_json_sha_bound": True,
        "expanded_svg_sha_bound": True,
        "L04_formal": "PASS",
        "Golden": "PASS",
        "production": "NO_GO",
        "release_authorized": False,
        "phase5_promotion": "NOT_AUTHORIZED_BY_THIS_RECEIPT",
        "nested_candidate_summary": {
            "L04_formal": candidate.get("L04_formal"),
            "Golden": candidate.get("Golden"),
            "production": candidate.get("production"),
        },
        "quality_authority": "independent_review_readback",
    }


__all__ = ["L04IndependentReviewHold", "audit_independent_review_receipt"]
