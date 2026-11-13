from pathlib import Path

import pytest

from tools.research.prepare_local_l02_phase4_receipt import (
    FORM_SCHEMA,
    Phase4PreparationHold,
    materialize_receipt,
    render_review_form,
)
from tools.research.verify_local_l02_phase4_receipt import CASES, SOURCE_SHA256


def freeze_receipt():
    return {
        "schema": "minimalizer.sapiens2.candidate-freeze.v1",
        "human_labels_used": False,
        "unknown_not_treated_as_negative": True,
        "cases": {
            case: {"candidate_array_sha256": (chr(97 + index) * 64)}
            for index, case in enumerate(CASES)
        },
    }


def _complete_form(freeze):
    lines = render_review_form(freeze).splitlines()
    replacements = {
        "reviewer_id:": "reviewer_id: independent-reviewer-1",
        "reviewed_at_utc:": "reviewed_at_utc: 2026-11-10T12:00:00Z",
        "signature_record:": "signature_record: signed-review-record-1",
    }
    global_flags = {
        "signature_verified",
        "unseen_data",
        "labels_unavailable_before_inference",
        "evaluator_independent",
        "semantic_review_complete",
        "unknown_mask_is_unknown",
        "human_masks_used_in_inference",
        "review_json_used_in_inference",
        "output_frozen_before_scoring",
    }
    case_flags = {
        "source_sha_verified",
        "candidate_sha_verified",
        "correct_garment_preserved",
        "wrong_owner_removed_only_where_justified",
        "sleeve_recovery_owner_exclusive",
        "occlusion_and_critical_parts_preserved",
        "visual_regression_acceptable",
        "change_visibility_sufficient",
        "unknown_not_negative",
    }
    current_case = None
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            current_case = stripped[1:-1]
        key = stripped.split(":", 1)[0] if ":" in stripped else ""
        if stripped in replacements:
            line = replacements[stripped]
        elif key in global_flags or key in case_flags:
            value = "NO" if key in {"human_masks_used_in_inference", "review_json_used_in_inference"} else "YES"
            line = f"{key}: {value}"
        result.append(line)
    return "\n".join(result) + "\n"


def test_init_form_uses_current_freeze_hashes():
    freeze = freeze_receipt()
    form = render_review_form(freeze)
    assert f"form_schema: {FORM_SCHEMA}" in form
    for index, case in enumerate(CASES):
        assert f"candidate_sha256: {chr(97 + index) * 64}" in form
        assert f"source_sha256: {SOURCE_SHA256[case]}" in form


def test_complete_form_materializes_only_after_verifier_passes():
    freeze = freeze_receipt()
    result = materialize_receipt(_complete_form(freeze), freeze)
    assert result["phase4"] == "PASS"
    assert result["phase5"] == "NO_GO"
    assert result["production"] == "NO_GO"
    assert result["reviewer_id"] == "independent-reviewer-1"
    assert result["signature_record"] == "signed-review-record-1"
    assert result["cases"]["H06"]["candidate_sha256"] == "b" * 64
    assert result["verification"]["phase4"] == "PASS"


def test_old_candidate_hash_cannot_be_reused():
    freeze = freeze_receipt()
    form = _complete_form(freeze).replace(
        "candidate_sha256: " + ("a" * 64),
        "candidate_sha256: " + ("f" * 64),
        1,
    )
    with pytest.raises(Phase4PreparationHold, match="CANDIDATE_SHA_MISMATCH:H04"):
        materialize_receipt(form, freeze)


def test_unanswered_visual_fields_do_not_materialize():
    freeze = freeze_receipt()
    form = _complete_form(freeze)
    form = form.replace("visual_regression_acceptable: YES", "visual_regression_acceptable: UNANSWERED", 1)
    with pytest.raises(Phase4PreparationHold, match="UNANSWERED_OR_INVALID:H04:visual_regression_acceptable"):
        materialize_receipt(form, freeze)
