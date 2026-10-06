from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from minimalizer_zerobase.evaluation.component_economy_evidence import (
    ComponentEconomyEvidence,
    RoleComponentEvidence,
)
from minimalizer_zerobase.semantic_abstraction.adaptive_primitive_budget import (
    AdaptivePrimitiveBudget,
)
from minimalizer_zerobase.semantic_abstraction.macro_geometry_reauthoring import (
    MacroGeometryPrimitive,
)

SA10_COMPONENT_PRIMITIVE_SUPPORT_VERSION = "sa10.5-v1"
DEFAULT_MIN_COMPONENT_COVERAGE = 0.50
DEFAULT_MIN_PRIMITIVE_SUPPORT = 0.65


def _rasterize(polygon: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    canvas = np.zeros(shape, np.uint8)
    cv2.fillPoly(canvas, [np.asarray(polygon, dtype=np.int32)], 1)
    return canvas.astype(bool)


def _major_components(mask: np.ndarray) -> tuple[np.ndarray, ...]:
    src = np.asarray(mask).astype(np.uint8)
    source_area = int(src.sum())
    if source_area == 0:
        return ()
    k = max(3, int(round(min(src.shape) * 0.008)) | 1)
    clean = cv2.morphologyEx(src, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(clean, 8)
    minimum = max(12, int(source_area * 0.02))
    rows = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= minimum:
            rows.append((area, int(stats[label, cv2.CC_STAT_TOP]), int(stats[label, cv2.CC_STAT_LEFT]), label))
    rows.sort(key=lambda x: (-x[0], x[1], x[2], x[3]))
    return tuple(labels == label for _, _, _, label in rows)


def measure_component_primitive_support(
    *,
    role_masks: dict[str, np.ndarray],
    primitives: tuple[MacroGeometryPrimitive, ...],
    budget: AdaptivePrimitiveBudget,
    min_component_coverage: float = DEFAULT_MIN_COMPONENT_COVERAGE,
    min_primitive_support: float = DEFAULT_MIN_PRIMITIVE_SUPPORT,
) -> ComponentEconomyEvidence:
    if not 0 <= min_component_coverage <= 1 or not 0 <= min_primitive_support <= 1:
        raise ValueError("support thresholds must be within [0, 1]")
    roles: list[RoleComponentEvidence] = []
    for entry in budget.entries:
        if entry.role not in role_masks:
            raise ValueError(f"missing role mask for {entry.role}")
        mask = np.asarray(role_masks[entry.role]).astype(bool)
        components = _major_components(mask)
        if len(components) != entry.major_component_count:
            raise ValueError(f"component frame mismatch for {entry.role}")
        emitted = tuple(p for p in primitives if p.semantic_part == entry.role)
        if len(emitted) != entry.allocated_primitives:
            raise ValueError(f"primitive frame mismatch for {entry.role}")
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

        roles.append(RoleComponentEvidence(
            role=entry.role,
            source_components=len(components),
            represented_components=represented,
            emitted_primitives=len(emitted),
            source_supported_primitives=supported,
        ))

    return ComponentEconomyEvidence(
        roles=tuple(roles),
        source_components=sum(r.source_components for r in roles),
        represented_components=sum(r.represented_components for r in roles),
        emitted_primitives=sum(r.emitted_primitives for r in roles),
        source_supported_primitives=sum(r.source_supported_primitives for r in roles),
    )
