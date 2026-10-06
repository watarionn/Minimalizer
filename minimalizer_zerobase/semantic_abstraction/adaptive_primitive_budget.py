from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np


ADAPTIVE_PRIMITIVE_BUDGET_VERSION = "sa7.43-v1"
DEFAULT_MIN_COMPONENT_RATIO = 0.02
DEFAULT_MIN_COMPONENT_PIXELS = 12


@dataclass(frozen=True)
class AdaptivePrimitiveBudgetEntry:
    role: str
    required_minimum: int
    hard_maximum: int
    source_area: int
    major_component_count: int
    major_component_areas: tuple[int, ...]
    contour_vertices: int
    complexity_score: float
    allocated_primitives: int
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "required_minimum": self.required_minimum,
            "hard_maximum": self.hard_maximum,
            "source_area": self.source_area,
            "major_component_count": self.major_component_count,
            "major_component_areas": list(self.major_component_areas),
            "contour_vertices": self.contour_vertices,
            "complexity_score": round(float(self.complexity_score), 6),
            "allocated_primitives": self.allocated_primitives,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class AdaptivePrimitiveBudget:
    global_cap: int
    allocated_total: int
    unallocated: int
    entries: tuple[AdaptivePrimitiveBudgetEntry, ...]
    version: str = ADAPTIVE_PRIMITIVE_BUDGET_VERSION

    def __post_init__(self) -> None:
        if self.global_cap < 0:
            raise ValueError("global_cap must be non-negative")
        if self.allocated_total < 0 or self.allocated_total > self.global_cap:
            raise ValueError("allocated_total must be within global_cap")
        if self.unallocated != self.global_cap - self.allocated_total:
            raise ValueError("unallocated must equal global_cap - allocated_total")

    def for_role(self, role: str) -> int:
        for entry in self.entries:
            if entry.role == role:
                return entry.allocated_primitives
        return 0

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "global_cap": self.global_cap,
            "allocated_total": self.allocated_total,
            "unallocated": self.unallocated,
            "entries": [entry.to_dict() for entry in self.entries],
        }


@dataclass(frozen=True)
class _RoleEvidence:
    role: str
    minimum: int
    maximum: int
    source_area: int
    component_areas: tuple[int, ...]
    contour_vertices: int
    complexity_score: float


def _major_components(
    mask: np.ndarray,
    *,
    min_component_ratio: float,
    min_component_pixels: int,
) -> tuple[np.ndarray, ...]:
    src = np.asarray(mask).astype(bool)
    source_area = int(src.sum())
    if source_area <= 0:
        return ()

    binary = src.astype(np.uint8)
    kernel_size = max(3, int(round(min(src.shape) * 0.008)) | 1)
    clean = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        np.ones((kernel_size, kernel_size), np.uint8),
    )
    count, labels, stats, _ = cv2.connectedComponentsWithStats(clean, 8)
    minimum = max(
        int(min_component_pixels),
        int(source_area * float(min_component_ratio)),
    )
    rows: list[tuple[int, int, int, int, np.ndarray]] = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < minimum:
            continue
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        rows.append((area, y, x, label, labels == label))
    rows.sort(key=lambda row: (-row[0], row[1], row[2], row[3]))
    return tuple(row[-1] for row in rows)


