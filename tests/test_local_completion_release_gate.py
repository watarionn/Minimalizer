from tools.research.local_completion_release_gate import (
    EXPECTED_CANDIDATE_RECEIPT_SHA256,
    EXPECTED_PRODUCTION_WORKER_COMMIT,
    assess_release_binding,
)


def _evidence():
    return {
        "L04_formal": "PASS",
        "Golden": "PASS",
        "production": "GO",
        "release_authorized": True,
    }, {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "production_worker_commit": EXPECTED_PRODUCTION_WORKER_COMMIT,
    }, {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "production_worker_commit": EXPECTED_PRODUCTION_WORKER_COMMIT,
    }


def test_release_requires_all_lanes_bound_to_current_worker():
    l04, l05, l07 = _evidence()
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        l04=l04,
        l05=l05,
        l07=l07,
        owner_action_required=False,
    )
    assert result.status == "PASS"
    assert result.release_authorized is True
    assert result.failures == ()


def test_stale_worker_readiness_cannot_authorize_release():
    l04, l05, l07 = _evidence()
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit="c68dc17bdc2bbd3b0ba0841b7108177553891913c",
        l04=l04,
        l05=l05,
        l07=l07,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert result.release_authorized is False
    assert "production Worker commit mismatch" in result.failures


def test_l04_hold_and_owner_action_keep_release_closed():
    l04, l05, l07 = _evidence()
    l04["L04_formal"] = "HOLD"
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        l04=l04,
        l05=l05,
        l07=l07,
        owner_action_required=True,
    )
    assert result.status == "HOLD"
    assert result.release_authorized is False
    assert "L04_formal mismatch" in result.failures
    assert "owner action required" in result.failures


def test_stale_worker_receipt_cannot_bind_even_when_candidate_matches():
    l04, l05, l07 = _evidence()
    l07["production_worker_commit"] = "c68dc17bdc2bbd3b0ba0841b7108177553891913c"
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        l04=l04,
        l05=l05,
        l07=l07,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert result.release_authorized is False
    assert "L07 Worker binding mismatch" in result.failures
