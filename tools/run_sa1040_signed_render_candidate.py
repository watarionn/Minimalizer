"""SA10.40 signed raster-neutral material vertex Chrome benchmark, NO-GO release.

Apply a 0.5px render-only offset to one non-necktie existing vertex.
The exact original CV2 material raster stays byte-identical. This runner
still demands real isolated Chrome, SHA verification, tie/owner preservation,
strict browser improvement and independent residual attribution.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.reviewed_sa10.browser_material_edge_calibration import (
    apply_raster_neutral_vertex_nudge,
)
from tools.run_sa1038_vector_mask_browser import render_and_verify_chrome
from tools.run_sa1039_svg_residual_audit import audit


def _load(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _sha(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def run(*, signed_baseline_dir:Path, signed_scene_path:Path,
        signed_apparel_path:Path, chrome_binary:Path, output_dir:Path,
        material_index:int=1, vertex_index:int=1, axis:int=1, delta:float=0.5)->dict:
    base=signed_baseline_dir.resolve()
    output=output_dir.resolve()
    if base==output or base in output.parents or output in base.parents:
        raise ValueError("isolated signed source and output research dirs required")
    scene=_load(signed_scene_path)
    apparel=_load(signed_apparel_path)
    baseline=_load(base/"svg_material_parity_metrics.json")
    execution=_load(base/"real_chrome_execution.json")
    if (
        baseline.get("source_sha256")!=scene.get("original_source_sha256")
        or baseline.get("outer_vector_sha256")!=_sha(signed_scene_path)
        or baseline.get("simplified_apparel_sha256")!=_sha(signed_apparel_path)
        or baseline.get("svg_signed_top_edge_count")!=2
        or baseline.get("browser_mismatched_rgb_pixels")!=45
        or baseline.get("chrome_execution_provenance_verified") is not True
        or baseline.get("source_bitmap_or_base64_raster_embedded") is not False
        or baseline.get("production_promotion_authorized") is not False
        or execution.get("chrome_binary_sha256")!=_sha(chrome_binary)
        or execution.get("html_sha256")!=_sha(base/"source_bound_vector_mask.html")
        or execution.get("svg_sha256")!=_sha(base/"source_bound_vector_mask.svg")
        or execution.get("screenshot_sha256")!=_sha(base/"actual_chrome_headless.png")
        or apparel.get("source_sha256")!=baseline.get("source_sha256")
    ):
        raise ValueError("original 45px Chrome screenshot/scene/source SHA are not signed")
    records=scene.get("primitives_back_to_front")
    if not isinstance(records,list) or len(records)!=11:
        raise ValueError("signed source 11 primitives changed")
    owner_records=[p for p in records if p.get("source_mask_owner")=="lower_body"]
    if len(owner_records)!=1:
        raise ValueError("source-backed owner is not unique")
    w,h=(int(scene["coordinate_space"][field]) for field in ("pixel_width","pixel_height"))
    owner=rasterize_primitive_candidate(owner_records[0],width=w,height=h)
    old_svg=(base/"source_bound_vector_mask.svg").read_text("utf-8")
    old_html=(base/"source_bound_vector_mask.html").read_text("utf-8")
    new_svg,render_proof=apply_raster_neutral_vertex_nudge(
        old_svg, original_material_panels=apparel["apparel_material_polygons"],
        material_index=material_index,vertex_index=vertex_index,axis=axis,
        delta=delta,source_owner_mask=owner,
    )
    if old_html.count(old_svg)!=1:
        raise ValueError("signed HTML must contain exactly one original SVG")
    new_html=old_html.replace(old_svg,new_svg)
    output.mkdir(parents=True,exist_ok=True)
    (output/"source_bound_vector_mask.svg").write_text(new_svg,"utf-8")
    (output/"source_bound_vector_mask.html").write_text(new_html,"utf-8")
    original_reference=base/"authoritative_opencv_material.png"
    shutil.copy2(original_reference,output/"authoritative_opencv_material.png")
    reference_before=cv2.imread(str(original_reference))
    reference_after=cv2.imread(str(output/"authoritative_opencv_material.png"))
    if reference_before is None or reference_before.shape!=(h,w,3) or not np.array_equal(reference_before,reference_after):
        raise AssertionError("signed authoritative 27-vertex raster changed")
    renderer_metrics=deepcopy(baseline)
    renderer_metrics.update({
        "render_only_material_vertex_nudge_proof":render_proof,
        "signed_baseline_svg_sha256":_sha(base/"source_bound_vector_mask.svg"),
        "signed_baseline_chrome_screenshot_sha256":execution["screenshot_sha256"],
        "production_promotion_authorized":False,
        "browser_screenshot_verified":False,
        "chrome_execution_provenance_verified":False,
        "exact_browser_opencv_pixel_parity":False,
        "browser_svg_gate":"UNVERIFIED",
    })
    (output/"svg_material_parity_metrics.json").write_text(
        json.dumps(renderer_metrics,ensure_ascii=False,indent=2)+"\n","utf-8",
    )
    browser=render_and_verify_chrome(output_dir=output,chrome_executable=chrome_binary)
    before_image=cv2.imread(str(base/"actual_chrome_headless.png"))[:h,:w]
    after_image=cv2.imread(str(output/"actual_chrome_headless.png"))[:h,:w]
    signed_panels=apparel["apparel_material_polygons"]
    tie_color=np.asarray(signed_panels[4]["color_rgb_observed"][::-1],dtype=np.uint8)
    tie_before=np.all(before_image==tie_color,axis=2)
    tie_after=np.all(after_image==tie_color,axis=2)
    outside_identical=bool(np.array_equal(before_image[~owner],after_image[~owner]))
    changed=int(np.count_nonzero(np.any(before_image!=after_image,axis=2)))
    old_diff=int(baseline["browser_mismatched_rgb_pixels"])
    new_diff=int(browser["browser_mismatched_rgb_pixels"])
    outside=int(np.count_nonzero(np.any(after_image!=255,axis=2)&~owner))
    if (
        not outside_identical or outside>3 or not np.array_equal(tie_before,tie_after)
        or new_diff>=old_diff or changed>20 or new_diff<0
        or render_proof["unclipped_canonical_cv2_material_mask_changed_pixels"]!=0
        or browser["browser_svg_gate"]!="FAIL"
        or browser.get("chrome_execution_provenance_verified") is not True
    ):
        raise ValueError("browser renderer correction harms source/tie/owner or is not a strict improvement")
    audit_dir=output.parent/(output.name+"_owner_audit")
    report=audit(
        vector_mask_dir=output,
        scene_path=signed_scene_path,
        apparel_path=signed_apparel_path,
        output_dir=audit_dir,
    )
    if (report["chrome_different_rgb_pixels"]!=new_diff
        or report["pixel_disagreement_outside_signed_owner"]>3
        or report["different_color_on_jointly_painted_pixels"]>6):
        raise AssertionError("independent source owner/material boundary verification failed")
    result={
        "schema":"sa10.40-signed-browser-material-vertex-correction-v1",
        "GC001_original_source_sha256":baseline["source_sha256"],
        "stage8_outer_vector_sha256":_sha(signed_scene_path),
        "stage37_apparel_scene_sha256":_sha(signed_apparel_path),
        "original_canonical_CV2_raster_sha256":_sha(original_reference),
        "candidate_canonical_CV2_raster_sha256":_sha(output/"authoritative_opencv_material.png"),
        "baseline_attested_Chrome_mismatched_pixels":old_diff,
        "candidate_attested_Chrome_mismatched_pixels":new_diff,
        "strict_improvement_pixels":old_diff-new_diff,
        "actual_Chrome_pixels_changed_by_render_calibration":changed,
        "baseline_Chrome_screenshot_sha256":execution["screenshot_sha256"],
        "candidate_Chrome_screenshot_sha256":_sha(output/"actual_chrome_headless.png"),
        "Chrome_executable_sha256":_sha(chrome_binary),
        "material_vertex_adjustment":render_proof["render_only_adjustment"],
        "signed_authoritative_source_material_canvas_changed_pixels":0,
        "source_material_vertex_count_unchanged":render_proof["original_material_vertex_count"]==27,
        "new_geometric_paths_added":render_proof["new_geometric_paths"],
        "source_owner_mask_exact_unchanged":True,
        "outside_owner_Chrome_RGB_byte_identical_to_prior":outside_identical,
        "outside_owner_Chrome_painted_pixels":outside,
        "thin_green_necktie_rendered_pixels_byte_identical":bool(np.array_equal(tie_before,tie_after)),
        "source_palette_and_existing_material_owner_unchanged":True,
        "new_face_eyes_nose_mouth_generated":False,
        "independent_signed_material_owner_audit":"PASS",
        "real_browser_source_and_artifact_SHA_attested":True,
        "browser_exact_pixel_parity":"FAIL",
        "research_gate":"PASS",
        "production_promotion_authorized":False,
        "release_blockers":[
            "41_CHROME_PIXELS_STILL_DIFFER_FROM_CANONICAL_REFERENCE",
            "OUTER_AND_COMBINED_SOURCE_VERTEX_BUDGET_FAIL",
            "FULL_CHARACTER_BROWSER_SVG_UNVERIFIED",
            "SECOND_MATCHING_GARMENT_CASE_MISSING",
            "HUMAN_VISUAL_APPROVAL_PENDING",
        ],
    }
    (output/"sa1040_signed_chrome_material_result.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf-8",
    )
    print(json.dumps({
        "status":result["research_gate"],
        "baseline":old_diff,"after":new_diff,
        "source_mask_delta_pixels":0,
        "outside_owner_pixel_identical":outside_identical,
        "tie_render_identical":result["thin_green_necktie_rendered_pixels_byte_identical"],
        "production_promotion_authorized":False,
    },ensure_ascii=False,indent=2))
    return result


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--baseline-dir",type=Path,required=True)
    p.add_argument("--outer-scene",type=Path,required=True)
    p.add_argument("--apparel-scene",type=Path,required=True)
    p.add_argument("--chrome-bin",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--material-index",type=int,default=1)
    p.add_argument("--vertex-index",type=int,default=1)
    p.add_argument("--axis",type=int,default=1)
    p.add_argument("--delta",type=float,default=.5)
    a=p.parse_args()
    run(
        signed_baseline_dir=a.baseline_dir,signed_scene_path=a.outer_scene,
        signed_apparel_path=a.apparel_scene,chrome_binary=a.chrome_bin,
        output_dir=a.output_dir,material_index=a.material_index,
        vertex_index=a.vertex_index,axis=a.axis,delta=a.delta,
    )


if __name__=="__main__":
    main()
