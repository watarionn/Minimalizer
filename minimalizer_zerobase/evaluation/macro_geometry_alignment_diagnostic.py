from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from minimalizer_zerobase.semantic_abstraction.adaptive_primitive_budget import (
    AdaptivePrimitiveBudget,
    allocate_adaptive_primitive_budget,
)
from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import (
    DEFAULT_MACRO_GLOBAL_CAP,
    MAX_EXPANSION_RATIO,
    MIN_SOURCE_COVERAGE,
    _MACRO_IMPORTANCE,
    _MACRO_MAXIMUMS,
    _MACRO_MINIMUMS,
    _coarse_polygon,
    _masses,
    _primitive_for_mass,
)

SA10_MACRO_ALIGNMENT_DIAGNOSTIC_VERSION = "sa10.9-v1"


@dataclass(frozen=True)
class MacroPrimitiveDropDiagnostic:
    mass_index: int
    reason: str
    expansion_ratio: float | None
    source_coverage: float | None

    def to_dict(self) -> dict:
        return {
            "mass_index": self.mass_index,
            "reason": self.reason,
            "expansion_ratio": self.expansion_ratio,
            "source_coverage": self.source_coverage,
        }


@dataclass(frozen=True)
class MacroAlignmentRoleDiagnostic:
    role: str
    allocated_primitives: int
    major_component_count: int
    mass_candidates: int
    emitted_primitives: int
    dropped_mass_indices: tuple[int, ...]
    drop_details: tuple[MacroPrimitiveDropDiagnostic, ...]
    status: str

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "allocated_primitives": self.allocated_primitives,
            "major_component_count": self.major_component_count,
            "mass_candidates": self.mass_candidates,
            "emitted_primitives": self.emitted_primitives,
            "dropped_mass_indices": list(self.dropped_mass_indices),
            "drop_details": [detail.to_dict() for detail in self.drop_details],
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


def _diagnose_primitive_drop(
    source: np.ndarray,
    mass: np.ndarray,
    *,
    mass_index: int,
) -> MacroPrimitiveDropDiagnostic:
    polygon = _coarse_polygon(mass)
    if polygon is None:
        return MacroPrimitiveDropDiagnostic(mass_index, "NO_COARSE_POLYGON", None, None)

    canvas = np.zeros(source.shape, np.uint8)
    cv2.fillPoly(canvas, [polygon.astype(np.int32)], 1)
    dilated = cv2.dilate(
        source.astype(np.uint8),
        np.ones((5, 5), np.uint8),
    ) > 0
    clipped = (canvas > 0) & dilated
    polygon2 = _coarse_polygon(clipped)
    if polygon2 is None:
        return MacroPrimitiveDropDiagnostic(mass_index, "NO_CLIPPED_POLYGON", None, None)

    final = np.zeros(source.shape, np.uint8)
    cv2.fillPoly(final, [polygon2.astype(np.int32)], 1)
    source_n = max(1, int(mass.sum()))
    expansion = int(final.sum()) / source_n
    coverage = int(((final > 0) & mass).sum()) / source_n

    if expansion <= MAX_EXPANSION_RATIO and coverage >= MIN_SOURCE_COVERAGE:
        return MacroPrimitiveDropDiagnostic(
            mass_index,
            "UNKNOWN_REJECTION",
            float(expansion),
            float(coverage),
        )

    contours, _ = cv2.findContours(
        mass.astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    if not contours:
        return MacroPrimitiveDropDiagnostic(mass_index, "NO_FALLBACK_CONTOUR", None, None)
    contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(contour, True)
    fallback = cv2.approxPolyDP(
        contour,
        max(1.5, 0.01 * perimeter),
        True,
    ).reshape(-1, 2)
    if len(fallback) < 3:
        return MacroPrimitiveDropDiagnostic(mass_index, "FALLBACK_TOO_FEW_VERTICES", None, None)

    final = np.zeros(source.shape, np.uint8)
    cv2.fillPoly(final, [fallback.astype(np.int32)], 1)
    expansion = int(final.sum()) / source_n
    coverage = int(((final > 0) & mass).sum()) / source_n
    expansion_bad = expansion > MAX_EXPANSION_RATIO
    coverage_bad = coverage < MIN_SOURCE_COVERAGE
    if expansion_bad and coverage_bad:
        reason = "EXPANSION_AND_COVERAGE"
    elif expansion_bad:
        reason = "EXPANSION_EXCEEDED"
    elif coverage_bad:
        reason = "COVERAGE_BELOW_MINIMUM"
    else:
        reason = "UNKNOWN_REJECTION"
    return MacroPrimitiveDropDiagnostic(
        mass_index,
        reason,
        float(expansion),
        float(coverage),
    )


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
        drop_details: list[MacroPrimitiveDropDiagnostic] = []
        emitted = 0
        for index, mass in enumerate(masses):
            primitive = _primitive_for_mass(role, source, mass)
            if primitive is None:
                dropped.append(index)
                drop_details.append(_diagnose_primitive_drop(source, mass, mass_index=index))
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
                drop_details=tuple(drop_details),
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
