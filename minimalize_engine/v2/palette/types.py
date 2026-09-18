from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.types import RegionId

LabColor = NDArray[np.float64]


def _readonly_lab(value: NDArray[np.floating]) -> LabColor:
    lab = np.array(value, dtype=np.float64, copy=True)
    if lab.shape != (3,) or not np.all(np.isfinite(lab)):
        raise ValueError("Lab color must be finite with shape (3,)")
    lab.flags.writeable = False
    return lab


def _validate_rgb(rgb: tuple[int, int, int]) -> None:
    if len(rgb) != 3 or any(not 0 <= int(value) <= 255 for value in rgb):
        raise ValueError("RGB color must contain three uint8 values")

@dataclass(frozen=True, slots=True)
class RegionColorSample:
    region_id: RegionId
    lab: LabColor
    rgb: tuple[int, int, int]
    source_xy: tuple[int, int]
    pixel_count: int
    anchor_ids: tuple[int, ...] = ()
    semantic_tag: str | None = None
    semantic_confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.region_id < 0 or self.pixel_count <= 0:
            raise ValueError("region color sample requires valid id and pixels")
        _validate_rgb(self.rgb)
        x, y = self.source_xy
        if x < 0 or y < 0:
            raise ValueError("source coordinates must be non-negative")
        if tuple(sorted(set(self.anchor_ids))) != self.anchor_ids:
            raise ValueError("anchor ids must be unique and sorted")
        if not 0.0 <= self.semantic_confidence <= 1.0:
            raise ValueError("semantic confidence must be within [0, 1]")
        if self.semantic_tag is None and self.semantic_confidence > 0.0:
            raise ValueError("semantic confidence requires a semantic tag")
        object.__setattr__(self, "lab", _readonly_lab(self.lab))


@dataclass(frozen=True, slots=True)
class PaletteRelationship:
    region_a: RegionId
    region_b: RegionId
    original_delta_e: float
    original_delta_l: float
    protection: float
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.region_a < 0 or self.region_b < 0 or self.region_a >= self.region_b:
            raise ValueError("palette relationship endpoints must be canonical")
        if not np.isfinite(self.original_delta_e) or self.original_delta_e < 0.0:
            raise ValueError("original DeltaE must be finite and non-negative")
        if not np.isfinite(self.original_delta_l):
            raise ValueError("original DeltaL must be finite")
        if not np.isfinite(self.protection) or not 0.0 <= self.protection <= 1.0:
            raise ValueError("relationship protection must be within [0, 1]")
        if not self.reasons or len(self.reasons) != len(set(self.reasons)):
            raise ValueError("relationship reasons must be non-empty and unique")


@dataclass(frozen=True, slots=True)
class PaletteNode:
    id: int
    left_id: int | None
    right_id: int | None
    member_regions: tuple[RegionId, ...]
    representative_region_id: RegionId
    lab: LabColor
    rgb: tuple[int, int, int]
    source_xy: tuple[int, int]
    merge_cost: float = 0.0
    hierarchy_height: float = 0.0
    anchor_ids: tuple[int, ...] = ()
    semantic_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.id < 0 or not self.member_regions:
            raise ValueError("palette node requires id and member regions")
        if tuple(sorted(set(self.member_regions))) != self.member_regions:
            raise ValueError("member regions must be unique and sorted")
        if self.representative_region_id not in self.member_regions:
            raise ValueError("representative region must belong to node")
        if (self.left_id is None) != (self.right_id is None):
            raise ValueError("palette node children must both be set or both be absent")
        if self.left_id is not None and self.left_id == self.right_id:
            raise ValueError("palette children must differ")
        if not np.isfinite(self.merge_cost) or self.merge_cost < 0.0:
            raise ValueError("palette merge cost must be finite and non-negative")
        if not np.isfinite(self.hierarchy_height) or self.hierarchy_height < self.merge_cost:
            raise ValueError("palette hierarchy height must be monotonic")
        _validate_rgb(self.rgb)
        if tuple(sorted(set(self.anchor_ids))) != self.anchor_ids:
            raise ValueError("palette anchor ids must be unique and sorted")
        if tuple(sorted(set(self.semantic_tags))) != self.semantic_tags:
            raise ValueError("palette semantic tags must be unique and sorted")
        object.__setattr__(self, "lab", _readonly_lab(self.lab))


