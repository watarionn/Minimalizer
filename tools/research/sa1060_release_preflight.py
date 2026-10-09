"""SA10.60 preflight for the frozen SA10.58/59 evidence. Never authorizes deployment.

Public, coordinate-free metrics only. The independently governed historical Stage8
policy and authentic human Golden cannot be cleared by changing a JSON status flag.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CASES = ("Raden", "GC001")
MIN_REVIEW_CORPUS = 18  # expansion target, not a substitute for Approved-78 Phase14
CRITERIA = (
    "faceless_default_and_no_skin_plate",
    "recognizable_hair_flow_and_head_shape",
    "source_costume_planes_and_distinctive_accessories",
    "anatomically_legible_both_arms_and_pose",
    "overall_silhouette_and_person_identity",
    "no_unapproved_generated_or_raster_detail",
)


def audit(stage8: dict, golden: dict, human: dict | None = None) -> dict:
    """Inspect only evidence, with fixed HOLD. Not an approval-signature verifier."""
    reasons: set[str] = set()
    summary: dict[str, dict] = {}
    if not isinstance(stage8, dict) or stage8.get("stage") != "SA10.58":
        reasons.add("INVALID_STAGE8_EVIDENCE")
    if not isinstance(golden, dict) or golden.get("stage") != "SA10.59":
        reasons.add("INVALID_GOLDEN_EVIDENCE")
    s_cases = stage8.get("cases", {}) if isinstance(stage8, dict) else {}
    g_cases = golden.get("cases", {}) if isinstance(golden, dict) else {}
    if not isinstance(s_cases, dict) or not isinstance(g_cases, dict) or set(s_cases) != set(CASES) or set(g_cases) != set(CASES):
        reasons.add("SIGNED_CASE_SET_MISMATCH")
    for name in CASES:
        s, g = s_cases.get(name), g_cases.get(name)
        if not isinstance(s, dict) or not isinstance(g, dict):
            reasons.add("MISSING_SIGNED_CASE_EVIDENCE")
            continue
        n, cap, deployed = s.get("original_stage8_ring_vertices"), s.get("original_stage8_budget"), g.get("stages", {}).get("SA10.57", {}).get("expanded_vertices")
        valid = all(type(x) is int and x > 0 for x in (n, cap, deployed))
        if not valid or n != g.get("source_original_stage8_ring_vertices") or cap != g.get("historic_stage8_source_ring_budget"):
            reasons.add("STAGE8_SVG_LEDGER_MISMATCH")
            continue
        if s.get("source_input_sha256") != g.get("signed_source_sha256") or not s.get("source_input_sha256"):
            reasons.add("SIGNED_SOURCE_PIN_MISMATCH")
        if not g.get("default_faceless_pass") or g.get("face_iris_mouth_detail_should_be_visible") is not False:
            reasons.add("FACELESS_DEFAULT_NOT_VERIFIED")
        if deployed > cap:
            reasons.add("DEPLOYED_SVG_VERTEX_CAP_EXCEEDED")
        # Check numerical originals, never a mutable claim like source_stage8_budget_pass.
        if n > cap:
            reasons.add("IMMUTABLE_ORIGINAL_STAGE8_RING_CAP_EXCEEDED")
        owner = s.get("full_source_ownership_replay", {})
        if not isinstance(owner, dict) or any(type(owner.get(k)) is not int for k in ("source_ownership_mismatched_pixels", "changed_signed_arm_ownership_pixels")):
            reasons.add("INVALID_SOURCE_OWNER_REPLAY")
        elif owner["source_ownership_mismatched_pixels"] != 0 or owner["changed_signed_arm_ownership_pixels"] != 0:
            reasons.add("STAGE8_COMPRESSED_CANDIDATE_CHANGES_SOURCE_OWNERS")
        if s.get("candidate_source_exact_release_gate") is not True:
            reasons.add("STAGE8_SAFE_EQUIVALENCE_UNPROVEN")
        if not g.get("signed_face_pixels_identical_across_stages") or not g.get("signed_arms_pixels_identical_across_stages"):
            reasons.add("FACE_ARM_INTERSTAGE_REGRESSION")
        summary[name] = {"immutable_source_ring_vertices": n, "unchanged_stage8_cap": cap,
                         "research_svg_vertices": deployed, "stage8_overrun": max(0, n - cap),
                         "human_identity": g.get("human_identity_verdict", "MISSING")}
    if golden.get("total_independent_signed_input_images") != len(CASES) or golden.get("total_chromium_stage_replays") != 6:
        reasons.add("GOLDEN_REPLAY_LEDGER_MISMATCH")
    if golden.get("total_independent_signed_input_images", 0) < MIN_REVIEW_CORPUS:
        reasons.add("SIGNED_GOLDEN_CORPUS_BELOW_18")
    if golden.get("full_character_golden") != "PASS" or golden.get("all_human_reviews") != "PASS":
        reasons.add("HUMAN_ARTISTIC_GOLDEN_PENDING")
    # An edited form is not an authenticated signoff. Preserve out-of-band approval.
    human_cases = human.get("cases", {}) if isinstance(human, dict) else {}
    for name in CASES:
        h = human_cases.get(name, {}) if isinstance(human_cases, dict) else {}
        if not isinstance(h, dict) or not all(h.get("criteria", {}).get(c) == "PASS" for c in CRITERIA) or h.get("artistic_identity") != "PASS" or not h.get("reviewer") or not h.get("reviewed_at"):
            reasons.add("HUMAN_REVIEW_FORM_INCOMPLETE")
    reasons.add("HUMAN_APPROVAL_PROVENANCE_REQUIRES_INDEPENDENT_VERIFICATION")
    reasons.add("STAGE8_POLICY_DECISION_REQUIRES_EXPLICIT_VERSIONED_APPROVAL")
    reasons.add("PHASE15_RUNTIME_AND_DEVICE_GATES_NOT_RUN")
    return {"stage": "SA10.60-preflight", "schema": "non-promoting-frozen-evidence-audit-v1",
            "reviewed_signed_cases": len(summary), "case_summary": summary,
            "research_evidence_audit": "HOLD", "blockers": sorted(reasons),
            "stage8_policy_changed": False, "faceless_rule_changed": False,
            "production_promotion_authorized": False, "phase15_executed": False,
            "production_changed": False,
            "note": "This read-only audit cannot verify a human signoff or approve a versioned Stage8 policy change."}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage8", type=Path, required=True)
    p.add_argument("--golden", type=Path, required=True)
    p.add_argument("--human", type=Path)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    def read(path):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Evidence JSON must contain a top-level object")
        return payload
    result = audit(read(a.stage8), read(a.golden), read(a.human) if a.human else None)
    if any(a.out.resolve() == q.resolve() for q in (a.stage8, a.golden, a.human) if q):
        raise ValueError("DO_NOT_OVERWRITE_SIGNED_OR_REVIEW_EVIDENCE")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["research_evidence_audit"], "blockers": result["blockers"]}, ensure_ascii=False))
    return 2  # Explicit HOLD; never a zero/approval result.


if __name__ == "__main__":
    raise SystemExit(main())
