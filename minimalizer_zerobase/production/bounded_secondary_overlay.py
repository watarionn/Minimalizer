from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from minimalizer_zerobase.production.palette_role_candidates import (
    PaletteRolePrimitiveCandidate,
    propose_palette_role_candidates,
)


BOUNDED_SECONDARY_OVERLAY_VERSION = "sa8.1-v1"


@dataclass(frozen=True)
class SecondaryPaletteOverlay:
    candidate: PaletteRolePrimitiveCandidate
    uncovered_mask: np.ndarray
    coverage_gain_pixels: int
    coverage_gain_ratio: float


def propose_bounded_secondary_overlays(
    rgb: np.ndarray,
    part_mask: np.ndarray,
    semantic_part: str,
    established_masks: tuple[np.ndarray, ...],
    *,
    palette_role_budget: int = 3,
    candidate_budget: int = 6,
    overlay_budget: int = 2,
    min_role_ratio: float = 0.085,
    min_component_ratio: float = 0.025,
    min_coverage_gain_ratio: float = 0.035,
) -> tuple[SecondaryPaletteOverlay, ...]:
    """Select only source-supported SA8 components that add missing coverage.

    Established renderer masses remain authoritative. SA8 may supplement them,
    never replace them. The selector is deterministic and part-local.
    """
    if overlay_budget < 0:
        raise ValueError("overlay_budget must be >= 0")
    if overlay_budget == 0:
        return ()

    authority = np.asarray(part_mask).astype(bool)
    covered = np.zeros_like(authority)
    for item in established_masks:
        mask = np.asarray(item).astype(bool)
        if mask.shape != authority.shape:
            raise ValueError("shape mismatch")
        covered |= mask & authority

    total = int(authority.sum())
    if total == 0:
        return ()

    candidates = propose_palette_role_candidates(
        rgb,
        authority,
        semantic_part,
        palette_role_budget=palette_role_budget,
        primitive_budget=candidate_budget,
        min_role_ratio=min_role_ratio,
        min_component_ratio=min_component_ratio,
    )
    selected: list[SecondaryPaletteOverlay] = []
    for candidate in candidates:
        uncovered = candidate.mask & authority & ~covered
        gain = int(uncovered.sum())
        ratio = float(gain / total)
        if gain == 0 or ratio < min_coverage_gain_ratio:
            continue
        selected.append(
            SecondaryPaletteOverlay(
                candidate=candidate,
                uncovered_mask=uncovered,
                coverage_gain_pixels=gain,
                coverage_gain_ratio=ratio,
            )
        )
        covered |= uncovered
        if len(selected) >= overlay_budget:
            break
    return tuple(selected)