@dataclass(slots=True)
class PaletteHierarchy:
    nodes: dict[int, PaletteNode]
    leaf_ids: frozenset[int]
    roots: set[int]
    merge_sequence: list[int]

    def __post_init__(self) -> None:
        node_ids = set(self.nodes)
        if not self.leaf_ids <= node_ids or not self.roots <= node_ids:
            raise ValueError("palette hierarchy ids must reference nodes")
        if len(self.merge_sequence) != len(set(self.merge_sequence)):
            raise ValueError("palette merge sequence must be unique")
        if any(node_id not in node_ids for node_id in self.merge_sequence):
            raise ValueError("palette merge sequence must reference nodes")


@dataclass(frozen=True, slots=True)
class PaletteEntry:
    palette_id: int
    member_regions: tuple[RegionId, ...]
    representative_region_id: RegionId
    lab: LabColor
    rgb: tuple[int, int, int]
    source_xy: tuple[int, int]
    anchor_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.palette_id < 0 or not self.member_regions:
            raise ValueError("palette entry requires id and member regions")
        if self.representative_region_id not in self.member_regions:
            raise ValueError("palette representative must belong to entry")
        _validate_rgb(self.rgb)
        if tuple(sorted(set(self.anchor_ids))) != self.anchor_ids:
            raise ValueError("palette entry anchor ids must be unique and sorted")
        object.__setattr__(self, "lab", _readonly_lab(self.lab))


