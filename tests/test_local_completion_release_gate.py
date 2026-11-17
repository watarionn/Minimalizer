from tools.research.local_completion_release_gate import (
    EXPECTED_CANDIDATE_RECEIPT_SHA256,
    EXPECTED_PRODUCTION_WORKER_COMMIT,
    assess_release_binding,
)


def _evidence():
    a = {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "six_capabilities": True,
        "same_config_three_cases": True,
        "source_only_inference": True,
        "human_labels_used_for_inference": False,
        "unknown_preserved": True,
        "h04_pass": True,
        "h06_pass": True,
        "h08_pass": True,
    }
    phase4 = {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "independent_evaluator": True,
        "output_frozen_before_scoring": True,
        "semantic_review_complete": True,
        "unknown_not_negative": True,
        "source_alpha_bounds_pass": True,
        "owner_exclusivity_pass": True,
        "components4_pass": True,
        "components8_pass": True,
        "holes4_pass": True,
        "holes8_pass": True,
        "occlusion_and_critical_parts_pass": True,
    }
    phase5 = {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "exact_replay": True,
        "same_config_three_cases": True,
        "source_sha_match": True,
        "output_sha_match": True,
    }
    l04 = {
        "L04_formal": "PASS",
        "Golden": "PASS",
        "production": "GO",
        "release_authorized": True,
    }
    l05 = {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "production_worker_commit": EXPECTED_PRODUCTION_WORKER_COMMIT,
    }
    l07 = {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "production_worker_commit": EXPECTED_PRODUCTION_WORKER_COMMIT,
    }
    acceptance = {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "production_worker_commit": EXPECTED_PRODUCTION_WORKER_COMMIT,
        "pc": True,
        "iphone_safari": True,
        "iphone_pwa": True,
        "png": True,
        "svg": True,
        "offline_recovery": True,
        "failure_paths": True,
        "fallback": True,
        "rollback": True,
    }
    return a, phase4, phase5, l04, l05, l07, acceptance


def test_release_requires_all_lanes_bound_to_current_worker():
    a, phase4, phase5, l04, l05, l07, acceptance = _evidence()
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04,
        l05=l05,
        l07=l07,
        acceptance=acceptance,
        owner_action_required=False,
    )
    assert result.status == "PASS"
    assert result.release_authorized is True
    assert result.failures == ()


def test_stale_worker_readiness_cannot_authorize_release():
    a, phase4, phase5, l04, l05, l07, acceptance = _evidence()
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit="c68dc17bdc2bbd3b0ba0841b7108177553891913c",
        a=a, phase4=phase4, phase5=phase5,
        l04=l04,
        l05=l05,
        l07=l07,
        acceptance=acceptance,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert result.release_authorized is False
    assert "production Worker commit mismatch" in result.failures


def test_l04_hold_and_owner_action_keep_release_closed():
    a, phase4, phase5, l04, l05, l07, acceptance = _evidence()
    l04["L04_formal"] = "HOLD"
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04,
        l05=l05,
        l07=l07,
        acceptance=acceptance,
        owner_action_required=True,
    )
    assert result.status == "HOLD"
    assert result.release_authorized is False
    assert "L04_formal mismatch" in result.failures
    assert "owner action required" in result.failures


def test_stale_worker_receipt_cannot_bind_even_when_candidate_matches():
    a, phase4, phase5, l04, l05, l07, acceptance = _evidence()
    l07["production_worker_commit"] = "c68dc17bdc2bbd3b0ba0841b7108177553891913c"
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04,
        l05=l05,
        l07=l07,
        acceptance=acceptance,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert result.release_authorized is False
    assert "L07 Worker binding mismatch" in result.failures


def test_missing_a_quality_gate_cannot_be_hidden_by_passing_b():
    a, phase4, phase5, l04, l05, l07, acceptance = _evidence()
    a["six_capabilities"] = False
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04, l05=l05, l07=l07, acceptance=acceptance,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert "A six_capabilities is not PASS" in result.failures


def test_phase4_and_phase5_are_required_before_release():
    a, phase4, phase5, l04, l05, l07, acceptance = _evidence()
    phase4["status"] = "FAIL"
    phase5["exact_replay"] = False
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04, l05=l05, l07=l07, acceptance=acceptance,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert "Phase4 status is not PASS" in result.failures
    assert "Phase5 exact_replay is not PASS" in result.failures


def test_current_iphone_acceptance_is_required():
    a, phase4, phase5, l04, l05, l07, acceptance = _evidence()
    acceptance["iphone_pwa"] = False
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04, l05=l05, l07=l07, acceptance=acceptance,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert "device acceptance iphone_pwa is not PASS" in result.failures
