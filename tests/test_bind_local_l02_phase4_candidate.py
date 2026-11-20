from __future__ import annotations

import pytest

from tools.research.bind_local_l02_phase4_candidate import (
    CASES,
    Phase4CandidateBindingHold,
    SCHEMA,
    audit_phase4_candidate_binding,
)
from tools.research.local_completion_release_gate import EXPECTED_CANDIDATE_RECEIPT_SHA256 as CANDIDATE


def _sha(char: str) -> str:
    return char * 64


def _binding():
    return {
        "schema": SCHEMA,
        "candidate_receipt_sha256": CANDIDATE,
        "source_only": True,
        "human_labels_used_for_inference": False,
        "same_config_three_cases": list(CASES),
        "cases": {
            case: {"source_sha256": _sha(str(index + 1)), "candidate_sha256": _sha(str(index + 4))}
            for index, case in enumerate(CASES)
        },
    }


def _phase4():
    return {
        "schema": "minimalizer/l02/phase4-independent-review/v1",
        "phase4": "PASS",
        "unseen_data": True,
        "labels_unavailable_before_inference": True,
        "evaluator_independent": True,
        "semantic_review_complete": True,
        "review_json_used_in_inference": False,
        "output_frozen_before_scoring": True,
        "cases": {
            case: {
                "source_sha256": _sha(str(index + 1)),
                "candidate_sha256": _sha(str(index + 4)),
                "correct_garment_preserved": True,
                "wrong_owner_removed_only_where_justified": True,
                "sleeve_recovery_owner_exclusive": True,
                "occlusion_and_critical_parts_preserved": True,
                "unknown_not_negative": True,
            }
            for index, case in enumerate(CASES)
        },
    }


def test_explicit_three_case_binding_passes_without_private_artifacts():
    result = audit_phase4_candidate_binding(_phase4(), _binding())

    assert result["status"] == "PASS"
    assert result["candidate_receipt_sha256"] == CANDIDATE
    assert result["release_authorized"] is False
    assert result["private_artifacts_opened"] is False


def test_missing_or_wrong_candidate_binding_fails_closed():
    binding = _binding()
    binding["candidate_receipt_sha256"] = _sha("0")

    with pytest.raises(Phase4CandidateBindingHold, match="CANDIDATE_RECEIPT_MISMATCH"):
        audit_phase4_candidate_binding(_phase4(), binding)


def test_phase4_candidate_array_mismatch_fails_closed():
    phase4 = _phase4()
    phase4["cases"]["H08"]["candidate_sha256"] = _sha("f")

    with pytest.raises(Phase4CandidateBindingHold, match="CANDIDATE_ARRAY_SHA_MISMATCH:H08"):
        audit_phase4_candidate_binding(phase4, _binding())


def test_phase4_human_label_inference_is_rejected():
    phase4 = _phase4()
    phase4["review_json_used_in_inference"] = True

    with pytest.raises(Phase4CandidateBindingHold, match="PHASE4_REVIEW_JSON_IN_INFERENCE"):
        audit_phase4_candidate_binding(phase4, _binding())
