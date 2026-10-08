"""SA10.37 simplify existing apparel polygons without changing material semantics.

Research-only source-grounded vertex pruning. Five painted polygons remain
five polygons; no additional shapes or points or source bitmap overlays.
Accept an edit only after re-rendering the whole color stack and passing hard
owner, original material-class, tie shape and full-color nonregression checks.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any

import cv2
import numpy as np

from .semantic_apparel_material_planes import (
    MINIMUM_COLOR_PRECISION,
    MAX_NECKTIE_EXPANSION,
    _rgb_mask_conditions,
    material_polygon_mask,
    render_source_uniform_panels,
)

SCHEMA = "sa10.37-topology-locked-apparel-geometry-v1"


def _lab_error(source_rgb: np.ndarray, candidate_rgb: np.ndarray, mask: np.ndarray) -> float:
    source_lab = cv2.cvtColor(source_rgb, cv2.COLOR_RGB2LAB).astype(np.float64)
    candidate_lab = cv2.cvtColor(candidate_rgb, cv2.COLOR_RGB2LAB).astype(np.float64)
    return float(np.mean(np.sum((source_lab[mask] - candidate_lab[mask]) ** 2, axis=1)))


def _cross(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    u = b - a
    v = c - a
    return float(u[0] * v[1] - u[1] * v[0])


def _simple_polygon(points: list[list[float]]) -> bool:
    arr = np.asarray(points, dtype=np.float64)
    if len(arr) < 3 or arr.ndim != 2 or arr.shape[1] != 2 or not np.isfinite(arr).all():
        return False
    if abs(float(cv2.contourArea(arr.astype(np.float32)))) < 3.0:
        return False
    n = len(arr)
    for i in range(n):
        a, b = arr[i], arr[(i + 1) % n]
        if np.array_equal(a, b):
            return False
        for j in range(i + 1, n):
            if (j == i + 1 or (i == 0 and j == n - 1)):
                continue
            c, d = arr[j], arr[(j + 1) % n]
            o1, o2 = _cross(a, b, c), _cross(a, b, d)
            o3, o4 = _cross(c, d, a), _cross(c, d, b)
            def endpoint_on_line(point: np.ndarray, start: np.ndarray, end: np.ndarray) -> bool:
                return bool(
                    min(start[0], end[0]) - 1e-9 <= point[0] <= max(start[0], end[0]) + 1e-9
                    and min(start[1], end[1]) - 1e-9 <= point[1] <= max(start[1], end[1]) + 1e-9
                )
            crossing = (
                (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)
                and all(abs(v) > 1e-9 for v in (o1, o2, o3, o4))
            )
            touching = (
                (abs(o1) <= 1e-9 and endpoint_on_line(c, a, b))
                or (abs(o2) <= 1e-9 and endpoint_on_line(d, a, b))
                or (abs(o3) <= 1e-9 and endpoint_on_line(a, c, d))
                or (abs(o4) <= 1e-9 and endpoint_on_line(b, c, d))
            )
            if crossing or touching:
                return False
    return True


def _largest(mask: np.ndarray) -> int:
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    return max((int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, count)), default=0)


def optimize_apparel_polygon_vertices(
    *, original_panels: list[dict], source_rgb: np.ndarray,
    baseline_rgb: np.ndarray, owner_visible: np.ndarray, protected: np.ndarray,
    allowed_lab_mse_increase: float = 0.02,
    minimum_class_overlap_ratio: float = 0.92,
    maximum_change_fraction: float = 0.06,
    minimum_saved_vertices: int = 1,
) -> tuple[list[dict], np.ndarray, dict[str, Any]]:
    """Conservatively delete contour vertices, never vertices of other owners.

    The comparison is always against the full *original five-panel* render.
    No visual-quality or browser-validity approval is implied.
    """
    source = np.asarray(source_rgb)
    base = np.asarray(baseline_rgb)
    if (source.dtype != np.uint8 or base.dtype != np.uint8
            or source.shape != base.shape or source.ndim != 3 or source.shape[2] != 3):
        raise ValueError("RGB input and reference must be uint8 images of identical size")
    h, w = source.shape[:2]
    owner = np.asarray(owner_visible).astype(bool)
    forbidden = np.asarray(protected).astype(bool)
    if owner.shape != (h, w) or forbidden.shape != (h, w):
        raise ValueError("owner and protected mask must match RGB canvas")
    if not 0 <= allowed_lab_mse_increase <= 0.05:
        raise ValueError("cannot loosen source Lab error by more than 5%")
    if not 0.8 <= minimum_class_overlap_ratio <= 1.0:
        raise ValueError("minimum retained material overlap must be at least 80%")
    if not 0 <= maximum_change_fraction <= 0.10 or minimum_saved_vertices < 1:
        raise ValueError("invalid pixel/color simplification budget")
    if [p.get("material") for p in original_panels] != [
        "dark_uniform", "dark_uniform", "white_shirt",
        "white_shirt", "green_necktie",
    ]:
        raise ValueError("five previously signed semantic panels required")
    source_classes = {name: m & owner & ~forbidden
                      for name, m in _rgb_mask_conditions(source).items()}
    tie_mask = source_classes["green_necktie"]
    tie_x = np.flatnonzero(tie_mask.any(axis=0))
    if len(tie_x) == 0:
        raise ValueError("source has no confirmed tie")
    original = deepcopy(original_panels)
    working = deepcopy(original_panels)
    for p in working:
        if p.get("owner") != "lower_body" or not p.get("source_rgb_color_provenance"):
            raise ValueError("material provenance missing")
        if len(p.get("points", [])) < 3:
            raise ValueError("invalid pre-existing material polygon")
    baseline_invalid = [
        i for i, p in enumerate(working) if not _simple_polygon(p["points"])
    ]
    # Signed SA10.36 contour may be self-touching. Never promote unresolved rings.
    original_image, _ = render_source_uniform_panels(
        base_rgb=base, panels=original,
        parent_visible=owner, protected=forbidden,
    )
    signed_pixels = [
        material_polygon_mask(p, parent_visible=owner, protected=forbidden)
        for p in original
    ]
    signed_overlap = [
        int(np.count_nonzero(mask & source_classes[p["material"]]))
        for p, mask in zip(original, signed_pixels)
    ]
    old_lab_error = _lab_error(source, original_image, owner)
    old_vertex_count = sum(len(p["points"]) for p in original)
    original_neutral_rgb = np.asarray(original[0].get("parent_palette_rgb", [104, 91, 86]), np.uint8)
    # The baseline parent color is provided via its existing frozen RGB layer.
    base_color = np.asarray([104, 91, 86], np.uint8)
    # Detect unchanged parent color by scanning a fixed sample known to remain
    # after the five signed panels, using the most-common baseline RGB.
    eligible_pixels = base[owner & ~forbidden].reshape(-1, 3)
    if len(eligible_pixels):
        colors, counts = np.unique(eligible_pixels, axis=0, return_counts=True)
        base_color = colors[int(np.argmax(counts))]
    signed_gray_component = _largest(np.all(original_image == base_color, axis=2) & owner)
    accepted: list[dict] = []
    while True:
        # Repair signed source-contour self intersections BEFORE discretionary
        # reductions; otherwise minor edits can exhaust the color error budget.
        broken = [
            i for i, p in enumerate(working) if not _simple_polygon(p["points"])
        ]
        eligible_changes: list[tuple[float, int, int, np.ndarray, float]] = []
        for part_index, panel in enumerate(working):
            if broken and part_index not in broken:
                continue
            points = panel["points"]
            if len(points) <= 3:
                continue
            for index in range(len(points)):
                candidate = points[:index] + points[index + 1:]
                if not _simple_polygon(candidate):
                    continue
                old_points = panel["points"]
                panel["points"] = candidate
                candidate_mask = material_polygon_mask(
                    panel, parent_visible=owner, protected=forbidden
                )
                panel["points"] = old_points
                if not np.any(candidate_mask):
                    continue
                source_class = source_classes[panel["material"]]
                overlap = int(np.count_nonzero(candidate_mask & source_class))
                area = int(candidate_mask.sum())
                if overlap / area < MINIMUM_COLOR_PRECISION[panel["material"]]:
                    continue
                original_color = np.asarray(panel["color_rgb_observed"], dtype=np.uint8)
                if not np.any(np.all(source[source_class] == original_color, axis=1)):
                    raise ValueError("original palette no longer appears in its source material")
                source_overlap = source[candidate_mask & source_class]
                source_color = np.asarray(panel["color_rgb_observed"], dtype=np.uint8)
                if not np.any(np.all(source_overlap == source_color, axis=1)):
                    continue
                if overlap + 1e-9 < minimum_class_overlap_ratio * signed_overlap[part_index]:
                    continue
                old_area = int(signed_pixels[part_index].sum())
                if area < 0.78 * old_area or area > 1.18 * old_area:
                    continue
                if panel["material"] == "green_necktie":
                    xs = np.flatnonzero(candidate_mask.any(axis=0))
                    if (not len(xs) or xs.min() < tie_x.min() - 2
                            or xs.max() > tie_x.max() + 2
                            or area > MAX_NECKTIE_EXPANSION * int(tie_mask.sum())):
                        continue
                new_panels = deepcopy(working)
                new_panels[part_index]["points"] = candidate
                try:
                    output, painted = render_source_uniform_panels(
                        base_rgb=base, panels=new_panels,
                        parent_visible=owner, protected=forbidden,
                    )
                except ValueError:
                    continue
                changed_against_signed = np.any(output != original_image, axis=2)
                if int(changed_against_signed.sum()) > maximum_change_fraction * int(owner.sum()):
                    continue
                if np.any(changed_against_signed & ~owner) or np.any(changed_against_signed & forbidden):
                    continue
                mse = _lab_error(source, output, owner)
                if mse > old_lab_error * (1.0 + allowed_lab_mse_increase) + 1e-9:
                    continue
                gray_component = _largest(np.all(output == base_color, axis=2) & owner)
                if gray_component > signed_gray_component * 1.02 + 1:
                    continue
                # Closest source fit first, then prefer deleting from complex polygons.
                score = mse / max(old_lab_error, 1.0) + (
                    int(changed_against_signed.sum()) / max(int(owner.sum()), 1)
                ) * 0.14
                eligible_changes.append((score, part_index, index, candidate_mask, mse))
        if not eligible_changes:
            break
        eligible_changes.sort(key=lambda x: (x[0], -len(working[x[1]]["points"]), x[1], x[2]))
        _, chosen_part, chosen_vertex, _, _ = eligible_changes[0]
        working[chosen_part]["points"] = (
            working[chosen_part]["points"][:chosen_vertex]
            + working[chosen_part]["points"][chosen_vertex + 1:]
        )
        accepted.append({
            "material": working[chosen_part]["material"],
            "panel_index": chosen_part,
            "removed_original_or_reindexed_vertex": chosen_vertex,
        })
    output, _ = render_source_uniform_panels(
        base_rgb=base, panels=working,
        parent_visible=owner, protected=forbidden,
    )
    current_lab_error = _lab_error(source, output, owner)
    for i, panel in enumerate(working):
        current_mask = material_polygon_mask(
            panel, parent_visible=owner, protected=forbidden
        )
        class_overlap = current_mask & source_classes[panel["material"]]
        if not np.any(class_overlap):
            raise AssertionError("lost material source provenance")
        panel["polygon_vertex_count"] = len(panel["points"])
        panel["panel_area_pixels"] = int(current_mask.sum())
        panel["source_class_covered_pixels"] = int(class_overlap.sum())
        panel["material_class_precision"] = round(
            float(class_overlap.sum() / current_mask.sum()), 6
        )
        panel["source_class_color_sha256"] = sha256(
            np.ascontiguousarray(source[class_overlap]).tobytes()
        ).hexdigest()
        panel["sa1037_vertex_simplified"] = len(panel["points"]) < len(original[i]["points"])
        if not np.any(np.all(
            source[source_classes[panel["material"]]] == np.asarray(panel["color_rgb_observed"]),
            axis=1,
        )):
            raise ValueError("palette is not observed in the original owner material")
        panel["original_source_palette_rgb_unchanged"] = True
    candidate_invalid = [
        i for i, p in enumerate(working) if not _simple_polygon(p["points"])
    ]
    saved = old_vertex_count - sum(len(p["points"]) for p in working)
    ratio = current_lab_error / old_lab_error if old_lab_error else 1.
    result = {
        "schema": SCHEMA,
        "existing_material_subpaths": len(working),
        "original_total_vertices": old_vertex_count,
        "candidate_total_vertices": old_vertex_count - saved,
        "saved_vertices": saved,
        "baseline_self_intersecting_panels": baseline_invalid,
        "candidate_self_intersecting_panels": candidate_invalid,
        "all_filled_polygons_simple": not candidate_invalid,
        "accepted_vertex_removals": accepted,
        "lab_mse_before": round(old_lab_error, 6),
        "lab_mse_after": round(current_lab_error, 6),
        "relative_mse_delta": round(ratio-1.0, 6),
        "source_color_nonregression_gate": current_lab_error <= old_lab_error * (1+allowed_lab_mse_increase)+1e-9,
        "material_precision_gate": True,
        "all_five_subpaths_and_owners_unchanged": True,
        "face_arm_protected": True,
        "outer_silhouette_unchanged": True,
        "necktie_source_width_protected": True,
        "minimum_saved_vertices_target_met": saved >= minimum_saved_vertices,
        "production_promotion_authorized": False,
        "browser_svg_raster_parity_pending": True,
        "status": (
            "RESEARCH_GEOMETRIC_VERTEX_REDUCTION_HOLD"
            if saved >= minimum_saved_vertices and not candidate_invalid
            else "HOLD_UNRESOLVED_SELF_INTERSECTION"
            if candidate_invalid else "HOLD_NO_SAFE_VERTEX_PRUNING"
        ),
    }
    return working, output, result
