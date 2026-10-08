"""SA10.41 real source-provenanced FULL CHARACTER Chrome SVG research.

This refuses source-image/raster embedding in SVG, verifies the actual
Phase8->Phase9->Phase37 OpenCV composition against signed saved preview,
then measures actual headless Chrome performance for ALL original owners.
An exact-bitmap mismatch is always FAIL; this is research-only.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.reviewed_sa10.full_character_svg import compile_full_character_svg
from minimalizer_zerobase.reviewed_sa10.interior_color_planes import render_with_interior_planes
from minimalizer_zerobase.reviewed_sa10.semantic_apparel_material_planes import render_source_uniform_panels
from minimalizer_zerobase.semantic_abstraction.face_raster_guard import apply_face_raster_guard

SCHEMA="sa10.41-source-signed-full-character-browser-research-v1"


def _sha(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def _load(path:Path)->dict:
    result=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(result,dict):
        raise ValueError("signed source JSON object required")
    return result


def _rgb(path:Path)->np.ndarray:
    image=cv2.imdecode(np.fromfile(str(path),dtype=np.uint8),cv2.IMREAD_UNCHANGED)
    if image is None or image.ndim!=3:
        raise ValueError("signed image source missing/invalid")
    if image.shape[2]==4:
        return cv2.cvtColor(image,cv2.COLOR_BGRA2RGB)
    if image.shape[2]==3:
        return cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
    raise ValueError("only original RGB/RGBA images are supported")


def _write_rgb(path:Path,img:np.ndarray)->None:
    if not cv2.imwrite(str(path),cv2.cvtColor(img,cv2.COLOR_RGB2BGR)):
        raise IOError("research PNG write failed")


def prepare(*, scene_path:Path, stage9_dir:Path, stage37_dir:Path,
            stage04_dir:Path, original_image:Path, output_dir:Path)->dict:
    output_dir=output_dir.resolve()
    for authority in (scene_path,stage9_dir,stage37_dir,stage04_dir,original_image):
        root=authority.resolve()
        if root==output_dir or root in output_dir.parents or output_dir in root.parents:
            raise ValueError("research output must be isolated from signed authority files")
    scene=_load(scene_path)
    stage9=_load(stage9_dir/"interior_plane_proposals.json")
    stage9_metrics=_load(stage9_dir/"interior_plane_metrics.json")
    apparel=_load(stage37_dir/"apparel_simplified_subpaths.json")
    apparel_metrics=_load(stage37_dir/"apparel_simplified_metrics.json")
    stage04=_load(stage04_dir/"stage.json")
    source_hash=_sha(original_image)
    if (
        scene.get("schema")!="sa10.34-adaptive-contour-scene-v1"
        or stage9.get("schema")!="sa10.35-interior-overlay-scene-v1"
        or apparel.get("schema")!="sa10.37-apparel-simplified-scene-v1"
        or source_hash!=scene.get("original_source_sha256")
        or source_hash!=stage04.get("source",{}).get("sha256")
        or source_hash!=stage9.get("source_sha256")
        or source_hash!=stage9_metrics.get("source_sha256")
        or source_hash!=apparel.get("source_sha256")
        or source_hash!=apparel_metrics.get("case_source_sha256")
        or stage9.get("original_outer_scene_sha256")!=_sha(scene_path)
        or stage9_metrics.get("outer_scene_original_sha256")!=_sha(scene_path)
        or apparel.get("stage8_outer_vector_sha256")!=_sha(scene_path)
        or apparel_metrics.get("candidate_geometry_sha256")!=_sha(stage37_dir/"apparel_simplified_subpaths.json")
        or apparel_metrics.get("candidate_preview_sha256")!=_sha(stage37_dir/"apparel_simplified_preview.png")
        or stage9_metrics.get("source_stage04_provenance_verified") is not True
        or stage9_metrics.get("original_adaptive_preview_pixels_equal") is not True
        or apparel_metrics.get("Stage04_source_masks_verified") is not True
        or apparel_metrics.get("Stage08_outer_sha_verified") is not True
        or apparel_metrics.get("Stage36_material_provenance_verified") is not True
        or apparel_metrics.get("face_left_right_arm_rgb_unchanged") is not True
        or apparel_metrics.get("production_promotion_authorized") is not False
    ):
        raise ValueError("Stage04/08/09/37 source lineage or guarded preview SHA mismatch")
    rec=scene.get("primitives_back_to_front")
    if not isinstance(rec,list) or len(rec)!=11:
        raise ValueError("must have exactly 11 original source owner primitive records")
    w,h=(int(scene["coordinate_space"][k]) for k in ("pixel_width","pixel_height"))
    source=_rgb(original_image)
    if source.shape!=(h,w,3):
        raise ValueError("original RGB input canvas shape changed")
    original_stage04={}
    for owner in ("face","left_arm","right_arm"):
        f=stage04_dir/"part_masks"/f"{owner}.png"
        if stage04.get("outputs",{}).get(f"part_masks/{owner}.png")!=_sha(f):
            raise ValueError(f"Stage04 source semantic mask SHA mismatch: {owner}")
        decoded=cv2.imdecode(np.fromfile(str(f),dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
        if decoded is None or decoded.shape!=(h,w):
            raise ValueError(f"source-provenanced mask unavailable: {owner}")
        original_stage04[owner]=decoded>0
    protected=original_stage04["face"]|original_stage04["left_arm"]|original_stage04["right_arm"]
    selected_masks={}
    owner_visible=np.full((h,w),-1,np.int32)
    for i,p in enumerate(rec):
        mask=rasterize_primitive_candidate(p,width=w,height=h)
        selected_masks[p["primitive_id"]]=mask
        if p.get("structural_support_only") is not True:
            owner_visible[mask]=i
    planes=stage9.get("additional_fill_subpaths")
    if not isinstance(planes,list) or len(planes)!=stage9_metrics.get("interior_subplane_count"):
        raise ValueError("Phase9 signed material plane count mismatches evidence")
    base,stage9_candidate,_=render_with_interior_planes(
        primitives=rec,primitive_masks=selected_masks,
        planes=planes,protected_mask=protected,
    )
    face_color=apply_face_raster_guard(
        stage9_candidate,source,original_stage04["face"]
    )
    signed_stage9=face_color.rgb
    saved_stage9=_rgb(stage9_dir/"interior_color_candidate.png")
    if not np.array_equal(saved_stage9,signed_stage9):
        differing=int(np.count_nonzero(np.any(saved_stage9!=signed_stage9,axis=2)))
        raise ValueError(f"Phase9 exact OpenCV source canonical RGB reconstruction FAILED: {differing} pixels")
    lower_owners=[
        i for i,p in enumerate(rec)
        if p.get("source_mask_owner")=="lower_body"
        and p.get("semantic_part_id")=="lower_body"
    ]
    if len(lower_owners)!=1:
        raise ValueError("unique lower_body owner required")
    apparel_planes=apparel.get("apparel_material_polygons")
    if not isinstance(apparel_planes,list) or len(apparel_planes) not in (0,5):
        raise ValueError("must have source-approved 0 or 5 clothing color subpaths")
    if len(apparel_planes)==0 and apparel_metrics.get("status")!="NONMATCHING_CASE_NO_OP":
        raise ValueError("no-apparel branch must be source-verified negative control")
    if len(apparel_planes)==5 and apparel_metrics.get("candidate_total_vertices")!=sum(
        len(p["points"]) for p in apparel_planes
    ):
        raise ValueError("clothing source vertex geometry count changed")
    original_visible=(owner_visible==lower_owners[0])&~protected
    expected,changed=render_source_uniform_panels(
        base_rgb=signed_stage9,panels=apparel_planes,
        parent_visible=original_visible,protected=protected
    ) if apparel_planes else (signed_stage9.copy(),np.zeros((h,w),bool))
    signed_full=_rgb(stage37_dir/"apparel_simplified_preview.png")
    if not np.array_equal(expected,signed_full):
        differing=int(np.count_nonzero(np.any(expected!=signed_full,axis=2)))
        raise ValueError(f"whole-character original OpenCV pipeline NOT reproducible: {differing} RGB pixels")
    if np.any(changed&protected):
        raise AssertionError("protected original face/arm scene edited")
    svg,geometry=compile_full_character_svg(
        records=rec,stage9_planes=planes,
        garment_panels=apparel_planes,stage04_masks=original_stage04,
        face_guard_rgb=face_color.fill_rgb,width=w,height=h,
    )
    html=(
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<style>html,body{margin:0;padding:0;overflow:hidden}svg{display:block}</style>'
        '</head><body>'+svg+'</body></html>'
    )
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/"full_character_vector.svg").write_text(svg,"utf-8")
    (output_dir/"full_character_vector.html").write_text(html,"utf-8")
    _write_rgb(output_dir/"signed_full_opencv_reference.png",expected)
    body_mask=(owner_visible==lower_owners[0]).astype(np.uint8)*255
    if not cv2.imwrite(str(output_dir/"signed_final_visible_lower_body_mask.png"),body_mask):
        raise IOError("owner mask write failed")
    for owner in ("face","left_arm","right_arm"):
        if not cv2.imwrite(str(output_dir/f"signed_{owner}_stage04_mask.png"),original_stage04[owner].astype(np.uint8)*255):
            raise IOError("stage04 mask write failed")
    metadata={
        "schema":SCHEMA,
        "original_source_sha256":source_hash,
        "original_stage8_scene_sha256":_sha(scene_path),
        "original_stage9_scene_sha256":_sha(stage9_dir/"interior_plane_proposals.json"),
        "original_stage37_scene_sha256":_sha(stage37_dir/"apparel_simplified_subpaths.json"),
        "original_stage37_preview_sha256":_sha(stage37_dir/"apparel_simplified_preview.png"),
        "full_canonical_cv2_reference_sha256":_sha(output_dir/"signed_full_opencv_reference.png"),
        "source_stage04_mask_sha256":{
            owner:_sha(stage04_dir/"part_masks"/f"{owner}.png")
            for owner in ("face","left_arm","right_arm")
        },
        "source_face_guard_flat_observed_rgb":list(face_color.fill_rgb),
        "saved_stage9_candidate_pixel_equal":True,
        "saved_stage37_full_preview_pixel_equal":True,
        "source_stage8_owner_order_unchanged":True,
        "source_immutable_face_and_both_arms":True,
        "source_apparel_pixels_changed_outside_visible_lower_body":0,
        "original_face_feature_geometry_added":False,
        "SVG_source_bitmap_embedded":False,
        "stage37_no_apparel_negative_control":not bool(apparel_planes),
        "full_scene_chrome_executed":False,
        "full_scene_chrome_exact_rgb_parity":"UNVERIFIED",
        "all_original_vertex_and_mask_complexity_counted":True,
        "original_GC001_outer_vertex_budget_limit":1887 if w==340 and h==340 and apparel_planes else None,
        "production_promotion_authorized":False,
        **geometry,
    }
    (output_dir/"full_character_svg_metrics.json").write_text(
        json.dumps(metadata,ensure_ascii=False,indent=2)+"\n","utf-8"
    )
    print(json.dumps({
        "status":"FULL_SCENE_SOURCE_RECONSTRUCTION_PASS",
        "all_saved_candidate_RGB_pixels_exact":True,
        "original_source_owners":len(rec),
        "stage9_planes":len(planes),
        "stage37_apparel_planes":len(apparel_planes),
        "source_degenerate_contours":geometry["source_topological_degenerate_ring_count"],
        "original_source_vertices":geometry["original_source_ring_vertices_including_support"],
        "total_geometric_source_vertex_occurrences":geometry["combined_mask_vector_source_vertex_occurrences_counted"],
        "release_authorized":False,
    },ensure_ascii=False,indent=2))
    return metadata


def render_chrome(*,output_dir:Path,chrome_binary:Path)->dict:
    output_dir=output_dir.resolve()
    mpath=output_dir/"full_character_svg_metrics.json"
    report=_load(mpath)
    if report.get("schema")!=SCHEMA or report.get("saved_stage37_full_preview_pixel_equal") is not True:
        raise ValueError("Chrome may only render independently source-signed full scene")
    svg=output_dir/"full_character_vector.svg"
    page=output_dir/"full_character_vector.html"
    if not svg.exists() or not page.exists() or not chrome_binary.is_file():
        raise ValueError("full source vector or real Chrome executable missing")
    if svg.read_text("utf-8") not in page.read_text("utf-8"):
        raise ValueError("actual HTML no longer contains the full signed SVG")
    w,h=(
        int(report.get("original_GC001_outer_vertex_budget_limit") is not None or 340),
        340,
    )
    expected=cv2.imread(str(output_dir/"signed_full_opencv_reference.png"),cv2.IMREAD_COLOR)
    if expected is None or expected.ndim!=3:
        raise ValueError("original full source OpenCV preview missing")
    h,w=expected.shape[:2]
    output=output_dir/"real_chrome_full_character.png"
    if output.exists():
        output.unlink()
    args=[
        str(chrome_binary.resolve()),"--headless=new","--disable-gpu",
        "--no-first-run","--no-default-browser-check","--disable-extensions",
        "--hide-scrollbars","--force-device-scale-factor=1",
        "--window-size=800,600",
        f"--user-data-dir={output_dir/'isolated-chrome-profile'}",
        f"--screenshot={output}",page.as_uri(),
    ]
    proc=subprocess.run(args,capture_output=True,timeout=60,check=False)
    if proc.returncode!=0 or not output.exists():
        raise RuntimeError("real headless Chrome full-character SVG execution failed")
    screenshot=cv2.imread(str(output),cv2.IMREAD_COLOR)
    if screenshot is None or screenshot.shape[0]<h or screenshot.shape[1]<w:
        raise ValueError("browser screenshot undersized or corrupt")
    chrome=screenshot[:h,:w]
    diff=cv2.absdiff(chrome,expected)
    mismatch=np.any(chrome!=expected,axis=2)
    reference_bg=np.asarray((236,238,238),dtype=np.uint8) # BGR of (238,238,236)
    background_difference=np.any(chrome!=reference_bg,axis=2)^np.any(expected!=reference_bg,axis=2)
    owned={}
    for owner in ("face","left_arm","right_arm"):
        mask=cv2.imread(str(output_dir/f"signed_{owner}_stage04_mask.png"),cv2.IMREAD_GRAYSCALE)
        if mask is None or mask.shape!=(h,w):
            raise ValueError("signed protected semantic region missing")
        mask=mask>0
        owned[owner]={
            "original_stage04_source_pixels":int(np.count_nonzero(mask)),
            "chrome_different_rgb_pixels_in_source_mask":int(np.count_nonzero(mismatch&mask)),
            "strong_RGB_mismatches_gt48":int(np.count_nonzero((diff.max(axis=2)>48)&mask)),
        }
    lower=cv2.imread(str(output_dir/"signed_final_visible_lower_body_mask.png"),cv2.IMREAD_GRAYSCALE)
    if lower is None or lower.shape!=(h,w):
        raise ValueError("canonical owner-visible mask missing")
    lower=lower>0
    metrics={
        "real_chrome_full_character_execute_verified":True,
        "chrome_executable_sha256":_sha(chrome_binary),
        "svg_sha256":_sha(svg),
        "html_sha256":_sha(page),
        "screenshot_sha256":_sha(output),
        "authoritative_full_opencv_reference_sha256":_sha(output_dir/"signed_full_opencv_reference.png"),
        "canvas_width":w,"canvas_height":h,
        "full_scene_RGB_mismatched_pixels":int(np.count_nonzero(mismatch)),
        "full_scene_strong_RGB_mismatch_pixels_gt48":int(np.count_nonzero(diff.max(axis=2)>48)),
        "full_scene_rgb_mae":round(float(diff.mean()),6),
        "full_scene_background_occupancy_mismatch_pixels":int(np.count_nonzero(background_difference)),
        "full_scene_different_pixels_outside_signed_final_lower_body":int(np.count_nonzero(mismatch&~lower)),
        "full_scene_protected_semantic_parts":owned,
        "true_full_scene_browser_exact_RGB_parity":"PASS" if not np.any(mismatch) else "FAIL",
        "full_character_face_and_arm_browser_parity":"PASS" if all(
            item["chrome_different_rgb_pixels_in_source_mask"]==0 for item in owned.values()
        ) else "FAIL",
        "production_promotion_authorized":False,
    }
    report.update(metrics)
    report["full_scene_chrome_executed"]=True
    report["full_scene_chrome_exact_rgb_parity"]=metrics["true_full_scene_browser_exact_RGB_parity"]
    report["release_blockers"]=[
        "FULL_CHARACTER_BROWSER_RGB_PARITY_NOT_PROVEN" if np.any(mismatch) else "",
        "FACE_OR_BOTH_ARMS_BROWSER_PIXEL_PARITY_FAILED"
        if metrics["full_character_face_and_arm_browser_parity"]!="PASS" else "",
        "COMBINED_VECTOR_VERTEX_BUDGET_EXCEEDED",
        "POSITIVE_SECOND_CHARACTER_NOT_VERIFIED",
        "HUMAN_VISUAL_REVIEW_PENDING",
    ]
    report["release_blockers"]=[x for x in report["release_blockers"] if x]
    mpath.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf-8")
    cv2.imwrite(str(output_dir/"full_character_chrome_difference.png"),
                np.clip(diff.astype(np.int16)*2,0,255).astype(np.uint8))
    before=expected.copy()
    browser_canvas=chrome.copy()
    diff_canvas=np.full_like(before,245)
    diff_canvas[mismatch]=[0,0,245]
    board=np.full((h+44,w*3,3),245,np.uint8)
    for i,(name,img) in enumerate((
        ("SIGNED SOURCE CV2",before),("ACTUAL CHROME SVG",browser_canvas),("RGB ERRORS RED",diff_canvas)
    )):
        board[44:44+h,i*w:(i+1)*w]=img
        cv2.putText(board,name,(i*w+5,27),cv2.FONT_HERSHEY_SIMPLEX,.47,(20,20,20),1,cv2.LINE_AA)
    cv2.imwrite(str(output_dir/"full_character_chrome_3way.png"),board)
    print(json.dumps({
        "status":"REAL_CHROME_FULL_CHARACTER_RESEARCH_EXECUTED",
        "RGB_mismatched_pixels":metrics["full_scene_RGB_mismatched_pixels"],
        "face_and_arms":owned,
        "browser_parity":metrics["true_full_scene_browser_exact_RGB_parity"],
        "geometry_vertices_counted":report["combined_mask_vector_source_vertex_occurrences_counted"],
        "production_promotion_authorized":False,
    },ensure_ascii=False,indent=2))
    return report


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--scene",type=Path)
    p.add_argument("--stage9-dir",type=Path)
    p.add_argument("--stage37-dir",type=Path)
    p.add_argument("--stage04-dir",type=Path)
    p.add_argument("--source",type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--render-chrome",action="store_true")
    p.add_argument("--chrome-bin",type=Path)
    a=p.parse_args()
    if a.render_chrome:
        if a.chrome_bin is None:
            raise ValueError("real Chrome binary path required")
        render_chrome(output_dir=a.output_dir,chrome_binary=a.chrome_bin)
    else:
        if any(getattr(a,key) is None for key in (
            "scene","stage9_dir","stage37_dir","stage04_dir","source"
        )):
            raise ValueError("all original signed input authorities are mandatory")
        prepare(
            scene_path=a.scene,stage9_dir=a.stage9_dir,
            stage37_dir=a.stage37_dir,stage04_dir=a.stage04_dir,
            original_image=a.source,output_dir=a.output_dir,
        )


if __name__=="__main__":
    main()
