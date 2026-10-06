from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np

from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.render import SvgRenderer

from .required_semantic_mass import (
    MAX_EXPANSION_RATIO,
    MIN_SOURCE_COVERAGE,
    ROLE_CLUSTER_COUNTS,
    RequiredSemanticMass,
)

REQUIRED_MASS_SCENE_VERSION = "sa7.39-v1"
PROTECTED_ROLES = (
    "face",
    "head",
    "hair",
    "major_clothing",
    "accessory_or_held_object",
)


@dataclass(frozen=True)
class RequiredMassSceneResult:
    scene: VectorScene
    svg: str
    added_count: int


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % tuple(int(np.clip(v, 0, 255)) for v in rgb)


def _rasterize_polygon(
    polygon: tuple[tuple[float, float], ...],
    shape: tuple[int, int],
) -> np.ndarray:
    points = np.asarray(polygon, dtype=np.float32)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3:
        raise ValueError("reservation polygon must be Nx2 with at least 3 points")
    raster = np.zeros(shape, dtype=np.uint8)
    cv2.fillPoly(raster, [points.astype(np.int32)], 1)
    return raster.astype(bool)


def apply_required_semantic_mass_scene(
    scene: VectorScene,
    reservations: tuple[RequiredSemanticMass, ...],
    semantic_masks: Mapping[str, np.ndarray],
) -> RequiredMassSceneResult:
    """Add source-only required semantic masses as late canonical primitives.

    Every reservation must remain fully inside its semantic role, avoid all
    protected semantic masks, and avoid every other reservation polygon.
    Golden and hard-gate evidence are not inputs.
    """
    masks = {
        str(role): np.asarray(mask, dtype=bool)
        for role, mask in semantic_masks.items()
    }
    expected_shape = (scene.height, scene.width)
    if any(mask.shape != expected_shape for mask in masks.values()):
        raise ValueError("semantic mask shape mismatch")

    allowed_roles = set(ROLE_CLUSTER_COUNTS)
    protected_union = np.zeros(expected_shape, dtype=bool)
    for role in PROTECTED_ROLES:
        mask = masks.get(role)
        if mask is not None:
            protected_union |= mask

    validated: list[tuple[RequiredSemanticMass, np.ndarray]] = []
    occupied_by_role: dict[str, np.ndarray] = {}

    for reservation in reservations:
        if reservation.role not in allowed_roles:
            raise ValueError(f"unauthorized reservation role: {reservation.role}")
        if reservation.source_coverage < MIN_SOURCE_COVERAGE:
            raise ValueError("reservation source coverage below contract")
        if reservation.expansion_ratio > MAX_EXPANSION_RATIO:
            raise ValueError("reservation expansion exceeds contract")
        if reservation.outside_role_pixels != 0:
            raise ValueError("reservation reports semantic-role spill")

        role_mask = masks.get(reservation.role)
        if role_mask is None or not np.any(role_mask):
            raise ValueError(f"missing semantic mask for reservation role: {reservation.role}")

        raster = _rasterize_polygon(reservation.polygon, expected_shape)
        outside = int((raster & ~role_mask).sum())
        if outside:
            raise ValueError(
                f"reservation polygon exits role {reservation.role}: {outside} pixels"
            )

        protected = int((raster & protected_union).sum())
        if protected:
            raise ValueError(
                f"reservation polygon overlaps protected semantic roles: {protected} pixels"
            )

        cross_role_overlap = 0
        for other_role, other_mask in occupied_by_role.items():
            if other_role == reservation.role:
                continue
            cross_role_overlap += int((raster & other_mask).sum())
        if cross_role_overlap:
            raise ValueError(
                "reservation polygons overlap across semantic roles: "
                f"{cross_role_overlap} pixels"
            )

        if reservation.role not in occupied_by_role:
            occupied_by_role[reservation.role] = np.zeros(
                expected_shape, dtype=bool
            )
        occupied_by_role[reservation.role] |= raster
        validated.append((reservation, raster))

    kept = tuple(scene.primitives)
    top = max((primitive.z_order for primitive in kept), default=0) + 1
    added: list[ComposedPrimitive] = []

    for index, (reservation, _) in enumerate(
        sorted(
            validated,
            key=lambda row: (
                row[0].role,
                -row[0].source_area,
                row[0].rgb,
                row[0].cluster_index,
            ),
        )
    ):
        added.append(
            ComposedPrimitive(
                primitive_id=f"required-semantic-mass:{reservation.role}:{index}",
                source_region_id=reservation.role,
                selected_candidate_id=(
                    f"required-semantic-mass:{REQUIRED_MASS_SCENE_VERSION}:"
                    f"{reservation.role}:{reservation.cluster_index}"
                ),
                primitive_type="convex_polygon",
                parameters={
                    "points": [
                        [float(x), float(y)]
                        for x, y in reservation.polygon
                    ]
                },
                fill_ref=_hex(reservation.rgb),
                z_order=top + index,
            )
        )

    merged = tuple(
        sorted(
            kept + tuple(added),
            key=lambda primitive: (primitive.z_order, primitive.primitive_id),
        )
    )
    out = VectorScene(
        scene.width,
        scene.height,
        merged,
        {
            **scene.provenance,
            "required_semantic_mass_scene": REQUIRED_MASS_SCENE_VERSION,
            "required_semantic_mass_added_count": len(added),
            "required_semantic_mass_protected_roles": list(PROTECTED_ROLES),
            "golden_raster_used": False,
        },
    )
    return RequiredMassSceneResult(
        scene=out,
        svg=SvgRenderer().render(out),
        added_count=len(added),
    )
