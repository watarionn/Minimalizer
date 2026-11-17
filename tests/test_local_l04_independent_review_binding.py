import copy
import json
from pathlib import Path

import pytest

from tools.research.local_l04_independent_review_binding import (
    L04IndependentReviewHold,
    audit_independent_review_receipt,
)


RECEIPT_PATH = Path(r"C:\Work\Temp\minimalizer-l04-v12-independent-visual-delta-receipt.json")


def _receipt():
    return json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))


def test_existing_independent_review_binds_quality_only():
    result = audit_independent_review_receipt(_receipt())
    assert result["L04_formal"] == "PASS"
    assert result["Golden"] == "PASS"
    assert result["production"] == "NO_GO"
    assert result["release_authorized"] is False
    assert result["triple_case_delivery_verified"] is True
    assert result["nested_candidate_summary"]["L04_formal"] == "HOLD"


def test_candidate_sha_mismatch_is_rejected():
    receipt = _receipt()
    receipt["candidate_receipt_sha256"] = "0" * 64
    with pytest.raises(L04IndependentReviewHold, match="CANDIDATE_RECEIPT_MISMATCH"):
        audit_independent_review_receipt(receipt)


def test_independence_must_be_explicit():
    receipt = _receipt()
    receipt["review_readback"]["reviewer_independent"] = False
    with pytest.raises(L04IndependentReviewHold, match="INVALID_FIELD:reviewer_independent"):
        audit_independent_review_receipt(receipt)


def test_review_cannot_authorize_production():
    receipt = copy.deepcopy(_receipt())
    receipt["review_readback"]["production"] = "GO"
    with pytest.raises(L04IndependentReviewHold, match="INVALID_FIELD:production"):
        audit_independent_review_receipt(receipt)
