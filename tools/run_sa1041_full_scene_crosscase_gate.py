"""SA10.41 cross-character whole-figure research evaluation, not a release gate.

The research stage completes when two real, SHA-distinct scenes reconstruct
source RGB exactly and are actually rendered by Chrome. This evidence
explicitly *fails* the product pixel/topology/vertex/protected-part gates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def decide(*, gc001:dict,raden:dict)->dict:
    for name,data in (("GC001",gc001),("Raden",raden)):
        if data.get("schema")!="sa10.41-source-signed-full-character-browser-research-v1":
            raise ValueError(f"{name} is not a signed complete-character scene")
        if (data.get("saved_stage9_candidate_pixel_equal") is not True
            or data.get("saved_stage37_full_preview_pixel_equal") is not True
            or data.get("source_stage8_owner_order_unchanged") is not True
            or data.get("source_immutable_face_and_both_arms") is not True
            or data.get("source_apparel_pixels_changed_outside_visible_lower_body")!=0
            or data.get("source_raster_pixels_embedded") is not False
            or data.get("original_face_feature_geometry_added") is not False
            or data.get("all_generated_elements_geometric_svg") is not True
            or data.get("svg_protected_mask_geometry_counted") is not True
            or data.get("svg_flat_face_guard_original_stage04_mask_counted") is not True
            or data.get("all_original_vertex_and_mask_complexity_counted") is not True
            or data.get("production_promotion_authorized") is not False):
            raise ValueError(f"{name} violates protected non-generative stage41 source contract")
        if data.get("full_scene_chrome_executed") is not True or data.get(
            "real_chrome_full_character_execute_verified"
        ) is not True:
            raise ValueError(f"{name} has no actual browser-rendering execution")
        if data.get("original_source_primitive_records")!=11 or data.get(
            "source_owner_rendered_count"
        )!=10 or data.get("full_scene_chrome_exact_rgb_parity")!="FAIL":
            raise ValueError(f"{name} must retain all original owner geometry and genuine browser mismatch")
        if data.get("original_source_ring_vertex_budget_pass") is not False or data.get(
            "combined_source_geometry_budget_pass"
        ) is not False:
            raise ValueError(f"{name} inherited geometry budget must not be relaxed")
        for k in ("original_source_sha256","screenshot_sha256","chrome_executable_sha256",
                  "html_sha256","svg_sha256","original_stage37_preview_sha256"):
            val=data.get(k)
            if not isinstance(val,str) or len(val)!=64:
                raise ValueError(f"{name} browser/source SHA evidence incomplete: {k}")
        if data.get("true_full_scene_browser_exact_RGB_parity")!="FAIL" or data.get(
            "full_character_face_and_arm_browser_parity"
        )!="FAIL":
            raise ValueError(f"{name} must report actual failed browser/protected pixel parity")
        if data.get("full_scene_RGB_mismatched_pixels",0)<=0:
            raise ValueError(f"{name} real browser mismatch missing")
        parts=data.get("full_scene_protected_semantic_parts",{})
        if set(parts)!={"face","left_arm","right_arm"} or any(
            not isinstance(parts[key].get("chrome_different_rgb_pixels_in_source_mask"),int)
            or parts[key]["chrome_different_rgb_pixels_in_source_mask"]<=0
            for key in ("face","left_arm","right_arm")
        ):
            raise ValueError(f"{name} protection audit incomplete")
    a=gc001.get("original_source_sha256")
    b=raden.get("original_source_sha256")
    if a==b:
        raise ValueError("two independent original source image SHA required")
    if (gc001.get("phase9_interior_filled_subpaths")!=3
        or gc001.get("phase37_apparel_filled_subpaths")!=5
        or gc001.get("phase37_apparel_polygon_vertices")!=27
        or gc001.get("stage37_no_apparel_negative_control") is not False
        or raden.get("phase9_interior_filled_subpaths")!=1
        or raden.get("phase37_apparel_filled_subpaths")!=0
        or raden.get("stage37_no_apparel_negative_control") is not True):
        raise ValueError("full owner/material positive vs unrelated negative control mutated")
    for data in (gc001,raden):
        if data["original_source_ring_vertices_including_support"]<=data["original_source_ring_vertex_budget_limit"]:
            raise ValueError("source ring budget evidence contradictory")
        if data["combined_mask_vector_source_vertex_occurrences_counted"]<=data["original_source_ring_vertex_budget_limit"]:
            raise ValueError("unaccounted additional SVG mask geometry")
    return {
        "schema":"sa10.41-two-character-full-svg-browser-research-v1",
        "original_image_count":2,
        "distinct_source_sha_verified":True,
        "source_rebuilt_full_RGB_pixel_exact_for_both":True,
        "both_real_headless_Chrome_full_character_runs_attested":True,
        "source_11_owner_back_to_front_and_flat_face_policy_retained":True,
        "new_eyes_nose_mouth_generated":False,
        "no_svg_source_bitmap_overlay":True,
        "GC001":{
            "source_sha256":a,
            "original_source_ring_vertices":gc001["original_source_ring_vertices_including_support"],
            "original_ring_budget_limit":gc001["original_source_ring_vertex_budget_limit"],
            "combined_vertex_occurrences":gc001["combined_mask_vector_source_vertex_occurrences_counted"],
            "micro_contour_count":gc001["source_topological_degenerate_ring_count"],
            "stage9_planes":3,
            "apparel_planes":5,
            "full_scene_RGB_differing_pixels":gc001["full_scene_RGB_mismatched_pixels"],
            "original_face_wrong_pixels":gc001["full_scene_protected_semantic_parts"]["face"]["chrome_different_rgb_pixels_in_source_mask"],
            "left_arm_wrong_pixels":gc001["full_scene_protected_semantic_parts"]["left_arm"]["chrome_different_rgb_pixels_in_source_mask"],
            "right_arm_wrong_pixels":gc001["full_scene_protected_semantic_parts"]["right_arm"]["chrome_different_rgb_pixels_in_source_mask"],
        },
        "Raden":{
            "source_sha256":b,
            "original_source_ring_vertices":raden["original_source_ring_vertices_including_support"],
            "original_ring_budget_limit":raden["original_source_ring_vertex_budget_limit"],
            "combined_vertex_occurrences":raden["combined_mask_vector_source_vertex_occurrences_counted"],
            "micro_contour_count":raden["source_topological_degenerate_ring_count"],
            "stage9_planes":1,
            "apparel_planes":0,
            "full_scene_RGB_differing_pixels":raden["full_scene_RGB_mismatched_pixels"],
            "original_face_wrong_pixels":raden["full_scene_protected_semantic_parts"]["face"]["chrome_different_rgb_pixels_in_source_mask"],
            "left_arm_wrong_pixels":raden["full_scene_protected_semantic_parts"]["left_arm"]["chrome_different_rgb_pixels_in_source_mask"],
            "right_arm_wrong_pixels":raden["full_scene_protected_semantic_parts"]["right_arm"]["chrome_different_rgb_pixels_in_source_mask"],
        },
        "research_evidence_gate":"PASS",
        "full_character_browser_exact_RGB_parity_gate":"FAIL",
        "source_protected_face_left_right_arm_browser_gate":"FAIL",
        "original_and_combined_vertex_budget_gate":"FAIL",
        "second_positive_five_panel_garment_gate":"NOT_TESTED",
        "human_visual_review":"PENDING",
        "production_promotion_authorized":False,
        "release_blockers":[
            "GC001_FULL_CHARACTER_CHROME_RGB_PIXEL_PARITY_FAIL",
            "RADEN_FULL_CHARACTER_CHROME_RGB_PIXEL_PARITY_FAIL",
            "FACE_LEFT_RIGHT_ARM_BROWSER_BOUNDARY_PARITY_FAIL",
            "ORIGINAL_CONTOUR_AND_COMBINED_SVG_VERTEX_BUDGET_FAIL",
            "SECOND_INDEPENDENT_POSITIVE_FIVE_PLANE_APPAREL_IMAGE_MISSING",
            "HUMAN_VISUAL_APPROVAL_MISSING",
        ],
    }


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--gc001",type=Path,required=True)
    p.add_argument("--raden",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=decide(gc001=json.loads(a.gc001.read_text(encoding="utf-8-sig")),
                  raden=json.loads(a.raden.read_text(encoding="utf-8-sig")))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["research_evidence_gate"]!="PASS":
        raise SystemExit(2)


if __name__=="__main__":
    main()