def _contour_vertices(components: tuple[np.ndarray, ...]) -> int:
    total = 0
    for component in components:
        contours, _ = cv2.findContours(
            component.astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        if not contours:
            continue
        contour = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(
            contour,
            max(1.0, 0.01 * perimeter),
            True,
        )
        total += int(len(polygon))
    return total


def _role_evidence(
    role: str,
    mask: np.ndarray,
    *,
    minimum: int,
    maximum: int,
    weight: float,
    min_component_ratio: float,
    min_component_pixels: int,
) -> _RoleEvidence:
    src = np.asarray(mask).astype(bool)
    source_area = int(src.sum())
    if source_area <= 0:
        return _RoleEvidence(
            role=role,
            minimum=0,
            maximum=max(0, maximum),
            source_area=0,
            component_areas=(),
            contour_vertices=0,
            complexity_score=0.0,
        )

    components = _major_components(
        src,
        min_component_ratio=min_component_ratio,
        min_component_pixels=min_component_pixels,
    )
    areas = tuple(int(component.sum()) for component in components)
    vertices = _contour_vertices(components)
    normalized_component_support = sum(
        (area / max(1, source_area)) ** 0.5
        for area in areas
    )
    normalized_vertex_term = min(1.0, vertices / 32.0)
    complexity = float(weight) * (
        normalized_component_support + 0.25 * normalized_vertex_term
    )
    return _RoleEvidence(
        role=role,
        minimum=max(0, int(minimum)),
        maximum=max(max(0, int(minimum)), int(maximum)),
        source_area=source_area,
        component_areas=areas,
        contour_vertices=vertices,
        complexity_score=complexity,
    )


def allocate_adaptive_primitive_budget(
    role_masks: Mapping[str, np.ndarray],
    *,
    global_cap: int,
    minimums: Mapping[str, int] | None = None,
    maximums: Mapping[str, int] | None = None,
    importance: Mapping[str, float] | None = None,
    min_component_ratio: float = DEFAULT_MIN_COMPONENT_RATIO,
    min_component_pixels: int = DEFAULT_MIN_COMPONENT_PIXELS,
) -> AdaptivePrimitiveBudget:
    """Allocate a bounded primitive budget from source-supported geometry.

    Required minima are reserved first. Remaining slots correspond to
    additional major connected components and compete globally by their
    source-supported area ratio. Tiny components below the component contract
    never create demand.
    """
    if not isinstance(global_cap, int) or isinstance(global_cap, bool):
        raise ValueError("global_cap must be an integer")
    if global_cap < 0:
        raise ValueError("global_cap must be non-negative")
    if not 0.0 <= float(min_component_ratio) <= 1.0:
        raise ValueError("min_component_ratio must be within [0, 1]")
    if int(min_component_pixels) < 1:
        raise ValueError("min_component_pixels must be positive")

    minimums = dict(minimums or {})
    maximums = dict(maximums or {})
    importance = dict(importance or {})

    evidence = tuple(
        _role_evidence(
            role,
            np.asarray(role_masks[role]),
            minimum=minimums.get(role, 1),
            maximum=maximums.get(role, 3),
            weight=importance.get(role, 1.0),
            min_component_ratio=min_component_ratio,
            min_component_pixels=min_component_pixels,
        )
        for role in sorted(role_masks)
    )

    minimum_total = sum(item.minimum for item in evidence)
    if minimum_total > global_cap:
        raise ValueError(
            f"global cap {global_cap} cannot satisfy required minimum {minimum_total}"
        )

    allocated = {item.role: item.minimum for item in evidence}
    remaining = global_cap - minimum_total

    marginal: list[tuple[float, str, int]] = []
    for item in evidence:
        demand = min(
            item.maximum,
            max(item.minimum, len(item.component_areas)),
        )
        for ordinal in range(item.minimum, demand):
            area = item.component_areas[ordinal]
            support = area / max(1, item.source_area)
            score = float(importance.get(item.role, 1.0)) * support
            marginal.append((score, item.role, ordinal))

    marginal.sort(key=lambda row: (-row[0], row[1], row[2]))
    for _, role, _ in marginal:
        if remaining <= 0:
            break
        allocated[role] += 1
        remaining -= 1

    entries: list[AdaptivePrimitiveBudgetEntry] = []
    for item in evidence:
        extras = max(0, allocated[item.role] - item.minimum)
        reasons = [
            "required_minimum_reserved" if item.minimum else "no_required_minimum",
            f"major_components={len(item.component_areas)}",
        ]
        if extras:
            reasons.append(f"source_supported_extras={extras}")
        if allocated[item.role] >= item.maximum:
            reasons.append("hard_maximum_reached")
        elif len(item.component_areas) <= allocated[item.role]:
            reasons.append("no_additional_major_component_demand")
        entries.append(
            AdaptivePrimitiveBudgetEntry(
                role=item.role,
                required_minimum=item.minimum,
                hard_maximum=item.maximum,
                source_area=item.source_area,
                major_component_count=len(item.component_areas),
                major_component_areas=item.component_areas,
                contour_vertices=item.contour_vertices,
                complexity_score=item.complexity_score,
                allocated_primitives=allocated[item.role],
                reasons=tuple(reasons),
            )
        )

    total = sum(allocated.values())
    return AdaptivePrimitiveBudget(
        global_cap=global_cap,
        allocated_total=total,
        unallocated=global_cap - total,
        entries=tuple(entries),
    )
