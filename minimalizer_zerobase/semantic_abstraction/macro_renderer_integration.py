from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.render import SvgRenderer

from .macro_geometry_reauthoring import MacroGeometryPrimitive


MACRO_RENDER_VERSION = "sa7.44-v1"
_ALLOWED = ("hair", "major_clothing")


@dataclass(frozen=True)
class MacroRenderResult:
    scene: VectorScene
    svg: str
    replaced_roles: tuple[str, ...]


def _points(poly: np.ndarray) -> list[list[float]]:
    a = np.asarray(poly)
    if a.ndim != 2 or a.shape[1] != 2 or len(a) < 3:
        raise ValueError("macro polygon must be Nx2")
    return [[float(x), float(y)] for x, y in a]


def replace_macro_roles(
    scene: VectorScene,
    macros: Iterable[MacroGeometryPrimitive],
    palette: dict[str, str],
    *,
    require_roles: tuple[str, ...] = ("hair", "major_clothing"),
) -> MacroRenderResult:
    rows = tuple(macros)
    by_role = {role: [] for role in _ALLOWED}

    for macro in rows:
        if macro.semantic_part not in by_role:
            raise ValueError("unauthorized macro role")
        by_role[macro.semantic_part].append(macro)

    for role in require_roles:
        if role not in by_role or not by_role[role]:
            raise ValueError(f"missing required macro role: {role}")
        if role not in palette:
            raise ValueError(f"missing macro palette: {role}")

    kept = [
        primitive
        for primitive in scene.primitives
        if primitive.source_region_id not in set(require_roles)
    ]
    base_z = {
        role: min(
            (
                primitive.z_order
                for primitive in scene.primitives
                if primitive.source_region_id == role
            ),
            default=len(scene.primitives),
        )
        for role in require_roles
    }

    added: list[ComposedPrimitive] = []
    for role in require_roles:
        base_ordinal = 0
        residual_ordinal = 0
        for macro in by_role[role]:
            if macro.layer_kind == "residual":
                ordinal = (
                    macro.component_index
                    if macro.component_index is not None
                    else residual_ordinal
                )
                primitive_id = f"semantic-macro-residual:{role}:{ordinal}"
                candidate_id = (
                    f"semantic-macro:{MACRO_RENDER_VERSION}:"
                    f"{role}:residual:{ordinal}"
                )
                residual_ordinal += 1
            else:
                primitive_id = f"semantic-macro:{role}:{base_ordinal}"
                candidate_id = (
                    f"semantic-macro:{MACRO_RENDER_VERSION}:"
                    f"{role}:base:{base_ordinal}"
                )
                base_ordinal += 1

            added.append(
                ComposedPrimitive(
                    primitive_id=primitive_id,
                    source_region_id=role,
                    selected_candidate_id=candidate_id,
                    primitive_type="convex_polygon",
                    parameters={"points": _points(macro.polygon)},
                    fill_ref=palette[role],
                    z_order=base_z[role] + len(added),
                )
            )

    protected = [
        primitive
        for primitive in kept
        if primitive.source_region_id not in set(require_roles)
        and (
            "accent" in primitive.primitive_id.lower()
            or "identity" in primitive.primitive_id.lower()
            or "accent" in primitive.selected_candidate_id.lower()
            or "identity" in primitive.selected_candidate_id.lower()
        )
    ]
    protected_ids = {primitive.primitive_id for primitive in protected}
    ordinary = [
        primitive
        for primitive in kept
        if primitive.primitive_id not in protected_ids
    ]

    ordered = sorted(
        ordinary + added,
        key=lambda primitive: (primitive.z_order, primitive.primitive_id),
    )
    top = max(
        [primitive.z_order for primitive in ordered],
        default=0,
    ) + 1
    promoted = [
        ComposedPrimitive(
            primitive.primitive_id,
            primitive.source_region_id,
            primitive.selected_candidate_id,
            primitive.primitive_type,
            primitive.parameters,
            primitive.fill_ref,
            top + index,
        )
        for index, primitive in enumerate(
            sorted(
                protected,
                key=lambda primitive: (
                    primitive.z_order,
                    primitive.primitive_id,
                ),
            )
        )
    ]
    merged = tuple(
        sorted(
            ordered + promoted,
            key=lambda primitive: (
                primitive.z_order,
                primitive.primitive_id,
            ),
        )
    )

    output = VectorScene(
        width=scene.width,
        height=scene.height,
        primitives=merged,
        provenance={
            **scene.provenance,
            "semantic_macro_renderer": MACRO_RENDER_VERSION,
            "macro_semantic_authority": "upstream_authorized_masks",
            "golden_raster_used": False,
        },
    )
    return MacroRenderResult(
        output,
        SvgRenderer().render(output),
        tuple(require_roles),
    )
