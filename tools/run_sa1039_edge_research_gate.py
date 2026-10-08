"""SA10.39 real-Chrome incremental geometric boundary quality gates.

Measure change from the *signed* SA10.38 69px Chrome baseline to SA10.39,
require independently verified source/material SHA, no other-character edits,
and count every added stroke pass. A research PASS is never product release.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SVG_SCHEMA="sa10.38-source-contour-vector-mask-browser-v1"
AUDIT_SCHEMA="sa10.39-signed-svg-residual-pixel-audit-v1"
RADEN_SCHEMA="sa10.37-topology-locked-apparel-geometry-v1"
SCHEMA="sa10.39-two-source-edge-correction-research-v1"


def decide(*, prior:dict, current:dict, audit:dict, raden:dict)->dict:
    if prior.get("schema")!=SVG_SCHEMA or current.get("schema")!=SVG_SCHEMA:
        raise ValueError("two source-signed real Chrome SVG measurements required")
    if audit.get("schema")!=AUDIT_SCHEMA or raden.get("schema")!=RADEN_SCHEMA:
        raise ValueError("missing residual attribution and independent untouched character")
    source=prior.get("source_sha256")
    control=raden.get("case_source_sha256")
    if (not isinstance(source,str) or len(source)!=64 or
        not isinstance(control,str) or len(control)!=64 or source==control or
        current.get("source_sha256")!=source or audit.get("source_sha256")!=source):
        raise ValueError("cross-source provenance mismatch or duplicate")
    old=prior.get("browser_mismatched_rgb_pixels")
    new=current.get("browser_mismatched_rgb_pixels")
    if not isinstance(old,int) or not isinstance(new,int) or not (0<=new<old):
        raise ValueError("missing independently improved real browser pixel evidence")
    if audit.get("chrome_different_rgb_pixels")!=new:
        raise ValueError("pixel cluster diagnostic and real Chrome gate disagree")
    for record in (prior,current):
        if (record.get("chrome_execution_provenance_verified") is not True
            or record.get("browser_screenshot_verified") is not True
            or record.get("source_bitmap_or_base64_raster_embedded") is not False
            or record.get("production_promotion_authorized") is not False
            or record.get("isolated_material_layer_only_not_full_scene") is not True):
            raise ValueError("source/real Chrome attestation or release hold missing")
    improved=(old-new)/old
    geometry_constraints=(
        current.get("outer_vector_sha256")==prior.get("outer_vector_sha256")
        and current.get("simplified_apparel_sha256")==prior.get("simplified_apparel_sha256")
        and current.get("svg_apparel_filled_subpath_count")==prior.get("svg_apparel_filled_subpath_count")==5
        and current.get("svg_apparel_polygon_vertices")==prior.get("svg_apparel_polygon_vertices")==27
        and current.get("signed_original_primitive_count")==prior.get("signed_original_primitive_count")==11
        and current.get("degenerate_source_rings_proven_raster_neutral") is True
        and current.get("degenerate_removal_changed_owner_pixels")==0
        and current.get("added_hole_boundary_svg_stroke_paint_passes_are_counted") is True
        and current.get("svg_mask_hole_boundary_stroke_paths")==prior.get("svg_mask_hole_boundary_stroke_paths")==5
        and current.get("svg_parent_outline_stroke_paint_passes")==1
        and current.get("svg_parent_outline_stroke_px",0)>0
        and current.get("svg_parent_outline_extra_stroke_counted") is True
        and current.get("svg_parent_outline_reused_ring_point_occurrences")==current.get("source_owner_svg_mask_ring_vertices")
    )
    audit_constraints=(
        audit.get("signed_outer_vector_sha256")==current.get("outer_vector_sha256")
        and audit.get("signed_material_scene_sha256")==current.get("simplified_apparel_sha256")
        and audit.get("actual_source_owner_boundary_immutable") is True
        and audit.get("actual_five_material_subpaths_immutable") is True
        and audit.get("chrome_executed_and_sha_attested") is True
        and audit.get("new_svg_geometry_created") is False
        and audit.get("production_promotion_authorized") is False
        and sum(audit.get("source_owner_parent_boundary",{}).values())==new
        and audit.get("occupancy_differences",0)+audit.get("different_color_on_jointly_painted_pixels",0)==new
        and audit.get("browser_svg_gate")==current.get("browser_svg_gate")
    )
    control_constraints=(
        raden.get("status")=="NONMATCHING_CASE_NO_OP"
        and raden.get("Stage04_source_masks_verified") is True
        and raden.get("Stage08_outer_sha_verified") is True
        and raden.get("Stage36_material_provenance_verified") is True
        and raden.get("face_left_right_arm_rgb_unchanged") is True
        and raden.get("existing_outer_primitive_count")==11
        and raden.get("apparel_subpaths_before")==raden.get("apparel_subpaths_after")==0
        and raden.get("candidate_preview_sha256")==raden.get("baseline_source36_preview_sha256")
        and raden.get("production_promotion_authorized") is False
    )
    passes=geometry_constraints and audit_constraints and control_constraints and improved>0.10
    blockers=[
        "BROWSER_SVG_EXACT_PIXEL_PARITY_FAIL" if new else "",
        "OUTER_AND_COMBINED_GEOMETRY_VERTEX_BUDGET_FAIL",
        "FULL_CHARACTER_CHROME_RENDER_NOT_VERIFIED",
        "SECOND_MATCHING_UNIFORM_IMAGE_NOT_VERIFIED",
        "HUMAN_ART_REVIEW_PENDING",
    ]
    return {
        "schema":SCHEMA,
        "gc001_source_sha256":source,
        "raden_distinct_source_sha256":control,
        "signed_chrome_previous_mismatch_pixels":old,
        "signed_chrome_candidate_mismatch_pixels":new,
        "chrome_pixel_disagreement_improvement_from_previous":round(improved,6),
        "chrome_pixel_disagreement_improvement_from_sa1037":round((528-new)/528,6),
        "remaining_occupancy_boundary_errors":audit.get("occupancy_differences"),
        "remaining_jointly_painted_color_boundary_errors":audit.get("different_color_on_jointly_painted_pixels"),
        "additional_source_parent_outline_stroke_paint_passes":current.get("svg_parent_outline_stroke_paint_passes"),
        "additional_source_parent_contour_point_occurrences_counted":current.get("svg_parent_outline_reused_ring_point_occurrences"),
        "source_owner_and_material_shape_sha_unchanged":geometry_constraints,
        "independent_residual_geometry_audit_passed":audit_constraints,
        "independent_raden_control_unchanged":control_constraints,
        "real_chrome_browser_exact_pixel_gate":"PASS" if new==0 else "FAIL",
        "research_gate":"PASS" if passes else "FAIL",
        "research_status":"SA1039_EDGE_ATTRIBUTION_AND_CHROME_IMPROVEMENT_VERIFIED_NO_GO" if passes else "HOLD_INCOMPLETE",
        "production_promotion_authorized":False,
        "release_blockers":[item for item in blockers if item],
    }


def main()->None:
    p=argparse.ArgumentParser()
    for item in ("prior","current","audit","raden"):
        p.add_argument("--"+item,type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=decide(**{
        key:json.loads(getattr(args,key).read_text(encoding="utf-8-sig"))
        for key in ("prior","current","audit","raden")
    })
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["research_gate"]!="PASS":
        raise SystemExit(2)


if __name__=="__main__":
    main()
