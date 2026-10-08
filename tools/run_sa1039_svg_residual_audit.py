"""SA10.39: trace residual vector-SVG Chrome differences to signed geometry.

Audit is diagnostic only: uses real-headless-Chrome SHA-attested screenshot
and separately rasterized signed polygons. It never changes SVG, pixels,
materials, source ownership, hard acceptance metrics or production flags.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.reviewed_sa10.semantic_apparel_material_planes import material_polygon_mask

SCHEMA="sa10.39-signed-svg-residual-pixel-audit-v1"


def _load(path:Path)->dict:
    payload=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload,dict):
        raise ValueError("signed evidence must be JSON object")
    return payload


def _digest(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def _border(mask:np.ndarray,*,margin:int=0)->np.ndarray:
    binary=np.asarray(mask).astype(np.uint8)
    if binary.ndim!=2:
        raise ValueError("source owner or material mask must be 2D")
    edge=cv2.morphologyEx(binary,cv2.MORPH_GRADIENT,np.ones((3,3),dtype=np.uint8))
    if margin:
        edge=cv2.dilate(edge,np.ones((margin*2+1,margin*2+1),dtype=np.uint8))
    return edge>0


def classify_residual_pixels(
    *, authoritative_rgb:np.ndarray, chrome_rgb:np.ndarray,
    owner_mask:np.ndarray, material_masks:list[np.ndarray],
) -> tuple[dict,np.ndarray]:
    expected=np.asarray(authoritative_rgb)
    actual=np.asarray(chrome_rgb)
    if (expected.dtype!=np.uint8 or actual.dtype!=np.uint8
        or expected.ndim!=3 or expected.shape[2]!=3
        or expected.shape!=actual.shape):
        raise ValueError("RGB and screenshot must have byte-identical canvas size")
    if owner_mask.shape!=expected.shape[:2]:
        raise ValueError("original signed owner mask canvas mismatch")
    if len(material_masks)!=5 or any(x.shape!=owner_mask.shape for x in material_masks):
        raise ValueError("exactly five original material owner masks are required")
    mismatched=np.any(expected!=actual,axis=2)
    error=cv2.absdiff(expected,actual)
    maxchannel=np.max(error,axis=2)
    background=np.all(expected==255,axis=2)
    realcolor=np.all(actual==255,axis=2)
    occupancy=background^realcolor
    chromatic=mismatched & ~occupancy
    owner_edge=_border(owner_mask,margin=1)
    material_edge=np.logical_or.reduce([_border(m,margin=1) for m in material_masks])
    category={
        "owner_and_material_edge":int((mismatched&owner_edge&material_edge).sum()),
        "owner_edge_only":int((mismatched&owner_edge&~material_edge).sum()),
        "material_edge_only":int((mismatched&~owner_edge&material_edge).sum()),
        "outside_near_edge":int((mismatched&~owner_edge&~material_edge).sum()),
    }
    if sum(category.values())!=int(mismatched.sum()):
        raise AssertionError("residual geometry attribution is not exhaustive")
    count,labels,stats,_=cv2.connectedComponentsWithStats(mismatched.astype(np.uint8),8)
    clusters=[]
    for i in range(1,count):
        x,y,w,h,area=(int(value) for value in stats[i])
        clusters.append({
            "area_pixels":area,"bbox_xywh":[x,y,w,h],
            "strong_pixels":int(np.count_nonzero((labels==i)&(maxchannel>48))),
            "color_vs_blank_pixels":int(np.count_nonzero((labels==i)&occupancy)),
        })
    clusters.sort(key=lambda z:(-z["area_pixels"],z["bbox_xywh"]))
    border=owner_edge|material_edge
    data={
        "canvas_width":expected.shape[1],"canvas_height":expected.shape[0],
        "chrome_different_rgb_pixels":int(mismatched.sum()),
        "strong_rgb_channel_error_gt48_pixels":int((maxchannel>48).sum()),
        "rgb_mae":round(float(error.mean()),6),
        "occupancy_differences":int(occupancy.sum()),
        "different_color_on_jointly_painted_pixels":int(chromatic.sum()),
        "source_owner_parent_boundary":category,
        "pixel_disagreement_inside_signed_owner":int((mismatched&owner_mask).sum()),
        "pixel_disagreement_outside_signed_owner":int((mismatched&~owner_mask).sum()),
        "source_material_boundary_near_pixel_count":int((mismatched&border).sum()),
        "connected_mismatch_region_count":len(clusters),
        "ten_largest_regions":clusters[:10],
        "mismatch_y_row_245":int(mismatched[245].sum()) if len(mismatched)>245 else None,
        "mismatched_fraction_of_canvas":round(float(mismatched.mean()),8),
        "svg_exact_pixel_parity":not np.any(mismatched),
    }
    # Purely explanatory visualization, never used in SVG or promotion.
    overlay=expected.copy()
    overlay[mismatched]=[0,0,255] # red in OpenCV BGR
    overlay[(maxchannel>48)&mismatched]=[0,0,255]
    return data,overlay


def audit(
    *, vector_mask_dir:Path, scene_path:Path, apparel_path:Path,
    output_dir:Path,
)->dict:
    vector_mask_dir=vector_mask_dir.resolve()
    original_svg=_load(vector_mask_dir/"svg_material_parity_metrics.json")
    chrome=_load(vector_mask_dir/"real_chrome_execution.json")
    outer=_load(scene_path)
    apparel=_load(apparel_path)
    if (
        original_svg.get("schema")!="sa10.38-source-contour-vector-mask-browser-v1"
        or chrome.get("schema")!="sa10.38-real-chrome-execution-v1"
        or original_svg.get("browser_screenshot_verified") is not True
        or original_svg.get("chrome_execution_provenance_verified") is not True
        or original_svg.get("browser_svg_gate")!="FAIL"
        or original_svg.get("production_promotion_authorized") is not False
        or original_svg.get("source_sha256")!=outer.get("original_source_sha256")
        or original_svg.get("simplified_apparel_sha256")!=_digest(apparel_path)
        or original_svg.get("outer_vector_sha256")!=_digest(scene_path)
        or chrome.get("html_sha256")!=_digest(vector_mask_dir/"source_bound_vector_mask.html")
        or chrome.get("svg_sha256")!=_digest(vector_mask_dir/"source_bound_vector_mask.svg")
        or chrome.get("screenshot_sha256")!=_digest(vector_mask_dir/"actual_chrome_headless.png")
        or chrome.get("browser_engine_executed") is not True
        or chrome.get("used_private_isolated_chrome_profile") is not True
    ):
        raise ValueError("browser and original signed source/geometry provenance failed")
    existing=outer.get("primitives_back_to_front")
    if not isinstance(existing,list) or len(existing)!=11:
        raise ValueError("signed scene requires 11 source owners")
    owner=[p for p in existing if p.get("source_mask_owner")=="lower_body"]
    if len(owner)!=1:
        raise ValueError("cannot identify source lower_body")
    body=owner[0]
    panels=apparel.get("apparel_material_polygons")
    if not isinstance(panels,list) or len(panels)!=5:
        raise ValueError("five signed geometric material planes required")
    if any(p.get("parent_primitive_id")!=body["primitive_id"] for p in panels):
        raise ValueError("unbound material or changed source owner")
    w,h=int(outer["coordinate_space"]["pixel_width"]),int(outer["coordinate_space"]["pixel_height"])
    img_expected=cv2.imread(str(vector_mask_dir/"authoritative_opencv_material.png"),cv2.IMREAD_COLOR)
    img_browser=cv2.imread(str(vector_mask_dir/"actual_chrome_headless.png"),cv2.IMREAD_COLOR)
    if (img_expected is None or img_browser is None or img_expected.shape!=(h,w,3)
        or img_browser.shape[0]<h or img_browser.shape[1]<w):
        raise ValueError("browser canvas missing or inconsistent")
    img_browser=img_browser[:h,:w]
    signed_mask=rasterize_primitive_candidate(body,width=w,height=h)
    material_masks=[
        material_polygon_mask(
            panel,parent_visible=signed_mask,
            protected=np.zeros((h,w),dtype=bool)
        ) for panel in panels
    ]
    rebuilt=np.full((h,w,3),255,dtype=np.uint8)
    for panel,mask in zip(panels,material_masks):
        rebuilt[mask]=np.asarray(panel["color_rgb_observed"],dtype=np.uint8)[::-1]
    if not np.array_equal(rebuilt,img_expected):
        raise AssertionError("reference image cannot be faithfully reconstructed from signed geometry")
    classified,debug=classify_residual_pixels(
        authoritative_rgb=img_expected,chrome_rgb=img_browser,
        owner_mask=signed_mask,material_masks=material_masks,
    )
    if classified["chrome_different_rgb_pixels"]!=original_svg["browser_mismatched_rgb_pixels"]:
        raise ValueError("pixel audit and Chrome verification disagree")
    output_dir=output_dir.resolve()
    if output_dir==vector_mask_dir or output_dir in vector_mask_dir.parents or vector_mask_dir in output_dir.parents:
        raise ValueError("output must be isolated from original signed Chrome evidence")
    output_dir.mkdir(parents=True,exist_ok=True)
    metadata={
        "schema":SCHEMA,
        "source_sha256":original_svg["source_sha256"],
        "signed_outer_vector_sha256":_digest(scene_path),
        "signed_material_scene_sha256":_digest(apparel_path),
        "real_chrome_executable_sha256":chrome["chrome_binary_sha256"],
        "real_chrome_screenshot_sha256":chrome["screenshot_sha256"],
        "actual_source_owner_boundary_immutable":True,
        "actual_five_material_subpaths_immutable":True,
        "chrome_executed_and_sha_attested":True,
        "new_svg_geometry_created":False,
        "source_bitmap_embedded_in_svg":False,
        "production_promotion_authorized":False,
        "browser_svg_gate":"FAIL" if classified["chrome_different_rgb_pixels"] else "PASS",
        **classified,
    }
    (output_dir/"svg_residual_geometry_audit.json").write_text(
        json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    cv2.imwrite(str(output_dir/"svg_residual_error_overlay.png"),debug)
    print(json.dumps({
        "schema":SCHEMA,
        "mismatched_pixels":metadata["chrome_different_rgb_pixels"],
        "occupancy":metadata["occupancy_differences"],
        "colored_regions":metadata["different_color_on_jointly_painted_pixels"],
        "attribution":metadata["source_owner_parent_boundary"],
        "clusters":metadata["connected_mismatch_region_count"],
        "svg_gate":metadata["browser_svg_gate"],
    },ensure_ascii=False,indent=2))
    return metadata


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--vector-mask-dir",required=True,type=Path)
    p.add_argument("--scene",required=True,type=Path)
    p.add_argument("--apparel",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    audit(vector_mask_dir=a.vector_mask_dir,scene_path=a.scene,
          apparel_path=a.apparel,output_dir=a.output_dir)


if __name__=="__main__":
    main()
