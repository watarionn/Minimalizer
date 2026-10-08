"""SA10.40 two real source image gate: raster-neutral Chrome improvement.

The real-positive GC001 coat pixel differences must decrease without
changed source material raster, off-owner drawing, or necktie. Juufuutei-
Raden remains an SHA-distinct unchanged negative control. This NEVER
makes the full-character SVG or geometry budget pass.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def decide(*, gc001: dict, raden: dict, audit: dict)->dict:
    if (gc001.get("schema")!="sa10.40-signed-browser-material-vertex-correction-v1"
        or raden.get("schema")!="sa10.37-topology-locked-apparel-geometry-v1"
        or audit.get("schema")!="sa10.39-signed-svg-residual-pixel-audit-v1"):
        raise ValueError("actual signed image records required")
    source=gc001.get("GC001_original_source_sha256")
    control=raden.get("case_source_sha256")
    if (
        not isinstance(source,str) or len(source)!=64
        or not isinstance(control,str) or len(control)!=64
        or source==control or audit.get("source_sha256")!=source
    ):
        raise ValueError("distinct source image SHA verification failed")
    old=gc001.get("baseline_attested_Chrome_mismatched_pixels")
    new=gc001.get("candidate_attested_Chrome_mismatched_pixels")
    if not isinstance(old,int) or not isinstance(new,int) or not (0<=new<old):
        raise ValueError("unattested or non-improving Chrome measurement")
    good_gc001=(
        old==45 and new<=42
        and gc001.get("strict_improvement_pixels")==old-new
        and gc001.get("signed_authoritative_source_material_canvas_changed_pixels")==0
        and gc001.get("original_canonical_CV2_raster_sha256")==gc001.get("candidate_canonical_CV2_raster_sha256")
        and gc001.get("source_material_vertex_count_unchanged") is True
        and gc001.get("new_geometric_paths_added")==0
        and gc001.get("source_owner_mask_exact_unchanged") is True
        and gc001.get("outside_owner_Chrome_RGB_byte_identical_to_prior") is True
        and gc001.get("outside_owner_Chrome_painted_pixels")==3
        and gc001.get("thin_green_necktie_rendered_pixels_byte_identical") is True
        and gc001.get("source_palette_and_existing_material_owner_unchanged") is True
        and gc001.get("new_face_eyes_nose_mouth_generated") is False
        and gc001.get("independent_signed_material_owner_audit")=="PASS"
        and gc001.get("real_browser_source_and_artifact_SHA_attested") is True
        and gc001.get("browser_exact_pixel_parity")=="FAIL"
        and gc001.get("production_promotion_authorized") is False
        and gc001.get("material_vertex_adjustment")=={
            "material_index":1,"vertex_index":1,"axis":"y","delta_px":.5,
        }
    )
    good_audit=(
        audit.get("chrome_different_rgb_pixels")==new
        and audit.get("chrome_executed_and_sha_attested") is True
        and audit.get("actual_source_owner_boundary_immutable") is True
        and audit.get("actual_five_material_subpaths_immutable") is True
        and audit.get("new_svg_geometry_created") is False
        and audit.get("different_color_on_jointly_painted_pixels",999)<=6
        and audit.get("source_owner_parent_boundary",{}).get("material_edge_only",999)<=27
        and audit.get("pixel_disagreement_outside_signed_owner")==3
        and audit.get("browser_svg_gate")=="FAIL"
        and audit.get("production_promotion_authorized") is False
    )
    good_control=(
        raden.get("status")=="NONMATCHING_CASE_NO_OP"
        and raden.get("Stage04_source_masks_verified") is True
        and raden.get("Stage08_outer_sha_verified") is True
        and raden.get("Stage36_material_provenance_verified") is True
        and raden.get("Stage36_original_RGB_pixel_replay_equal") is True
        and raden.get("face_left_right_arm_rgb_unchanged") is True
        and raden.get("existing_outer_primitive_count")==11
        and raden.get("apparel_subpaths_before")==0
        and raden.get("apparel_subpaths_after")==0
        and raden.get("baseline_source36_preview_sha256")==raden.get("candidate_preview_sha256")
        and raden.get("production_promotion_authorized") is False
    )
    result={
        "schema":"sa10.40-two-source-raster-neutral-material-research-v1",
        "source_sha256_GC001":source,
        "source_sha256_Raden":control,
        "GC001_real_browser_material_improvement_gate":"PASS" if good_gc001 else "FAIL",
        "GC001_independent_source_residual_audit_gate":"PASS" if good_audit else "FAIL",
        "Raden_unrelated_outfit_frozen_gate":"PASS" if good_control else "FAIL",
        "original_source_material_raster_changed_pixels":gc001.get("signed_authoritative_source_material_canvas_changed_pixels"),
        "before_chrome_mismatched_pixels":old,
        "after_chrome_mismatched_pixels":new,
        "material_only_edge_mismatches_after":audit.get("source_owner_parent_boundary",{}).get("material_edge_only"),
        "outside_owner_draw_diff_regression_detected":not gc001.get("outside_owner_Chrome_RGB_byte_identical_to_prior",False),
        "new_svg_shapes_added":gc001.get("new_geometric_paths_added"),
        "original_five_color_plane_27_vertex_count_unchanged":good_gc001,
        "research_gate":"PASS" if good_gc001 and good_audit and good_control else "FAIL",
        "SVG_browser_exact_pixel_parity":"FAIL",
        "production_promotion_authorized":False,
        "outstanding_release_blockers":[
            "CHROME_SVG_REFERENCE_STILL_DIFFERING_PIXELS",
            "INHERITED_TOTAL_VECTOR_VERTEX_BUDGET_FAIL",
            "COMPLETE_CHARACTER_CHROME_OWNER_ZORDER_NOT_VALIDATED",
            "SECOND_INDEPENDENT_POSITIVE_GARMENT_NOT_VALIDATED",
            "HUMAN_ART_REVIEW_REQUIRED",
        ],
    }
    return result


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--gc001",required=True,type=Path)
    p.add_argument("--raden",required=True,type=Path)
    p.add_argument("--audit",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    result=decide(gc001=json.loads(a.gc001.read_text("utf-8-sig")),
                  raden=json.loads(a.raden.read_text("utf-8-sig")),
                  audit=json.loads(a.audit.read_text("utf-8-sig")))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["research_gate"]!="PASS":
        raise SystemExit(2)


if __name__=="__main__":
    main()
