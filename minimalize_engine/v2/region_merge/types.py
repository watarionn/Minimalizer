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
        if self.id < 0:
            raise ValueError("region id must be non-negative")
        if self.pixel_count <= 0:
            raise ValueError("pixel_count must be positive")
        scalar_values = (
            self.sum_x, self.sum_y, self.sum_xx, self.sum_yy, self.sum_xy,
            self.perimeter_px, self.hull_area, self.subject_prob_sum,
            self.subject_confidence_sum, self.semantic_confidence,
        )
        if not all(np.isfinite(value) for value in scalar_values):
            raise ValueError("RegionStats scalar values must be finite")
        if self.perimeter_px <= 0.0 or self.hull_area <= 0.0:
            raise ValueError("perimeter_px and hull_area must be positive")
        if not 0.0 <= self.subject_prob_sum <= self.pixel_count:
            raise ValueError("subject_prob_sum must be within [0, pixel_count]")
        if not 0.0 <= self.subject_confidence_sum <= self.pixel_count:
            raise ValueError("subject_confidence_sum must be within [0, pixel_count]")
        if not 0.0 <= self.semantic_confidence <= 1.0:
            raise ValueError("semantic_confidence must be within [0, 1]")
        if self.semantic_tag is None and self.semantic_confidence != 0.0:
            raise ValueError("semantic_confidence requires semantic_tag")
        support_ids = tuple(item.anchor_id for item in self.characteristic_supports)
        if len(support_ids) != len(set(support_ids)):
            raise ValueError("characteristic support anchor ids must be unique")
        sum_lab = _readonly_copy(self.sum_lab, np.float64)
        sum_sq_lab = _readonly_copy(self.sum_sq_lab, np.float64)
        hull_xy = _readonly_copy(self.hull_xy, np.float32)
        if sum_lab.shape != (3,) or sum_sq_lab.shape != (3,):
            raise ValueError("Lab accumulators must have shape (3,)")
        if not np.all(np.isfinite(sum_lab)) or not np.all(np.isfinite(sum_sq_lab)):
            raise ValueError("Lab accumulators must be finite")
        if np.any(sum_sq_lab < 0.0):
            raise ValueError("sum_sq_lab must be non-negative")
        if hull_xy.ndim != 2 or hull_xy.shape[1] != 2 or hull_xy.shape[0] < 3:
            raise ValueError("hull_xy must have shape (N, 2) with N >= 3")
        if not np.all(np.isfinite(hull_xy)):
            raise ValueError("hull_xy must be finite")
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
        if self.a < 0 or self.b < 0:
            raise ValueError("region edge endpoints must be non-negative")
        if self.a == self.b:
            raise ValueError("region edge endpoints must differ")
        a, b = sorted((int(self.a), int(self.b)))
        raw = _readonly_copy(self.raw_gradient_hist, np.int64)
        structural = _readonly_copy(self.structural_gradient_hist, np.int64)
        if raw.ndim != 1 or structural.ndim != 1 or raw.shape != structural.shape or raw.size < 2:
            raise ValueError("gradient histograms must be matching 1D arrays with at least 2 bins")
        if np.any(raw < 0) or np.any(structural < 0):
            raise ValueError("gradient histogram counts must be non-negative")
        if int(raw.sum()) != int(structural.sum()):
            raise ValueError("raw and structural histogram counts must match")
        if not np.isfinite(self.shared_boundary_px) or self.shared_boundary_px <= 0.0:
            raise ValueError("shared_boundary_px must be finite and positive")
        if not np.isfinite(self.alpha_boundary_fraction) or not 0.0 <= self.alpha_boundary_fraction <= 1.0:
            raise ValueError("alpha_boundary_fraction must be within [0, 1]")
        object.__setattr__(self, "a", a)
        object.__setattr__(self, "b", b)
        object.__setattr__(self, "raw_gradient_hist", raw)
        object.__setattr__(self, "structural_gradient_hist", structural)
        object.__setattr__(self, "alpha_boundary_fraction", float(self.alpha_boundary_fraction))


