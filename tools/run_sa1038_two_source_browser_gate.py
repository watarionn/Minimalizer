"""SA10.38 independently sourced Chrome SVG improvement vs unaffected control.

A research benchmark PASS means that the real browser SVG pixel discrepancy
was measurably reduced, NOT that exact browser parity or production quality
passed. Never lower original geometry/source-topology budgets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SVG_SCHEMA="sa10.38-source-contour-vector-mask-browser-v1"
RADEN_SCHEMA="sa10.37-topology-locked-apparel-geometry-v1"
PREVIOUS_CHROME_MISMATCH=528


def evaluate_research(
    *, gc001: dict, raden: dict, previous_chrome_mismatch: int=PREVIOUS_CHROME_MISMATCH,
) -> dict:
    if not isinstance(previous_chrome_mismatch,int) or previous_chrome_mismatch<1:
        raise ValueError("baseline Chrome mismatch must be a verified positive integer")
    if gc001.get("schema")!=SVG_SCHEMA or raden.get("schema")!=RADEN_SCHEMA:
        raise ValueError("source-specific evidence schema mismatch")
    sha_a=gc001.get("source_sha256")
    sha_b=raden.get("case_source_sha256")
    if (
        not isinstance(sha_a,str) or len(sha_a)!=64
        or not isinstance(sha_b,str) or len(sha_b)!=64
        or sha_a==sha_b
    ):
        raise ValueError("two independent original character source hashes required")
    diff=gc001.get("browser_mismatched_rgb_pixels")
    heavy=gc001.get("browser_mismatched_rgb_pixels_strong_gt48")
    if not isinstance(diff,int) or not isinstance(heavy,int) or diff<0 or heavy<0 or heavy>diff:
        raise ValueError("real browser pixel evidence missing")
    color_improvement=1-diff/previous_chrome_mismatch
    gc001_pass=(
        gc001.get("chrome_execution_provenance_verified") is True
        and gc001.get("browser_screenshot_verified") is True
        and gc001.get("degenerate_source_rings_proven_raster_neutral") is True
        and gc001.get("degenerate_removal_changed_owner_pixels")==0
        and gc001.get("source_bitmap_or_base64_raster_embedded") is False
        and gc001.get("svg_mask_hole_boundary_stroke_paths")==5
        and gc001.get("added_hole_boundary_svg_stroke_paint_passes_are_counted") is True
        and gc001.get("svg_apparel_filled_subpath_count")==5
        and gc001.get("svg_apparel_polygon_vertices")==27
        and gc001.get("signed_original_primitive_count")==11
        and gc001.get("isolated_material_layer_only_not_full_scene") is True
        and gc001.get("exact_browser_opencv_pixel_parity") is False
        and gc001.get("browser_svg_gate")=="FAIL"
        and 0<diff<previous_chrome_mismatch
        and color_improvement>=0.80
        and gc001.get("production_promotion_authorized") is False
    )
    raden_pass=(
        raden.get("status")=="NONMATCHING_CASE_NO_OP"
        and raden.get("Stage04_source_masks_verified") is True
        and raden.get("Stage08_outer_sha_verified") is True
        and raden.get("Stage36_material_provenance_verified") is True
        and raden.get("Stage36_original_RGB_pixel_replay_equal") is True
        and raden.get("face_left_right_arm_rgb_unchanged") is True
        and raden.get("existing_outer_primitive_count")==11
        and raden.get("apparel_subpaths_before")==0
        and raden.get("apparel_subpaths_after")==0
        and raden.get("candidate_preview_sha256")==raden.get("baseline_source36_preview_sha256")
        and raden.get("production_promotion_authorized") is False
    )
    complete=gc001_pass and raden_pass
    return {
        "schema":"sa10.38-two-source-browser-research-gate-v1",
        "source_count":2,
        "source_sha256":{"GC001":sha_a,"Juufuutei-Raden":sha_b},
        "GC001_attested_real_browser_research":"PASS" if gc001_pass else "FAIL",
        "Raden_unrelated_outfit_unchanged":"PASS" if raden_pass else "FAIL",
        "previous_signed_chrome_differing_pixels":previous_chrome_mismatch,
        "current_attested_chrome_differing_pixels":diff,
        "chrome_strong_different_pixels":heavy,
        "browser_mismatch_reduction_ratio":round(color_improvement,6),
        "one_source_micro_hole_raster_neutral_proved":gc001.get("degenerate_source_rings_proven_raster_neutral") is True,
        "five_source_hole_boundary_stroke_passes_accounted":gc001.get("svg_mask_hole_boundary_stroke_paths")==5,
        "isolated_apparel_svg_exact_pixel_parity":"FAIL",
        "research_gate":"PASS" if complete else "FAIL",
        "research_status":"SA1038_CHROME_DELTA_REDUCTION_VERIFIED_NO_GO" if complete else "HOLD_RESEARCH",
        "production_promotion_authorized":False,
        "release_blockers":[
            "REAL_CHROME_SVG_EXACT_PIXEL_PARITY_FAIL",
            "ORIGINAL_AND_COMBINED_VERTEX_BUDGET_FAIL",
            "COMPLETE_CHARACTER_BROWSER_SCENE_NOT_VERIFIED",
            "HUMAN_VISUAL_REVIEW_PENDING",
        ],
    }


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--gc001",required=True,type=Path)
    p.add_argument("--raden",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    result=evaluate_research(
        gc001=json.loads(args.gc001.read_text(encoding="utf-8-sig")),
        raden=json.loads(args.raden.read_text(encoding="utf-8-sig")),
    )
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["research_gate"]!="PASS":
        raise SystemExit(2)


if __name__=="__main__":
    main()
