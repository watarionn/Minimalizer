"""SA10.37 actual browser SVG clip-path parity research (not production).

Render five *geometric* apparel polygons within their existing lower_body
contour path, without embedding source pixels in SVG. Capture in real Chrome
headless separately; report raw pixel parity as FAIL unless exact.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.reviewed_sa10.semantic_apparel_material_planes import (
    material_polygon_mask,
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _rgb(color: list[int]) -> str:
    if len(color)!=3 or any(not isinstance(c,int) or c<0 or c>255 for c in color):
        raise ValueError("invalid observed RGB vector")
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def _points(points: list[list[float]], *, pixel_shift: float = 0.0) -> str:
    if not isinstance(points,list) or len(points)<3:
        raise ValueError("SVG filled polygon must have >=3 vertices")
    arr=np.asarray(points,dtype=float)
    if arr.ndim!=2 or arr.shape[1]!=2 or not np.all(np.isfinite(arr)):
        raise ValueError("invalid SVG vertex coordinates")
    return " ".join(f"{x+pixel_shift:g},{y+pixel_shift:g}" for x,y in arr)


def _owner_ring_path(parent: dict, *, pixel_shift: float = 0.0) -> tuple[str,int]:
    rings=parent.get("parameters",{}).get("rings")
    if not isinstance(rings,list) or not rings:
        raise ValueError("existing source polygon rings not found")
    subs=[]
    degenerate=0
    for ring in rings:
        p=ring.get("points")
        if not isinstance(p,list):
            raise ValueError("corrupt existing ring")
        if len(p)<3:
            degenerate+=1
            continue
        points=_points(p, pixel_shift=pixel_shift).split(" ")
        subs.append("M "+" L ".join(t.replace(","," ") for t in points)+" Z")
    if not subs:
        raise ValueError("no browser-valid parent polygon rings")
    return " ".join(subs),degenerate


def prepare_svg(*, scene_path: Path, panels_path: Path,
                output_dir: Path, pixel_shift: float = 0.0,
                shape_rendering: str = "crispEdges") -> dict:
    scene=_json(scene_path)
    selection=_json(panels_path)
    records=scene["primitives_back_to_front"]
    material=selection["apparel_material_polygons"]
    w=scene["coordinate_space"]["pixel_width"]
    h=scene["coordinate_space"]["pixel_height"]
    parent=[p for p in records if p.get("source_mask_owner")=="lower_body"]
    if len(parent)!=1 or len(material)!=5:
        raise ValueError("expected five semantic polygons in one existing body owner")
    parent=parent[0]
    if not all(panel["parent_primitive_id"]==parent["primitive_id"] for panel in material):
        raise ValueError("source owner mismatch")
    if not -0.5 <= pixel_shift <= 0.5 or not np.isfinite(pixel_shift):
        raise ValueError("pixel shift must be finite and within [-0.5,+0.5]")
    if shape_rendering not in ("crispEdges", "geometricPrecision", "auto"):
        raise ValueError("unsupported browser geometry raster rule")
    d,degenerate=_owner_ring_path(parent,pixel_shift=pixel_shift)
    # SVG clips the source-backed existing parent path. Tiny 1/2-point source
    # contours cannot be assumed to survive SVG even-odd fill semantics.
    svg=''.join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" shape-rendering="{shape_rendering}">',
        '<defs><clipPath id="existing-lower-body" clipPathUnits="userSpaceOnUse">',
        f'<path d="{d}" clip-rule="evenodd" fill-rule="evenodd"/></clipPath></defs>',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>',
        '<g clip-path="url(#existing-lower-body)">',
        *[
            f'<polygon points="{_points(p["points"],pixel_shift=pixel_shift)}" fill="{_rgb(p["color_rgb_observed"])}" />'
            for p in material
        ],
        '</g></svg>',
    ])
    html=''.join([
        '<!doctype html><html><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<style>html,body{margin:0;padding:0;background:#ffffff;overflow:hidden}svg{display:block}</style>',
        '</head><body>',svg,'</body></html>',
    ])
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/"apparel_svg_browser_probe.html").write_text(html,encoding="utf-8")
    (output_dir/"apparel_svg_browser_probe.svg").write_text(svg,encoding="utf-8")
    p_mask=rasterize_primitive_candidate(parent,width=w,height=h)
    reference=np.full((h,w,3),255,np.uint8)
    for panel in material:
        painted=material_polygon_mask(
            panel,parent_visible=p_mask,protected=np.zeros((h,w),bool),
        )
        reference[painted]=panel["color_rgb_observed"]
    cv2.imwrite(str(output_dir/"apparel_opencv_vector_reference.png"),
                cv2.cvtColor(reference,cv2.COLOR_RGB2BGR))
    report={
        "schema":"sa10.37-apparel-browser-svg-v1",
        "existing_parent_owner":"lower_body",
        "original_parent_primitive_id":parent["primitive_id"],
        "new_svg_filled_polygon_subpaths":len(material),
        "new_svg_polygon_vertices":sum(len(x["points"]) for x in material),
        "existing_parent_svg_path_ring_count":len(parent["parameters"]["rings"]),
        "svg_pixel_shift":pixel_shift,
        "shape_rendering":shape_rendering,
        "unrepresentable_one_or_two_point_parent_rings":degenerate,
        "source_image_or_png_embedded":False,
        "protected_masks_not_replaced_with_raster":True,
        "browser_screenshot_verified":False,
        "svg_exact_parity_pass":False,
        "production_promotion_authorized":False,
    }
    (output_dir/"apparel_svg_browser_metrics.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return report


def compare_chrome(*, output_dir: Path) -> dict:
    report_path=output_dir/"apparel_svg_browser_metrics.json"
    report=_json(report_path)
    screenshot=cv2.imread(str(output_dir/"apparel_chrome_headless.png"),cv2.IMREAD_COLOR)
    expected=cv2.imread(str(output_dir/"apparel_opencv_vector_reference.png"),cv2.IMREAD_COLOR)
    if screenshot is None or expected is None or screenshot.shape[0]<expected.shape[0] or screenshot.shape[1]<expected.shape[1]:
        raise ValueError("actual Chrome screenshot missing or smaller than SVG canvas")
    h,w=expected.shape[:2]
    actual=screenshot[:h,:w]
    delta=cv2.absdiff(actual,expected)
    max_diff=np.max(delta,axis=2)
    any_difference=np.any(actual!=expected,axis=2)
    report.update({
        "browser_screenshot_verified":True,
        "browser_snapshot_crop":[w,h],
        "browser_exact_rgb_differing_pixels":int(any_difference.sum()),
        "browser_pixels_with_channel_delta_above_16":int((max_diff>16).sum()),
        "browser_pixels_with_channel_delta_above_48":int((max_diff>48).sum()),
        "browser_pixel_mae_rgb":round(float(delta.mean()),6),
        "browser_max_channel_error":int(delta.max()),
        "svg_exact_parity_pass":bool(not np.any(any_difference) and
            report["unrepresentable_one_or_two_point_parent_rings"]==0),
        "svg_browser_gate":"PASS" if not np.any(any_difference) and report["unrepresentable_one_or_two_point_parent_rings"]==0 else "FAIL",
        "production_promotion_authorized":False,
    })
    cv2.imwrite(str(output_dir/"apparel_browser_difference.png"),delta*2)
    report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return report


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--scene",type=Path)
    p.add_argument("--panels",type=Path)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--compare",action="store_true")
    p.add_argument("--pixel-shift",type=float,default=0.0)
    p.add_argument("--shape-rendering",default="crispEdges")
    args=p.parse_args()
    if args.compare:
        compare_chrome(output_dir=args.output_dir)
    else:
        if not args.scene or not args.panels:
            raise ValueError("--scene and --panels required for prepare mode")
        prepare_svg(scene_path=args.scene,panels_path=args.panels,output_dir=args.output_dir,
                    pixel_shift=args.pixel_shift,shape_rendering=args.shape_rendering)


if __name__=="__main__":
    main()
