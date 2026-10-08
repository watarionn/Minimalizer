"""SA10.40 opt-in material-edge SVG raster calibration.

This module changes SVG *paint attributes* only. Signed source polygon
vertices, owner clip masks, source colors, semantic order, thin green
necktie and full source SHA lineage remain immutable.

A calibration is NOT a geometric source truth or a production default.
Only a Chrome screenshot and independent source-mask replay can prove
whether the proposed browser paint adjustment is safe on a given image.
"""
from __future__ import annotations

import re
from typing import Any
import math

POLYGON_TAG = re.compile(
    r'<polygon points="[^"]+" fill="#[0-9a-f]{6}" '
    r'stroke="#[0-9a-f]{6}" stroke-width="[^"]+" '
    r'stroke-linejoin="(?:miter|bevel|round)"(?: transform="[^"]+")?'
    r'(?: shape-rendering="[^"]+")?/>'
)
PROHIBITED_SVG = ("<image", "data:image/", "base64,", "<foreignObject")


def _check_number(value: Any, *, name: str, lo: float, hi: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{name} must be a finite number")
    f = float(value)
    if not math.isfinite(f) or f < lo or f > hi:
        raise ValueError(f"{name} outside the authorized render adjustment")
    return f


def _fmt(value: float) -> str:
    return f"{value:g}"


def apply_material_edge_calibration(
    signed_svg: str, proposed: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    """Change only up to four of the five existing paint tags.

    No path vertex/palette changes. Never touch the signed green necktie
    tag (index 4), clip, source-owner mask, SVG dimensions, or draw order.
    """
    if not isinstance(signed_svg, str) or not signed_svg.startswith("<svg "):
        raise ValueError("real signed SVG required")
    if any(bad in signed_svg for bad in PROHIBITED_SVG):
        raise ValueError("bitmap/foreign SVG elements forbidden")
    tags = list(POLYGON_TAG.finditer(signed_svg))
    if len(tags) != 5 or signed_svg.count("<polygon ") != 5:
        raise ValueError("exactly five existing source-grounded material polygon tags required")
    if not isinstance(proposed, list) or not proposed or len(proposed) > 4:
        raise ValueError("one to four non-tie polygons may receive opt-in calibration")

    indices: set[int] = set()
    updates: dict[int, str] = {}
    verified: list[dict[str, Any]] = []
    for entry in proposed:
        if not isinstance(entry, dict) or set(entry) - {"index", "dx", "dy", "stroke_width", "join", "shape_rendering"}:
            raise ValueError("unknown or untrusted SVG raster calibration entry")
        index = entry.get("index")
        if not isinstance(index, int) or isinstance(index, bool) or index not in range(4) or index in indices:
            raise ValueError("source colors 0..3 only, never green tie or duplicate")
        indices.add(index)
        dx = _check_number(entry.get("dx", 0.0), name="dx", lo=-0.5, hi=0.5)
        dy = _check_number(entry.get("dy", 0.0), name="dy", lo=-0.5, hi=0.5)
        width = _check_number(entry.get("stroke_width", 1.0), name="stroke_width", lo=0.75, hi=1.25)
        join = entry.get("join", "miter")
        shape = entry.get("shape_rendering")
        if join not in ("miter", "bevel", "round"):
            raise ValueError("unsupported polygon stroke join")
        if shape not in (None, "crispEdges", "auto", "geometricPrecision"):
            raise ValueError("unsupported SVG raster rendering mode")
        if dx == dy == 0 and width == 1.0 and join == "miter" and shape in (None, "crispEdges"):
            raise ValueError("no-op calibration is not an improvement candidate")

        original = tags[index].group(0)
        revised = original.replace('stroke-width="1"', f'stroke-width="{_fmt(width)}"')
        if revised == original and width != 1:
            raise ValueError("unsigned original stroke rule")
        revised = revised.replace('stroke-linejoin="miter"', f'stroke-linejoin="{join}"')
        if dx or dy:
            revised = revised[:-2] + f' transform="translate({_fmt(dx)} {_fmt(dy)})"/>'
        if shape is not None:
            revised = revised[:-2] + f' shape-rendering="{shape}"/>'
        updates[index] = revised
        verified.append({
            "index": index, "dx": dx, "dy": dy,
            "stroke_width": width, "join": join,
            "shape_rendering": shape,
        })

    new_svg = signed_svg
    for index in sorted(updates, reverse=True):
        match = tags[index]
        new_svg = new_svg[:match.start()] + updates[index] + new_svg[match.end():]
    if any(bad in new_svg for bad in PROHIBITED_SVG):
        raise ValueError("unsafe SVG content")
    revised_tags = list(POLYGON_TAG.finditer(new_svg))
    if len(revised_tags) != 5:
        raise AssertionError("malformed SVG material tags")
    # Zero material vertices/colors/number changed, and in particular tie
    # polygon tag is identical before and after.
    if revised_tags[4].group(0) != tags[4].group(0):
        raise AssertionError("necktie source polygon was modified")
    source_shell = POLYGON_TAG.sub("<SIGNED_MATERIAL/>", signed_svg)
    updated_shell = POLYGON_TAG.sub("<SIGNED_MATERIAL/>", new_svg)
    if source_shell != updated_shell:
        raise AssertionError("source contour/holes/owner mask HTML was touched")
    for i, (before, after) in enumerate(zip(tags, revised_tags)):
        header = r'<polygon points="([^"]+)" fill="(#[0-9a-f]{6})" stroke="(#[0-9a-f]{6})"'
        source_match = re.match(header, before.group(0))
        output_match = re.match(header, after.group(0))
        if source_match is None or output_match is None or source_match.groups() != output_match.groups():
            raise AssertionError(f"source vertices/palette altered in material {i}")
    return new_svg, {
        "schema": "sa10.40-chrome-material-paint-calibration-v1",
        "research_only": True,
        "source_material_polygon_count": 5,
        "green_necktie_tag_unchanged": True,
        "source_polygon_vertex_geometry_unchanged": True,
        "source_rgb_material_palette_unchanged": True,
        "source_owner_mask_and_holes_unchanged": True,
        "added_svg_geometric_paths": 0,
        "material_stroke_paint_pass_count_unchanged": True,
        "opt_in_adjustments": verified,
        "production_promotion_authorized": False,
    }
