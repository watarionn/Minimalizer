from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from minimalizer_zerobase.semantic_abstraction.palette_role_adapter import adapt_palette_roles


PALETTE_ROLE_CANDIDATE_VERSION = "sa8-candidate-v1"


@dataclass(frozen=True)
class PaletteRolePrimitiveCandidate:
    semantic_part: str
    palette_role_index: int
    component_index: int
    component_id: str
    mask: np.ndarray
    rgb: tuple[int, int, int]
    pixel_count: int


def propose_palette_role_candidates(
    rgb: np.ndarray,
    part_mask: np.ndarray,
    semantic_part: str,
    *,
    palette_role_budget: int = 3,
    primitive_budget: int = 6,
    min_role_ratio: float = 0.085,
    min_component_ratio: float = 0.025,
) -> tuple[PaletteRolePrimitiveCandidate, ...]:
    """Bridge SA8 source-only palette roles into bounded production candidates.

    Palette-role count and primitive count are intentionally independent.
    Every candidate is an exact source-supported connected component. This
    bridge does not alter semantic ownership, anatomy, topology, or z-order.
    """
    if primitive_budget < 0:
        raise ValueError("primitive_budget must be >= 0")
    if primitive_budget == 0:
        return ()

    report = adapt_palette_roles(
        rgb,
        part_mask,
        semantic_part,
        max_roles=palette_role_budget,
        min_role_ratio=min_role_ratio,
        min_component_ratio=min_component_ratio,
    )
    candidates = [
        PaletteRolePrimitiveCandidate(
            semantic_part=role.semantic_part,
            palette_role_index=role.palette_role_index,
            component_index=component.component_index,
            component_id=component.component_id,
            mask=component.mask,
            rgb=component.rgb,
            pixel_count=component.pixel_count,
        )
        for role in report.roles
        for component in role.components
    ]
    candidates.sort(
        key=lambda item: (
            -item.pixel_count,
            item.palette_role_index,
            item.component_index,
            item.component_id,
        )
    )
    return tuple(candidates[:primitive_budget])
