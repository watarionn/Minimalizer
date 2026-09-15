from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np

_ARTIFACT_LEVELS = ("none", "summary", "standard", "full")


@dataclass(frozen=True, slots=True)
class RegressionManifest:
    run_id: str
    timestamp_utc: str
    code_revision: str
    config_hash: str
    python_version: str
    opencv_version: str
    platform: str
    preset: str
    phase_configs: Mapping[str, object]
    source_hash: str
    reference_hash: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.run_id, self.timestamp_utc, self.code_revision,
            self.config_hash, self.python_version, self.opencv_version,
            self.platform, self.preset, self.source_hash,
        )
        if any(not value for value in required):
            raise ValueError("regression manifest fields must be non-empty")
        object.__setattr__(self, "phase_configs", MappingProxyType(dict(self.phase_configs)))


@dataclass(frozen=True, slots=True)
class InvariantCheck:
    name: str
    passed: bool
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("invariant name must be non-empty")
@dataclass(frozen=True, slots=True)
class RegressionMetrics:
    initial_region_count: int
    selected_region_count: int
    micro_region_ratio: float
    thin_region_ratio: float
    vertex_count: int
    contour_iou: float
    max_directional_loss: float
    primitive_conversion_rate: float
    polygon_fallback_rate: float
    neighbor_leakage: float
    palette_count: int
    characteristic_anchor_recall: float | None
    contrast_retention: float
    lightness_flip_count: int
    visual_group_count: int
    visible_edge_density: float
    long_line_support: float
    long_line_count: int
    total_complexity: float
    subject_background_leakage: float | None
    runtime_seconds: float
    phase_timings: Mapping[str, float]

    def __post_init__(self) -> None:
        counts = (
            self.initial_region_count, self.selected_region_count,
            self.vertex_count, self.palette_count,
            self.lightness_flip_count, self.visual_group_count, self.long_line_count,
        )
        if any(value < 0 for value in counts):
            raise ValueError("regression counts must be non-negative")
        bounded = (
            self.micro_region_ratio, self.thin_region_ratio,
            self.contour_iou, self.max_directional_loss,
            self.primitive_conversion_rate, self.polygon_fallback_rate,
            self.neighbor_leakage, self.contrast_retention,
            self.visible_edge_density, self.long_line_support,
        )
        if any(not np.isfinite(value) or not 0.0 <= value <= 1.0 for value in bounded):
            raise ValueError("bounded regression metrics must be within [0, 1]")
        for value in (self.characteristic_anchor_recall, self.subject_background_leakage):
            if value is not None and (not np.isfinite(value) or not 0.0 <= value <= 1.0):
                raise ValueError("optional regression ratios must be within [0, 1]")
        if not np.isfinite(self.total_complexity) or self.total_complexity < 0.0:
            raise ValueError("total complexity must be finite and non-negative")
        if not np.isfinite(self.runtime_seconds) or self.runtime_seconds < 0.0:
            raise ValueError("runtime must be finite and non-negative")
        timings = dict(self.phase_timings)
        if any(not np.isfinite(value) or value < 0.0 for value in timings.values()):
            raise ValueError("phase timings must be finite and non-negative")
        object.__setattr__(self, "phase_timings", MappingProxyType(timings))
@dataclass(frozen=True, slots=True)
class RegressionConfig:
    artifact_level: str = "standard"
    main_preset: str = "minimal"
    micro_region_area_ratio: float = 0.001
    thin_region_ratio_threshold: float = 0.15
    performance_warning_factor: float = 1.5
    long_line_min_diagonal_ratio: float = 0.04
    long_line_max_gap_diagonal_ratio: float = 0.007
    long_line_hough_threshold: int = 25

    def __post_init__(self) -> None:
        if self.artifact_level not in _ARTIFACT_LEVELS:
            raise ValueError("unknown debug artifact level")
        if self.main_preset not in {"ultra_minimal", "minimal", "balanced", "detailed"}:
            raise ValueError("unknown regression preset")
        for value in (
            self.micro_region_area_ratio, self.thin_region_ratio_threshold,
            self.long_line_min_diagonal_ratio, self.long_line_max_gap_diagonal_ratio,
        ):
            if not np.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError("regression ratio thresholds must be within [0, 1]")
        if self.long_line_hough_threshold <= 0:
            raise ValueError("long-line Hough threshold must be positive")
        if not np.isfinite(self.performance_warning_factor) or self.performance_warning_factor < 1.0:
            raise ValueError("performance warning factor must be at least 1")


@dataclass(frozen=True, slots=True)
class RegressionCaseResult:
    manifest: RegressionManifest
    metrics: RegressionMetrics
    invariants: tuple[InvariantCheck, ...]
    algorithm_digest: str
    debug_artifacts: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.algorithm_digest:
            raise ValueError("algorithm digest must be non-empty")
        artifacts = dict(self.debug_artifacts)
        if any(not key or not value for key, value in artifacts.items()):
            raise ValueError("debug artifact mapping must contain non-empty paths")
        object.__setattr__(self, "debug_artifacts", MappingProxyType(artifacts))

    @property
    def invariant_failures(self) -> tuple[InvariantCheck, ...]:
        return tuple(item for item in self.invariants if not item.passed)


@dataclass(frozen=True, slots=True)
class MetricDelta:
    name: str
    current: float
    baseline: float
    delta: float
    relative_delta: float | None
    severity: str

    def __post_init__(self) -> None:
        if self.severity not in {"ok", "warning", "failure"}:
            raise ValueError("unknown metric delta severity")
