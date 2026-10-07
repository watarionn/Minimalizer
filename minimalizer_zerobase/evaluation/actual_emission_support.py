from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from minimalizer_zerobase.semantic_abstraction.adaptive_primitive_budget import (
    AdaptivePrimitiveBudget,
)
from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import (
    MacroGeometryPrimitive,
)

SA10_ACTUAL_EMISSION_VERSION = "sa10.10-v1"
DEFAULT_MIN_COMPONENT_COVERAGE = 0.50
DEFAULT_MIN_PRIMITIVE_SUPPORT = 0.65


def _major_components(mask: np.ndarray) -> tuple[np.ndarray, ...]:
    src = np.asarray(mask).astype(np.uint8)
    area = int(src.sum())
    if area == 0:
        return ()
    k = max(3, int(round(min(src.shape) * 0.008)) | 1)
    clean = cv2.morphologyEx(src, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(clean, 8)
    minimum = max(12, int(area * 0.02))
    rows = []
    for label in range(1, count):
        component_area = int(stats[label, cv2.CC_STAT_AREA])
        if component_area >= minimum:
            rows.append((
                component_area,
                int(stats[label, cv2.CC_STAT_TOP]),
                int(stats[label, cv2.CC_STAT_LEFT]),
                label,
            ))
    rows.sort(key=lambda row: (-row[0], row[1], row[2], row[3]))
    return tuple(labels == label for _, _, _, label in rows)


def _rasterize(polygon: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    canvas = np.zeros(shape, np.uint8)
    cv2.fillPoly(canvas, [np.asarray(polygon, dtype=np.int32)], 1)
    return canvas.astype(bool)


@dataclass(frozen=True)
class ActualEmissionRoleDiagnostic:
    role: str
    source_components: int
    represented_components: int
    allocated_primitives: int
    emitted_primitives: int
    source_supported_primitives: int

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "source_components": self.source_components,
            "represented_components": self.represented_components,
            "allocated_primitives": self.allocated_primitives,
            "emitted_primitives": self.emitted_primitives,
            "source_supported_primitives": self.source_supported_primitives,
        }


@dataclass(frozen=True)
class ActualEmissionSupportDiagnostic:
    roles: tuple[ActualEmissionRoleDiagnostic, ...]
    source_components: int
    represented_components: int
    allocated_primitives: int
    emitted_primitives: int
    source_supported_primitives: int
    authoritative: bool = False
    version: str = SA10_ACTUAL_EMISSION_VERSION

    @property
    def actual_component_representation_ratio(self) -> float | None:
        if self.source_components == 0:
            return None
        return self.represented_components / self.source_components

    @property
    def actual_primitive_support_ratio(self) -> float | None:
        if self.emitted_primitives == 0:
            return None
        return self.source_supported_primitives / self.emitted_primitives

    @property
    def emission_realization_ratio(self) -> float | None:
        if self.allocated_primitives == 0:
            return None
        return self.emitted_primitives / self.allocated_primitives

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "authoritative": False,
            "diagnostic_only": True,
            "maps_to_sa10_component_survival": False,
            "maps_to_sa10_primitive_economy": False,
            "source_components": self.source_components,
            "represented_components": self.represented_components,
            "actual_component_representation_ratio": self.actual_component_representation_ratio,
            "allocated_primitives": self.allocated_primitives,
            "emitted_primitives": self.emitted_primitives,
            "emission_realization_ratio": self.emission_realization_ratio,
            "source_supported_primitives": self.source_supported_primitives,
            "actual_primitive_support_ratio": self.actual_primitive_support_ratio,
            "roles": [row.to_dict() for row in self.roles],
        }


def measure_actual_emission_support(
    *,
    role_masks: dict[str, np.ndarray],
    primitives: tuple[MacroGeometryPrimitive, ...],
    budget: AdaptivePrimitiveBudget,
    min_component_coverage: float = DEFAULT_MIN_COMPONENT_COVERAGE,
    min_primitive_support: float = DEFAULT_MIN_PRIMITIVE_SUPPORT,
) -> ActualEmissionSupportDiagnostic:
    if not 0 <= min_component_coverage <= 1:
        raise ValueError("min_component_coverage must be within [0, 1]")
    if not 0 <= min_primitive_support <= 1:
        raise ValueError("min_primitive_support must be within [0, 1]")

    rows: list[ActualEmissionRoleDiagnostic] = []
    for entry in budget.entries:
        if entry.role not in role_masks:
            raise ValueError(f"missing role mask: {entry.role}")
        mask = np.asarray(role_masks[entry.role]).astype(bool)
        components = _major_components(mask)
        if len(components) != entry.major_component_count:
            raise ValueError(f"component frame mismatch for {entry.role}")

        emitted = tuple(p for p in primitives if p.semantic_part == entry.role)
        rasters = tuple(_rasterize(p.polygon, mask.shape) for p in emitted)

        represented = 0
        for component in components:
            area = int(component.sum())
            coverage = max(
                (int((component & raster).sum()) / area for raster in rasters),
                default=0.0,
            )
            if coverage >= min_component_coverage:
                represented += 1

        supported = 0
        for raster in rasters:
            area = int(raster.sum())
            support = 0.0 if area == 0 else int((raster & mask).sum()) / area
            if support >= min_primitive_support:
                supported += 1

        rows.append(ActualEmissionRoleDiagnostic(
            role=entry.role,
            source_components=len(components),
            represented_components=represented,
            allocated_primitives=entry.allocated_primitives,
            emitted_primitives=len(emitted),
            source_supported_primitives=supported,
        ))

    return ActualEmissionSupportDiagnostic(
        roles=tuple(rows),
        source_components=sum(row.source_components for row in rows),
        represented_components=sum(row.represented_components for row in rows),
        allocated_primitives=sum(row.allocated_primitives for row in rows),
        emitted_primitives=sum(row.emitted_primitives for row in rows),
        source_supported_primitives=sum(row.source_supported_primitives for row in rows),
    )
