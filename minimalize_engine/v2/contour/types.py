from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.types import RegionId


PointArray = NDArray[np.float32]


def _readonly_points(value: NDArray[np.floating]) -> PointArray:
    points = np.array(value, dtype=np.float32, copy=True)
    if points.ndim != 2 or points.shape[1] != 2 or points.shape[0] < 2:
        raise ValueError("boundary points must have shape (N, 2) with N >= 2")
    if not np.all(np.isfinite(points)):
        raise ValueError("boundary points must be finite")
    points.flags.writeable = False
    return points


@dataclass(frozen=True, slots=True)
class BoundaryVertex:
    id: int
    x: float
    y: float
    protected: bool = False
    protection_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.id < 0:
            raise ValueError("boundary vertex id must be non-negative")
        if not np.isfinite(self.x) or not np.isfinite(self.y):
            raise ValueError("boundary vertex coordinates must be finite")
        if len(self.protection_reasons) != len(set(self.protection_reasons)):
            raise ValueError("boundary vertex protection reasons must be unique")
        if self.protection_reasons and not self.protected:
            raise ValueError("protection reasons require protected=True")


@dataclass(frozen=True, slots=True)
class BoundaryChain:
    id: int
    start_vertex: int
    end_vertex: int
    points: PointArray
    regions: tuple[RegionId, ...]
    protected: bool = False
    protection_reasons: tuple[str, ...] = ()
    original_point_count: int = 0

    def __post_init__(self) -> None:
        if self.id < 0 or self.start_vertex < 0 or self.end_vertex < 0:
            raise ValueError("boundary chain ids must be non-negative")
        if not 1 <= len(self.regions) <= 2:
            raise ValueError("boundary chain must border one or two regions")
        if tuple(sorted(set(self.regions))) != self.regions:
            raise ValueError("boundary chain regions must be unique and sorted")
        points = _readonly_points(self.points)
        if self.original_point_count <= 0:
            object.__setattr__(self, "original_point_count", int(points.shape[0]))
        if self.original_point_count < points.shape[0]:
            raise ValueError("original_point_count cannot be below final point count")
        if len(self.protection_reasons) != len(set(self.protection_reasons)):
            raise ValueError("boundary chain protection reasons must be unique")
        if self.protection_reasons and not self.protected:
            raise ValueError("protection reasons require protected=True")
        object.__setattr__(self, "points", points)


@dataclass(frozen=True, slots=True)
class OrientedChainRef:
    chain_id: int
    reversed: bool


@dataclass(slots=True)
class BoundaryGraph:
    vertices: dict[int, BoundaryVertex]
    chains: dict[int, BoundaryChain]
    region_chains: dict[RegionId, list[OrientedChainRef]]

    def __post_init__(self) -> None:
        if not self.chains:
            raise ValueError("BoundaryGraph must contain at least one chain")
        for chain_id, chain in self.chains.items():
            if chain_id != chain.id:
                raise ValueError("boundary chain key must match chain.id")
            if chain.start_vertex not in self.vertices or chain.end_vertex not in self.vertices:
                raise ValueError("boundary chain references a missing vertex")
        for region_id, refs in self.region_chains.items():
            if region_id < 0 or not refs:
                raise ValueError("every BoundaryGraph region must reference chains")
            for ref in refs:
                if ref.chain_id not in self.chains:
                    raise ValueError("region chain reference is missing")
                if region_id not in self.chains[ref.chain_id].regions:
                    raise ValueError("region chain reference does not border region")


@dataclass(frozen=True, slots=True)
class RegionContour:
    region_id: RegionId
    loops: tuple[PointArray, ...]
    area_px: int
    centroid: tuple[float, float]
    semantic_tag: str | None = None
    semantic_confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.region_id < 0 or self.area_px <= 0:
            raise ValueError("RegionContour requires non-negative id and positive area")
        if not self.loops:
            raise ValueError("RegionContour must contain at least one loop")
        normalized: list[PointArray] = []
        for loop in self.loops:
            points = np.array(loop, dtype=np.float32, copy=True)
            if points.ndim != 2 or points.shape[1] != 2 or points.shape[0] < 3:
                raise ValueError("contour loops must have shape (N, 2) with N >= 3")
            if not np.all(np.isfinite(points)):
                raise ValueError("contour loop points must be finite")
            points.flags.writeable = False
            normalized.append(points)
        if not all(np.isfinite(value) for value in self.centroid):
            raise ValueError("RegionContour centroid must be finite")
        if not 0.0 <= self.semantic_confidence <= 1.0:
            raise ValueError("semantic_confidence must be within [0, 1]")
        if self.semantic_tag is None and self.semantic_confidence > 0.0:
            raise ValueError("semantic confidence requires semantic tag")
        object.__setattr__(self, "loops", tuple(normalized))


