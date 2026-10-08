"""SA10.41 all-vector FULL character SVG research renderer.

Preserves the source-defined back/front owner order, three interior planes,
five clothing planes and face-flatten guard. The OpenCV/source raster is NEVER
embedded in SVG. All source 1/2-point rings are made visible to accounting.
Browser raster equivalence is NOT assumed: it must be measured independently.
"""
from __future__ import annotations
from collections import Counter
from typing import Any
import cv2
import numpy as np

from minimalizer_zerobase.composition.artifacts import BACKGROUND_COLOR

SCHEMA="sa10.41-full-character-svg-research-v1"
PROTECTED=("face","left_arm","right_arm")


def _rgb(color: Any)->str:
    if not isinstance(color,(list,tuple)) or len(color)!=3 or any(
        not isinstance(x,(int,np.integer)) or x<0 or x>255 for x in color
    ):
        raise ValueError("signed RGB palette required")
    return "#"+"".join(f"{int(c):02x}" for c in color)


def _pts(points: Any, *, delta:float=0.5)->str:
    arr=np.asarray(points,dtype=np.float64)
    if arr.ndim!=2 or arr.shape[1]!=2 or not len(arr) or not np.all(np.isfinite(arr)):
        raise ValueError("invalid source polygon points")
    return " ".join(f"{x+delta:g},{y+delta:g}" for x,y in arr)


def _path(points: Any, *, delta:float=0.5)->str:
    arr=np.asarray(points,dtype=np.float64)
    if arr.ndim!=2 or arr.shape[1]!=2 or len(arr)<3 or not np.all(np.isfinite(arr)):
        raise ValueError("browser polygon paths require at least three points")
    return "M "+" L ".join(f"{x+delta:g} {y+delta:g}" for x,y in arr)+" Z"


def _contour_mask_svg(
    *, name:str, rings:list[dict], width:int, height:int,
)->tuple[str,dict]:
    """Literal source ring vertex accounting, including 1/2 pixel contours."""
    if not rings:
        raise ValueError("owner cannot have zero source contour rings")
    valid=[]
    micro=[]
    for i,ring in enumerate(rings):
        points=ring.get("points")
        depth=ring.get("depth")
        if not isinstance(points,list) or not isinstance(depth,int) or depth<0:
            raise ValueError("unsigned ring contour")
        if ring.get("role")!=("fill" if depth%2==0 else "hole"):
            raise ValueError("source contour depth/role conflict")
        if len(points)>=3:
            valid.append(_path(points))
        elif len(points)==2:
            raw=np.asarray(points,dtype=np.float64)
            if raw.shape!=(2,2) or not np.all(np.isfinite(raw)):
                raise ValueError("invalid two-point source contour")
            x0,y0=raw[0];x1,y1=raw[1]
            color="#ffffff" if depth%2==0 else "#000000"
            micro.append(f'<line x1="{x0+0.5:g}" y1="{y0+0.5:g}" '
                         f'x2="{x1+0.5:g}" y2="{y1+0.5:g}" '
                         f'stroke="{color}" stroke-width="1" shape-rendering="crispEdges"/>')
        elif len(points)==1:
            raw=np.asarray(points,dtype=np.float64)
            if raw.shape!=(1,2) or not np.all(np.isfinite(raw)):
                raise ValueError("invalid one-point source contour")
            x,y=raw[0]
            color="#ffffff" if depth%2==0 else "#000000"
            micro.append(f'<rect x="{int(np.rint(x))}" y="{int(np.rint(y))}" '
                         f'width="1" height="1" fill="{color}"/>')
        else:
            raise ValueError("empty source contour")
    if not valid:
        # SVG can represent tiny components without pretending they are polygons.
        valid_path=""
    else:
        valid_path=(
            '<path d="'+" ".join(valid)+
            '" fill="#ffffff" fill-rule="evenodd" shape-rendering="crispEdges"/>'
        )
    # Even-odd full rings first, degenerate spans after. This is a browser
    # research approximation to OpenCV drawContours inclusive fill; no parity
    # is claimed or silently inferred from shape existence.
    markup=(
        f'<mask id="{name}" x="0" y="0" width="{width}" height="{height}" '
        f'maskUnits="userSpaceOnUse" maskContentUnits="userSpaceOnUse" mask-type="luminance">'
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#000000"/>'
        +valid_path+"".join(micro)+'</mask>'
    )
    counts={
        "source_ring_count":len(rings),
        "source_ring_vertices":sum(len(r["points"]) for r in rings),
        "source_small_ring_count":sum(len(r["points"])<3 for r in rings),
        "source_singleton_ring_count":sum(len(r["points"])==1 for r in rings),
        "source_two_point_ring_count":sum(len(r["points"])==2 for r in rings),
        "svg_filled_ring_paths":int(bool(valid)),
        "svg_degenerate_rect_or_line_elements":len(micro),
        "svg_usable_polygon_ring_count":len(valid),
    }
    return markup,counts


