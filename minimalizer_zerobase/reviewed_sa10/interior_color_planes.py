"""SA10.35 research-only interior color planes, clipped to immutable outer geometry.

No img2img, generative fill, copied source-image pixels, or new face detail.
Candidate palettes are colors *observed* in the original RGB input. Internal
planes are explicitly counted as new SVG subpaths, NOT free 11-primitive geometry.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping

import cv2
import numpy as np

# In particular, FACE, LEFT_ARM, RIGHT_ARM and UNKNOWN are never edited.
INTERIOR_ELIGIBLE_OWNERS = frozenset(("hair", "torso", "major_clothing", "lower_body"))
PROTECTED_OWNERS = frozenset(("face", "left_arm", "right_arm"))
INTERIOR_RESEARCH_SCHEMA = "sa10.35-source-grounded-interior-planes-v1"


def _mask(value: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    result = np.asarray(value)
    if result.ndim != 2 or result.shape != shape:
        raise ValueError("mask must be same-sized, two-dimensional pixels")
    return result.astype(bool)


def _rgb_lab(color: tuple[int, int, int] | list[int]) -> np.ndarray:
    rgb = np.asarray(color, dtype=np.uint8)
    if rgb.shape != (3,):
        raise ValueError("palette color must contain three RGB components")
    return cv2.cvtColor(rgb.reshape(1, 1, 3), cv2.COLOR_RGB2LAB)[0, 0].astype(np.float64)


def _color_provenance(source: np.ndarray, valid: np.ndarray) -> tuple[list[int], np.ndarray]:
    if not np.any(valid):
        raise ValueError("color needs observed source pixels")
    pixels = source[valid].reshape(-1, 3)
    samples = cv2.cvtColor(pixels.reshape(1, -1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float64)
    center = np.median(samples, axis=0)
    # Choosing the closest *actual source pixel* avoids inventing colors.
    distance = np.sum((samples - center) ** 2, axis=1)
    color = [int(x) for x in pixels[int(np.argmin(distance))]]
    return color, _rgb_lab(color)


def _two_centroids(samples: np.ndarray) -> np.ndarray | None:
    """Deterministic 2-color separation in LAB; no random CV2 k-means seed."""
    if len(samples) < 32:
        return None
    axis = int(np.argmax(np.std(samples, axis=0)))
    cut = float(np.median(samples[:, axis]))
    high = samples[:, axis] > cut
    if int(high.sum()) < 16 or int((~high).sum()) < 16:
        return None
    centers = np.vstack([samples[~high].mean(axis=0), samples[high].mean(axis=0)])
    for _ in range(10):
        d = np.sum((samples[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        labels = np.argmin(d, axis=1)
        if not np.any(labels == 0) or not np.any(labels == 1):
            return None
        updated = np.vstack([samples[labels == i].mean(axis=0) for i in range(2)])
        if np.max(np.abs(updated - centers)) < 0.2:
            centers = updated
            break
        centers = updated
    if float(np.linalg.norm(centers[0] - centers[1])) < 24.0:
        return None
    return centers


def _polygon_candidates(binary: np.ndarray, *, max_vertices: int) -> list[list[list[float]]]:
    found, _ = cv2.findContours(binary.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not found:
        return []
    contour = max(found, key=cv2.contourArea)
    perimeter = float(cv2.arcLength(contour, True))
    if perimeter <= 0.0:
        return []
    for ratio in (0.012, 0.02, 0.035, 0.055, 0.08):
        approx = cv2.approxPolyDP(contour, perimeter * ratio, True).reshape(-1, 2)
        if 3 <= len(approx) <= max_vertices:
            return [approx.astype(float).tolist()]
    return []


def rasterize_interior_plane(
    plane: Mapping[str, Any], *, width: int, height: int,
    parent_mask: np.ndarray, protected_mask: np.ndarray,
) -> np.ndarray:
    if plane.get("schema") != INTERIOR_RESEARCH_SCHEMA:
        raise ValueError("unknown interior plane version")
    if plane.get("owner") not in INTERIOR_ELIGIBLE_OWNERS:
        raise ValueError("face/arms/unbound cannot be repainted")
    shape = (height, width)
    parent = _mask(parent_mask, shape)
    protected = _mask(protected_mask, shape)
    points = np.asarray(plane.get("points"), dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2 or not 3 <= len(points) <= 32 or not np.all(np.isfinite(points)):
        raise ValueError("invalid polygon vertices")
    if "observed_rgb" not in plane or len(plane["observed_rgb"]) != 3:
        raise ValueError("source-observed RGB required")
    raster = np.zeros(shape, np.uint8)
    cv2.fillPoly(raster, [np.rint(points).astype(np.int32)], 1)
    return (raster > 0) & parent & ~protected


def propose_interior_plane(
    *, owner: str, parent_primitive_id: str, source_rgb: np.ndarray,
    owner_mask: np.ndarray, parent_palette_rgb: list[int],
    protected_mask: np.ndarray, min_pixels: int = 120,
    minimum_owner_fraction: float = 0.05, maximum_owner_fraction: float = 0.30,
    minimum_owner_mse_reduction: float = 0.075, maximum_vertices: int = 28,
) -> tuple[dict, np.ndarray] | None:
    """One eligible existing-owner subplane, accepted only on raw source LAB MSE."""
    if owner not in INTERIOR_ELIGIBLE_OWNERS:
        return None
    raw = np.asarray(source_rgb)
    if raw.ndim != 3 or raw.shape[2] != 3 or raw.dtype != np.uint8:
        raise ValueError("source must be original uint8 HxWx3 RGB")
    h, w = raw.shape[:2]
    parent = _mask(owner_mask, (h, w))
    protected = _mask(protected_mask, (h, w))
    eligible = parent & ~protected
    total = int(parent.sum())
    if total < 2 * min_pixels or int(eligible.sum()) < 2 * min_pixels:
        return None
    lab = cv2.cvtColor(raw, cv2.COLOR_RGB2LAB).astype(np.float32)
    # Blurring observed LAB *only selects geometric regions*; never paints pixels.
    spatial = cv2.GaussianBlur(lab, (9, 9), sigmaX=2.0)
    centroids = _two_centroids(spatial[eligible].astype(np.float64))
    if centroids is None:
        return None
    baseline_lab = _rgb_lab(parent_palette_rgb)
    old_lab = lab[eligible].astype(np.float64)
    old_error = float(np.mean(np.sum((old_lab - baseline_lab) ** 2, axis=1)))
    if old_error < 1e-10:
        return None
    choices: list[tuple[float, dict, np.ndarray]] = []
    yx_error = np.sum((spatial.astype(np.float64)[..., None, :] - centroids[None, None, :, :]) ** 2, axis=3)
    chosen_map = np.argmin(yx_error, axis=2)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    for cluster in (0, 1):
        label = (chosen_map == cluster) & eligible
        label = cv2.morphologyEx(label.astype(np.uint8), cv2.MORPH_OPEN, kernel) > 0
        label = cv2.morphologyEx(label.astype(np.uint8), cv2.MORPH_CLOSE, kernel) > 0
        label &= eligible
        if int(label.sum()) < min_pixels:
            continue
        polygons = _polygon_candidates(label, max_vertices=maximum_vertices)
        if not polygons:
            continue
        polygon = polygons[0]
        trial = {
            "schema": INTERIOR_RESEARCH_SCHEMA,
            "owner": owner,
            "parent_primitive_id": parent_primitive_id,
            "points": polygon,
            "observed_rgb": [0, 0, 0],
            "parent_palette_rgb": [int(c) for c in parent_palette_rgb],
            "source_provenance": "input-image-original-rgb-inside-existing-owner",
            "additional_geometric_subpath": True,
            "source_bitmap_overlay": False,
            "face_or_arm_repaint": False,
        }
        # Derive palette from the *actual trial polygon area*, not arbitrary kmeans centers.
        trial_mask = rasterize_interior_plane(trial, width=w, height=h, parent_mask=parent, protected_mask=protected)
        area = int(trial_mask.sum())
        fraction = area / total
        if area < min_pixels or not minimum_owner_fraction <= fraction <= maximum_owner_fraction:
            continue
        color, palette_lab = _color_provenance(raw, trial_mask)
        if float(np.linalg.norm(palette_lab - baseline_lab)) < 25.0:
            continue
        trial["observed_rgb"] = color
        old_distance = np.sum((lab.astype(np.float64) - baseline_lab) ** 2, axis=2)
        new_distance = np.sum((lab.astype(np.float64) - palette_lab) ** 2, axis=2)
        difference = float((old_distance[trial_mask] - new_distance[trial_mask]).sum())
        improvement = difference / int(eligible.sum())
        mse_after = old_error - improvement
        relative = float(improvement / old_error)
        if relative < minimum_owner_mse_reduction:
            continue
        trial.update({
            "plane_area_pixels": area,
            "owner_area_pixels": total,
            "area_fraction_of_owner": round(float(fraction), 6),
            "polygon_vertex_count": len(polygon),
            "before_lab_mse": round(old_error, 6),
            "after_lab_mse": round(mse_after, 6),
            "relative_lab_mse_reduction": round(relative, 6),
            "source_rgb_pixel_sha256": sha256(np.ascontiguousarray(raw[trial_mask]).tobytes()).hexdigest(),
        })
        choices.append((relative, trial, trial_mask))
    if not choices:
        return None
    _, best, raster = max(choices, key=lambda x: (x[0], -len(x[1]["points"]), -x[1]["plane_area_pixels"]))
    return best, raster


def render_with_interior_planes(
    *, primitives: list[dict], primitive_masks: Mapping[str, np.ndarray],
    planes: list[dict], protected_mask: np.ndarray,
    background_rgb: tuple[int, int, int] = (235, 235, 235),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Paint at parent's z-order, preserving original silhouette and protected RGB."""
    if not primitives or len(set(p["primitive_id"] for p in primitives)) != len(primitives):
        raise ValueError("unique existing primitives required")
    shape = next(iter(primitive_masks.values())).shape
    if len(shape) != 2:
        raise ValueError("mask canvas invalid")
    protected = _mask(protected_mask, shape)
    base = np.full((*shape, 3), background_rgb, np.uint8)
    edited = base.copy()
    union = np.zeros(shape, dtype=bool)
    by_id: dict[str, list[dict]] = {}
    ids = {p["primitive_id"] for p in primitives}
    for plane in planes:
        if plane.get("parent_primitive_id") not in ids:
            raise ValueError("interior plane parent missing")
        if plane.get("owner") not in INTERIOR_ELIGIBLE_OWNERS:
            raise ValueError("protected owner cannot contain interior plane")
        by_id.setdefault(plane["parent_primitive_id"], []).append(plane)
    if any(len(value) > 1 for value in by_id.values()):
        raise ValueError("at most one additional color plane per existing primitive")
    plane_union = np.zeros(shape, dtype=bool)
    for p in primitives:
        key = p["primitive_id"]
        if key not in primitive_masks:
            raise ValueError("primitive missing original geometry")
        owner_mask = _mask(primitive_masks[key], shape)
        if p.get("structural_support_only") is True:
            if key in by_id:
                raise ValueError("invisible support cannot have new interior colors")
            continue
        union |= owner_mask
        rgb = np.asarray(p["palette_color_rgb"], dtype=np.uint8)
        base[owner_mask] = rgb
        edited[owner_mask] = rgb
        if key in by_id:
            plane = by_id[key][0]
            owner = p.get("semantic_part_id")
            if owner != plane["owner"] or owner in PROTECTED_OWNERS:
                raise ValueError("interior plane owner inconsistent with parent")
            mask = rasterize_interior_plane(plane, width=shape[1], height=shape[0], parent_mask=owner_mask, protected_mask=protected)
            if not np.any(mask):
                raise ValueError("empty candidate interior area")
            color = np.asarray(plane["observed_rgb"], dtype=np.uint8)
            edited[mask] = color
            plane_union |= mask
    if not np.array_equal(base[protected], edited[protected]):
        raise AssertionError("protected face/arms changed")
    if np.any(plane_union & ~union):
        raise AssertionError("interior colors changed outer silhouette")
    if np.any((np.any(base != edited, axis=2)) & ~plane_union):
        raise AssertionError("unexpected exterior pixel change")
    return base, edited, plane_union
