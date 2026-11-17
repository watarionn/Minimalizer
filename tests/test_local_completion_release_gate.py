from tools.research.local_completion_release_gate import (
    EXPECTED_CANDIDATE_RECEIPT_SHA256,
    EXPECTED_PRODUCTION_WORKER_COMMIT,
    assess_release_binding,
)


def _evidence():
    a = {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "observer_capabilities": [
            "arm", "instance_grouping", "occlusion_garment_body",
            "occlusion_outerwear_underlayer", "occlusion_sleeve_arm",
            "outerwear", "sleeve", "underlayer",
        ],
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
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "L04_formal": "PASS",
        "Golden": "PASS",
        "production": "GO",
        "release_authorized": True,
        "triple_case_delivery_verified": True,
        "source_sha_bound": True,
        "stage8_json_sha_bound": True,
        "expanded_svg_sha_bound": True,
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
        "generation_pinned": True,
        "rollback_available": True,
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
    regression = {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "l06_golden_pass": True,
        "approved18_to_78_pass": True,
        "browser_render_pass": True,
        "performance_pass": True,
    }
    preservation = {
        "status": "PASS",
        "candidate_receipt_sha256": EXPECTED_CANDIDATE_RECEIPT_SHA256,
        "release_sha_bound": True,
        "artifact_sha_bound": True,
        "private_drive_saved": True,
        "private_drive_readback": True,
        "source_free_ledger": True,
    }
    return a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation


def test_release_requires_all_lanes_bound_to_current_worker():
    a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation = _evidence()
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04,
        l05=l05,
        l07=l07,
        acceptance=acceptance,
        regression=regression,
        preservation=preservation,
        owner_action_required=False,
    )
    assert result.status == "PASS"
    assert result.release_authorized is True
    assert result.failures == ()


def test_stale_worker_readiness_cannot_authorize_release():
    a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation = _evidence()
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit="c68dc17bdc2bbd3b0ba0841b7108177553891913c",
        a=a, phase4=phase4, phase5=phase5,
        l04=l04,
        l05=l05,
        l07=l07,
        acceptance=acceptance,
        regression=regression,
        preservation=preservation,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert result.release_authorized is False
    assert "production Worker commit mismatch" in result.failures


def test_l04_hold_and_owner_action_keep_release_closed():
    a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation = _evidence()
    l04["L04_formal"] = "HOLD"
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04,
        l05=l05,
        l07=l07,
        acceptance=acceptance,
        regression=regression,
        preservation=preservation,
        owner_action_required=True,
    )
    assert result.status == "HOLD"
    assert result.release_authorized is False
    assert "L04_formal mismatch" in result.failures
    assert "owner action required" in result.failures


def test_stale_worker_receipt_cannot_bind_even_when_candidate_matches():
    a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation = _evidence()
    l07["production_worker_commit"] = "c68dc17bdc2bbd3b0ba0841b7108177553891913c"
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04,
        l05=l05,
        l07=l07,
        acceptance=acceptance,
        regression=regression,
        preservation=preservation,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert result.release_authorized is False
    assert "L07 Worker binding mismatch" in result.failures


def test_missing_a_quality_gate_cannot_be_hidden_by_passing_b():
    a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation = _evidence()
    a["six_capabilities"] = False
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04, l05=l05, l07=l07, acceptance=acceptance,
        regression=regression, preservation=preservation,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert "A six_capabilities is not PASS" in result.failures


def test_summary_flag_cannot_replace_exact_observer_contract():
    a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation = _evidence()
    a.pop("observer_capabilities")
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04, l05=l05, l07=l07, acceptance=acceptance,
        regression=regression, preservation=preservation,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert "A observer_capabilities contract is missing" in result.failures


def test_phase4_and_phase5_are_required_before_release():
    a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation = _evidence()
    phase4["status"] = "FAIL"
    phase5["exact_replay"] = False
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04, l05=l05, l07=l07, acceptance=acceptance,
        regression=regression, preservation=preservation,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert "Phase4 status is not PASS" in result.failures
    assert "Phase5 exact_replay is not PASS" in result.failures


def test_current_iphone_acceptance_is_required():
    a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation = _evidence()
    acceptance["iphone_pwa"] = False
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04, l05=l05, l07=l07, acceptance=acceptance,
        regression=regression, preservation=preservation,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert "device acceptance iphone_pwa is not PASS" in result.failures


def test_l04_quality_cannot_be_rebound_from_another_candidate():
    a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation = _evidence()
    l04["candidate_receipt_sha256"] = "0" * 64
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04, l05=l05, l07=l07, acceptance=acceptance,
        regression=regression, preservation=preservation,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert "L04 candidate binding mismatch" in result.failures


def test_regression_and_preservation_are_required():
    a, phase4, phase5, l04, l05, l07, acceptance, regression, preservation = _evidence()
    regression["approved18_to_78_pass"] = False
    preservation["private_drive_readback"] = False
    result = assess_release_binding(
        candidate_receipt_sha256=EXPECTED_CANDIDATE_RECEIPT_SHA256,
        production_worker_commit=EXPECTED_PRODUCTION_WORKER_COMMIT,
        a=a, phase4=phase4, phase5=phase5,
        l04=l04, l05=l05, l07=l07, acceptance=acceptance,
        regression=regression, preservation=preservation,
        owner_action_required=False,
    )
    assert result.status == "HOLD"
    assert "regression approved18_to_78_pass is not PASS" in result.failures
    assert "preservation private_drive_readback is not PASS" in result.failures