def _binary_mask_svg(*, name:str, mask:np.ndarray,
                     width:int,height:int, invert:bool=False)->tuple[str,dict]:
    binary=np.asarray(mask,dtype=bool)
    if binary.shape!=(height,width):
        raise ValueError("signed stage04 mask canvas mismatch")
    contours,hierarchy=cv2.findContours(
        binary.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE,
    )
    rings=[]
    for c in contours:
        coords=c.reshape(-1,2).tolist()
        if coords:rings.append({"points":coords,"depth":0,"role":"fill"})
    # OpenCV RETR_TREE contour nesting. Compute depths using parent links and
    # feed even-odd combined SVG path, without embedding a source bitmap.
    if hierarchy is not None:
        records=hierarchy[0]
        for i,row in enumerate(records):
            parent=int(row[3]);depth=0
            while parent>=0:
                depth+=1;parent=int(records[parent][3])
            rings[i]["depth"]=depth
            rings[i]["role"]="hole" if depth%2 else "fill"
    xml,summary=_contour_mask_svg(name=name,rings=rings,width=width,height=height)
    if invert:
        # Foreground face/arms become black in this inverse mask. Use white
        # background with black filled contour, explicitly do not claim parity.
        xml=xml.replace('fill="#000000"/>', 'fill="#ffffff"/>',1)
        xml=xml.replace('fill="#ffffff" fill-rule="evenodd"', 'fill="#000000" fill-rule="evenodd"')
        # Tiny contours need inverse polarity as well; source-mask topology
        # will be checked in actual Chrome, not assumed to match source pixels.
        xml=xml.replace('stroke="#ffffff"', 'stroke="#TEMP"').replace(
            'stroke="#000000"','stroke="#ffffff"').replace('stroke="#TEMP"','stroke="#000000"')
    return xml,summary


