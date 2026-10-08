"""SA10.35 multi-source interior color research gates.

Coverage != production quality. Color differences are quantitative only; a human
must review artwork and the browser must validate SVG geometry and clipping.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "sa10.35-internal-color-evaluation-v1"


def evaluate_crosscase(cases: dict[str, dict]) -> dict:
    if len(cases) < 2:
        raise ValueError("minimum two distinct real-image cases required")
    sources: set[str] = set()
    output: dict[str, dict] = {}
    gated = True
    produced = False
    for case_name, record in sorted(cases.items()):
        if record.get("schema") != SCHEMA:
            raise ValueError(f"invalid interior evidence: {case_name}")
        sha = record.get("source_sha256")
        if not isinstance(sha, str) or len(sha) != 64:
            raise ValueError(f"source SHA256 absent: {case_name}")
        if sha in sources:
            raise ValueError(f"duplicate source image evidence: {case_name}")
        sources.add(sha)
        valid = (
            record.get("source_stage04_provenance_verified") is True
            and record.get("original_adaptive_preview_sha256_verified") is True
            and record.get("original_adaptive_preview_pixels_equal") is True
            and record.get("outer_raw_topology_gate") == "PASS"
            and record.get("external_geometry_changed") is False
            and record.get("face_and_both_arms_unchanged") is True
            and record.get("source_bitmap_painted") is False
            and record.get("observed_source_colors_only") is True
            and record.get("pixels_changed_outside_outer_silhouette") == 0
            and record.get("pixels_changed_outside_interior_subplanes") == 0
            and record.get("outer_primitive_count_before") == record.get("outer_primitive_count_after")
            and record.get("interior_subplane_count") == len(record.get("planes", []))
            and record.get("interior_subplane_count", 0) <= 3
            and record.get("new_geometric_subpaths_counted") == record.get("interior_subplane_count")
            and record.get("candidate_color_lab_mse_after", 0) <= record.get("candidate_color_lab_mse_before", -1)
            and record.get("production_promotion_authorized") is False
        )
        gated &= valid
        produced |= record.get("interior_subplane_count", 0) > 0
        output[case_name] = {
            "research_provenance_gate": "PASS" if valid else "FAIL",
            "outer_silhouette_iou": record.get("outer_silhouette_iou"),
            "outer_raw_topology_gate": record.get("outer_raw_topology_gate"),
            "interior_subplanes": record.get("interior_subplane_count"),
            "subpath_vertices": record.get("interior_subplane_vertices"),
            "colors_lab_mse_improvement": record.get("eligible_color_mse_improvement_ratio"),
            "owners": [p["owner"] for p in record.get("planes", [])],
            "face_and_arms_protected": record.get("face_and_both_arms_unchanged"),
            "original_vector_budget_pass": record.get("original_outer_vector_budget_pass"),
        }
    blockers: list[str] = []
    if not gated or not produced:
        blockers.append("RESEARCH_EVIDENCE_MISSING_OR_FAILED")
    if any(p.get("original_outer_vector_budget_pass") is not True for p in cases.values()):
        blockers.append("ORIGINAL_OUTER_GEOMETRY_VERTEX_BUDGET_FAIL")
    blockers.extend(["BROWSER_SVG_CLIP_PARITY_UNVERIFIED", "HUMAN_VISUAL_APPROVAL_PENDING"])
    return {
        "schema": "sa10.35-two-case-interior-research-v1",
        "case_count": len(cases),
        "distinct_source_count": len(sources),
        "reproducible_research_gate": "PASS" if gated and produced else "FAIL",
        "color_metrics_are_not_visual_quality": True,
        "case_results": output,
        "hard_blockers": blockers,
        "promotion_authorized": False,
        "status": "RESEARCH_INTERIOR_COMPLETE_NO_GO" if gated and produced else "HOLD_EVIDENCE",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--case", action="append", required=True, help="name=path_to_metrics.json")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    items = {}
    for entry in args.case:
        if "=" not in entry:
            raise ValueError("use name=path")
        name, path = entry.split("=", 1)
        if not name.strip() or name in items:
            raise ValueError("invalid or duplicate case name")
        items[name] = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    result = evaluate_crosscase(items)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["reproducible_research_gate"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