@dataclass(slots=True)
class RegionGraph:
    nodes: dict[RegionId, RegionStats]
    edges: dict[EdgeKey, RegionEdge]
    adjacency: dict[RegionId, set[RegionId]]
    initial_labels: LabelMap
    next_region_id: RegionId

    def __post_init__(self) -> None:
        labels = np.array(self.initial_labels, dtype=np.int32, copy=True)
        if labels.ndim != 2 or labels.size == 0 or np.any(labels < 0):
            raise ValueError("initial_labels must be a non-empty 2D non-negative label map")
        if self.next_region_id < 0:
            raise ValueError("next_region_id must be non-negative")
        if self.nodes and self.next_region_id <= max(self.nodes):
            raise ValueError("next_region_id must be greater than all active region ids")
        for region_id, stats in self.nodes.items():
            if region_id != stats.id:
                raise ValueError("RegionGraph node key must match RegionStats.id")
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

    def __post_init__(self) -> None:
        if self.region_id < 0 or self.stats.id != self.region_id:
            raise ValueError("merge-tree region id must match stats.id and be non-negative")
        if (self.left_id is None) != (self.right_id is None):
            raise ValueError("merge-tree nodes must have either zero or two children")
        if self.left_id is not None and self.left_id == self.right_id:
            raise ValueError("merge-tree children must differ")
        if not np.isfinite(self.raw_merge_cost) or self.raw_merge_cost < 0.0:
            raise ValueError("raw_merge_cost must be finite and non-negative")
        if not np.isfinite(self.hierarchy_height) or self.hierarchy_height < self.raw_merge_cost:
            raise ValueError("hierarchy_height must be finite and at least raw_merge_cost")
        if not self.stage:
            raise ValueError("merge-tree stage must not be empty")


@dataclass(slots=True)
class RegionMergeTree:
    nodes: dict[RegionId, MergeTreeNode]
    leaf_ids: frozenset[RegionId]
    roots: set[RegionId]
    merge_sequence: list[RegionId]

    def __post_init__(self) -> None:
        node_ids = set(self.nodes)
        if not self.leaf_ids <= node_ids:
            raise ValueError("leaf_ids must reference merge-tree nodes")
        if not self.roots <= node_ids:
            raise ValueError("roots must reference merge-tree nodes")
        if len(self.merge_sequence) != len(set(self.merge_sequence)):
            raise ValueError("merge_sequence must not contain duplicates")
        if any(region_id not in node_ids for region_id in self.merge_sequence):
            raise ValueError("merge_sequence must reference merge-tree nodes")


@dataclass(frozen=True, slots=True)
class RegionMergeMetrics:
    initial_edge_count: int
    evaluation_count: int
    blocked_evaluation_count: int
    safe_candidate_count: int
    final_root_count: int
    barrier_counts: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "initial_edge_count", "evaluation_count", "blocked_evaluation_count",
            "safe_candidate_count", "final_root_count",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        keys = tuple(key for key, _ in self.barrier_counts)
        if len(keys) != len(set(keys)) or any(count < 0 for _, count in self.barrier_counts):
            raise ValueError("barrier_counts must contain unique non-negative entries")


@dataclass(frozen=True, slots=True)
class RegionMergeResult:
    initial_labels: LabelMap
    tree: RegionMergeTree
    initial_region_count: int
    safe_merge_count: int
    hierarchy_merge_count: int
    metrics: RegionMergeMetrics

    def __post_init__(self) -> None:
        labels = np.array(self.initial_labels, dtype=np.int32, copy=True)
        if labels.ndim != 2 or labels.size == 0 or np.any(labels < 0):
            raise ValueError("initial_labels must be a non-empty 2D non-negative map")
        labels.flags.writeable = False
        object.__setattr__(self, "initial_labels", labels)
        if self.initial_region_count <= 0:
            raise ValueError("initial_region_count must be positive")
        if self.safe_merge_count < 0 or self.hierarchy_merge_count < 0:
            raise ValueError("merge counts must be non-negative")
        total_merges = self.safe_merge_count + self.hierarchy_merge_count
        if total_merges != len(self.tree.merge_sequence):
            raise ValueError("merge counts must match merge-tree sequence")
        if self.metrics.final_root_count != len(self.tree.roots):
            raise ValueError("metrics final_root_count must match tree roots")
        if len(self.tree.leaf_ids) != self.initial_region_count:
            raise ValueError("initial_region_count must match merge-tree leaves")
        if self.initial_region_count - total_merges != len(self.tree.roots):
            raise ValueError("initial regions minus merges must equal root count")
