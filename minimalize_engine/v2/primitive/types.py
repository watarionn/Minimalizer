from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.types import RegionId

PointArray = NDArray[np.float32]


def _readonly_points(value: NDArray | None, *, minimum: int = 1) -> PointArray | None:
    if value is None:
        return None
    points = np.array(value, dtype=np.float32, copy=True)
    if points.ndim != 2 or points.shape[1] != 2 or points.shape[0] < minimum:
        raise ValueError("primitive points must have shape (N, 2)")
    if not np.all(np.isfinite(points)):
        raise ValueError("primitive points must be finite")
    points.flags.writeable = False
    return points


@dataclass(frozen=True, slots=True)
class PrimitiveGeometry:
    kind: str
    loops: tuple[PointArray, ...] = ()
    points: PointArray | None = None
    center: tuple[float, float] | None = None
    axes: tuple[float, float] | None = None
    angle_deg: float = 0.0
    segment_start: tuple[float, float] | None = None
    segment_end: tuple[float, float] | None = None
    radius: float | None = None
    def __post_init__(self) -> None:
        allowed = {"polygon", "oriented_rectangle", "ellipse", "capsule", "trapezoid"}
        if self.kind not in allowed:
            raise ValueError("unknown primitive kind")
        loops: list[PointArray] = []
        for loop in self.loops:
            normalized = _readonly_points(loop, minimum=3)
            assert normalized is not None
            loops.append(normalized)
        object.__setattr__(self, "loops", tuple(loops))
        object.__setattr__(self, "points", _readonly_points(self.points, minimum=3))
        if not np.isfinite(self.angle_deg):
            raise ValueError("primitive angle must be finite")
        if self.kind == "polygon" and not self.loops:
            raise ValueError("polygon geometry requires loops")
        if self.kind in {"oriented_rectangle", "trapezoid"}:
            if self.points is None or self.points.shape[0] != 4:
                raise ValueError("four-point primitive requires four points")
        if self.kind == "ellipse":
            if self.center is None or self.axes is None:
                raise ValueError("ellipse requires center and axes")
            if min(self.axes) <= 0.0:
                raise ValueError("ellipse axes must be positive")
        if self.kind == "capsule":
            if self.segment_start is None or self.segment_end is None or self.radius is None:
                raise ValueError("capsule requires a segment and radius")
            if self.radius <= 0.0:
                raise ValueError("capsule radius must be positive")


@dataclass(frozen=True, slots=True)
class PrimitiveMetrics:
    iou: float
    undercoverage: float
    overcoverage: float
    neighbor_leakage: float
    critical_neighbor_leakage: float
    centroid_shift_ratio: float
    directional_under_loss: float
    directional_over_loss: float
    symmetric_boundary_distance: float
    protected_boundary_error: float
    contact_retention: float
    complexity_gain: float

    def __post_init__(self) -> None:
        names = (
            "iou", "undercoverage", "overcoverage", "neighbor_leakage",
            "critical_neighbor_leakage", "centroid_shift_ratio",
            "directional_under_loss", "directional_over_loss",
            "symmetric_boundary_distance", "protected_boundary_error",
            "contact_retention", "complexity_gain",
        )
        for name in names:
            value = float(getattr(self, name))
            if not np.isfinite(value) or value < 0.0 or value > 1.0:
                raise ValueError("primitive metric must be finite and within [0, 1]")


@dataclass(frozen=True, slots=True)
class PrimitiveCandidate:
    region_id: RegionId
    geometry: PrimitiveGeometry
    metrics: PrimitiveMetrics
    complexity: float
    baseline_complexity: float
    visual_error: float
    objective: float
    eligible: bool
    rejection_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.region_id < 0:
            raise ValueError("candidate region id must be non-negative")
        values = (self.complexity, self.baseline_complexity, self.visual_error, self.objective)
        if any(not np.isfinite(value) for value in values):
            raise ValueError("candidate scores must be finite")
        if self.complexity <= 0.0 or self.baseline_complexity <= 0.0:
            raise ValueError("candidate complexity must be positive")
        if len(self.rejection_reasons) != len(set(self.rejection_reasons)):
            raise ValueError("candidate reasons must be unique")
        if self.eligible and self.rejection_reasons:
            raise ValueError("eligible candidate cannot have reasons")


@dataclass(frozen=True, slots=True)
class RegionPrimitive:
    region_id: RegionId
    selected: PrimitiveCandidate
    candidates: tuple[PrimitiveCandidate, ...]

    def __post_init__(self) -> None:
        if self.region_id != self.selected.region_id:
            raise ValueError("selected candidate region mismatch")
        if not self.candidates:
            raise ValueError("region requires primitive candidates")
        if any(item.region_id != self.region_id for item in self.candidates):
            raise ValueError("candidate region mismatch")
        if self.selected not in self.candidates:
            raise ValueError("selected candidate must belong to candidates")

    @property
    def converted(self) -> bool:
        return self.selected.geometry.kind != "polygon"


