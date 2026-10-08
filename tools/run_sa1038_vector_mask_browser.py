"""SA10.38 source-bound vector-mask Chrome parity research.

All markup is SVG geometry: owner contour paths (with explicit hole-edge
strokes) and the five previously verified, low-vertex apparel polygons.
No PNG/img2img/canvas paint/source pixel embedding, invented body parts,
source-mask relabeling or production promotion.

The raster-neutrally degenerate source ring may be omitted ONLY if an
independent canonical OpenCV replay proves zero changed owner-mask pixels.
Observed Chrome screenshot mismatches are a HARD FAIL, not an assumed pass.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.reviewed_sa10.apparel_vertex_simplifier import _simple_polygon
from minimalizer_zerobase.reviewed_sa10.semantic_apparel_material_planes import (
    material_polygon_mask,
)

SCHEMA = "sa10.38-source-contour-vector-mask-browser-v1"
MATERIAL_SEQUENCE = (
    "dark_uniform","dark_uniform","white_shirt","white_shirt","green_necktie"
)


def _load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError(f"invalid saved JSON object: {path}")
    return obj


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _path(points: list[list[float]], *, shift: float = 0.0) -> str:
    array = np.asarray(points, dtype=np.float64)
    if array.ndim!=2 or array.shape[1]!=2 or len(array)<3 or not np.all(np.isfinite(array)):
        raise ValueError("SVG fill needs a finite closed path of >=3 vertices")
    return "M " + " L ".join(f"{x+shift:g} {y+shift:g}" for x,y in array) + " Z"



def _polygon_points(points: list[list[float]], *, shift: float=0.0) -> str:
    array=np.asarray(points,dtype=np.float64)
    if array.ndim!=2 or array.shape[1]!=2 or len(array)<3 or not np.all(np.isfinite(array)):
        raise ValueError("invalid SVG material polygon")
    return " ".join(f"{x+shift:g},{y+shift:g}" for x,y in array)



def _rgb(color: list[int]) -> str:
    if (not isinstance(color,list) or len(color)!=3
        or not all(isinstance(x,int) and 0<=x<=255 for x in color)):
        raise ValueError("untrusted non-RGB observed material color")
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def prove_degenerate_rings_raster_neutral(
    parent: dict, *, width: int, height: int,
) -> tuple[list[dict], dict]:
    """Reject any omitted micro-ring that changes ONE source-owner pixel."""
    if parent.get("primitive_type")!="polygon":
        raise ValueError("only verified existing polygon source owners supported")
    rings=parent.get("parameters",{}).get("rings")
    if not isinstance(rings,list) or not rings:
        raise ValueError("existing source owner must contain canonical rings")
    valid=[]
    suppressed=[]
    for index,ring in enumerate(rings):
        if not isinstance(ring,dict):
            raise ValueError("untrusted ring entry")
        depth=ring.get("depth")
        points=ring.get("points")
        if not isinstance(depth,int) or depth<0 or not isinstance(points,list) or not points:
            raise ValueError("invalid source contour evidence")
        if ring.get("role")!=("fill" if depth%2==0 else "hole"):
            raise ValueError("invalid source contour nesting")
        if len(points)<3:
            suppressed.append({"ring_index":index,"depth":depth,"point_count":len(points),"points":points})
        else:
            valid.append(ring)
    if not valid:
        raise ValueError("owner has no valid SVG source polygon")
    if suppressed:
        without=deepcopy(parent)
        without["parameters"]=deepcopy(parent["parameters"])
        without["parameters"]["rings"]=deepcopy(valid)
        original_mask=rasterize_primitive_candidate(parent,width=width,height=height)
        without_mask=rasterize_primitive_candidate(without,width=width,height=height)
        difference=int(np.count_nonzero(original_mask^without_mask))
        if difference:
            raise ValueError(f"degenerate source contour changes {difference} owner pixels; SVG omission forbidden")
    else:
        difference=0
    return valid,{
        "degenerate_source_ring_count":len(suppressed),
        "degenerate_source_ring_indices":[r["ring_index"] for r in suppressed],
        "degenerate_source_rings_proven_raster_neutral":True,
        "degenerate_removal_changed_owner_pixels":difference,
        "original_source_ring_count":len(rings),
        "valid_browser_parent_ring_count":len(valid),
    }


def _verified_owner_top_segments(parent: dict, source_rings: list[dict], *, width: int, height: int) -> tuple[list[tuple[float,float,float]],int]:
    """Reuse only recorded horizontal top edges; prove exact top row coverage."""
    parent_mask=rasterize_primitive_candidate(parent,width=width,height=height)
    rows=np.flatnonzero(np.any(parent_mask,axis=1))
    if len(rows)==0:
        raise ValueError("empty signed owner has no top edge")
    top=int(rows[0])
    selected=[]
    for ring in source_rings:
        if ring["depth"]%2:
            continue
        points=ring["points"]
        for index in range(len(points)):
            x0,y0=points[index]
            x1,y1=points[(index+1)%len(points)]
            if abs(y0-top)<1e-9 and abs(y1-top)<1e-9 and abs(x0-x1)>1e-9:
                selected.append((float(min(x0,x1)),float(max(x0,x1)),float(top)))
    selected=sorted(set(selected))
    if not selected:
        raise ValueError("no signed horizontal top contour segment to replay")
    mask_top=np.flatnonzero(parent_mask[top])
    reconstructed=np.unique(np.concatenate([
        np.arange(int(round(x0)),int(round(x1))+1,dtype=np.int32)
        for x0,x1,_ in selected
    ]))
    if not np.array_equal(reconstructed,mask_top):
        raise ValueError("source top-edge segments cannot reproduce canonical owner top-row pixels")
    return selected,top


def prepare_vector_mask(
    *, original_outer_scene: Path, simplified_apparel_scene: Path,
    simplified_apparel_metrics: Path, output_dir: Path,
    parent_dx: float=-0.25, parent_dy: float=0.5,
    material_shift: float=0.5, material_stroke: float=1.0,
    hole_edge_stroke: float=1.0,
    parent_outline_stroke: float=0.0,
    signed_top_edge_stroke: float=0.0,
    signed_top_edge_y_shift: float=1.0,
) -> dict:
    for value in (parent_dx,parent_dy,material_shift):
        if not np.isfinite(value) or abs(value)>1.0:
            raise ValueError("SVG coordinate calibration limited to 1px")
    for value in (material_stroke,hole_edge_stroke):
        if not np.isfinite(value) or not 0.5<=value<=1.5:
            raise ValueError("SVG stroke-width calibration limited to [0.5,1.5]px")
    if not np.isfinite(parent_outline_stroke) or not 0.0<=parent_outline_stroke<=2.0:
        raise ValueError("SVG parent-owner boundary stroke must be within [0,2]px")
    if not np.isfinite(signed_top_edge_stroke) or not 0.0<=signed_top_edge_stroke<=2.0:
        raise ValueError("signed source top-edge stroke must be in [0,2]px")
    if not np.isfinite(signed_top_edge_y_shift) or not 0<=signed_top_edge_y_shift<=1.5:
        raise ValueError("source top-edge coordinate shift cannot exceed 1.5px")
    if signed_top_edge_stroke>0 and parent_outline_stroke>0:
        raise ValueError("cannot stack global parent outline and selective source top edge")
    scene=_load(original_outer_scene)
    garment=_load(simplified_apparel_scene)
    report=_load(simplified_apparel_metrics)
    if (scene.get("schema")!="sa10.34-adaptive-contour-scene-v1"
        or garment.get("schema")!="sa10.37-apparel-simplified-scene-v1"
        or report.get("schema")!="sa10.37-topology-locked-apparel-geometry-v1"
        or report.get("candidate_geometry_sha256")!=_digest(simplified_apparel_scene)
        or garment.get("stage8_outer_vector_sha256")!=_digest(original_outer_scene)
        or scene.get("original_source_sha256")!=garment.get("source_sha256")
        or garment.get("source_sha256")!=report.get("case_source_sha256")
        or report.get("Stage04_source_masks_verified") is not True
        or report.get("Stage36_material_provenance_verified") is not True
        or report.get("all_filled_polygons_simple") is not True
        or report.get("candidate_self_intersecting_panels")!=[]
        or report.get("face_left_right_arm_rgb_unchanged") is not True):
        raise ValueError("not an independently signed source-grounded source/apparel candidate")
    records=scene.get("primitives_back_to_front")
    if not isinstance(records,list) or len(records)!=11:
        raise ValueError("existing original primitive contract changed")
    owners=[p for p in records if p.get("source_mask_owner")=="lower_body"
            and p.get("semantic_part_id")=="lower_body"]
    if len(owners)!=1:
        raise ValueError("must use exactly one existing semantic lower_body owner")
    parent=owners[0]
    apparel=garment.get("apparel_material_polygons")
    if not isinstance(apparel,list) or [p.get("material") for p in apparel]!=list(MATERIAL_SEQUENCE):
        raise ValueError("exactly five signed material subpaths required")
    if not all(p.get("parent_primitive_id")==parent.get("primitive_id")
                   and p.get("owner")=="lower_body"
                   and p.get("schema")=="sa10.36-uniform-material-panel-v1"
                   and p.get("additional_filled_geometric_subpath") is True
                   and _simple_polygon(p.get("points",[])) for p in apparel):
        raise ValueError("owner mismatch or invalid apparel contour geometry")
    space=scene["coordinate_space"]
    width,height=int(space["pixel_width"]),int(space["pixel_height"])
    if width<=0 or height<=0 or width>8192 or height>8192:
        raise ValueError("invalid canvas")
    source_rings,neutral=prove_degenerate_rings_raster_neutral(
        parent,width=width,height=height,
    )
    source_filled_path=" ".join(_path(r["points"],shift=material_shift) for r in source_rings)
    hole_paths=[_path(r["points"],shift=material_shift)
                for r in source_rings if r["depth"]%2==1]
    material_paths=[_polygon_points(p["points"],shift=material_shift) for p in apparel]
    mask_trans=f"translate({parent_dx:g} {parent_dy:g})"
    # Optional extra white paint pass on the *existing source contour*.
    # Count its reused contour points explicitly; it is not free geometry.
    parent_outline_css=(
        f' stroke="#ffffff" stroke-width="{parent_outline_stroke:g}" stroke-linejoin="round"'
        if parent_outline_stroke>0 else ""
    )
    head=(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">'
        '<defs><mask id="signed-existing-lower-body" maskUnits="userSpaceOnUse" '
        'maskContentUnits="userSpaceOnUse" mask-type="luminance" '
        f'x="0" y="0" width="{width}" height="{height}">'
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#000000"/>'
        f'<path d="{source_filled_path}" fill="#ffffff" fill-rule="evenodd" '
        f'transform="{mask_trans}"{parent_outline_css} shape-rendering="crispEdges"/>'
    )
    if signed_top_edge_stroke>0:
        top_segments,top_y=_verified_owner_top_segments(
            parent,source_rings,width=width,height=height,
        )
    else:
        top_segments=[]
        top_y=None
    top_svg=[
        f'<path d="M {x0+material_shift:g} {y+signed_top_edge_y_shift:g} '
        f'L {x1+material_shift:g} {y+signed_top_edge_y_shift:g}" '
        f'fill="none" stroke="#ffffff" stroke-width="{signed_top_edge_stroke:g}" '
        f'shape-rendering="crispEdges"/>'
        for x0,x1,y in top_segments
    ]
    hole_svg=[
        f'<path d="{data}" fill="none" stroke="#ffffff" '
        f'stroke-width="{hole_edge_stroke:g}" shape-rendering="crispEdges"/>'
        for data in hole_paths
    ]
    # Hole boundary stroke is a separate, explicitly counted SVG paint pass.
    # This mirrors OpenCV filled-contour boundary inclusion in mask semantics.
    svg=''.join([
        head,*hole_svg,*top_svg,'</mask></defs>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        '<g mask="url(#signed-existing-lower-body)">',
        *[
            f'<polygon points="{d}" fill="{_rgb(p["color_rgb_observed"])}" '
            f'stroke="{_rgb(p["color_rgb_observed"])}" '
            f'stroke-width="{material_stroke:g}" stroke-linejoin="miter"/>'
            for p,d in zip(apparel,material_paths)
        ],
        '</g></svg>',
    ])
    html=''.join([
        '<!doctype html><html><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<style>html,body{margin:0;padding:0;background:#ffffff;overflow:hidden}'
        'svg{display:block}</style></head><body>',
        svg,'</body></html>',
    ])
    parent_mask=rasterize_primitive_candidate(parent,width=width,height=height)
    expected=np.full((height,width,3),255,dtype=np.uint8)
    for panel in apparel:
        region=material_polygon_mask(
            panel,parent_visible=parent_mask,
            protected=np.zeros((height,width),dtype=bool),
        )
        expected[region]=np.asarray(panel["color_rgb_observed"],dtype=np.uint8)
    output_dir=output_dir.resolve()
    for authority in (original_outer_scene,simplified_apparel_scene,simplified_apparel_metrics):
        if output_dir==authority.resolve() or authority.resolve() in output_dir.parents:
            raise ValueError("research output may not overwrite source authorities")
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/"source_bound_vector_mask.svg").write_text(svg,encoding="utf-8")
    (output_dir/"source_bound_vector_mask.html").write_text(html,encoding="utf-8")
    if not cv2.imwrite(str(output_dir/"authoritative_opencv_material.png"),
                       cv2.cvtColor(expected,cv2.COLOR_RGB2BGR)):
        raise ValueError("OpenCV research baseline image write failed")
    metrics={
        "schema":SCHEMA,
        "source_sha256":garment["source_sha256"],
        "outer_vector_sha256":_digest(original_outer_scene),
        "simplified_apparel_sha256":_digest(simplified_apparel_scene),
        "source_owner":"lower_body",
        "owner_primitive_id":parent["primitive_id"],
        "signed_original_primitive_count":len(records),
        "svg_apparel_filled_subpath_count":len(apparel),
        "svg_apparel_polygon_vertices":sum(len(p["points"]) for p in apparel),
        "source_owner_svg_mask_ring_vertices":sum(len(r["points"]) for r in source_rings),
        "svg_mask_hole_boundary_stroke_paths":len(hole_paths),
        "svg_parent_outline_stroke_px":parent_outline_stroke,
        "svg_signed_top_edge_stroke_px":signed_top_edge_stroke,
        "svg_signed_top_edge_y_offset_px":signed_top_edge_y_shift if top_segments else None,
        "svg_signed_top_edge_y_original":top_y,
        "svg_signed_top_edge_count":len(top_segments),
        "svg_signed_top_edge_reused_endpoint_occurrences":len(top_segments)*2,
        "svg_signed_top_edge_paint_passes_are_counted":True,
        "svg_signed_top_edge_top_row_exact_replay_verified":bool(top_segments),
        "svg_signed_top_edge_source_segments":[[x0,x1,y] for x0,x1,y in top_segments],
        "svg_parent_outline_stroke_paint_passes":int(parent_outline_stroke>0),
        "svg_parent_outline_reused_ring_point_occurrences":(
            sum(len(r["points"]) for r in source_rings) if parent_outline_stroke>0 else 0
        ),
        "svg_parent_outline_extra_stroke_counted":True,
        "svg_mask_hole_boundary_stroke_vertices":sum(len(r["points"]) for r in source_rings if r["depth"]%2==1),
        "added_hole_boundary_svg_stroke_paint_passes_are_counted":True,
        **neutral,
        "svg_parent_offset":[parent_dx,parent_dy],
        "svg_material_offset":material_shift,
        "svg_material_border_stroke_px":material_stroke,
        "svg_hole_boundary_stroke_px":hole_edge_stroke,
        "source_bitmap_or_base64_raster_embedded":False,
        "outside_owner_no_raster_inpainting":True,
        "isolated_material_layer_only_not_full_scene":True,
        "browser_screenshot_verified":False,
        "exact_browser_opencv_pixel_parity":False,
        "browser_svg_gate":"UNVERIFIED",
        "production_promotion_authorized":False,
        "gate_blockers":[
            "BROWSER_PIXEL_PARITY_UNVERIFIED",
            "OUTER_AND_COMBINED_GEOMETRY_BUDGET_NOT_PASSED",
            "HUMAN_VISUAL_APPROVAL_PENDING",
        ],
    }
    (output_dir/"svg_material_parity_metrics.json").write_text(
        json.dumps(metrics,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps({
        "status":"SVG_VECTOR_MASK_PREPARED",
        "source":metrics["source_sha256"],
        "apparel_vertices":metrics["svg_apparel_polygon_vertices"],
        "owner_contour_rings":metrics["valid_browser_parent_ring_count"],
        "verified_neutral_degenerate_rings":metrics["degenerate_source_ring_count"],
        "hole_boundary_strokes":metrics["svg_mask_hole_boundary_stroke_paths"],
        "dir":str(output_dir),
    },ensure_ascii=False,indent=2))
    return metrics



def render_and_verify_chrome(*, output_dir: Path, chrome_executable: Path) -> dict:
    """Launch the actual Chromium executable before comparing signed pixels."""
    output_dir=output_dir.resolve()
    chrome_executable=chrome_executable.resolve()
    input_html=output_dir/"source_bound_vector_mask.html"
    input_svg=output_dir/"source_bound_vector_mask.svg"
    if not chrome_executable.is_file() or not input_html.is_file() or not input_svg.is_file():
        raise ValueError("actual Chrome binary and both signed vector assets required")
    report=_load(output_dir/"svg_material_parity_metrics.json")
    if report.get("schema")!=SCHEMA:
        raise ValueError("invalid browser probe schema")
    html_hash=_digest(input_html)
    svg_hash=_digest(input_svg)
    screenshot=output_dir/"actual_chrome_headless.png"
    # Chromium is launched with a fresh isolated user data directory; never
    # open the user's normal Chrome profile or access network images.
    argv=[
        str(chrome_executable), "--headless=new", "--disable-gpu",
        "--no-first-run","--no-default-browser-check","--disable-extensions",
        "--hide-scrollbars","--force-device-scale-factor=1",
        "--window-size=800,600",
        f"--user-data-dir={output_dir/'chrome-isolated-profile'}",
        f"--screenshot={screenshot}", input_html.as_uri(),
    ]
    run=subprocess.run(
        argv,capture_output=True,timeout=40,check=False
    )
    if run.returncode!=0 or not screenshot.is_file():
        raise ValueError(
            f"real headless Chrome did not produce a verified screenshot: exit {run.returncode}"
        )
    # Version output may be missing on packaged Windows Chrome. Record both
    # executable identity and byte hash instead of fabricating a version.
    try:
        version=subprocess.run(
            [str(chrome_executable),"--version"],capture_output=True,timeout=2,
            check=False
        )
        version_stdout=version.stdout.decode("utf-8","replace").strip()
        version_exit_code=version.returncode
        version_probe_status="OK" if version.returncode==0 else "NONZERO_EXIT"
    except subprocess.TimeoutExpired:
        # Windows packaged Chrome can hang when launched with --version
        # without a console. Browser validity is proven by the actual
        # headless screenshot and executable SHA, NOT this optional probe.
        version_stdout=""
        version_exit_code=None
        version_probe_status="TIMEOUT_OPTIONAL"
    execution={
        "schema":"sa10.38-real-chrome-execution-v1",
        "chrome_binary_sha256":_digest(chrome_executable),
        "chrome_version_stdout":version_stdout,
        "chrome_version_probe_status":version_probe_status,
        "chrome_version_exit_code":version_exit_code,
        "chrome_run_exit_code":run.returncode,
        "html_sha256":html_hash,
        "svg_sha256":svg_hash,
        "screenshot_sha256":_digest(screenshot),
        "window_size":[800,600],
        "device_pixel_ratio":1,
        "used_private_isolated_chrome_profile":True,
        "browser_engine_executed":True,
        "production_promotion_authorized":False,
    }
    (output_dir/"real_chrome_execution.json").write_text(
        json.dumps(execution,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    return evaluate_real_chrome(output_dir=output_dir)


def evaluate_real_chrome(*, output_dir: Path) -> dict:
    output_dir=output_dir.resolve()
    metrics_path=output_dir/"svg_material_parity_metrics.json"
    report=_load(metrics_path)
    if report.get("schema")!=SCHEMA:
        raise ValueError("expected SA10.38 signed SVG probe")
    expected=cv2.imread(str(output_dir/"authoritative_opencv_material.png"),cv2.IMREAD_COLOR)
    actual_image=cv2.imread(str(output_dir/"actual_chrome_headless.png"),cv2.IMREAD_COLOR)
    if expected is None or actual_image is None or actual_image.shape[0]<expected.shape[0] or actual_image.shape[1]<expected.shape[1]:
        raise ValueError("real Chrome screenshot is absent or has wrong canvas")
    height,width=expected.shape[:2]
    browser=actual_image[:height,:width]
    delta=cv2.absdiff(browser,expected)
    mismatch=np.any(delta!=0,axis=2)
    severe=delta.max(axis=2)
    background=np.array([255,255,255],dtype=np.uint8)
    colored_ref=np.any(expected!=background,axis=2)
    colored_browser=np.any(browser!=background,axis=2)
    edge=cv2.Canny(cv2.cvtColor(expected,cv2.COLOR_BGR2GRAY),50,100)
    near=cv2.dilate(edge,np.ones((3,3),np.uint8))>0
    execution_path=output_dir/"real_chrome_execution.json"
    if execution_path.is_file():
        execution=_load(execution_path)
        browser_executed=(
            execution.get("schema")=="sa10.38-real-chrome-execution-v1"
            and execution.get("browser_engine_executed") is True
            and execution.get("chrome_run_exit_code")==0
            and execution.get("html_sha256")==_digest(output_dir/"source_bound_vector_mask.html")
            and execution.get("svg_sha256")==_digest(output_dir/"source_bound_vector_mask.svg")
            and execution.get("screenshot_sha256")==_digest(output_dir/"actual_chrome_headless.png")
            and execution.get("used_private_isolated_chrome_profile") is True
        )
        if not browser_executed:
            raise ValueError("Chrome execution evidence does not match current SVG and screenshot")
    else:
        browser_executed=False
    report.update({
        "browser_screenshot_verified":True,
        "chrome_execution_provenance_verified":browser_executed,
        "chrome_canvas_pixels":[width,height],
        "browser_mismatched_rgb_pixels":int(np.count_nonzero(mismatch)),
        "browser_mismatched_rgb_pixels_strong_gt48":int(np.count_nonzero(severe>48)),
        "browser_rgb_mae":round(float(delta.mean()),6),
        "browser_occupancy_disagreement_pixels":int(np.count_nonzero(colored_ref^colored_browser)),
        "browser_color_mismatch_in_jointly_painted_pixels":int(np.count_nonzero(mismatch&colored_ref&colored_browser)),
        "browser_mismatch_near_reference_edges":int(np.count_nonzero(mismatch&near)),
        "browser_mismatch_far_reference_edges":int(np.count_nonzero(mismatch&~near)),
        "exact_browser_opencv_pixel_parity":bool(not np.any(mismatch)),
        "browser_svg_gate":"PASS" if not np.any(mismatch) and browser_executed else "FAIL",
        "production_promotion_authorized":False,
    })
    report["gate_blockers"]=([
        "BROWSER_PIXEL_PARITY_FAIL" if np.any(mismatch) else "",
        "OUTER_AND_COMBINED_GEOMETRY_BUDGET_NOT_PASSED",
        "HUMAN_VISUAL_APPROVAL_PENDING",
        "" if browser_executed else "REAL_CHROME_EXECUTION_NOT_ATTESTED",
    ])
    report["gate_blockers"]=[x for x in report["gate_blockers"] if x]
    if not cv2.imwrite(str(output_dir/"chrome_vs_opencv_pixel_diff.png"),
                np.clip(delta.astype(np.int16)*2,0,255).astype(np.uint8)):
        raise ValueError("pixel difference heatmap write failed")
    metrics_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "svg_browser_gate":report["browser_svg_gate"],
        "mismatched_pixels":report["browser_mismatched_rgb_pixels"],
        "strong_rgb_mismatches":report["browser_mismatched_rgb_pixels_strong_gt48"],
        "neutral_degenerate_rings":report["degenerate_source_ring_count"],
        "added_stroke_paint_passes_counted":report["svg_mask_hole_boundary_stroke_paths"],
    },ensure_ascii=False,indent=2))
    return report


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--outer-scene",type=Path)
    p.add_argument("--apparel-scene",type=Path)
    p.add_argument("--apparel-metrics",type=Path)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--compare-chrome",action="store_true")
    p.add_argument("--render-chrome",action="store_true")
    p.add_argument("--chrome-bin",type=Path)
    p.add_argument("--parent-dx",type=float,default=-0.25)
    p.add_argument("--parent-dy",type=float,default=0.5)
    p.add_argument("--material-shift",type=float,default=0.5)
    p.add_argument("--material-stroke",type=float,default=1.0)
    p.add_argument("--hole-stroke",type=float,default=1.0)
    p.add_argument("--parent-outline-stroke",type=float,default=0.0)
    p.add_argument("--signed-top-edge-stroke",type=float,default=0.0)
    p.add_argument("--signed-top-edge-y-shift",type=float,default=1.0)
    args=p.parse_args()
    if args.compare_chrome and args.render_chrome:
        raise ValueError("choose one real Chrome execution mode")
    if args.render_chrome:
        if args.chrome_bin is None:
            raise ValueError("--chrome-bin required for real Chrome launch")
        render_and_verify_chrome(output_dir=args.output_dir,chrome_executable=args.chrome_bin)
    elif args.compare_chrome:
        evaluate_real_chrome(output_dir=args.output_dir)
    else:
        if not args.outer_scene or not args.apparel_scene or not args.apparel_metrics:
            raise ValueError("all three signed geometry authority paths are required")
        prepare_vector_mask(
            original_outer_scene=args.outer_scene,
            simplified_apparel_scene=args.apparel_scene,
            simplified_apparel_metrics=args.apparel_metrics,
            output_dir=args.output_dir,
            parent_dx=args.parent_dx,parent_dy=args.parent_dy,
            material_shift=args.material_shift,material_stroke=args.material_stroke,
            hole_edge_stroke=args.hole_stroke,
            parent_outline_stroke=args.parent_outline_stroke,
            signed_top_edge_stroke=args.signed_top_edge_stroke,
            signed_top_edge_y_shift=args.signed_top_edge_y_shift,
        )


if __name__=="__main__":
    main()
