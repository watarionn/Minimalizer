from __future__ import annotations

from dataclasses import dataclass, replace
import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.pipeline import (
    MinimalizerV2Result,
    SceneModel,
    SceneShape,
    _semantic_part_shape_limit,
)
from minimalize_engine.v2.primitive.scoring import rasterize_geometry
from minimalize_engine.v2.render import render_scene


@dataclass(frozen=True, slots=True)
class SemanticAdvisorCandidate:
    """One hidden semantic plane that measurably changes rendered output.

    The candidate is observation-only. It carries numeric/runtime features for
    a separate semantic advisor and never changes scene visibility itself.
    """

    part_name: str
    preset: str
    region_id: int
    support_pixels: int
    support_ratio: float
    color_distance_to_dominant: float
    color_distance_to_nearest_visible: float
    adjacent_to_near_color: bool
    adjacency_gap_px: float
    coverage_without_candidate: float
    outside_part_ratio: float
    current_plane_count: int
    visible_plane_count: int
    target_plane_limit: int
    geometry_vertices: int
    is_largest_plane: bool
    changed_pixels: int
    changed_ratio_of_part: float
    source_part_mae_improvement: float

    def as_dict(self) -> dict[str, object]:
        return {
            "part_name": self.part_name,
            "preset": self.preset,
            "region_id": self.region_id,
            "support_pixels": self.support_pixels,
            "support_ratio": self.support_ratio,
            "color_distance_to_dominant": self.color_distance_to_dominant,
            "color_distance_to_nearest_visible": self.color_distance_to_nearest_visible,
            # Backward-compatible Jev feature key used by the isolation lab.
            "color_distance_to_nearest_kept": self.color_distance_to_nearest_visible,
            "adjacent_to_near_color": self.adjacent_to_near_color,
            "adjacency_gap_px": self.adjacency_gap_px,
            "coverage_without_candidate": self.coverage_without_candidate,
            "outside_part_ratio": self.outside_part_ratio,
            "current_plane_count": self.current_plane_count,
            "visible_plane_count": self.visible_plane_count,
            "target_plane_limit": self.target_plane_limit,
            "geometry_vertices": self.geometry_vertices,
            "is_largest_plane": self.is_largest_plane,
            "changed_pixels": self.changed_pixels,
            "changed_ratio_of_part": self.changed_ratio_of_part,
            "source_part_mae_improvement": self.source_part_mae_improvement,
        }


def _geometry_vertex_count(shape: SceneShape) -> int:
    geometry = shape.geometry
    if geometry.kind == "polygon":
        return int(sum(len(loop) for loop in geometry.loops))
    points = geometry.points
    return 0 if points is None else int(len(points))


def _mask_for_shape(
    shape: SceneShape,
    image_shape: tuple[int, int],
) -> NDArray[np.bool_]:
    return np.asarray(
        rasterize_geometry(
            shape.geometry,
            image_shape,
            origin=(0, 0),
            scale=2,
        ),
        dtype=bool,
    )


def _gap_pixels(
    mask: NDArray[np.bool_],
    other: NDArray[np.bool_],
) -> float:
    if np.any(mask & other):
        return 0.0
    if not np.any(mask) or not np.any(other):
        return float("inf")
    inverse = (~other).astype(np.uint8)
    distance = cv2.distanceTransform(inverse, cv2.DIST_L2, 3)
    values = distance[mask]
    return float(values.min()) if values.size else float("inf")


