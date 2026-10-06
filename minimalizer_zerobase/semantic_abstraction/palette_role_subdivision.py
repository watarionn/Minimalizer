from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from minimalizer_zerobase.semantic_abstraction.palette_role_adapter import (
    MAX_PALETTE_ROLES_PER_PART,
    MIN_COMPONENT_RATIO,
    MIN_PALETTE_ROLE_RATIO,
    adapt_palette_roles,
)


PALETTE_SUBDIVISION_VERSION = "sa8-compat-v1"
MAX_ROLES_PER_PART = MAX_PALETTE_ROLES_PER_PART
MIN_ROLE_RATIO = MIN_PALETTE_ROLE_RATIO


@dataclass(frozen=True)
class PaletteRoleMass:
    semantic_part: str
    role_index: int
    mask: np.ndarray
    rgb: tuple[int, int, int]
    source_ratio: float


def observe_palette_role_masses(
    rgb: np.ndarray,
    part_mask: np.ndarray,
    semantic_part: str,
    *,
    max_roles: int = MAX_ROLES_PER_PART,
) -> tuple[PaletteRoleMass, ...]:
    """Compatibility view over the SA8 Palette Role Adapter.

    A PaletteRoleMass now represents the union of every accepted connected
    component belonging to one palette role. Component identity remains in the
    SA8 adapter IR instead of being collapsed to the largest island.
    """
    report = adapt_palette_roles(
        rgb,
        part_mask,
        semantic_part,
        max_roles=max_roles,
        min_role_ratio=MIN_ROLE_RATIO,
        min_component_ratio=MIN_COMPONENT_RATIO,
    )
    masses: list[PaletteRoleMass] = []
    for role in report.roles:
        union_mask = np.logical_or.reduce(
            [component.mask for component in role.components]
        )
        masses.append(
            PaletteRoleMass(
                semantic_part=role.semantic_part,
                role_index=role.palette_role_index,
                mask=union_mask,
                rgb=role.rgb,
                source_ratio=role.source_ratio,
            )
        )
    return tuple(masses)
