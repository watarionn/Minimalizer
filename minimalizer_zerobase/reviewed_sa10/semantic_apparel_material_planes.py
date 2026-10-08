"""SA10.36: source-provenanced apparel material panels inside a frozen owner.

Research only. Decompose one oversimplified neutral lower-body region into
two dark-uniform, two white-shirt and one narrow necktie geometric subpaths.
No mask/pixel overlay in the candidate: only closed polygons with observed RGB
colors, owner clipping, protected face/arm masks and original z-order.

Every extra subpath is counted; no changes to the existing 11 primitives.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any

import cv2
import numpy as np

from .interior_color_planes import _color_provenance

SCHEMA = "sa10.36-uniform-material-panel-v1"
SEQUENCE = (("dark_uniform", 2), ("white_shirt", 2), ("green_necktie", 1))
MINIMUM_COLOR_PRECISION = {
    "dark_uniform": 0.60,
    "white_shirt": 0.74,
    "green_necktie": 0.82,
}
MAX_NECKTIE_EXPANSION = 1.10


def _rgb_mask_conditions(rgb: np.ndarray) -> dict[str, np.ndarray]:
    channels = rgb.astype(np.int16)
    minimum = np.min(channels, axis=2)
    maximum = np.max(channels, axis=2)
    spread = maximum - minimum
    return {
        "dark_uniform": maximum < 115,
        "white_shirt": (minimum > 175) & (spread < 55),
        "green_necktie": (
            (channels[:, :, 1] > channels[:, :, 0] + 30)
            & (channels[:, :, 1] > channels[:, :, 2] + 25)
        ),
    }


def _components(target: np.ndarray, *, count: int) -> list[np.ndarray]:
    closed = cv2.morphologyEx(
        target.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)
    )
    total, labels, stats, _ = cv2.connectedComponentsWithStats(closed, 8)
    indices = sorted(
        range(1, total), key=lambda k: (-int(stats[k, cv2.CC_STAT_AREA]),
                                       int(stats[k, cv2.CC_STAT_LEFT]))
    )[:count]
    return [labels == index for index in indices]


def _simplified_polygon(region: np.ndarray, *, maximum_vertices: int = 16) -> list[list[float]] | None:
    contours, _ = cv2.findContours(
        region.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    length = float(cv2.arcLength(contour, True))
    if length < 5:
        return None
    for epsilon_ratio in (0.025, 0.035, 0.05, 0.07):
        approximated = cv2.approxPolyDP(contour, epsilon_ratio * length, True)
        points = approximated.reshape(-1, 2)
        if 3 <= len(points) <= maximum_vertices:
            return points.astype(float).tolist()
    return None


def material_polygon_mask(
    panel: dict, *, parent_visible: np.ndarray,
    protected: np.ndarray,
) -> np.ndarray:
    if panel.get("schema") != SCHEMA or panel.get("owner") != "lower_body":
        raise ValueError("invalid owner or semantic apparel panel")
    if panel.get("material") not in dict(SEQUENCE):
        raise ValueError("unexpected apparel material")
    shape = parent_visible.shape
    if protected.shape != shape or len(shape) != 2:
        raise ValueError("parent/protected canvas mismatch")
    points = np.asarray(panel.get("points"), dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2 or not 3 <= len(points) <= 16:
        raise ValueError("material polygon must contain 3-16 source-derived points")
    if not np.all(np.isfinite(points)):
        raise ValueError("nonfinite contour coordinates")
    raster = np.zeros(shape, dtype=np.uint8)
    cv2.fillPoly(raster, [np.rint(points).astype(np.int32)], 1)
    return (raster > 0) & np.asarray(parent_visible).astype(bool) & ~np.asarray(protected).astype(bool)


def propose_source_uniform_panels(
    *, source_rgb: np.ndarray, parent_visible: np.ndarray,
    protected: np.ndarray, parent_primitive_id: str,
) -> tuple[list[dict], dict] | None:
    """Fail closed except for a clear two-panel shirt + central green tie layout."""
    source = np.asarray(source_rgb)
    if (
        source.ndim != 3 or source.shape[2] != 3 or source.dtype != np.uint8
        or not parent_primitive_id
    ):
        raise ValueError("a real RGB input and existing owner primitive ID are required")
    h, w = source.shape[:2]
    parent = np.asarray(parent_visible).astype(bool)
    protect = np.asarray(protected).astype(bool)
    if parent.shape != (h, w) or protect.shape != (h, w):
        raise ValueError("source, owner and protected masks must share a canvas")
    eligible = parent & ~protect
    total_pixels = int(eligible.sum())
    if total_pixels < 2000:
        return None
    target = {name: region & eligible for name, region in _rgb_mask_conditions(source).items()}
    if not (
        target["dark_uniform"].sum() >= 0.20 * total_pixels
        and target["white_shirt"].sum() >= 0.15 * total_pixels
        and target["green_necktie"].sum() >= 0.06 * total_pixels
    ):
        return None
    green_y, green_x = np.nonzero(target["green_necktie"])
    if not len(green_x):
        return None
    # Prevent unrelated bright material components from widening the necktie.
    tie_bounds = (int(green_x.min()), int(green_x.max()))
    candidates = []
    for material, component_count in SEQUENCE:
        components = _components(target[material], count=component_count)
        if len(components) != component_count:
            return None
        source_class = target[material]
        for component in components:
            # Reject detached trim and incidental reflections.
            component_pixels = int(component.sum())
            minimum_fraction = {"dark_uniform": 0.12,
                                "white_shirt": 0.085,
                                "green_necktie": 0.06}[material]
            if component_pixels < minimum_fraction * total_pixels:
                return None
            polygon = _simplified_polygon(component)
            if polygon is None:
                return None
            record: dict[str, Any] = {
                "schema": SCHEMA,
                "parent_primitive_id": parent_primitive_id,
                "owner": "lower_body",
                "material": material,
                "points": polygon,
                "color_rgb_observed": [0, 0, 0],
                "source_rgb_color_provenance": "original-image-RGB-pixel-within-material-class",
                "additional_filled_geometric_subpath": True,
                "original_parent_geometry_mutated": False,
            }
            rendered = material_polygon_mask(
                record, parent_visible=eligible, protected=protect
            )
            region_pixels = int(rendered.sum())
            if not region_pixels:
                return None
            overlap = rendered & source_class
            precision = int(overlap.sum()) / region_pixels
            if precision < MINIMUM_COLOR_PRECISION[material]:
                return None
            if material == "green_necktie":
                if region_pixels > MAX_NECKTIE_EXPANSION * int(source_class.sum()):
                    return None
                xcoords = np.nonzero(rendered)[1]
                if (int(xcoords.min()) < tie_bounds[0] - 2
                        or int(xcoords.max()) > tie_bounds[1] + 2):
                    return None
            color, _ = _color_provenance(source, overlap)
            record["color_rgb_observed"] = color
            record.update({
                "material_class_precision": round(float(precision), 6),
                "source_class_pixels": int(source_class.sum()),
                "panel_area_pixels": region_pixels,
                "source_class_covered_pixels": int(overlap.sum()),
                "polygon_vertex_count": len(polygon),
                "source_class_color_sha256": sha256(
                    np.ascontiguousarray(source[overlap]).tobytes()
                ).hexdigest(),
            })
            candidates.append(record)
    if len(candidates) != 5:
        return None
    report = {
        "status": "FIVE_PROVENANCED_APPAREL_MATERIAL_SUBPATHS",
        "parent_owner": "lower_body",
        "panel_count": len(candidates),
        "source_class_areas": {k: int(v.sum()) for k, v in target.items()},
        "total_extra_vertices": sum(p["polygon_vertex_count"] for p in candidates),
        "necktie_area_ratio": next(p["panel_area_pixels"] / p["source_class_pixels"]
                                 for p in candidates if p["material"] == "green_necktie"),
        "source_necktie_bbox_x": list(tie_bounds),
        "geometry_counted_as_new_filled_subpaths": True,
        "original_parent_color_and_shape_unchanged": True,
    }
    return candidates, report


def render_source_uniform_panels(
    *, base_rgb: np.ndarray, panels: list[dict],
    parent_visible: np.ndarray, protected: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    base = np.asarray(base_rgb)
    if base.ndim != 3 or base.shape[2] != 3 or base.dtype != np.uint8:
        raise ValueError("base must be RGB uint8")
    if parent_visible.shape != base.shape[:2] or protected.shape != base.shape[:2]:
        raise ValueError("owner canvas mismatch")
    if [p.get("material") for p in panels] != [
        "dark_uniform", "dark_uniform", "white_shirt", "white_shirt", "green_necktie"
    ]:
        raise ValueError("wrong clothing layering or incomplete material set")
    if len({p.get("parent_primitive_id") for p in panels}) != 1:
        raise ValueError("mixed semantic parents")
    output = base.copy()
    all_changed = np.zeros(base.shape[:2], dtype=bool)
    for panel in panels:
        mask = material_polygon_mask(
            panel, parent_visible=parent_visible, protected=protected
        )
        color = np.asarray(panel.get("color_rgb_observed"), dtype=np.uint8)
        if color.shape != (3,):
            raise ValueError("source-provenanced RGB palette is required")
        output[mask] = color
        all_changed |= mask
    if not np.array_equal(output[protected], base[protected]):
        raise AssertionError("protected human regions changed")
    if np.any(np.any(output != base, axis=2) & ~all_changed):
        raise AssertionError("unauthorized color change")
    return output, all_changed
