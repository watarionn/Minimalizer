"""SA10.40 isolated Chrome test for bounded existing APPAREL vertex nudges.

No source authority or production scene is modified. Candidate SVG pixels
must be attested by actual Chrome, with all five material fills intact.
The green necktie is frozen, zero polygons/vertices are introduced, and
off-owner painting may not increase. This is research, not product SVG parity.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.reviewed_sa10.apparel_vertex_simplifier import _simple_polygon
from minimalizer_zerobase.reviewed_sa10.semantic_apparel_material_planes import material_polygon_mask

PATTERN=re.compile(r'<polygon points="([^"]+)" fill="#[0-9a-f]{6}" stroke="#[0-9a-f]{6}"')
SCHEMA="sa10.40-bounded-apparel-vertex-chrome-probe-v1"


def modify_one_signed_polygon(svg: str, *, index: int, vertex: int,
                              axis: int, delta: float) -> str:
    if (not isinstance(index,int) or isinstance(index,bool) or index not in range(4)
        or not isinstance(vertex,int) or vertex<0 or axis not in (0,1)
        or delta not in (-0.5,0.5)):
        raise ValueError("only existing non-tie vertices with bounded 0.5px shift")
    matches=list(PATTERN.finditer(svg))
    if len(matches)!=5:
        raise ValueError("signed five-material source scene required")
    raw=matches[index].group(1)
    points=[list(map(float,p.split(","))) for p in raw.split()]
    if vertex>=len(points):
        raise ValueError("vertex index outside signed material geometry")
    points[vertex][axis]+=delta
    if not _simple_polygon(points):
        raise ValueError("render-only adjustment self-intersects")
    altered=" ".join(",".join(f"{x:g}" for x in p) for p in points)
    match=matches[index]
    changed=svg[:match.start(1)]+altered+svg[match.end(1):]
    if changed.count("<polygon ")!=5 or not PATTERN.findall(changed):
        raise AssertionError("material count changed")
    if list(PATTERN.finditer(changed))[4].group(0)!=matches[4].group(0):
        raise AssertionError("green tie changed")
    # The literal signed shell (owner mask, holes, z-order and non-selected
    # materials) cannot be changed by the renderer calibration.
    a=list(PATTERN.finditer(changed))
    if any(a[k].group(0)!=matches[k].group(0) for k in range(5) if k!=index):
        raise AssertionError("unrelated material vertex changed")
    return changed


def choose_source_edge_vertices(
    *, reference: np.ndarray, actual: np.ndarray,
    parent_mask: np.ndarray, panels: list[dict], maximum: int=8,
) -> list[tuple[int,int,int]]:
    """Rank **existing** contour vertices by nearby observed Chrome error."""
    if reference.shape!=actual.shape or reference.shape[:2]!=parent_mask.shape:
        raise ValueError("canonical Chrome source raster shape mismatch")
    if len(panels)!=5 or not 1<=maximum<=12:
        raise ValueError("signed 5-panel vertex ranking contract")
    error=np.argwhere(np.any(reference!=actual,axis=2))
    score:dict[tuple[int,int],int]={}
    for y,x in error:
        weights=[]
        xy=np.array([float(x),float(y)])
        for part,panel in enumerate(panels[:4]):
            points=np.asarray(panel["points"],dtype=float)
            for edge in range(len(points)):
                start,end=points[edge],points[(edge+1)%len(points)]
                segment=end-start
                projection=float(np.clip(np.dot(xy-start,segment)/max(float(np.dot(segment,segment)),1e-9),0,1))
                dist=float(np.linalg.norm(xy-(start+projection*segment)))
                weights.append((dist,part,edge))
        dist,part,edge=min(weights)
        if dist>1.5:
            continue
        for vertex in (edge,(edge+1)%len(panels[part]["points"])):
            key=(part,vertex)
            score[key]=score.get(key,0)+1
    winner=sorted(score,key=lambda k:(-score[k],k[0],k[1]))[:maximum]
    return [(p,v,score[p,v]) for p,v in winner]


def _sha(file:Path)->str:
    return sha256(file.read_bytes()).hexdigest()


def run(*, baseline_dir:Path, outer_scene:Path, apparel_scene:Path,
        chrome_binary:Path, output_dir:Path, maximum_vertices:int=8)->dict:
    if maximum_vertices<1 or maximum_vertices>12:
        raise ValueError("unsafe experiment budget")
    baseline_dir=baseline_dir.resolve()
    output_dir=output_dir.resolve()
    if output_dir==baseline_dir or output_dir in baseline_dir.parents or baseline_dir in output_dir.parents:
        raise ValueError("never overwrite the authorized signed baseline")
    signed_svg=(baseline_dir/"source_bound_vector_mask.svg").read_text("utf-8")
    original_html=(baseline_dir/"source_bound_vector_mask.html").read_text("utf-8")
    current_metrics=json.loads((baseline_dir/"svg_material_parity_metrics.json").read_text("utf-8-sig"))
    browser_execution=json.loads((baseline_dir/"real_chrome_execution.json").read_text("utf-8-sig"))
    data=json.loads(outer_scene.read_text("utf-8-sig"))
    materials=json.loads(apparel_scene.read_text("utf-8-sig"))
    if (
        current_metrics.get("source_sha256")!=data.get("original_source_sha256")
        or current_metrics.get("simplified_apparel_sha256")!=_sha(apparel_scene)
        or current_metrics.get("outer_vector_sha256")!=_sha(outer_scene)
        or current_metrics.get("svg_signed_top_edge_count")!=2
        or current_metrics.get("chrome_execution_provenance_verified") is not True
        or current_metrics.get("browser_mismatched_rgb_pixels")!=45
        or current_metrics.get("production_promotion_authorized") is not False
        or browser_execution.get("screenshot_sha256")!=_sha(baseline_dir/"actual_chrome_headless.png")
        or browser_execution.get("svg_sha256")!=_sha(baseline_dir/"source_bound_vector_mask.svg")
        or browser_execution.get("html_sha256")!=_sha(baseline_dir/"source_bound_vector_mask.html")
        or signed_svg not in original_html
        or signed_svg.count("<polygon ")!=5
        or current_metrics.get("svg_apparel_polygon_vertices")!=27
    ):
        raise ValueError("cannot independently reproduce signed original 45px Chrome evidence")
    existing=data.get("primitives_back_to_front")
    if not isinstance(existing,list) or len(existing)!=11:
        raise ValueError("original outer primitives changed")
    owner=[p for p in existing if p.get("source_mask_owner")=="lower_body"]
    if len(owner)!=1:
        raise ValueError("signed parent missing")
    w,h=int(data["coordinate_space"]["pixel_width"]),int(data["coordinate_space"]["pixel_height"])
    original_owner=rasterize_primitive_candidate(owner[0],width=w,height=h)
    original_panels=materials["apparel_material_polygons"]
    if len(original_panels)!=5 or not all(_simple_polygon(p["points"]) for p in original_panels):
        raise ValueError("signed five clean apparel material polygons required")
    reference=cv2.imread(str(baseline_dir/"authoritative_opencv_material.png"),cv2.IMREAD_COLOR)
    browser=cv2.imread(str(baseline_dir/"actual_chrome_headless.png"),cv2.IMREAD_COLOR)
    if reference is None or browser is None or reference.shape!=(h,w,3):
        raise ValueError("wrong Chrome baseline canvas")
    browser=browser[:h,:w]
    original_tie=np.all(browser==np.asarray(original_panels[4]["color_rgb_observed"][::-1],np.uint8),axis=2)
    original_outside=int(np.count_nonzero(np.any(browser!=255,axis=2)&~original_owner))
    if original_outside!=3:
        raise ValueError("old silhouette overflow not established")
    ranked=choose_source_edge_vertices(reference=reference,actual=browser,parent_mask=original_owner,panels=original_panels,maximum=maximum_vertices)
    candidates=[]
    winner=None
    output_dir.mkdir(parents=True,exist_ok=True)
    active_page=output_dir/"active.html"
    screenshot=output_dir/"active.png"
    for part,vertex,source_votes in ranked:
        for axis in (0,1):
            for delta in (-0.5,0.5):
                try:
                    altered=modify_one_signed_polygon(
                        signed_svg,index=part,vertex=vertex,axis=axis,delta=delta,
                    )
                except ValueError:
                    continue
                html=original_html.replace(signed_svg,altered)
                if html==original_html:
                    raise AssertionError("render-only candidate was not applied")
                active_page.write_text(html,"utf-8")
                if screenshot.exists():screenshot.unlink()
                args=[
                    str(chrome_binary),"--headless=new","--disable-gpu","--no-first-run",
                    "--no-default-browser-check","--disable-extensions","--hide-scrollbars",
                    "--force-device-scale-factor=1","--window-size=800,600",
                    f"--user-data-dir={output_dir/'isolated-profile'}",
                    f"--screenshot={screenshot}",active_page.as_uri(),
                ]
                result=subprocess.run(args,capture_output=True,check=False,timeout=30)
                if result.returncode or not screenshot.exists():
                    raise RuntimeError("actual isolated Chrome failed during source geometry research")
                rendered=cv2.imread(str(screenshot),cv2.IMREAD_COLOR)
                if rendered is None or rendered.shape[0]<h or rendered.shape[1]<w:
                    raise ValueError("invalid Chrome screenshot canvas")
                rendered=rendered[:h,:w]
                diff=cv2.absdiff(reference,rendered)
                tie=np.all(rendered==np.asarray(original_panels[4]["color_rgb_observed"][::-1],np.uint8),axis=2)
                metrics={
                    "material_index":part,"source_vertex_index":vertex,
                    "nearest_mismatch_votes":source_votes,
                    "axis":"xy"[axis],"delta_px":delta,
                    "mismatched_pixels":int(np.count_nonzero(np.any(diff!=0,axis=2))),
                    "severe_mismatch_pixels":int(np.count_nonzero(diff.max(axis=2)>48)),
                    "out_of_signed_owner_painted_pixels":int(np.count_nonzero(np.any(rendered!=255,axis=2)&~original_owner)),
                    "green_necktie_exact_render_pixels_changed":int(np.count_nonzero(tie^original_tie)),
                    "rgb_mae":round(float(diff.mean()),6),
                }
                metrics["source_safe_strict_improvement"]=(
                    metrics["mismatched_pixels"]<45
                    and metrics["out_of_signed_owner_painted_pixels"]<=original_outside
                    and metrics["green_necktie_exact_render_pixels_changed"]==0
                )
                candidates.append(metrics)
                if metrics["source_safe_strict_improvement"] and (
                    winner is None or (metrics["mismatched_pixels"],metrics["severe_mismatch_pixels"],metrics["rgb_mae"])
                    <(winner["mismatched_pixels"],winner["severe_mismatch_pixels"],winner["rgb_mae"])
                ):
                    winner=metrics.copy()
                    shutil.copyfile(screenshot,output_dir/"best_chrome.png")
                    (output_dir/"best_candidate.html").write_text(html,"utf-8")
                    (output_dir/"best_candidate.svg").write_text(altered,"utf-8")
                    print("BEST_REAL_CHROME",json.dumps(winner),flush=True)
        print("RANKED_VERTEX_PROBED",part,vertex,"runs",len(candidates),flush=True)
    evidence={
        "schema":SCHEMA,"source_sha256":current_metrics["source_sha256"],
        "outer_vector_sha256":_sha(outer_scene),"apparel_scene_sha256":_sha(apparel_scene),
        "baseline_chrome_svg_sha256":_sha(baseline_dir/"source_bound_vector_mask.svg"),
        "baseline_chrome_screenshot_sha256":_sha(baseline_dir/"actual_chrome_headless.png"),
        "baseline_mismatched_pixels":45,
        "baseline_off_owner_painted_pixels":original_outside,
        "signed_top_edges_preserved":True,
        "source_material_color_palette_preserved":True,
        "no_green_tie_vertex_changed":True,
        "original_material_vertex_count":27,
        "new_filled_geometry_count":0,
        "vertex_adjustment_magnitude_limit":0.5,
        "source_authorities_modified":False,
        "number_of_tested_vertices":len(ranked),
        "number_of_actual_chrome_trials":len(candidates),
        "source_ranked_vertices":ranked,
        "candidate_metrics":candidates,
        "best_strictly_source_safe_candidate":winner,
        "research_result":"BOUNDED_RENDER_VERTEX_IMPROVEMENT" if winner else "HOLD_NO_SAFE_VERTEX_GAIN",
        "browser_exact_parity_pass":False,
        "full_character_browser_pass":False,
        "production_promotion_authorized":False,
    }
    (output_dir/"source_vertex_paint_probe_metrics.json").write_text(
        json.dumps(evidence,ensure_ascii=False,indent=2)+"\n","utf-8",
    )
    print("SUMMARY",json.dumps({
        "chrome_trials":len(candidates),
        "best":winner,
        "status":evidence["research_result"],
        "production_promotion_authorized":False,
    },ensure_ascii=False),flush=True)
    return evidence


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--baseline-dir",type=Path,required=True)
    p.add_argument("--outer-scene",type=Path,required=True)
    p.add_argument("--apparel-scene",type=Path,required=True)
    p.add_argument("--chrome-bin",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--maximum-vertices",type=int,default=8)
    args=p.parse_args()
    run(baseline_dir=args.baseline_dir,outer_scene=args.outer_scene,
        apparel_scene=args.apparel_scene,chrome_binary=args.chrome_bin,
        output_dir=args.output_dir,maximum_vertices=args.maximum_vertices)


if __name__=="__main__":
    main()
