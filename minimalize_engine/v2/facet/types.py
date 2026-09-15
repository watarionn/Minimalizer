from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np

from minimalize_engine.v2.types import RegionId


@dataclass(frozen=True, slots=True)
class PlanarFacetCandidate:
    region_id: RegionId
    base_palette_id: int
    variant_rgb: tuple[int, int, int]
    line_a: float
    line_b: float
    line_c: float
    variant_side: int
    overlay_area_ratio: float
    source_gradient_range: float
    source_delta_e: float

    def __post_init__(self) -> None:
        if self.region_id < 0 or self.base_palette_id < 0:
            raise ValueError("facet ids must be non-negative")
        if len(self.variant_rgb) != 3 or any(not 0 <= int(v) <= 255 for v in self.variant_rgb):
            raise ValueError("facet RGB must contain three uint8 values")
        if self.variant_side not in {-1, 1}:
            raise ValueError("facet side must be -1 or 1")
        for value in (self.line_a, self.line_b, self.line_c, self.overlay_area_ratio,
                      self.source_gradient_range, self.source_delta_e):
            if not np.isfinite(value):
                raise ValueError("facet values must be finite")
        if np.hypot(self.line_a, self.line_b) <= 0.0:
            raise ValueError("facet line normal must be non-zero")
        if not 0.0 < self.overlay_area_ratio < 1.0:
            raise ValueError("facet overlay area ratio must be within (0, 1)")
        if self.source_gradient_range < 0.0 or self.source_delta_e < 0.0:
            raise ValueError("facet evidence must be non-negative")


@dataclass(frozen=True, slots=True)
class PlanarFacetMetrics:
    candidate_count: int
    candidate_area_ratio: float
    mean_gradient_range: float

    def __post_init__(self) -> None:
        if self.candidate_count < 0:
            raise ValueError("facet candidate count must be non-negative")
        if not np.isfinite(self.candidate_area_ratio) or self.candidate_area_ratio < 0.0:
            raise ValueError("facet candidate area ratio must be finite and non-negative")
        if not np.isfinite(self.mean_gradient_range) or self.mean_gradient_range < 0.0:
            raise ValueError("facet gradient mean must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class PlanarFacetResult:
    candidates: Mapping[RegionId, PlanarFacetCandidate]
    metrics: PlanarFacetMetrics

    def __post_init__(self) -> None:
        items = dict(self.candidates)
        if len(items) != self.metrics.candidate_count:
            raise ValueError("facet metrics do not match candidate mapping")
        for region_id, candidate in items.items():
            if region_id != candidate.region_id:
                raise ValueError("facet candidate mapping key mismatch")
        object.__setattr__(self, "candidates", MappingProxyType(items))


@dataclass(frozen=True, slots=True)
class PlanarFacetConfig:
    enabled_presets: tuple[str, ...] = ("minimal",)
    min_region_area_ratio: float = 0.012
    min_gradient_range: float = 5.0
    blend_alpha: float = 0.22
    min_source_half_ratio: float = 0.25
    min_overlay_half_ratio: float = 0.20
    min_rgb_delta: float = 4.0
    min_sample_pixels: int = 40
    critical_semantic_tags: tuple[str, ...] = ("face", "eye", "eyes", "mouth", "hand", "hands")

    def __post_init__(self) -> None:
        valid = {"ultra_minimal", "minimal", "balanced", "detailed"}
        if len(self.enabled_presets) != len(set(self.enabled_presets)):
            raise ValueError("facet presets must be unique")
        if set(self.enabled_presets) - valid:
            raise ValueError("facet presets contain unknown names")
        bounded = (self.min_region_area_ratio, self.blend_alpha, self.min_source_half_ratio, self.min_overlay_half_ratio)
        if any(not np.isfinite(v) or not 0.0 <= v <= 1.0 for v in bounded):
            raise ValueError("facet ratios must be finite and within [0, 1]")
        if self.min_source_half_ratio >= 0.5 or self.min_overlay_half_ratio >= 0.5:
            raise ValueError("facet minimum half-area ratios must be below 0.5")
        if not np.isfinite(self.min_gradient_range) or self.min_gradient_range < 0.0:
            raise ValueError("facet gradient range must be finite and non-negative")
        if not np.isfinite(self.min_rgb_delta) or self.min_rgb_delta < 0.0:
            raise ValueError("facet RGB delta must be finite and non-negative")
        if self.min_sample_pixels < 3:
            raise ValueError("facet sample pixel count must be at least 3")
        if len(self.critical_semantic_tags) != len(set(self.critical_semantic_tags)):
            raise ValueError("facet critical semantic tags must be unique")

    def enabled_for(self, preset: str) -> bool:
        if preset not in {"ultra_minimal", "minimal", "balanced", "detailed"}:
            raise ValueError(f"unknown facet preset: {preset}")
        return preset in self.enabled_presets
