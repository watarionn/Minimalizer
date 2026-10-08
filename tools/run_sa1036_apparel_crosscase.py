"""SA10.36 cross-character material correction, fail-closed research gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "sa10.36-uniform-material-benchmark-v1"
EXPECTED = ["dark_uniform", "dark_uniform", "white_shirt", "white_shirt", "green_necktie"]


def aggregate_real_material_cases(cases: dict[str, dict]) -> dict:
    if len(cases) < 2:
        raise ValueError("two real independent character sources required")
    sources = set()
    reports = {}
    changed = 0
    skipped = 0
    failures = []
    for name, metrics in sorted(cases.items()):
        if metrics.get("schema") != SCHEMA:
            raise ValueError(f"unsupported metrics schema: {name}")
        source = metrics.get("source_sha256")
        if not isinstance(source, str) or len(source) != 64 or source in sources:
            raise ValueError(f"invalid or duplicate source hash: {name}")
        sources.add(source)
        guarded = (
            metrics.get("stage04_mask_sha256_verified") is True
            and metrics.get("phase8_and_phase9_lineage_verified") is True
            and metrics.get("phase9_baseline_pixels_exact") is True
            and metrics.get("original_outer_silhouette_frozen") is True
            and metrics.get("original_outer_topology_pass") is True
            and metrics.get("face_and_both_arms_pixel_exact") is True
            and metrics.get("pixels_changed_outside_source_owner") == 0
            and metrics.get("original_outer_primitives_count") == 11
            and metrics.get("total_filled_geometric_element_estimate") ==
            (metrics.get("original_outer_primitives_count", 0)
             + metrics.get("phase9_existing_subpaths", 0)
             + metrics.get("material_subpaths_added", 0))
            and metrics.get("production_promotion_authorized") is False
            and metrics.get("browser_svg_owner_clip_verified") is False
            and metrics.get("human_visual_review") == "PENDING"
        )
        if metrics.get("research_status") == "GRAY_BLOCK_REPLACED_RESEARCH_HOLD":
            changed += 1
            measured = (
                metrics.get("apparel_materials") == EXPECTED
                and metrics.get("material_subpaths_added") == 5
                and metrics.get("lower_body_source_lab_mse_gain", 0) >= 0.20
                and metrics.get("gray_block_largest_connected_after_px", 0)
                < 0.20 * metrics.get("gray_block_largest_connected_before_px", 0)
                and metrics.get("green_tie_panel_area_pixels", 0)
                <= 1.10 * metrics.get("source_green_tie_pixels", -1)
                and metrics.get("source_green_tie_pixels", 0) > 0
                and metrics.get("material_extra_vertices", 10000) <= 80
            )
            guarded &= measured
        elif metrics.get("research_status") == "PATTERN_NOT_DETECTED_HOLD":
            skipped += 1
            guarded &= (
                metrics.get("material_subpaths_added") == 0
                and metrics.get("apparel_materials") == []
                and metrics.get("lower_body_source_lab_mse_gain") == 0
                and metrics.get("baseline_image_sha256") == metrics.get("candidate_image_sha256")
                and metrics.get("gray_block_largest_connected_before_px") ==
                    metrics.get("gray_block_largest_connected_after_px")
            )
        else:
            guarded = False
        if not guarded:
            failures.append(name)
        reports[name] = {
            "research_gate": "PASS" if guarded else "FAIL",
            "status": metrics.get("research_status"),
            "added_material_subpaths": metrics.get("material_subpaths_added"),
            "owner_lab_mse_gain": metrics.get("lower_body_source_lab_mse_gain"),
            "gray_block_largest_before_after": [
                metrics.get("gray_block_largest_connected_before_px"),
                metrics.get("gray_block_largest_connected_after_px"),
            ],
            "tie_source_and_painted_area": [
                metrics.get("source_green_tie_pixels"),
                metrics.get("green_tie_panel_area_pixels"),
            ],
        }
    pass_flag = bool(not failures and changed >= 1 and skipped >= 1)
    return {
        "schema": "sa10.36-two-source-material-review-v1",
        "cases": reports,
        "source_count": len(sources),
        "material_changed_real_cases": changed,
        "nonmatching_cases_unchanged": skipped,
        "research_gate": "PASS" if pass_flag else "FAIL",
        "failed_cases": failures,
        "core_geometric_budget_still_failed": True,
        "browser_svg_clip_path_verified": False,
        "human_visual_review": "PENDING",
        "production_promotion_authorized": False,
        "status": "MATERIAL_RESEARCH_COMPLETE_PRODUCTION_HOLD" if pass_flag else "HOLD_INCOMPLETE_EVIDENCE",
        "blockers": [
            "EXISTING_GEOMETRIC_VERTEX_BUDGET_FAILED",
            "BROWSER_SVG_CLIPPING_NOT_VERIFIED",
            "HUMAN_VISUAL_APPROVAL_MISSING",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append", required=True, help="Name=metrics.json")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    cases = {}
    for item in args.case:
        if "=" not in item:
            raise ValueError("expected Name=path")
        name, path = item.split("=", 1)
        if not name.strip() or name in cases:
            raise ValueError("invalid case key")
        cases[name] = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    report = aggregate_real_material_cases(cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["research_gate"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
