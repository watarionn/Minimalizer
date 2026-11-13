import importlib.util
from pathlib import Path

import pytest


SRC = Path(__file__).resolve().parents[1] / "tools/research/verify_local_l02_phase4_receipt.py"
spec = importlib.util.spec_from_file_location("verify_phase4_receipt", SRC)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def freeze_receipt():
    return {
        "human_labels_used": False,
        "unknown_not_treated_as_negative": True,
        "cases": {
            case: {"candidate_array_sha256": ("a" * 64)}
            for case in gate.CASES
        },
    }


def receipt(**overrides):
    result = {
        "schema": "minimalizer/l02/phase4-independent-review/v1",
        "phase4": "PASS",
        "reviewer_id": "independent-reviewer-1",
        "reviewed_at_utc": "2026-11-10T00:00:00Z",
        "signature_verified": True,
        "unseen_data": True,
        "labels_unavailable_before_inference": True,
        "evaluator_independent": True,
        "semantic_review_complete": True,
        "unknown_mask_is_unknown": True,
        "human_masks_used_in_inference": False,
        "review_json_used_in_inference": False,
        "output_frozen_before_scoring": True,
        "cases": {},
    }
    for case, source_sha in gate.SOURCE_SHA256.items():
        result["cases"][case] = {
            "source_sha256": source_sha,
            "candidate_sha256": "a" * 64,
            "source_sha_verified": True,
            "candidate_sha_verified": True,
            "correct_garment_preserved": True,
            "wrong_owner_removed_only_where_justified": True,
            "sleeve_recovery_owner_exclusive": True,
            "occlusion_and_critical_parts_preserved": True,
            "visual_regression_acceptable": True,
            "change_visibility_sufficient": True,
            "unknown_not_negative": True,
        }
    result.update(overrides)
    return result


def test_receipt_passes_without_authorizing_phase5():
    result = gate.verify_phase4_receipt(receipt(), freeze_receipt())
    assert result["phase4"] == "PASS"
    assert result["phase5"] == "NO_GO"
    assert result["production"] == "NO_GO"


def test_candidate_sha_mismatch_holds():
    review = receipt()
    review["cases"]["H08"]["candidate_sha256"] = "b" * 64
    with pytest.raises(gate.Phase4ReceiptHold, match="CANDIDATE_SHA_MISMATCH:H08"):
        gate.verify_phase4_receipt(review, freeze_receipt())


def test_source_sha_mismatch_holds():
    review = receipt()
    review["cases"]["H06"]["source_sha256"] = "0" * 64
    with pytest.raises(gate.Phase4ReceiptHold, match="SOURCE_SHA_MISMATCH:H06"):
        gate.verify_phase4_receipt(review, freeze_receipt())


def test_missing_independence_or_semantic_check_holds():
    review = receipt()
    review["evaluator_independent"] = False
    review["cases"]["H04"]["occlusion_and_critical_parts_preserved"] = False
    with pytest.raises(gate.Phase4ReceiptHold) as exc:
        gate.verify_phase4_receipt(review, freeze_receipt())
    assert "GLOBAL_FLAG_FAIL:evaluator_independent" in exc.value.failures
    assert "CASE_FLAG_FAIL:H04:occlusion_and_critical_parts_preserved" in exc.value.failures


def test_freeze_label_leak_holds():
    frozen = freeze_receipt()
    frozen["human_labels_used"] = True
    with pytest.raises(gate.Phase4ReceiptHold, match="FREEZE_LABEL_LEAK_FLAG"):
        gate.verify_phase4_receipt(receipt(), frozen)


def test_too_small_visual_delta_holds_without_relabeling_as_quality_fail():
    review = receipt()
    review["cases"]["H08"]["change_visibility_sufficient"] = False
    with pytest.raises(gate.Phase4ReceiptHold) as exc:
        gate.verify_phase4_receipt(review, freeze_receipt())
    assert "CASE_FLAG_FAIL:H08:change_visibility_sufficient" in exc.value.failures
