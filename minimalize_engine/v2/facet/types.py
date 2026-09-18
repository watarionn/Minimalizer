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


@dataclass(frozen=True, slots=True)
class PlanarFacetOverlay:
    region_id: RegionId
    rgb: tuple[int, int, int]
    line_a: float
    line_b: float
    line_c: float
    variant_side: int

    def __post_init__(self) -> None:
        if self.region_id < 0:
            raise ValueError("facet overlay region id must be non-negative")
        if len(self.rgb) != 3 or any(not 0 <= int(v) <= 255 for v in self.rgb):
            raise ValueError("facet overlay RGB must contain three uint8 values")
        if self.variant_side not in {-1, 1}:
            raise ValueError("facet overlay side must be -1 or 1")
        if not all(np.isfinite(v) for v in (self.line_a, self.line_b, self.line_c)):
            raise ValueError("facet overlay line must be finite")
        if np.hypot(self.line_a, self.line_b) <= 0.0:
            raise ValueError("facet overlay line normal must be non-zero")


@dataclass(frozen=True, slots=True)
class PlanarFacetGateDecision:
    region_id: RegionId
    accepted: bool
    reasons: tuple[str, ...]
    facet_count_delta: int
    large_share_delta: float
    mean_vertices_delta: float
    long_line_delta: float
    def __post_init__(self) -> None:
        if self.region_id < 0:
            raise ValueError("facet gate decision region id must be non-negative")
        if len(self.reasons) != len(set(self.reasons)):
            raise ValueError("facet gate reasons must be unique")
        if self.accepted and self.reasons:
            raise ValueError("accepted facet gate decision cannot have rejection reasons")
        for value in (self.large_share_delta, self.mean_vertices_delta, self.long_line_delta):
            if not np.isfinite(value):
                raise ValueError("facet gate deltas must be finite")


@dataclass(frozen=True, slots=True)
class PlanarFacetRenderMetrics:
    candidate_count: int
    accepted_count: int
    accepted_area_ratio: float
    baseline_facet_count: int
    final_facet_count: int
    baseline_large_share: float
    final_large_share: float
    baseline_mean_vertices: float
    final_mean_vertices: float
    baseline_long_line_support: float
    final_long_line_support: float

    def __post_init__(self) -> None:
        if not 0 <= self.accepted_count <= self.candidate_count:
            raise ValueError("accepted facet count must be within candidate count")
        if self.baseline_facet_count < 0 or self.final_facet_count < 0:
            raise ValueError("facet counts must be non-negative")
        bounded = (
            self.accepted_area_ratio, self.baseline_large_share, self.final_large_share,
            self.baseline_long_line_support, self.final_long_line_support,
        )
        if any(not np.isfinite(v) or not 0.0 <= v <= 1.0 for v in bounded):
            raise ValueError("facet render ratios must be within [0, 1]")
        for value in (self.baseline_mean_vertices, self.final_mean_vertices):
            if not np.isfinite(value) or value < 0.0:
                raise ValueError("facet render mean vertices must be non-negative")


@dataclass(frozen=True, slots=True)
class PlanarFacetRenderPlan:
    overlays: Mapping[RegionId, PlanarFacetOverlay]
    decisions: Mapping[RegionId, PlanarFacetGateDecision]
    metrics: PlanarFacetRenderMetrics

    def __post_init__(self) -> None:
        overlays = dict(self.overlays)
        decisions = dict(self.decisions)
        if set(overlays) - set(decisions):
            raise ValueError("facet overlays require gate decisions")
        if any(not decisions[rid].accepted for rid in overlays):
            raise ValueError("facet overlays must have accepted decisions")
        if self.metrics.accepted_count != len(overlays):
            raise ValueError("facet render metrics do not match overlays")
        if self.metrics.candidate_count != len(decisions):
            raise ValueError("facet render metrics do not match decisions")
        object.__setattr__(self, "overlays", MappingProxyType(overlays))
        object.__setattr__(self, "decisions", MappingProxyType(decisions))

@dataclass(frozen=True, slots=True)
class PlanarFacetGateConfig:
    enabled_presets: tuple[str, ...] = ("minimal",)
    max_long_line_loss: float = 0.005
    max_large_share_increase: float = 0.002
    max_mean_vertices_increase: float = 0.10
    min_large_share_gain: float = 0.002
    min_mean_vertices_gain: float = 0.05
    min_overlay_short_side_diagonal_ratio: float = 0.05
    max_overlay_aspect_ratio: float = 3.0
    protected_relationship_threshold: float = 0.75
    min_protected_contrast_ratio: float = 0.75
    significant_delta_l: float = 12.0
    line_min_diagonal_ratio: float = 0.04
    line_max_gap_diagonal_ratio: float = 0.007
    line_hough_threshold: int = 25
    macro_rgb_quantization: int = 32
    macro_min_area_ratio: float = 0.001
    macro_large_area_ratio: float = 0.02
    macro_polygon_epsilon_ratio: float = 0.02

    def __post_init__(self) -> None:
        valid = {"ultra_minimal", "minimal", "balanced", "detailed"}
        if len(self.enabled_presets) != len(set(self.enabled_presets)):
            raise ValueError("facet gate presets must be unique")
        if set(self.enabled_presets) - valid:
            raise ValueError("facet gate presets contain unknown names")
        bounded = (
            self.max_long_line_loss, self.max_large_share_increase,
            self.min_large_share_gain, self.min_overlay_short_side_diagonal_ratio,
            self.protected_relationship_threshold,
            self.min_protected_contrast_ratio, self.line_min_diagonal_ratio,
            self.line_max_gap_diagonal_ratio, self.macro_min_area_ratio,
            self.macro_large_area_ratio, self.macro_polygon_epsilon_ratio,
        )
        if any(not np.isfinite(v) or not 0.0 <= v <= 1.0 for v in bounded):
            raise ValueError("facet gate ratios must be within [0, 1]")
        positive = (
            self.max_mean_vertices_increase, self.min_mean_vertices_gain,
            self.significant_delta_l,
        )
        if any(not np.isfinite(v) or v < 0.0 for v in positive):
            raise ValueError("facet gate thresholds must be finite and non-negative")
        if not np.isfinite(self.max_overlay_aspect_ratio) or self.max_overlay_aspect_ratio < 1.0:
            raise ValueError("facet gate max overlay aspect ratio must be at least 1")
        if self.line_hough_threshold <= 0:
            raise ValueError("facet gate Hough threshold must be positive")
        if not 2 <= self.macro_rgb_quantization <= 128:
            raise ValueError("facet gate RGB quantization must be within [2, 128]")

    def enabled_for(self, preset: str) -> bool:
        if preset not in {"ultra_minimal", "minimal", "balanced", "detailed"}:
            raise ValueError(f"unknown facet gate preset: {preset}")
        return preset in self.enabled_presets