def compile_full_character_svg(
    *, records:list[dict], stage9_planes:list[dict],
    garment_panels:list[dict], stage04_masks:dict[str,np.ndarray],
    face_guard_rgb:tuple[int,int,int], width:int,height:int,
)->tuple[str,dict]:
    if width<8 or height<8 or width>4096 or height>4096:
        raise ValueError("signed source canvas size invalid")
    if len(records)!=11 or len({p.get("primitive_id") for p in records})!=11:
        raise ValueError("existing 11 signed source owners mandatory")
    if not isinstance(stage9_planes,list) or len(stage9_planes)>4:
        raise ValueError("untrusted Stage9 plane list")
    if len(garment_panels) not in (0,5):
        raise ValueError("either five observed apparel planes or none (negative control)")
    if garment_panels and [p.get("material") for p in garment_panels]!=[
        "dark_uniform","dark_uniform","white_shirt","white_shirt","green_necktie"
    ]:
        raise ValueError("wrong garment color material or z-order")
    if any(name not in stage04_masks for name in PROTECTED):
        raise ValueError("original face and both arm masks are required")

    elements=[]
    geometry=[]
    source_by_id={p["primitive_id"]:p for p in records}
    for i,p in enumerate(records):
        if p.get("primitive_type")!="polygon" or p.get("source_mask_replay") is not True:
            raise ValueError("only verified source polygon geometry may be painted")
        mark,name=_contour_mask_svg(
            name=f'sa1041-owner-{i}',rings=p["parameters"]["rings"],
            width=width,height=height,
        )
        elements.append(mark)
        geometry.append({
            "owner":p.get("source_mask_owner"),
            "primitive_id":p["primitive_id"],
            "structural_support_only":p.get("structural_support_only") is True,
            **name,
        })
    protected=stage04_masks["face"]|stage04_masks["left_arm"]|stage04_masks["right_arm"]
    protect_svg,protected_budget=_binary_mask_svg(
        name="sa1041-protected-clear",mask=protected,width=width,height=height,
        invert=True,
    )
    face_svg,face_budget=_binary_mask_svg(
        name="sa1041-original-face-guard",mask=stage04_masks["face"],
        width=width,height=height,
    )
    elements.extend([protect_svg,face_svg])
    by_parent={}
    for p in stage9_planes:
        parent=p.get("parent_primitive_id")
        if parent not in source_by_id or p.get("owner")!=source_by_id[parent].get("semantic_part_id"):
            raise ValueError("unbound Stage9 semantic color plane")
        if p.get("owner") in PROTECTED or p.get("owner") not in (
            "hair","torso","major_clothing","lower_body"
        ):
            raise ValueError("stage9 may not add protected facial or arm detail")
        by_parent.setdefault(parent,[]).append(p)
    if any(len(x)!=1 for x in by_parent.values()):
        raise ValueError("only one original Stage9 color plane per owner")
    lower=[p for p in records if p.get("source_mask_owner")=="lower_body"
           and p.get("semantic_part_id")=="lower_body"]
    if len(lower)!=1 or any(
        p.get("parent_primitive_id")!=lower[0]["primitive_id"]
        or p.get("owner")!="lower_body" for p in garment_panels
    ):
        raise ValueError("garments not tied to the existing lower body")
    painting=[]
    for i,part in enumerate(records):
        if part.get("structural_support_only") is True:
            if part["primitive_id"] in by_parent:
                raise ValueError("cannot color invisible structural support")
            continue
        color=_rgb(part["palette_color_rgb"])
        painting.append(
            f'<g data-owner-index="{i}" mask="url(#sa1041-owner-{i})">'
            f'<rect width="{width}" height="{height}" fill="{color}"/>'
        )
        if part["primitive_id"] in by_parent:
            p=by_parent[part["primitive_id"]][0]
            painting.append(
                '<g mask="url(#sa1041-protected-clear)">'
                f'<polygon points="{_pts(p["points"])}" fill="{_rgb(p["observed_rgb"])}" '
                'shape-rendering="crispEdges"/></g>'
            )
        if part["primitive_id"]==lower[0]["primitive_id"]:
            # Clothes inserted at original lower_body owner z-depth; all later
            # real source owners overwrite them. This is equivalent to the
            # signed Stage37 final-visible-owner rule if the browser owner
            # masks/ring inclusion were exact, which must be *tested*.
            painting.append('<g mask="url(#sa1041-protected-clear)">')
            for panel in garment_panels:
                painting.append(
                    f'<polygon points="{_pts(panel["points"])}" '
                    f'fill="{_rgb(panel["color_rgb_observed"])}" shape-rendering="crispEdges"/>'
                )
            painting.append('</g>')
        painting.append('</g>')
    # The original pipeline applies the face guard LAST, to flatten any
    # original stage04 face pixel to a single source-observed color.
    painting.append(
        '<g mask="url(#sa1041-original-face-guard)">'
        f'<rect width="{width}" height="{height}" fill="{_rgb(face_guard_rgb)}"/>'
        '</g>'
    )
    svg=(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" shape-rendering="crispEdges">'
        '<defs>'+"".join(elements)+'</defs>'
        f'<rect width="{width}" height="{height}" fill="{_rgb(BACKGROUND_COLOR)}"/>'
        +"".join(painting)+"</svg>"
    )
    if any(token in svg for token in ("<image","data:image","base64,","<foreignObject")):
        raise AssertionError("SVG may not embed source RGB, PNG, canvas raster or foreign objects")
    outer=sum(v["source_ring_vertices"] for v in geometry)
    extra9=sum(len(p["points"]) for p in stage9_planes)
    apparel=sum(len(p["points"]) for p in garment_panels)
    summary={
        "schema":SCHEMA,
        "original_source_primitive_records":len(records),
        "source_owner_rendered_count":sum(p.get("structural_support_only") is not True for p in records),
        "original_source_ring_vertices_including_support":outer,
        "source_topological_degenerate_ring_count":sum(v["source_small_ring_count"] for v in geometry),
        "source_topological_singleton_ring_count":sum(v["source_singleton_ring_count"] for v in geometry),
        "source_topological_two_point_ring_count":sum(v["source_two_point_ring_count"] for v in geometry),
        "svg_explicit_degenerate_rect_line_elements":sum(v["svg_degenerate_rect_or_line_elements"] for v in geometry),
        "phase9_interior_filled_subpaths":len(stage9_planes),
        "phase9_interior_polygon_vertices":extra9,
        "phase37_apparel_filled_subpaths":len(garment_panels),
        "phase37_apparel_polygon_vertices":apparel,
        "original_protected_mask_source_contour_vertices":protected_budget["source_ring_vertices"],
        "original_face_guard_mask_source_contour_vertices":face_budget["source_ring_vertices"],
        "svg_protected_mask_geometry_counted":True,
        "svg_flat_face_guard_original_stage04_mask_counted":True,
        "combined_visible_source_and_extra_fill_vertices_lower_bound":outer+extra9+apparel,
        "combined_mask_vector_source_vertex_occurrences_counted":(
            outer+extra9+apparel+
            protected_budget["source_ring_vertices"]+face_budget["source_ring_vertices"]
        ),
        "full_scene_svg_mask_primitive_count":len(records)+2,
        "source_order_retained":[p["source_mask_owner"] for p in records],
        "face_eyes_nose_mouth_explicit_geometry_added":False,
        "source_raster_pixels_embedded":False,
        "all_generated_elements_geometric_svg":True,
        "whole_scene_chrome_pixel_parity_proven":False,
        "production_promotion_authorized":False,
        "owner_ring_counts":geometry,
    }
    return svg,summary