@dataclass(frozen=True, slots=True)
class PaletteConsolidationMetrics:
    region_count: int
    palette_count: int
    target_min: int
    target_max: int
    protected_relationship_count: int
    repaired_split_count: int
    max_assignment_delta_e: float
    def __post_init__(self) -> None:
        if self.region_count <= 0 or self.palette_count <= 0:
            raise ValueError("palette metrics require positive counts")
        if not 1 <= self.palette_count <= self.region_count:
            raise ValueError("palette count must not exceed region count")
        if self.target_min <= 0 or self.target_max < self.target_min:
            raise ValueError("palette target range is invalid")
        if self.protected_relationship_count < 0 or self.repaired_split_count < 0:
            raise ValueError("palette metric counts must be non-negative")
        if not np.isfinite(self.max_assignment_delta_e) or self.max_assignment_delta_e < 0.0:
            raise ValueError("assignment DeltaE must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class PaletteConsolidationResult:
    entries: Mapping[int, PaletteEntry]
    region_to_palette: Mapping[RegionId, int]
    region_samples: Mapping[RegionId, RegionColorSample]
    relationships: tuple[PaletteRelationship, ...]
    hierarchy: PaletteHierarchy
    selected_node_ids: frozenset[int]
    metrics: PaletteConsolidationMetrics

    def __post_init__(self) -> None:
        entries = dict(self.entries)
        assignments = dict(self.region_to_palette)
        samples = dict(self.region_samples)
        if set(assignments) != set(samples):
            raise ValueError("every sampled region requires a palette assignment")
        if set(assignments.values()) - set(entries):
            raise ValueError("palette assignments reference missing entries")
        if set(entries) != set(self.selected_node_ids):
            raise ValueError("palette entries must match selected hierarchy nodes")
        if self.metrics.region_count != len(samples) or self.metrics.palette_count != len(entries):
            raise ValueError("palette result metrics do not match contents")
        object.__setattr__(self, "entries", MappingProxyType(entries))
        object.__setattr__(self, "region_to_palette", MappingProxyType(assignments))
        object.__setattr__(self, "region_samples", MappingProxyType(samples))


@dataclass(frozen=True, slots=True)
class PaletteConfig:
    mode: str = "auto"
    max_samples_per_region: int = 1024
    medoid_candidate_count: int = 64
    color_weight: float = 0.65
    anchor_weight: float = 0.15
    semantic_weight: float = 0.10
    relationship_weight: float = 0.10
    color_distance_scale: float = 25.0
    anchor_confidence_threshold: float = 0.80
    anchor_equivalence_delta_e: float = 6.0
    anchor_distinct_delta_e: float = 12.0
    contrast_original_delta_e: float = 12.0
    contrast_assigned_delta_e: float = 5.0
    significant_delta_l: float = 12.0
    major_region_area_ratio: float = 0.03
    semantic_confidence_threshold: float = 0.90
    subject_high_threshold: float = 0.80
    subject_low_threshold: float = 0.20
    subject_confidence_threshold: float = 0.80
    ultra_minimal_target: tuple[int, int] = (4, 6)
    minimal_target: tuple[int, int] = (6, 9)
    balanced_target: tuple[int, int] = (8, 12)
    detailed_target: tuple[int, int] = (12, 18)
    fixed_palette_size: int | None = None

    def __post_init__(self) -> None:
        if self.mode not in {"auto", "characteristic", "area", "fixed"}:
            raise ValueError("unknown palette mode")
        if self.max_samples_per_region <= 0 or self.medoid_candidate_count <= 0:
            raise ValueError("palette sampling limits must be positive")
        weights = (
            self.color_weight, self.anchor_weight,
            self.semantic_weight, self.relationship_weight,
        )
        if any(not np.isfinite(value) or value < 0.0 for value in weights):
            raise ValueError("palette weights must be finite and non-negative")
        if sum(weights) <= 0.0:
            raise ValueError("palette weights must have positive total")
        positive = (
            self.color_distance_scale, self.anchor_equivalence_delta_e,
            self.anchor_distinct_delta_e, self.contrast_original_delta_e,
            self.contrast_assigned_delta_e, self.significant_delta_l,
        )
        if any(not np.isfinite(value) or value <= 0.0 for value in positive):
            raise ValueError("palette distance thresholds must be positive")
        bounded = (
            self.anchor_confidence_threshold, self.major_region_area_ratio,
            self.semantic_confidence_threshold, self.subject_high_threshold,
            self.subject_low_threshold, self.subject_confidence_threshold,
        )
        if any(not np.isfinite(value) or not 0.0 <= value <= 1.0 for value in bounded):
            raise ValueError("palette bounded thresholds must be within [0, 1]")
        if self.subject_low_threshold > self.subject_high_threshold:
            raise ValueError("subject thresholds are reversed")
        if self.anchor_equivalence_delta_e >= self.anchor_distinct_delta_e:
            raise ValueError("anchor equivalence must be below distinct threshold")
        for target in (
            self.ultra_minimal_target, self.minimal_target,
            self.balanced_target, self.detailed_target,
        ):
            if len(target) != 2 or target[0] <= 0 or target[1] < target[0]:
                raise ValueError("palette target ranges must be positive and ordered")
        if self.mode == "fixed":
            if self.fixed_palette_size is None or self.fixed_palette_size <= 0:
                raise ValueError("fixed palette mode requires fixed_palette_size")
        elif self.fixed_palette_size is not None and self.fixed_palette_size <= 0:
            raise ValueError("fixed_palette_size must be positive when provided")

    def target_range(self, preset: str) -> tuple[int, int]:
        lookup = {
            "ultra_minimal": self.ultra_minimal_target,
            "minimal": self.minimal_target,
            "balanced": self.balanced_target,
            "detailed": self.detailed_target,
        }
        if preset not in lookup:
            raise ValueError(f"unknown preset: {preset}")
        if self.mode == "fixed":
            assert self.fixed_palette_size is not None
            return self.fixed_palette_size, self.fixed_palette_size
        return lookup[preset]
