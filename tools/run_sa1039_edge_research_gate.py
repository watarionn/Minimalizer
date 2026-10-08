"""SA10.39 strictly nonregressing, source-bound Chrome research gate.

The parent silhouette matters MORE than total pixel loss. A broad parent
outline got 56 mismatch pixels but expanded off-owner painted pixels from
3 to 22; this gate rejects that regression. It accepts only evidence-backed
source-top-segment strokes with unchanged exterior paint safety.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SVG_SCHEMA="sa10.38-source-contour-vector-mask-browser-v1"
AUDIT_SCHEMA="sa10.39-signed-svg-residual-pixel-audit-v1"
RADEN_SCHEMA="sa10.37-topology-locked-apparel-geometry-v1"
SCHEMA="sa10.39-two-source-selective-top-boundary-research-v1"


def decide(*, prior:dict, prior_audit:dict, current:dict, audit:dict, raden:dict)->dict:
    if prior.get("schema")!=SVG_SCHEMA or current.get("schema")!=SVG_SCHEMA:
        raise ValueError("two source-signed real Chrome SVG measurements required")
    if (audit.get("schema")!=AUDIT_SCHEMA or prior_audit.get("schema")!=AUDIT_SCHEMA
        or raden.get("schema")!=RADEN_SCHEMA):
        raise ValueError("both signed residual attribution reports and independent source required")
    source=prior.get("source_sha256")
    control=raden.get("case_source_sha256")
    if (
        not isinstance(source,str) or len(source)!=64
        or not isinstance(control,str) or len(control)!=64
        or source==control or current.get("source_sha256")!=source
        or audit.get("source_sha256")!=source or prior_audit.get("source_sha256")!=source
    ):
        raise ValueError("source identity not proven from two independent input images")
    old=prior.get("browser_mismatched_rgb_pixels")
    new=current.get("browser_mismatched_rgb_pixels")
    if not isinstance(old,int) or not isinstance(new,int) or not (0<=new<old):
        raise ValueError("invalid or unimproved real-Chrome pixel counts")
    if prior_audit.get("chrome_different_rgb_pixels")!=old or audit.get("chrome_different_rgb_pixels")!=new:
        raise ValueError("source-bound pixel audits and browser measurements disagree")
    for record in (prior,current):
        if (record.get("chrome_execution_provenance_verified") is not True
            or record.get("browser_screenshot_verified") is not True
            or record.get("source_bitmap_or_base64_raster_embedded") is not False
            or record.get("production_promotion_authorized") is not False
            or record.get("isolated_material_layer_only_not_full_scene") is not True):
            raise ValueError("real browser attestation or non-generative research contract broken")
    improvement=(old-new)/old
    source_structure=(
        current.get("outer_vector_sha256")==prior.get("outer_vector_sha256")
        and current.get("simplified_apparel_sha256")==prior.get("simplified_apparel_sha256")
        and current.get("signed_original_primitive_count")==prior.get("signed_original_primitive_count")==11
        and current.get("svg_apparel_filled_subpath_count")==prior.get("svg_apparel_filled_subpath_count")==5
        and current.get("svg_apparel_polygon_vertices")==prior.get("svg_apparel_polygon_vertices")==27
        and current.get("degenerate_source_rings_proven_raster_neutral") is True
        and current.get("degenerate_removal_changed_owner_pixels")==0
        and current.get("added_hole_boundary_svg_stroke_paint_passes_are_counted") is True
        and current.get("svg_mask_hole_boundary_stroke_paths")==prior.get("svg_mask_hole_boundary_stroke_paths")==5
        # Whole-parent thick strokes made source silhouette worse. Forbidden.
        and current.get("svg_parent_outline_stroke_paint_passes")==0
        and current.get("svg_parent_outline_stroke_px")==0
        # Two horizontal edges are truly existing topmost signed source rings.
        and current.get("svg_signed_top_edge_stroke_px",0)>0
        and current.get("svg_signed_top_edge_top_row_exact_replay_verified") is True
        and current.get("svg_signed_top_edge_count")==2
        and current.get("svg_signed_top_edge_reused_endpoint_occurrences")==4
        and current.get("svg_signed_top_edge_paint_passes_are_counted") is True
        and len(current.get("svg_signed_top_edge_source_segments",[]))==2
    )
    comparable_audit=(
        prior_audit.get("signed_outer_vector_sha256")==current.get("outer_vector_sha256")
        and audit.get("signed_outer_vector_sha256")==current.get("outer_vector_sha256")
        and prior_audit.get("signed_material_scene_sha256")==current.get("simplified_apparel_sha256")
        and audit.get("signed_material_scene_sha256")==current.get("simplified_apparel_sha256")
        and prior_audit.get("chrome_executed_and_sha_attested") is True
        and audit.get("chrome_executed_and_sha_attested") is True
        and audit.get("actual_source_owner_boundary_immutable") is True
        and audit.get("actual_five_material_subpaths_immutable") is True
        and audit.get("new_svg_geometry_created") is False
        and audit.get("production_promotion_authorized") is False
        and sum(audit.get("source_owner_parent_boundary",{}).values())==new
        and audit.get("occupancy_differences",0)+audit.get("different_color_on_jointly_painted_pixels",0)==new
        and audit.get("browser_svg_gate")==current.get("browser_svg_gate")
        and prior_audit.get("pixel_disagreement_outside_signed_owner") is not None
        and audit.get("pixel_disagreement_outside_signed_owner") is not None
        # Do not trade improved RGB MSE for worse silhouette ownership!
        and audit["pixel_disagreement_outside_signed_owner"]
            <=prior_audit["pixel_disagreement_outside_signed_owner"]
        and audit.get("different_color_on_jointly_painted_pixels",999)
            <=prior_audit.get("different_color_on_jointly_painted_pixels",-1)
        and audit.get("mismatch_y_row_245")==0
    )
    control_ok=(
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
    passes=source_structure and comparable_audit and control_ok and improvement>0.20
    return {
        "schema":SCHEMA,
        "GC001_original_sha256":source,
        "Raden_distinct_original_sha256":control,
        "prior_browser_pixel_mismatch_count":old,
        "current_browser_pixel_mismatch_count":new,
        "pixel_mismatch_improvement_over_SA1038":round(improvement,6),
        "pixel_mismatch_improvement_over_SA1037":round((528-new)/528,6),
        "prior_off_owner_mismatched_pixels":prior_audit.get("pixel_disagreement_outside_signed_owner"),
        "current_off_owner_mismatched_pixels":audit.get("pixel_disagreement_outside_signed_owner"),
        "source_silhouette_ownership_not_worsened":(
            audit.get("pixel_disagreement_outside_signed_owner",10**9)
            <=prior_audit.get("pixel_disagreement_outside_signed_owner",-1)
        ),
        "remaining_occupancy_boundary_errors":audit.get("occupancy_differences"),
        "remaining_jointly_painted_color_boundary_errors":audit.get("different_color_on_jointly_painted_pixels"),
        "existing_signed_top_edge_stroke_passes_counted":current.get("svg_signed_top_edge_count"),
        "existing_signed_top_edge_reused_endpoints_counted":current.get("svg_signed_top_edge_reused_endpoint_occurrences"),
        "signed_existing_geometry_and_materials_unchanged":source_structure,
        "independent_before_after_residual_pixel_audit_passed":comparable_audit,
        "Raden_unrelated_outfit_noop_gate":control_ok,
        "full_browser_exact_pixel_parity":"PASS" if new==0 else "FAIL",
        "research_gate":"PASS" if passes else "FAIL",
        "status":"SOURCE_TOP_EDGE_GEOMETRY_CLEANUP_RESEARCH_PASS_NO_GO" if passes else "HOLD_SOURCE_SILHOUETTE_OR_PIXEL_REGRESSION",
        "production_promotion_authorized":False,
        "unresolved_release_blockers":[
            "BROWSER_EXACT_PIXEL_PARITY_FAIL" if new else "",
            "OUTER_SOURCE_VECTOR_BUDGET_FAIL",
            "COMBINED_OUTER_AND_INTERIOR_GEOMETRY_BUDGET_FAIL",
            "FULL_CHARACTER_CHROME_RENDER_UNVERIFIED",
            "SECOND_MATCHING_GARMENT_IMAGE_MISSING",
            "HUMAN_VISUAL_APPROVAL_PENDING",
        ],
    }


def main()->None:
    p=argparse.ArgumentParser()
    for name in ("prior","prior_audit","current","audit","raden"):
        p.add_argument("--"+name.replace("_","-"),required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    result=decide(**{
        key:json.loads(getattr(args,key).read_text(encoding="utf-8-sig"))
        for key in ("prior","prior_audit","current","audit","raden")
    })
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["research_gate"]!="PASS":
        raise SystemExit(2)


if __name__=="__main__":
    main()
