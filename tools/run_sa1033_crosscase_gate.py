"""Cross-image SA10.33 hard-gate evidence aggregation (not a promotion API)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


WATCHED = ("face", "hair", "left_arm", "right_arm")


def aggregate_cases(cases: dict[str, dict], *, minimum_distinct: int = 2) -> dict:
    if minimum_distinct < 2:
        raise ValueError("real cross-case benchmark must contain at least two distinct sources")
    if not cases:
        raise ValueError("no case evidence supplied")
    seen_sha: set[str] = set()
    duplicate_source_count = 0
    output = {}
    provenance_all_pass = True
    quality_all_pass = True
    for name, case in sorted(cases.items()):
        if not isinstance(case, dict) or case.get("schema") != "sa10.33-phase7-full-scene-authority-v1":
            raise ValueError(f"invalid Phase7 evidence schema: {name}")
        source = case.get("provenance", {}).get("source_hash")
        if not isinstance(source, str) or len(source) != 64:
            raise ValueError(f"source SHA256 missing: {name}")
        if source in seen_sha:
            duplicate_source_count += 1
        seen_sha.add(source)
        anatomy = case.get("global", {}).get("global_anatomy_gate", {})
        parts = case.get("parts", {})
        if any(owner not in parts for owner in WATCHED):
            raise ValueError(f"required owner metrics missing: {name}")
        pr = case.get("provenance", {})
        provenance = (
            case.get("reproduction_pass") is True
            and case.get("owner_audit", {}).get("status") == "OWNER_AUDIT_PASS"
            and pr.get("selected_render_preview_pixel_equal") is True
            and pr.get("selected_serialized_records_equal") is True
            and pr.get("guard_changed_outside_face_pixels") == 0
        )
        quality = (
            provenance and anatomy.get("gate") == "PASS"
            and not case.get("source_topology_drift_owners")
            and not case.get("serialized_export_drift_owners")
            and not any(not parts[owner].get("raw_source_topology_pass", False) for owner in WATCHED)
        )
        provenance_all_pass &= provenance
        quality_all_pass &= quality
        output[name] = {
            "provenance_verified": provenance,
            "full_anatomy_gate": anatomy.get("gate"),
            "source_topology": anatomy.get("source_evidence", {}).get("topology"),
            "render_topology": anatomy.get("candidate_evidence", {}).get("topology"),
            "silhouette_iou": anatomy.get("metrics", {}).get("silhouette_iou"),
            "source_topology_drift_owners": case.get("source_topology_drift_owners"),
            "serialized_export_drift_owners": case.get("serialized_export_drift_owners"),
            "owner_source_to_render_iou": {
                owner: parts[owner].get("source_to_render", {}).get("iou")
                for owner in WATCHED
            },
            "tiny_missing_component_pixels": {
                owner: parts[owner].get("lost_source_components_in_render", {}).get(
                    "fully_missing_below_threshold_pixels"
                ) for owner in WATCHED
            },
        }
    enough_sources = len(seen_sha) >= minimum_distinct
    evidence_pass = enough_sources and provenance_all_pass
    blockers = []
    if not enough_sources:
        blockers.append("INSUFFICIENT_DISTINCT_REAL_CASES")
    if not provenance_all_pass:
        blockers.append("CASE_REPRODUCTION_FAILURE")
    if not quality_all_pass:
        blockers.append("STRUCTURAL_OR_VECTOR_QUALITY_FAILURE")
    blockers.append("HUMAN_VISUAL_REVIEW_REQUIRED")
    return {
        "schema": "sa10.33-crosscase-gate-v1",
        "case_count": len(cases),
        "distinct_source_count": len(seen_sha),
        "duplicate_source_count": duplicate_source_count,
        "crosscase_evidence_coverage": "PASS" if evidence_pass else "FAIL",
        "structural_quality": "PASS" if quality_all_pass else "FAIL",
        "cases": output,
        "hard_blockers": blockers,
        "human_visual_review": "PENDING",
        "promotion_authorized": False,
        "status": "RESEARCH_COMPLETE_NO_GO" if evidence_pass else "HOLD_INCOMPLETE_EVIDENCE",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--case", action="append", required=True,
                   help="case name=path_to_sa1033_evidence_json; repeat for >=2")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    cases = {}
    for arg in args.case:
        if "=" not in arg:
            raise ValueError("case must be name=path")
        name, raw = arg.split("=", 1)
        if not name.strip() or name in cases:
            raise ValueError("case name must be distinct and nonblank")
        cases[name] = json.loads(Path(raw).read_text(encoding="utf-8-sig"))
    report = aggregate_cases(cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["crosscase_evidence_coverage"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