@dataclass(frozen=True, slots=True)
class PrimitiveFittingMetrics:
    region_count: int
    converted_region_count: int
    primitive_counts: tuple[tuple[str, int], ...]
    mean_iou: float
    worst_critical_neighbor_leakage: float
    mean_complexity_gain: float

    def __post_init__(self) -> None:
        if self.region_count <= 0:
            raise ValueError("primitive metrics require regions")
        if not 0 <= self.converted_region_count <= self.region_count:
            raise ValueError("converted region count is invalid")
        keys = tuple(name for name, _ in self.primitive_counts)
        if len(keys) != len(set(keys)) or any(count < 0 for _, count in self.primitive_counts):
            raise ValueError("primitive counts must be unique and non-negative")
        for value in (self.mean_iou, self.worst_critical_neighbor_leakage, self.mean_complexity_gain):
            if not np.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError("primitive summary metrics must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class PrimitiveFittingResult:
    primitives: Mapping[RegionId, RegionPrimitive]
    metrics: PrimitiveFittingMetrics

    def __post_init__(self) -> None:
        items = dict(self.primitives)
        if len(items) != self.metrics.region_count:
            raise ValueError("primitive result region count mismatch")
        for region_id, primitive in items.items():
            if region_id != primitive.region_id:
                raise ValueError("primitive mapping key mismatch")
        object.__setattr__(self, "primitives", MappingProxyType(items))


@dataclass(frozen=True, slots=True)
class PrimitiveFitConfig:
    critical_neighbor_leakage_limit: float = 0.01
    adoption_margin: float = 0.03
    minimum_complexity_gain: float = 0.35
    min_iou: float = 0.88
    max_undercoverage: float = 0.12
    max_overcoverage: float = 0.12
    max_centroid_shift_ratio: float = 0.05
    max_directional_under_loss: float = 0.16
    max_directional_over_loss: float = 0.20
    max_boundary_distance: float = 0.04
    max_protected_boundary_error: float = 0.03
    min_contact_retention: float = 0.70
    contact_tolerance_px: float = 1.5
    protected_tolerance_px: float = 1.5
    complexity_reward: float = 0.20
    iou_weight: float = 0.28
    undercoverage_weight: float = 0.14
    overcoverage_weight: float = 0.10
    neighbor_leakage_weight: float = 0.10
    critical_leakage_weight: float = 0.30
    centroid_weight: float = 0.05
    directional_weight: float = 0.12
    boundary_distance_weight: float = 0.10
    protected_boundary_weight: float = 0.20
    contact_loss_weight: float = 0.10
    subject_critical_contrast: float = 0.65
    subject_confidence_threshold: float = 0.70
    semantic_hint_confidence: float = 0.80
    semantic_favored_bonus: float = 0.015
    semantic_disfavored_penalty: float = 0.015
    rectangle_complexity: float = 1.00
    ellipse_complexity: float = 1.10
    trapezoid_complexity: float = 1.15
    capsule_complexity: float = 1.20
    polygon_base_complexity: float = 1.00
    polygon_vertex_complexity: float = 0.18
    raster_scale: int = 2

    def __post_init__(self) -> None:
        bounded = (
            "critical_neighbor_leakage_limit", "minimum_complexity_gain", "min_iou",
            "max_undercoverage", "max_overcoverage", "max_centroid_shift_ratio",
            "max_directional_under_loss", "max_directional_over_loss",
            "max_boundary_distance", "max_protected_boundary_error",
            "min_contact_retention", "subject_critical_contrast",
            "subject_confidence_threshold", "semantic_hint_confidence",
        )
        for name in bounded:
            value = float(getattr(self, name))
            if not np.isfinite(value) or value < 0.0 or value > 1.0:
                raise ValueError("bounded primitive config must be within [0, 1]")
        positive = (
            "contact_tolerance_px", "protected_tolerance_px", "complexity_reward",
            "rectangle_complexity", "ellipse_complexity", "trapezoid_complexity",
            "capsule_complexity", "polygon_base_complexity", "polygon_vertex_complexity",
        )
        for name in positive:
            value = float(getattr(self, name))
            if not np.isfinite(value) or value <= 0.0:
                raise ValueError("positive primitive config must be finite and positive")
        weights = (
            self.iou_weight, self.undercoverage_weight, self.overcoverage_weight,
            self.neighbor_leakage_weight, self.critical_leakage_weight,
            self.centroid_weight, self.directional_weight,
            self.boundary_distance_weight, self.protected_boundary_weight,
            self.contact_loss_weight, self.semantic_favored_bonus,
            self.semantic_disfavored_penalty, self.adoption_margin,
        )
        if any(not np.isfinite(value) or value < 0.0 for value in weights):
            raise ValueError("primitive weights must be finite and non-negative")
        if self.raster_scale < 2:
            raise ValueError("primitive raster scale must be at least 2")
