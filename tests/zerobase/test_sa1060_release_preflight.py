"""Pure, no-private-input regressions for SA10.60 fail-closed preflight."""
import copy
import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "tools/research/sa1060_release_preflight.py"
spec = importlib.util.spec_from_file_location("sa1060_release_preflight", SCRIPT)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


def fixture():
    caps = {"Raden": (2370, 1412, 1409, 11), "GC001": (3604, 1887, 1873, 5)}
    stage8 = {"stage": "SA10.58", "cases": {}}
    golden = {"stage": "SA10.59", "cases": {}, "total_independent_signed_input_images": 2,
              "total_chromium_stage_replays": 6, "full_character_golden": "HOLD", "all_human_reviews": "PENDING"}
    for name, (n, cap, deployed, arm) in caps.items():
        pin = {name + "_source.png": "a" * 64}
        stage8["cases"][name] = {"original_stage8_ring_vertices": n, "original_stage8_budget": cap,
             "source_input_sha256": pin, "candidate_source_exact_release_gate": False,
             "full_source_ownership_replay": {"source_ownership_mismatched_pixels": 186, "changed_signed_arm_ownership_pixels": arm}}
        golden["cases"][name] = {"signed_source_sha256": pin,
             "source_original_stage8_ring_vertices": n, "historic_stage8_source_ring_budget": cap,
             "stages": {"SA10.57": {"expanded_vertices": deployed}},
             "default_faceless_pass": True, "face_iris_mouth_detail_should_be_visible": False,
             "signed_face_pixels_identical_across_stages": True,
             "signed_arms_pixels_identical_across_stages": True, "human_identity_verdict": "PENDING"}
    return stage8, golden


def test_current_two_case_evidence_is_hold():
    a, b = fixture(); out = s.audit(a, b)
    assert out["research_evidence_audit"] == "HOLD"
    assert not out["production_promotion_authorized"] and not out["phase15_executed"]
    assert "IMMUTABLE_ORIGINAL_STAGE8_RING_CAP_EXCEEDED" in out["blockers"]
    assert "SIGNED_GOLDEN_CORPUS_BELOW_18" in out["blockers"]
    assert out["case_summary"]["GC001"]["stage8_overrun"] == 1717


def test_forged_pass_status_does_not_clear_numeric_original_budget():
    a, b = fixture()
    a["source_stage8_release_gate"] = "PASS"
    for row in a["cases"].values():
        row["source_stage8_budget_pass"] = True
        row["candidate_source_exact_release_gate"] = True
    b["all_human_reviews"] = b["full_character_golden"] = "PASS"
    assert "IMMUTABLE_ORIGINAL_STAGE8_RING_CAP_EXCEEDED" in s.audit(a, b)["blockers"]
    assert not s.audit(a, b)["production_promotion_authorized"]


def test_bad_deployed_geometry_is_a_separate_blocker():
    a, b = fixture(); b["cases"]["Raden"]["stages"]["SA10.57"]["expanded_vertices"] = 1413
    assert "DEPLOYED_SVG_VERTEX_CAP_EXCEEDED" in s.audit(a, b)["blockers"]


def test_source_signature_lineage_mismatch_is_detected():
    a, b = fixture(); b["cases"]["GC001"]["signed_source_sha256"] = {"GC001_source.png": "b" * 64}
    assert "SIGNED_SOURCE_PIN_MISMATCH" in s.audit(a, b)["blockers"]


def test_face_features_require_default_off():
    a, b = fixture(); b["cases"]["Raden"]["face_iris_mouth_detail_should_be_visible"] = True
    assert "FACELESS_DEFAULT_NOT_VERIFIED" in s.audit(a, b)["blockers"]


def test_all_pass_manually_edited_review_is_not_authorized():
    a, b = fixture(); b["all_human_reviews"] = b["full_character_golden"] = "PASS"
    human = {"cases": {name: {"criteria": {x: "PASS" for x in s.CRITERIA},
              "artistic_identity": "PASS", "reviewer": "someone", "reviewed_at": "2026-10-09"} for name in s.CASES}}
    result = s.audit(a, b, human)
    assert "HUMAN_REVIEW_FORM_INCOMPLETE" not in result["blockers"]
    assert "HUMAN_APPROVAL_PROVENANCE_REQUIRES_INDEPENDENT_VERIFICATION" in result["blockers"]
    assert not result["production_promotion_authorized"]


def test_ownership_collision_cannot_be_passed_by_flag():
    a, b = fixture()
    for row in a["cases"].values(): row["candidate_source_exact_release_gate"] = True
    assert "STAGE8_COMPRESSED_CANDIDATE_CHANGES_SOURCE_OWNERS" in s.audit(a, b)["blockers"]


def test_missing_case_and_invalid_schema_fail_closed():
    a, b = fixture(); a["cases"].pop("GC001"); a["stage"] = "SA10.57"
    reasons = s.audit(a, b)["blockers"]
    assert "INVALID_STAGE8_EVIDENCE" in reasons
    assert "SIGNED_CASE_SET_MISMATCH" in reasons
    assert "MISSING_SIGNED_CASE_EVIDENCE" in reasons


def test_deterministic_numeric_only_public_summary():
    a, b = fixture()
    first = json.dumps(s.audit(a, b), sort_keys=True)
    second = json.dumps(s.audit(copy.deepcopy(a), copy.deepcopy(b)), sort_keys=True)
    assert first == second and "_source.png" not in first
