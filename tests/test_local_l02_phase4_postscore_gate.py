import importlib.util
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "tools/research/local_l02_phase4_postscore_gate.py"
spec = importlib.util.spec_from_file_location("phase4_postscore_gate", SRC)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


REVIEW = {name: value for name, value in {
    "signature_verified": True,
    "unseen_data": True,
    "labels_unavailable_before_inference": True,
    "evaluator_independent": True,
    "semantic_review_complete": True,
    "unknown_mask_is_unknown": True,
    "human_masks_used_in_inference": False,
    "review_json_used_in_inference": False,
    "output_frozen_before_scoring": True,
}.items()}
STRUCTURAL = {name: True for name in (
    "source_sha_verified", "prediction_sha_verified",
    "source_alpha_bounds_pass", "owner_provenance_pass",
    "owner_exclusivity_pass", "components4_pass", "components8_pass",
    "holes4_pass", "holes8_pass",
)}


def metrics(**overrides):
    values = {
        "candidate_added_px": 0,
        "candidate_removed_px": 4,
        "added_known_positive_garment_px": 0,
        "added_known_negative_owner_px": 0,
        "added_unknown_px": 0,
        "removed_known_positive_garment_px": 0,
        "removed_known_negative_owner_px": 4,
        "removed_unknown_px": 0,
        "owner_promotions": 0,
    }
    values.update(overrides)
    return values


def test_h06_narrow_postscore_pass_does_not_authorize_phase5():
    result = gate.evaluate_frozen_candidate(
        review=REVIEW, structural=STRUCTURAL, metrics=metrics())
    assert result["case_phase4"] == "PASS"
    assert result["phase5_authorized"] is False
    assert result["L02"] == "HOLD"


def test_unknown_mutation_holds_even_when_known_negative_improves():
    result = gate.evaluate_frozen_candidate(
        review=REVIEW, structural=STRUCTURAL,
        metrics=metrics(removed_known_negative_owner_px=3, removed_unknown_px=1,
                        candidate_removed_px=4))
    assert result["case_phase4"] == "HOLD"
    assert "UNKNOWN_MUTATION_NOT_ALLOWED" in result["failures"]


def test_garment_loss_holds():
    result = gate.evaluate_frozen_candidate(
        review=REVIEW, structural=STRUCTURAL,
        metrics=metrics(removed_known_positive_garment_px=1,
                        removed_known_negative_owner_px=3))
    assert result["case_phase4"] == "HOLD"
    assert "KNOWN_GARMENT_LOSS" in result["failures"]


def test_inference_label_leak_holds():
    review = dict(REVIEW, human_masks_used_in_inference=True)
    result = gate.evaluate_frozen_candidate(
        review=review, structural=STRUCTURAL, metrics=metrics())
    assert result["case_phase4"] == "HOLD"
    assert "review_FAIL:human_masks_used_in_inference" in result["failures"]


def test_structural_failure_holds():
    structural = dict(STRUCTURAL, holes8_pass=False)
    result = gate.evaluate_frozen_candidate(
        review=REVIEW, structural=structural, metrics=metrics())
    assert result["case_phase4"] == "HOLD"
    assert "structural_FAIL:holes8_pass" in result["failures"]