@dataclass(frozen=True, slots=True)
class ContourSimplificationConfig:
    detailed_epsilon_ratio: float = 0.008
    balanced_epsilon_ratio: float = 0.014
    minimal_epsilon_ratio: float = 0.022
    ultra_minimal_epsilon_ratio: float = 0.030
    epsilon_min_px: float = 0.75
    epsilon_max_px: float = 18.0
    candidate_factors: tuple[float, ...] = (1.0, 0.75, 0.50, 0.25, 0.0)
    strong_corner_threshold: float = 0.65
    characteristic_protection_confidence: float = 0.80
    semantic_protection_confidence: float = 0.90
    max_area_change: float = 0.08
    min_iou: float = 0.90
    max_centroid_shift_ratio: float = 0.04
    max_directional_loss: float = 0.14
    face_directional_factor: float = 0.65
    major_mass_directional_factor: float = 0.80
    major_mass_ratio: float = 0.03
    raster_scale: int = 2

    def __post_init__(self) -> None:
        ratios = (
            self.detailed_epsilon_ratio, self.balanced_epsilon_ratio,
            self.minimal_epsilon_ratio, self.ultra_minimal_epsilon_ratio,
        )
        if any(not np.isfinite(value) or value < 0.0 for value in ratios):
            raise ValueError("epsilon ratios must be finite and non-negative")
        if tuple(sorted(ratios)) != ratios:
            raise ValueError("coarser presets must not reduce epsilon ratio")
        if not 0.0 <= self.epsilon_min_px <= self.epsilon_max_px:
            raise ValueError("epsilon pixel clamp must be ordered and non-negative")
        if not self.candidate_factors or self.candidate_factors[-1] != 0.0:
            raise ValueError("candidate ladder must end with exact fallback factor 0")
        if any(
            not np.isfinite(value) or not 0.0 <= value <= 1.0
            for value in self.candidate_factors
        ):
            raise ValueError("candidate factors must be finite and within [0, 1]")
        if any(
            left < right
            for left, right in zip(self.candidate_factors, self.candidate_factors[1:])
        ):
            raise ValueError("candidate factors must be descending")
        for name in (
            "strong_corner_threshold", "characteristic_protection_confidence",
            "semantic_protection_confidence", "max_area_change", "min_iou",
            "max_centroid_shift_ratio", "max_directional_loss",
            "face_directional_factor", "major_mass_directional_factor",
            "major_mass_ratio",
        ):
            value = float(getattr(self, name))
            if not np.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and within [0, 1]")
        if self.raster_scale < 2:
            raise ValueError("raster_scale must be at least 2")

    def epsilon_ratio_for(self, preset: str) -> float:
        lookup = {
            "detailed": self.detailed_epsilon_ratio,
            "balanced": self.balanced_epsilon_ratio,
            "minimal": self.minimal_epsilon_ratio,
            "ultra_minimal": self.ultra_minimal_epsilon_ratio,
        }
        if preset not in lookup:
            raise ValueError(f"unknown contour preset: {preset}")
        return lookup[preset]


@dataclass(frozen=True, slots=True)
class ContourSimplificationMetrics:
    original_vertex_count: int
    simplified_vertex_count: int
    protected_chain_count: int
    fallback_chain_count: int
    rejected_candidate_count: int
    min_region_iou: float
    max_area_change: float
    max_centroid_shift_ratio: float
    max_directional_loss: float

    def __post_init__(self) -> None:
        for name in (
            "original_vertex_count", "simplified_vertex_count",
            "protected_chain_count", "fallback_chain_count",
            "rejected_candidate_count",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.simplified_vertex_count > self.original_vertex_count:
            raise ValueError("contour simplification cannot add vertices")
        for name in (
            "min_region_iou", "max_area_change",
            "max_centroid_shift_ratio", "max_directional_loss",
        ):
            value = float(getattr(self, name))
            if not np.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and within [0, 1]")


@dataclass(frozen=True, slots=True)
class ContourSimplificationResult:
    boundary_graph: BoundaryGraph
    contours: Mapping[RegionId, RegionContour]
    metrics: ContourSimplificationMetrics

    def __post_init__(self) -> None:
        contour_map = dict(self.contours)
        if set(contour_map) != set(self.boundary_graph.region_chains):
            raise ValueError("contour regions must exactly match BoundaryGraph regions")
        for region_id, contour in contour_map.items():
            if region_id != contour.region_id:
                raise ValueError("contour mapping key must match RegionContour.region_id")
        object.__setattr__(self, "contours", MappingProxyType(contour_map))
