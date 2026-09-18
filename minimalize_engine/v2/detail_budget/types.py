from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np

from minimalize_engine.v2.types import RegionId

RETAIN = "RETAIN"
COLLAPSE_STYLE = "COLLAPSE_STYLE"
HIDE_OVERLAY = "HIDE_OVERLAY"
DETAIL_ACTIONS = (RETAIN, COLLAPSE_STYLE, HIDE_OVERLAY)


@dataclass(frozen=True, slots=True)
class DetailShapeInfo:
    region_id: RegionId
    palette_id: int
    area_ratio: float
    area_score: float
    structural_score: float
    characteristic_score: float
    contrast_score: float
    semantic_score: float
    pose_score: float
    importance: float
    neighbor_ids: tuple[RegionId, ...] = ()
    anchor_ids: tuple[int, ...] = ()
    protected: bool = False
    protection_reasons: tuple[str, ...] = ()
    overlay: bool = False
    coverage_parent_id: RegionId | None = None

    def __post_init__(self) -> None:
        if self.region_id < 0 or self.palette_id < 0:
            raise ValueError("detail shape ids must be non-negative")
        for name in (
            "area_ratio", "area_score", "structural_score",
            "characteristic_score", "contrast_score", "semantic_score",
            "pose_score", "importance",
        ):
            value = float(getattr(self, name))
            if not np.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and within [0, 1]")
        if tuple(sorted(set(self.neighbor_ids))) != self.neighbor_ids:
            raise ValueError("neighbor ids must be unique and sorted")
        if self.region_id in self.neighbor_ids:
            raise ValueError("a shape cannot neighbor itself")
        if tuple(sorted(set(self.anchor_ids))) != self.anchor_ids:
            raise ValueError("anchor ids must be unique and sorted")
        if len(self.protection_reasons) != len(set(self.protection_reasons)):
            raise ValueError("protection reasons must be unique")
        if self.protection_reasons and not self.protected:
            raise ValueError("protection reasons require protected=True")
        if self.overlay and self.coverage_parent_id is None:
            raise ValueError("overlay shapes require a coverage parent")
        if not self.overlay and self.coverage_parent_id is not None:
            raise ValueError("core shapes cannot declare a coverage parent")


