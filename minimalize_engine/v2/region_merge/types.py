from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.types import (
    BBox,
    CharacteristicSupport,
    EdgeKey,
    LabelMap,
    RegionId,
)


def _readonly_copy(array: NDArray, dtype: np.dtype | type) -> NDArray:
    result = np.array(array, dtype=dtype, copy=True)
    result.flags.writeable = False
    return result


@dataclass(frozen=True, slots=True)
class RegionStats:
    id: RegionId
    pixel_count: int
    sum_lab: NDArray[np.float64]
    sum_sq_lab: NDArray[np.float64]
    sum_x: float
    sum_y: float
    sum_xx: float
    sum_yy: float
    sum_xy: float
    bbox: BBox
    perimeter_px: float
    hull_xy: NDArray[np.float32]
    hull_area: float
    subject_prob_sum: float = 0.0
    subject_confidence_sum: float = 0.0
    characteristic_supports: tuple[CharacteristicSupport, ...] = ()
    semantic_tag: str | None = None
    semantic_confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.pixel_count <= 0:
            raise ValueError("pixel_count must be positive")
        sum_lab = _readonly_copy(self.sum_lab, np.float64)
        sum_sq_lab = _readonly_copy(self.sum_sq_lab, np.float64)
        hull_xy = _readonly_copy(self.hull_xy, np.float32)
        if sum_lab.shape != (3,) or sum_sq_lab.shape != (3,):
            raise ValueError("Lab accumulators must have shape (3,)")
        if hull_xy.ndim != 2 or hull_xy.shape[1] != 2:
            raise ValueError("hull_xy must have shape (N, 2)")
        x0, y0, x1, y1 = self.bbox
        if x0 >= x1 or y0 >= y1:
            raise ValueError("bbox must use exclusive max coordinates")
        object.__setattr__(self, "sum_lab", sum_lab)
        object.__setattr__(self, "sum_sq_lab", sum_sq_lab)
        object.__setattr__(self, "hull_xy", hull_xy)

    @property
    def mean_lab(self) -> NDArray[np.float64]:
        return self.sum_lab / float(self.pixel_count)

    @property
    def lab_sse(self) -> float:
        channel_sse = self.sum_sq_lab - (self.sum_lab * self.sum_lab) / float(self.pixel_count)
        return float(np.maximum(channel_sse, 0.0).sum())

    @property
    def color_variance(self) -> float:
        return self.lab_sse / float(self.pixel_count)

    @property
    def centroid(self) -> tuple[float, float]:
        n = float(self.pixel_count)
        return self.sum_x / n, self.sum_y / n

    @property
    def subject_ratio(self) -> float:
        return self.subject_prob_sum / float(self.pixel_count)

    @property
    def subject_confidence(self) -> float:
        return self.subject_confidence_sum / float(self.pixel_count)

    @property
    def solidity(self) -> float:
        if self.hull_area <= 0.0:
            return 1.0
        return float(np.clip(self.pixel_count / self.hull_area, 0.0, 1.0))

    @property
    def covariance_xy(self) -> NDArray[np.float64]:
        n = float(self.pixel_count)
        cx, cy = self.centroid
        covariance = np.array(
            [
                [self.sum_xx / n - cx * cx, self.sum_xy / n - cx * cy],
                [self.sum_xy / n - cx * cy, self.sum_yy / n - cy * cy],
            ],
            dtype=np.float64,
        )
        covariance[np.abs(covariance) < 1e-12] = 0.0
        return covariance

    @property
    def principal_axis(self) -> tuple[float, float]:
        covariance = self.covariance_xy
        values, vectors = np.linalg.eigh(covariance)
        if float(values[-1]) <= 1e-12:
            return (1.0, 0.0)
        axis = vectors[:, -1].astype(np.float64, copy=False)
        if axis[0] < 0.0 or (abs(axis[0]) <= 1e-12 and axis[1] < 0.0):
            axis = -axis
        norm = float(np.linalg.norm(axis))
        if norm <= 1e-12:
            return (1.0, 0.0)
        return float(axis[0] / norm), float(axis[1] / norm)

    @property
    def elongation(self) -> float:
        values = np.maximum(np.linalg.eigvalsh(self.covariance_xy), 0.0)
        major = float(values[-1])
        minor = float(values[0])
        if major <= 1e-12:
            return 1.0
        return float(np.sqrt(major / max(minor, 1e-12)))

    @property
    def primary_anchor_id(self) -> int | None:
        if not self.characteristic_supports:
            return None
        support = max(
            self.characteristic_supports,
            key=lambda item: (item.support_mass * item.confidence, item.support_mass, -item.anchor_id),
        )
        return support.anchor_id

    @property
    def primary_anchor_confidence(self) -> float:
        if not self.characteristic_supports:
            return 0.0
        anchor_id = self.primary_anchor_id
        return max(
            item.confidence for item in self.characteristic_supports if item.anchor_id == anchor_id
        )


@dataclass(frozen=True, slots=True)
class RegionEdge:
    a: RegionId
    b: RegionId
    shared_boundary_px: float
    raw_gradient_hist: NDArray[np.int64]
    structural_gradient_hist: NDArray[np.int64]
    alpha_boundary_fraction: float = 0.0

    def __post_init__(self) -> None:
        if self.a == self.b:
            raise ValueError("region edge endpoints must differ")
        a, b = sorted((int(self.a), int(self.b)))
        raw = _readonly_copy(self.raw_gradient_hist, np.int64)
        structural = _readonly_copy(self.structural_gradient_hist, np.int64)
        if raw.ndim != 1 or structural.ndim != 1 or raw.shape != structural.shape:
            raise ValueError("gradient histograms must be 1D and have matching shapes")
        if self.shared_boundary_px <= 0.0:
            raise ValueError("shared_boundary_px must be positive")
        object.__setattr__(self, "a", a)
        object.__setattr__(self, "b", b)
        object.__setattr__(self, "raw_gradient_hist", raw)
        object.__setattr__(self, "structural_gradient_hist", structural)
        object.__setattr__(self, "alpha_boundary_fraction", float(np.clip(self.alpha_boundary_fraction, 0.0, 1.0)))


@dataclass(slots=True)
class RegionGraph:
    nodes: dict[RegionId, RegionStats]
    edges: dict[EdgeKey, RegionEdge]
    adjacency: dict[RegionId, set[RegionId]]
    initial_labels: LabelMap
    next_region_id: RegionId

    def __post_init__(self) -> None:
        labels = np.array(self.initial_labels, dtype=np.int32, copy=True)
        labels.flags.writeable = False
        self.initial_labels = labels


@dataclass(frozen=True, slots=True)
class MergeTreeNode:
    region_id: RegionId
    left_id: RegionId | None
    right_id: RegionId | None
    raw_merge_cost: float
    hierarchy_height: float
    stage: str
    stats: RegionStats


@dataclass(slots=True)
class RegionMergeTree:
    nodes: dict[RegionId, MergeTreeNode]
    leaf_ids: frozenset[RegionId]
    roots: set[RegionId]
    merge_sequence: list[RegionId]
