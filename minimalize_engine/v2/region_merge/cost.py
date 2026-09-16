from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from minimalize_engine.v2.region_merge.graph import _merged_hull
from minimalize_engine.v2.region_merge.types import RegionEdge, RegionStats


@dataclass(frozen=True, slots=True)
class RegionMergeConfig:
    color_weight: float = 0.30
    boundary_weight: float = 0.25
    structure_weight: float = 0.15
    topology_weight: float = 0.10
    anchor_weight: float = 0.10
    geometry_weight: float = 0.10
    redundancy_weight: float = 0.15
    color_tau: float = 25.0
    hull_inflation_tau: float = 0.25
    thin_neck_tau: float = 0.15
    subject_high_threshold: float = 0.80
    background_low_threshold: float = 0.20
    subject_confidence_threshold: float = 0.80
    alpha_hard_threshold: float = 0.80
    anchor_confidence_threshold: float = 0.80
    anchor_delta_e_threshold: float = 18.0
    semantic_confidence_threshold: float = 0.90
    semantic_hard_pairs: tuple[tuple[str, str], ...] = ()
    soft_protection_cap: float = 0.35
    major_mass_ratio: float = 0.03
    major_mass_weight: float = 0.20
    accent_weight: float = 0.15
    safe_area_ratio: float = 0.0008
    safe_color_cost: float = 0.08
    safe_boundary_cost: float = 0.15
    safe_structure_cost: float = 0.05
    safe_anchor_cost: float = 0.05
    safe_topology_cost: float = 0.25
    safe_shared_boundary_ratio: float = 0.35
    safe_soft_protection: float = 0.02
    gradient_bins: int = 32
    slic_iterations: int = 10
    edge_coverage_threshold: float = 0.75
    retry_scale: float = 0.80
    max_retry_target_factor: float = 2.5
    slic_provider: str = "numpy_slico"

    def __post_init__(self) -> None:
        positive = (
            "color_tau", "hull_inflation_tau", "thin_neck_tau",
            "anchor_delta_e_threshold", "major_mass_ratio",
            "max_retry_target_factor",
        )
        for name in positive:
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        for name in (
            "color_weight", "boundary_weight", "structure_weight",
            "topology_weight", "anchor_weight", "geometry_weight",
            "redundancy_weight",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
        for name in (
            "subject_high_threshold", "background_low_threshold",
            "subject_confidence_threshold", "alpha_hard_threshold",
            "anchor_confidence_threshold", "semantic_confidence_threshold",
            "soft_protection_cap", "major_mass_weight", "accent_weight",
            "safe_area_ratio", "safe_color_cost", "safe_boundary_cost",
            "safe_structure_cost", "safe_anchor_cost", "safe_topology_cost",
            "safe_shared_boundary_ratio", "safe_soft_protection",
            "edge_coverage_threshold", "retry_scale",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and within [0, 1]")
        if self.background_low_threshold >= self.subject_high_threshold:
            raise ValueError("background threshold must be below subject threshold")
        if self.gradient_bins <= 1 or self.slic_iterations <= 0:
            raise ValueError("gradient_bins and slic_iterations must be positive")
        if not isinstance(self.slic_provider, str) or not self.slic_provider:
            raise ValueError("slic_provider must be a non-empty string")
        if self.max_retry_target_factor < 1.0:
            raise ValueError("max_retry_target_factor must be at least 1")
        if not 0.0 < self.retry_scale < 1.0:
            raise ValueError("retry_scale must be in (0, 1)")
        for pair in self.semantic_hard_pairs:
            if len(pair) != 2 or not pair[0] or not pair[1]:
                raise ValueError("semantic_hard_pairs must contain non-empty string pairs")


@dataclass(frozen=True, slots=True)
class MergeEvaluation:
    allowed: bool
    total_cost: float
    color_cost: float
    boundary_cost: float
    structure_cost: float
    topology_cost: float
    anchor_cost: float
    geometry_cost: float
    soft_protection: float
    redundancy_reward: float
    blocked_by: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.allowed:
            if not math.isfinite(self.total_cost):
                raise ValueError("allowed merge total_cost must be finite")
        elif not math.isinf(self.total_cost):
            raise ValueError("blocked merge total_cost must be infinite")
        for name in (
            "color_cost", "boundary_cost", "structure_cost", "topology_cost",
            "anchor_cost", "geometry_cost", "redundancy_reward",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within [0, 1]")
        if not math.isfinite(self.soft_protection) or self.soft_protection < 0.0:
            raise ValueError("soft_protection must be finite and non-negative")


def _hist_quantile(hist: np.ndarray, q: float) -> float:
    counts = np.asarray(hist, dtype=np.int64)
    total = int(counts.sum())
    if total <= 0:
        return 0.0
    target = q * (total - 1)
    cumulative = np.cumsum(counts)
    index = int(np.searchsorted(cumulative, target + 1.0, side="left"))
    bins = counts.size
    return float(index / max(1, bins - 1))


def color_cost(left: RegionStats, right: RegionStats, *, tau: float) -> float:
    n_left = float(left.pixel_count)
    n_right = float(right.pixel_count)
    delta = left.mean_lab - right.mean_lab
    delta_sse = (n_left * n_right / (n_left + n_right)) * float(delta @ delta)
    per_pixel = delta_sse / (n_left + n_right)
    return float(1.0 - math.exp(-per_pixel / tau))


def boundary_cost(edge: RegionEdge) -> float:
    structural = 0.45 * _hist_quantile(edge.structural_gradient_hist, 0.75)
    structural += 0.55 * _hist_quantile(edge.structural_gradient_hist, 0.90)
    raw = 0.40 * _hist_quantile(edge.raw_gradient_hist, 0.90)
    raw += 0.60 * _hist_quantile(edge.raw_gradient_hist, 0.98)
    return float(np.clip(max(structural, 0.35 * raw), 0.0, 1.0))


def shared_boundary_ratio(left: RegionStats, right: RegionStats, edge: RegionEdge) -> float:
    denominator = max(1e-12, min(left.perimeter_px, right.perimeter_px))
    return float(np.clip(edge.shared_boundary_px / denominator, 0.0, 1.0))


def structure_cost(left: RegionStats, right: RegionStats) -> float:
    confidence = min(left.subject_confidence, right.subject_confidence)
    return float(np.clip(abs(left.subject_ratio - right.subject_ratio) * confidence, 0.0, 1.0))


def topology_cost(left: RegionStats, right: RegionStats, edge: RegionEdge, *, tau: float) -> float:
    ratio = shared_boundary_ratio(left, right, edge)
    return float(np.clip(math.exp(-ratio / tau), 0.0, 1.0))


def geometry_cost(left: RegionStats, right: RegionStats, edge: RegionEdge, *, tau: float) -> float:
    # Geometry cost only needs the merged hull area. Building a full RegionStats
    # candidate here repeats accumulator, annotation, and validation work that is
    # only required when a merge is actually applied.
    _, merged_hull_area = _merged_hull(left.hull_xy, right.hull_xy)
    base_hull = max(1e-12, left.hull_area + right.hull_area)
    inflation = max(0.0, merged_hull_area - base_hull) / base_hull
    return float(np.clip(1.0 - math.exp(-inflation / tau), 0.0, 1.0))


def _support_confidence(stats: RegionStats) -> dict[int, float]:
    return {support.anchor_id: support.confidence for support in stats.characteristic_supports}


def _distinct_anchor_signal(left: RegionStats, right: RegionStats) -> tuple[float, bool]:
    left_supports = _support_confidence(left)
    right_supports = _support_confidence(right)
    if not left_supports or not right_supports:
        return 0.0, False
    common = set(left_supports) & set(right_supports)
    if common:
        common_strength = max(min(left_supports[key], right_supports[key]) for key in common)
    else:
        common_strength = 0.0
    left_best = max(left_supports.values())
    right_best = max(right_supports.values())
    distinct_strength = min(left_best, right_best) * (1.0 - common_strength)
    return float(np.clip(distinct_strength, 0.0, 1.0)), not bool(common)


def anchor_cost(left: RegionStats, right: RegionStats, *, delta_e_threshold: float) -> tuple[float, float, bool]:
    signal, distinct = _distinct_anchor_signal(left, right)
    delta_e = float(np.linalg.norm(left.mean_lab - right.mean_lab))
    delta_factor = min(1.0, delta_e / delta_e_threshold)
    return float(np.clip(signal * delta_factor, 0.0, 1.0)), delta_e, distinct


def _semantic_pair_key(left: str, right: str) -> tuple[str, str]:
    return (left, right) if left <= right else (right, left)


def hard_barriers(
    left: RegionStats,
    right: RegionStats,
    edge: RegionEdge,
    *,
    anchor_delta_e: float,
    anchors_distinct: bool,
    config: RegionMergeConfig,
) -> tuple[str, ...]:
    blocked: list[str] = []
    left_subject = left.subject_ratio >= config.subject_high_threshold
    right_subject = right.subject_ratio >= config.subject_high_threshold
    left_background = left.subject_ratio <= config.background_low_threshold
    right_background = right.subject_ratio <= config.background_low_threshold
    left_confident = left.subject_confidence >= config.subject_confidence_threshold
    right_confident = right.subject_confidence >= config.subject_confidence_threshold
    if left_confident and right_confident and (
        (left_subject and right_background) or (right_subject and left_background)
    ):
        blocked.append("subject_background")
    if edge.alpha_boundary_fraction >= config.alpha_hard_threshold:
        blocked.append("alpha")

    left_anchor_conf = left.primary_anchor_confidence
    right_anchor_conf = right.primary_anchor_confidence
    if (
        anchors_distinct
        and left_anchor_conf >= config.anchor_confidence_threshold
        and right_anchor_conf >= config.anchor_confidence_threshold
    ):
        blocked.append("characteristic_anchor")

    if (
        left.semantic_tag is not None
        and right.semantic_tag is not None
        and left.semantic_confidence >= config.semantic_confidence_threshold
        and right.semantic_confidence >= config.semantic_confidence_threshold
    ):
        hard_pairs = {_semantic_pair_key(a, b) for a, b in config.semantic_hard_pairs}
        if _semantic_pair_key(left.semantic_tag, right.semantic_tag) in hard_pairs:
            blocked.append("semantic")

    return tuple(blocked)


def soft_protection(
    left: RegionStats,
    right: RegionStats,
    *,
    image_area: int,
    config: RegionMergeConfig,
) -> float:
    smaller_ratio = min(left.pixel_count, right.pixel_count) / float(image_area)
    major = config.major_mass_weight * min(1.0, smaller_ratio / config.major_mass_ratio)

    left_ids = {support.anchor_id for support in left.characteristic_supports}
    right_ids = {support.anchor_id for support in right.characteristic_supports}
    unique_anchor_conf = 0.0
    if left_ids - right_ids:
        unique_anchor_conf = max(unique_anchor_conf, left.primary_anchor_confidence)
    if right_ids - left_ids:
        unique_anchor_conf = max(unique_anchor_conf, right.primary_anchor_confidence)
    accent = config.accent_weight * unique_anchor_conf
    return float(min(config.soft_protection_cap, major + accent))


def redundancy_reward(
    left: RegionStats,
    right: RegionStats,
    edge: RegionEdge,
    *,
    image_area: int,
    color: float,
    boundary: float,
) -> float:
    smaller_ratio = min(left.pixel_count, right.pixel_count) / float(image_area)
    smallness = math.exp(-smaller_ratio / 0.01)
    similarity = 1.0 - color
    weak_boundary = 1.0 - boundary
    enclosure = min(1.0, shared_boundary_ratio(left, right, edge) / 0.50)
    return float(np.clip(smallness * similarity * weak_boundary * enclosure, 0.0, 1.0))


def evaluate_merge(
    left: RegionStats,
    right: RegionStats,
    edge: RegionEdge,
    *,
    image_area: int,
    config: RegionMergeConfig,
) -> MergeEvaluation:
    if image_area <= 0:
        raise ValueError("image_area must be positive")
    c_color = color_cost(left, right, tau=config.color_tau)
    c_boundary = boundary_cost(edge)
    c_structure = structure_cost(left, right)
    c_topology = topology_cost(left, right, edge, tau=config.thin_neck_tau)
    c_anchor, anchor_delta_e, anchors_distinct = anchor_cost(
        left,
        right,
        delta_e_threshold=config.anchor_delta_e_threshold,
    )
    c_geometry = geometry_cost(
        left,
        right,
        edge,
        tau=config.hull_inflation_tau,
    )
    protection = soft_protection(left, right, image_area=image_area, config=config)
    redundancy = redundancy_reward(
        left,
        right,
        edge,
        image_area=image_area,
        color=c_color,
        boundary=c_boundary,
    )
    blocked = hard_barriers(
        left,
        right,
        edge,
        anchor_delta_e=anchor_delta_e,
        anchors_distinct=anchors_distinct,
        config=config,
    )
    if blocked:
        return MergeEvaluation(
            allowed=False,
            total_cost=math.inf,
            color_cost=c_color,
            boundary_cost=c_boundary,
            structure_cost=c_structure,
            topology_cost=c_topology,
            anchor_cost=c_anchor,
            geometry_cost=c_geometry,
            soft_protection=protection,
            redundancy_reward=redundancy,
            blocked_by=blocked,
        )

    base_cost = (
        config.color_weight * c_color
        + config.boundary_weight * c_boundary
        + config.structure_weight * c_structure
        + config.topology_weight * c_topology
        + config.anchor_weight * c_anchor
        + config.geometry_weight * c_geometry
    )
    total = float(np.clip(base_cost + protection - config.redundancy_weight * redundancy, 0.0, 1.35))
    return MergeEvaluation(
        allowed=True,
        total_cost=total,
        color_cost=c_color,
        boundary_cost=c_boundary,
        structure_cost=c_structure,
        topology_cost=c_topology,
        anchor_cost=c_anchor,
        geometry_cost=c_geometry,
        soft_protection=protection,
        redundancy_reward=redundancy,
    )


def is_safe_consolidation(
    left: RegionStats,
    right: RegionStats,
    edge: RegionEdge,
    evaluation: MergeEvaluation,
    *,
    image_area: int,
    config: RegionMergeConfig,
) -> bool:
    if not evaluation.allowed:
        return False
    area_ratio = min(left.pixel_count, right.pixel_count) / float(image_area)
    return (
        area_ratio <= config.safe_area_ratio
        and evaluation.color_cost <= config.safe_color_cost
        and evaluation.boundary_cost <= config.safe_boundary_cost
        and evaluation.structure_cost <= config.safe_structure_cost
        and evaluation.anchor_cost <= config.safe_anchor_cost
        and evaluation.topology_cost <= config.safe_topology_cost
        and shared_boundary_ratio(left, right, edge) >= config.safe_shared_boundary_ratio
        and evaluation.soft_protection <= config.safe_soft_protection
    )