@dataclass(frozen=True, slots=True)
class DetailBudgetPolicy:
    preset: str
    target_min: int
    target_max: int
    collapse_importance_limit: float

    def __post_init__(self) -> None:
        if self.preset not in {"ultra_minimal", "minimal", "balanced", "detailed"}:
            raise ValueError("unknown detail-budget preset")
        if self.target_min <= 0 or self.target_max < self.target_min:
            raise ValueError("detail-budget target range is invalid")
        if not 0.0 <= self.collapse_importance_limit <= 1.0:
            raise ValueError("collapse importance limit must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class DetailBudgetMetrics:
    draw_geometry_count: int
    visual_group_count: int
    target_min: int
    target_max: int
    collapsed_style_count: int
    hidden_overlay_count: int
    protected_shape_count: int
    budget_overflow: bool

    def __post_init__(self) -> None:
        counts = (
            self.draw_geometry_count, self.visual_group_count,
            self.collapsed_style_count, self.hidden_overlay_count,
            self.protected_shape_count,
        )
        if any(value < 0 for value in counts):
            raise ValueError("detail-budget counts must be non-negative")
        if self.target_min <= 0 or self.target_max < self.target_min:
            raise ValueError("detail-budget target range is invalid")
        if self.visual_group_count > self.draw_geometry_count:
            raise ValueError("visual groups cannot exceed drawn geometry")


@dataclass(frozen=True, slots=True)
class DetailBudgetResult:
    shape_info: Mapping[RegionId, DetailShapeInfo]
    actions: Mapping[RegionId, str]
    effective_palette_by_region: Mapping[RegionId, int]
    fallback_region_by_region: Mapping[RegionId, RegionId | None]
    metrics: DetailBudgetMetrics

    def __post_init__(self) -> None:
        info = dict(self.shape_info)
        actions = dict(self.actions)
        palettes = dict(self.effective_palette_by_region)
        fallbacks = dict(self.fallback_region_by_region)
        keys = set(info)
        if set(actions) != keys or set(palettes) != keys or set(fallbacks) != keys:
            raise ValueError("detail-budget mappings must share identical region ids")
        if any(action not in DETAIL_ACTIONS for action in actions.values()):
            raise ValueError("detail-budget result contains unknown action")
        for region_id, item in info.items():
            if region_id != item.region_id:
                raise ValueError("detail shape mapping key mismatch")
            if actions[region_id] == HIDE_OVERLAY and not item.overlay:
                raise ValueError("core coverage regions cannot use HIDE_OVERLAY")
            if palettes[region_id] < 0:
                raise ValueError("effective palette ids must be non-negative")
        object.__setattr__(self, "shape_info", MappingProxyType(info))
        object.__setattr__(self, "actions", MappingProxyType(actions))
        object.__setattr__(self, "effective_palette_by_region", MappingProxyType(palettes))
        object.__setattr__(self, "fallback_region_by_region", MappingProxyType(fallbacks))


@dataclass(frozen=True, slots=True)
class DetailBudgetConfig:
    area_weight: float = 0.25
    structural_weight: float = 0.20
    characteristic_weight: float = 0.20
    contrast_weight: float = 0.15
    semantic_weight: float = 0.10
    pose_weight: float = 0.10
    structural_mass_area_ratio: float = 0.04
    silhouette_protection_ratio: float = 0.30
    pose_protection_threshold: float = 0.80
    semantic_protection_confidence: float = 0.90
    contrast_scale_delta_e: float = 30.0
    pose_full_elongation: float = 4.0
    critical_semantic_tags: tuple[str, ...] = (
        "face", "eye", "eyes", "mouth", "hand", "hands",
    )
    micro_detail_area_ratio: float = 0.0008
    micro_detail_importance_limit: float = 0.60
    micro_detail_presets: tuple[str, ...] = ("minimal",)
    medium_detail_area_ratio: float = 0.0015
    medium_detail_importance_limit: float = 0.60
    medium_detail_presets: tuple[str, ...] = ("minimal",)
    anchor_equivalence_delta_e: float = 6.0
    contrast_original_delta_e: float = 12.0
    contrast_assigned_delta_e: float = 5.0
    significant_delta_l: float = 12.0
    ultra_minimal_target: tuple[int, int] = (20, 40)
    minimal_target: tuple[int, int] = (28, 44)
    balanced_target: tuple[int, int] = (55, 95)
    detailed_target: tuple[int, int] = (90, 150)
    ultra_minimal_importance_limit: float = 0.64
    minimal_importance_limit: float = 0.60
    balanced_importance_limit: float = 0.48
    detailed_importance_limit: float = 0.40

    def __post_init__(self) -> None:
        weights = (
            self.area_weight, self.structural_weight, self.characteristic_weight,
            self.contrast_weight, self.semantic_weight, self.pose_weight,
        )
        if any(not np.isfinite(value) or value < 0.0 for value in weights):
            raise ValueError("importance weights must be finite and non-negative")
        if not np.isclose(sum(weights), 1.0, atol=1e-9):
            raise ValueError("importance weights must sum to 1")
        bounded = (
            self.structural_mass_area_ratio, self.silhouette_protection_ratio,
            self.pose_protection_threshold, self.semantic_protection_confidence,
            self.micro_detail_area_ratio, self.micro_detail_importance_limit,
            self.medium_detail_area_ratio, self.medium_detail_importance_limit,
        )
        if any(not np.isfinite(value) or not 0.0 <= value <= 1.0 for value in bounded):
            raise ValueError("detail-budget thresholds must be within [0, 1]")
        positive = (
            self.contrast_scale_delta_e, self.anchor_equivalence_delta_e,
            self.contrast_original_delta_e, self.contrast_assigned_delta_e,
            self.significant_delta_l,
        )
        if any(not np.isfinite(value) or value <= 0.0 for value in positive):
            raise ValueError("detail-budget distance thresholds must be positive")
        if self.pose_full_elongation <= 1.0:
            raise ValueError("pose_full_elongation must exceed 1")
        if self.contrast_assigned_delta_e >= self.contrast_original_delta_e:
            raise ValueError("assigned collapse threshold must be below original contrast threshold")
        if tuple(sorted(set(self.critical_semantic_tags))) != tuple(sorted(self.critical_semantic_tags)):
            raise ValueError("critical semantic tags must be unique")
        if len(self.micro_detail_presets) != len(set(self.micro_detail_presets)):
            raise ValueError("micro-detail presets must be unique")
        if len(self.medium_detail_presets) != len(set(self.medium_detail_presets)):
            raise ValueError("medium-detail presets must be unique")
        if self.medium_detail_area_ratio < self.micro_detail_area_ratio:
            raise ValueError("medium-detail area ratio must not be below micro-detail area ratio")
        valid_presets = {"ultra_minimal", "minimal", "balanced", "detailed"}
        if not set(self.micro_detail_presets) <= valid_presets:
            raise ValueError("micro-detail presets contain unknown names")
        if not set(self.medium_detail_presets) <= valid_presets:
            raise ValueError("medium-detail presets contain unknown names")
        for target in (
            self.ultra_minimal_target, self.minimal_target,
            self.balanced_target, self.detailed_target,
        ):
            if len(target) != 2 or target[0] <= 0 or target[1] < target[0]:
                raise ValueError("detail-budget target ranges must be ordered and positive")
        limits = (
            self.ultra_minimal_importance_limit, self.minimal_importance_limit,
            self.balanced_importance_limit, self.detailed_importance_limit,
        )
        if any(not np.isfinite(value) or not 0.0 <= value <= 1.0 for value in limits):
            raise ValueError("importance limits must be within [0, 1]")

    def policy_for(self, preset: str) -> DetailBudgetPolicy:
        targets = {
            "ultra_minimal": self.ultra_minimal_target,
            "minimal": self.minimal_target,
            "balanced": self.balanced_target,
            "detailed": self.detailed_target,
        }
        limits = {
            "ultra_minimal": self.ultra_minimal_importance_limit,
            "minimal": self.minimal_importance_limit,
            "balanced": self.balanced_importance_limit,
            "detailed": self.detailed_importance_limit,
        }
        if preset not in targets:
            raise ValueError(f"unknown detail-budget preset: {preset}")
        target_min, target_max = targets[preset]
        return DetailBudgetPolicy(preset, target_min, target_max, limits[preset])
