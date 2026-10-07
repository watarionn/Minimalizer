from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from minimalizer_zerobase.semantic_abstraction.adaptive_primitive_budget import (
    AdaptivePrimitiveBudget,
    allocate_adaptive_primitive_budget,
)
from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import (
    DEFAULT_MACRO_GLOBAL_CAP,
    _MACRO_IMPORTANCE,
    _MACRO_MAXIMUMS,
    _MACRO_MINIMUMS,
    _masses,
    _primitive_for_mass,
)

SA10_MACRO_ALIGNMENT_DIAGNOSTIC_VERSION = "sa10.9-v1"


@dataclass(frozen=True)
class MacroAlignmentRoleDiagnostic:
    role: str
    allocated_primitives: int
    major_component_count: int
    mass_candidates: int
    emitted_primitives: int
    dropped_mass_indices: tuple[int, ...]
    status: str

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "allocated_primitives": self.allocated_primitives,
            "major_component_count": self.major_component_count,
            "mass_candidates": self.mass_candidates,
            "emitted_primitives": self.emitted_primitives,
            "dropped_mass_indices": list(self.dropped_mass_indices),
            "status": self.status,
        }


@dataclass(frozen=True)
class MacroAlignmentDiagnostic:
    budget: AdaptivePrimitiveBudget
    roles: tuple[MacroAlignmentRoleDiagnostic, ...]
    aligned: bool
    authoritative: bool = False
    version: str = SA10_MACRO_ALIGNMENT_DIAGNOSTIC_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "authoritative": False,
            "aligned": self.aligned,
            "budget": self.budget.to_dict(),
            "roles": [role.to_dict() for role in self.roles],
        }


def classify_macro_alignment(
    *,
    allocated_primitives: int,
    mass_candidates: int,
    emitted_primitives: int,
) -> str:
    if min(allocated_primitives, mass_candidates, emitted_primitives) < 0:
        raise ValueError("alignment counts must be non-negative")
    if mass_candidates > allocated_primitives:
        raise ValueError("mass candidates cannot exceed allocated primitives")
    if emitted_primitives > mass_candidates:
        raise ValueError("emitted primitives cannot exceed mass candidates")
    if emitted_primitives == allocated_primitives:
        return "ALIGNED"
    if mass_candidates < allocated_primitives:
        return "BUDGET_MASS_GAP"
    if emitted_primitives < mass_candidates:
        return "PRIMITIVE_GENERATION_DROP"
    return "UNCLASSIFIED_MISMATCH"


def diagnose_macro_geometry_alignment(
    *,
    hair_mask: np.ndarray,
    clothing_mask: np.ndarray,
    global_primitive_budget: int = DEFAULT_MACRO_GLOBAL_CAP,
) -> MacroAlignmentDiagnostic:
    role_masks = {
        "hair": np.asarray(hair_mask).astype(bool),
        "major_clothing": np.asarray(clothing_mask).astype(bool),
    }
    budget = allocate_adaptive_primitive_budget(
        role_masks,
        global_cap=global_primitive_budget,
        minimums=_MACRO_MINIMUMS,
        maximums=_MACRO_MAXIMUMS,
        importance=_MACRO_IMPORTANCE,
    )

    rows: list[MacroAlignmentRoleDiagnostic] = []
    for role in ("hair", "major_clothing"):
        source = role_masks[role]
        allocated = budget.for_role(role)
        masses = _masses(source, allocated)
        dropped: list[int] = []
        emitted = 0
        for index, mass in enumerate(masses):
            primitive = _primitive_for_mass(role, source, mass)
            if primitive is None:
                dropped.append(index)
            else:
                emitted += 1
        budget_row = next(entry for entry in budget.entries if entry.role == role)
        rows.append(
            MacroAlignmentRoleDiagnostic(
                role=role,
                allocated_primitives=allocated,
                major_component_count=budget_row.major_component_count,
                mass_candidates=len(masses),
                emitted_primitives=emitted,
                dropped_mass_indices=tuple(dropped),
                status=classify_macro_alignment(
                    allocated_primitives=allocated,
                    mass_candidates=len(masses),
                    emitted_primitives=emitted,
                ),
            )
        )

    return MacroAlignmentDiagnostic(
        budget=budget,
        roles=tuple(rows),
        aligned=all(row.status == "ALIGNED" for row in rows),
    )