def probe_semantic_scene(
    scene: SceneModel,
    part_mask: NDArray[np.bool_],
    source_rgb: NDArray[np.uint8],
    *,
    part_name: str,
    preset: str,
    target_plane_limit: int,
    near_color_distance: float = 54.0,
    adjacency_radius_px: float = 2.5,
) -> tuple[SemanticAdvisorCandidate, ...]:
    """Probe hidden planes without mutating the scene.

    Only hidden shapes whose restoration changes rendered output inside the
    semantic part are returned. Approved/reference imagery is never used.
    """

    mask = np.asarray(part_mask, dtype=bool)
    source = np.asarray(source_rgb, dtype=np.uint8)
    if mask.shape != (scene.height, scene.width):
        raise ValueError("part_mask must match scene dimensions")
    if source.shape != (scene.height, scene.width, 3):
        raise ValueError("source_rgb must match scene dimensions")

    shapes = list(scene.shapes)
    palette_rgb = {
        entry.palette_id: np.asarray(entry.rgb, dtype=np.float32)
        for entry in scene.palette
    }

    geometry_masks = [
        _mask_for_shape(shape, mask.shape)
        for shape in shapes
    ]
    supports = [
        int(np.count_nonzero(geometry_mask & mask))
        for geometry_mask in geometry_masks
    ]
    active = [index for index, support in enumerate(supports) if support > 0]
    if not active:
        return ()

    part_pixels = max(int(np.count_nonzero(mask)), 1)
    largest_index = max(active, key=lambda index: (supports[index], -index))
    largest_rgb = palette_rgb.get(shapes[largest_index].palette_id)

    visible = [
        index for index in active
        if bool(shapes[index].visible)
    ]
    current = render_scene(scene, include_facets=False)
    current_float = current.astype(np.float32)
    source_float = source.astype(np.float32)
    current_source_error = float(
        np.abs(current_float[mask] - source_float[mask]).mean()
    )

    full_union = np.zeros(mask.shape, dtype=bool)
    for index in active:
        full_union |= geometry_masks[index] & mask
    full_pixels = max(int(np.count_nonzero(full_union)), 1)

    candidates: list[SemanticAdvisorCandidate] = []
    for index in active:
        shape = shapes[index]
        if shape.visible:
            continue

        restored_shapes = list(shapes)
        restored_shapes[index] = replace(shape, visible=True)
        restored_scene = replace(scene, shapes=tuple(restored_shapes))
        restored = render_scene(restored_scene, include_facets=False)

        changed = (
            np.any(restored != current, axis=2)
            & mask
        )
        changed_pixels = int(np.count_nonzero(changed))
        if changed_pixels == 0:
            continue

        restored_float = restored.astype(np.float32)
        restored_source_error = float(
            np.abs(restored_float[mask] - source_float[mask]).mean()
        )

        geometry_mask = geometry_masks[index]
        total_geometry_pixels = max(int(np.count_nonzero(geometry_mask)), 1)
        support = supports[index]

        candidate_rgb = palette_rgb.get(shape.palette_id)
        dominant_distance = 0.0
        if candidate_rgb is not None and largest_rgb is not None:
            dominant_distance = float(
                np.linalg.norm(candidate_rgb - largest_rgb)
            )

        nearest_visible_distance: float | None = None
        nearest_gap = float("inf")
        adjacent_near = False
        if candidate_rgb is not None:
            for other_index in visible:
                other_rgb = palette_rgb.get(shapes[other_index].palette_id)
                if other_rgb is None:
                    continue
                color_distance = float(
                    np.linalg.norm(candidate_rgb - other_rgb)
                )
                if (
                    nearest_visible_distance is None
                    or color_distance < nearest_visible_distance
                ):
                    nearest_visible_distance = color_distance
                if color_distance <= near_color_distance:
                    gap = _gap_pixels(
                        geometry_mask,
                        geometry_masks[other_index],
                    )
                    nearest_gap = min(nearest_gap, gap)
                    if gap <= adjacency_radius_px:
                        adjacent_near = True

        other_union = np.zeros(mask.shape, dtype=bool)
        for other_index in active:
            if other_index == index:
                continue
            other_union |= geometry_masks[other_index] & mask
        coverage_without = (
            int(np.count_nonzero(other_union & full_union))
            / float(full_pixels)
        )

        candidates.append(
            SemanticAdvisorCandidate(
                part_name=part_name,
                preset=preset,
                region_id=int(shape.region_id),
                support_pixels=support,
                support_ratio=support / float(part_pixels),
                color_distance_to_dominant=dominant_distance,
                color_distance_to_nearest_visible=(
                    dominant_distance
                    if nearest_visible_distance is None
                    else nearest_visible_distance
                ),
                adjacent_to_near_color=adjacent_near,
                adjacency_gap_px=(
                    999.0 if not np.isfinite(nearest_gap) else nearest_gap
                ),
                coverage_without_candidate=coverage_without,
                outside_part_ratio=(
                    int(np.count_nonzero(geometry_mask & ~mask))
                    / float(total_geometry_pixels)
                ),
                current_plane_count=len(active),
                visible_plane_count=len(visible),
                target_plane_limit=int(target_plane_limit),
                geometry_vertices=_geometry_vertex_count(shape),
                is_largest_plane=index == largest_index,
                changed_pixels=changed_pixels,
                changed_ratio_of_part=changed_pixels / float(part_pixels),
                source_part_mae_improvement=(
                    current_source_error - restored_source_error
                ),
            )
        )

    return tuple(candidates)


def collect_semantic_advisor_candidates(
    result: MinimalizerV2Result,
    *,
    preset: str = "minimal",
) -> tuple[SemanticAdvisorCandidate, ...]:
    """Collect render-impacting hidden semantic planes across person parts.

    This function is side-effect free. It never writes to the result, never
    changes SceneShape.visible, and never changes rendered output.
    """

    if result.person_parts is None:
        return ()

    source = np.asarray(result.bundle.analysis_rgb, dtype=np.uint8)
    candidates: list[SemanticAdvisorCandidate] = []

    for part_name, part_mask in result.person_parts.part_masks.items():
        part_presets = result.person_part_presets.get(part_name)
        if not part_presets or preset not in part_presets:
            continue
        preset_result = part_presets[preset]
        candidates.extend(
            probe_semantic_scene(
                preset_result.scene,
                np.asarray(part_mask, dtype=bool),
                source,
                part_name=part_name,
                preset=preset,
                target_plane_limit=_semantic_part_shape_limit(
                    part_name,
                    preset,
                ),
            )
        )

    return tuple(candidates)
