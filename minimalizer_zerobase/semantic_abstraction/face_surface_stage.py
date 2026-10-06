from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.render import SvgRenderer

FACE_SURFACE_STAGE_VERSION = "sa7.38-v1"


@dataclass(frozen=True)
class FaceSurfaceResult:
    scene: VectorScene
    svg: str
    fill_rgb: tuple[int, int, int]
    polygon_count: int
    covered_pixels: int
    face_pixels: int
    outside_face_pixels: int


def _observed_representative_rgb(
    source_rgb: np.ndarray,
    face_mask: np.ndarray,
) -> tuple[int, int, int]:
    values = np.asarray(source_rgb, dtype=np.uint8)[face_mask]
    if len(values) == 0:
        raise ValueError("face mask is empty")
    median = np.median(values, axis=0).astype(np.float32)
    distances = np.linalg.norm(values.astype(np.float32) - median, axis=1)
    chosen = values[int(np.argmin(distances))]
    return tuple(int(v) for v in chosen)


def _exact_face_polygons(face_mask: np.ndarray) -> tuple[tuple[tuple[float, float], ...], ...]:
    face = np.asarray(face_mask, dtype=bool)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        face.astype(np.uint8), 8
    )
    polygons: list[tuple[tuple[float, float], ...]] = []
    rebuilt = np.zeros_like(face, dtype=np.uint8)

    for label in range(1, count):
        component = labels == label
        if int(component.sum()) == 0:
            continue

        contours, hierarchy = cv2.findContours(
            component.astype(np.uint8),
            cv2.RETR_CCOMP,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        if not contours:
            raise ValueError("face component has no contour")

        # Filled polygon primitives cannot encode holes safely. Fail closed
        # rather than painting across a semantic hole.
        if hierarchy is not None and any(int(row[3]) >= 0 for row in hierarchy[0]):
            raise ValueError("face mask contains holes unsupported by flat polygons")

        outer = max(contours, key=cv2.contourArea)
        polygon = outer.reshape(-1, 2)
        if len(polygon) < 3:
            raise ValueError("face contour has fewer than three vertices")

        cv2.fillPoly(rebuilt, [polygon.astype(np.int32)], 1)
        polygons.append(tuple((float(x), float(y)) for x, y in polygon))

    rebuilt_bool = rebuilt.astype(bool)
    if not np.array_equal(rebuilt_bool, face):
        missing = int((face & ~rebuilt_bool).sum())
        spill = int((rebuilt_bool & ~face).sum())
        raise ValueError(
            f"face polygons do not exactly reproduce mask: missing={missing} spill={spill}"
        )
    return tuple(polygons)


def apply_face_surface_stage(
    scene: VectorScene,
    source_rgb: np.ndarray,
    face_mask: np.ndarray,
) -> FaceSurfaceResult:
    """Replace internal face variation with an exact source-derived flat surface.

    Inputs are source RGB and an authorized semantic face mask. Golden, adopted
    baseline pixels, and missing-feature evidence are deliberately absent.
    """
    rgb = np.asarray(source_rgb, dtype=np.uint8)
    face = np.asarray(face_mask, dtype=bool)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("source_rgb must be HxWx3")
    if face.shape != rgb.shape[:2]:
        raise ValueError("face mask shape mismatch")
    if rgb.shape[1] != scene.width or rgb.shape[0] != scene.height:
        raise ValueError("scene/source size mismatch")
    if int(face.sum()) < 16:
        raise ValueError("face mask is too small")

    polygons = _exact_face_polygons(face)
    fill_rgb = _observed_representative_rgb(rgb, face)
    fill_ref = "#%02x%02x%02x" % fill_rgb

    kept = tuple(p for p in scene.primitives if p.source_region_id != "face")
    head_face_z = [
        p.z_order
        for p in kept
        if p.source_region_id in {"head", "face"}
    ]
    z = max(head_face_z, default=max((p.z_order for p in kept), default=0)) + 1

    added = tuple(
        ComposedPrimitive(
            primitive_id=f"semantic-face-surface:{index}",
            source_region_id="face",
            selected_candidate_id=(
                f"semantic-face:{FACE_SURFACE_STAGE_VERSION}:surface:{index}"
            ),
            primitive_type="convex_polygon",
            parameters={"points": [[x, y] for x, y in polygon], "shape_rendering": "crispEdges"},
            fill_ref=fill_ref,
            z_order=z + index,
        )
        for index, polygon in enumerate(polygons)
    )

    merged = tuple(sorted(kept + added, key=lambda p: (p.z_order, p.primitive_id)))
    out = VectorScene(
        scene.width,
        scene.height,
        merged,
        {
            **scene.provenance,
            "face_surface_stage": FACE_SURFACE_STAGE_VERSION,
            "face_surface_polygon_count": len(added),
            "face_surface_fill_source": "observed_source_pixel_nearest_face_median",
            "face_surface_exact_mask": True,
            "golden_raster_used": False,
        },
    )
    return FaceSurfaceResult(
        scene=out,
        svg=SvgRenderer().render(out),
        fill_rgb=fill_rgb,
        polygon_count=len(added),
        covered_pixels=int(face.sum()),
        face_pixels=int(face.sum()),
        outside_face_pixels=0,
    )
