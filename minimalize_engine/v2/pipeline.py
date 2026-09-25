from __future__ import annotations

from dataclasses import dataclass, field, replace
from time import perf_counter
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

import cv2
import numpy as np
from numpy.typing import NDArray

from minimalize_engine.v2.analysis_guidance import (
    AnalysisGuidance,
    line_support_from_guide,
    semantic_regions_from_guide,
    structural_regions_from_guide,
)
from minimalize_engine.v2.characteristic import annotate_initial_regions
from minimalize_engine.v2.contour import (
    ContourSimplificationConfig,
    ContourSimplificationResult,
    simplify_region_contours,
)
from minimalize_engine.v2.detail_budget import (
    HIDE_OVERLAY,
    DetailBudgetConfig,
    DetailBudgetResult,
    analyze_shape_importance,
    apply_detail_budget,
)
from minimalize_engine.v2.facet import (
    PlanarFacetConfig, PlanarFacetGateConfig, PlanarFacetOverlay,
    PlanarFacetRenderPlan, PlanarFacetResult, build_facet_render_plan,
    build_planar_facets,
)
from minimalize_engine.v2.palette import (
    PaletteConfig,
    PaletteConsolidationResult,
    PaletteEntry,
    consolidate_palette,
)
from minimalize_engine.v2.preprocessing import (
    DEFAULT_ANALYSIS_MAX_SIDE,
    ShadingFlattenConfig,
    build_image_bundle,
)
from minimalize_engine.v2.person_parts import (
    PersonPartConfig,
    PersonPartPartition,
    build_person_part_partition,
    resize_person_part_partition,
)
from minimalize_engine.v2.primitive import (
    PrimitiveFitConfig,
    PrimitiveFittingResult,
    PrimitiveGeometry,
    fit_region_primitives,
)
from minimalize_engine.v2.region_merge.cost import RegionMergeConfig
from minimalize_engine.v2.region_merge.cut import (
    build_cut_family,
    default_cut_policies,
    materialize_region_selection,
)
from minimalize_engine.v2.region_merge.graph import build_region_graph
from minimalize_engine.v2.region_merge.hierarchy import run_region_merge_from_graph
from minimalize_engine.v2.region_merge.segmentation import oversegment
from minimalize_engine.v2.region_merge.types import (
    CutPolicy,
    HierarchyCut,
    HierarchyCutFamily,
    RegionMergeResult,
    RegionSelection,
)
from minimalize_engine.v2.types import CharacteristicContext, ImageBundle, RegionId

_CANONICAL_PRESETS = ("detailed", "balanced", "minimal", "ultra_minimal")
TimingObserver = Callable[[str, float], None]


def _timed(observer: TimingObserver | None, name: str, fn):
    started = perf_counter()
    result = fn()
    if observer is not None:
        observer(name, perf_counter() - started)
    return result
@dataclass(frozen=True, slots=True)
class SceneShape:
    region_id: RegionId
    geometry: PrimitiveGeometry
    palette_id: int
    visible: bool = True

    def __post_init__(self) -> None:
        if self.region_id < 0 or self.palette_id < 0:
            raise ValueError("scene shape ids must be non-negative")


@dataclass(frozen=True, slots=True)
class SceneModel:
    width: int
    height: int
    shapes: tuple[SceneShape, ...]
    palette: tuple[PaletteEntry, ...]
    facet_overlays: tuple[PlanarFacetOverlay, ...] = ()

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("scene dimensions must be positive")
        region_ids = tuple(shape.region_id for shape in self.shapes)
        if len(region_ids) != len(set(region_ids)):
            raise ValueError("scene region ids must be unique")
        palette_ids = {entry.palette_id for entry in self.palette}
        if any(shape.palette_id not in palette_ids for shape in self.shapes):
            raise ValueError("scene shape references unknown palette entry")
        overlay_ids = tuple(item.region_id for item in self.facet_overlays)
        if len(overlay_ids) != len(set(overlay_ids)):
            raise ValueError("scene facet overlay region ids must be unique")
        if set(overlay_ids) - set(region_ids):
            raise ValueError("scene facet overlays must reference scene regions")


@dataclass(frozen=True, slots=True)
class LayeredPersonConfig:
    enabled: bool = False
    independent_parts: bool = True
    coarse_part_primitives: bool = True
    semantic_shape_budget: bool = True
    semantic_plane_refit: bool = True
    semantic_coverage_guard: bool = True
    parts: PersonPartConfig = field(default_factory=PersonPartConfig)


@dataclass(frozen=True, slots=True)
class ShadingFlattenGuardConfig:
    enabled: bool = False
    max_polygon_vertex_ratio: float = 1.05
    max_part_polygon_vertex_ratio: float = 1.20
    max_initial_region_ratio: float = 1.10
    max_global_palette_delta: int = 1
    max_total_part_palette_ratio: float = 1.20
    max_single_part_palette_increase: int = 2
    max_relaxed_single_part_palette_increase: int = 4
    palette_growth_relax_part_reduction_ratio: float = 0.25
    min_edge_energy_retention: float = 0.65
    max_subject_color_mae: float = 0.08
    max_subject_color_p95: float = 0.22
    min_region_reduction_ratio: float = 0.02
    min_polygon_reduction_ratio: float = 0.02
    min_part_polygon_reduction_ratio: float = 0.08

    def __post_init__(self) -> None:
        for name in (
            "max_polygon_vertex_ratio",
            "max_part_polygon_vertex_ratio",
            "max_initial_region_ratio",
            "max_total_part_palette_ratio",
            "min_edge_energy_retention",
        ):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        for name in (
            "max_subject_color_mae",
            "max_subject_color_p95",
            "palette_growth_relax_part_reduction_ratio",
            "min_region_reduction_ratio",
            "min_polygon_reduction_ratio",
            "min_part_polygon_reduction_ratio",
        ):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
        for name in (
            "max_global_palette_delta",
            "max_single_part_palette_increase",
            "max_relaxed_single_part_palette_increase",
        ):
            if int(getattr(self, name)) < 0:
                raise ValueError(f"{name} must be non-negative")
        if (
            self.max_relaxed_single_part_palette_increase
            < self.max_single_part_palette_increase
        ):
            raise ValueError(
                "relaxed single-part palette increase must not be stricter"
            )


@dataclass(frozen=True, slots=True)
class ShadingFlattenDecision:
    accepted: bool
    reasons: tuple[str, ...]
    baseline_initial_regions: int
    candidate_initial_regions: int
    baseline_polygon_vertices: int
    candidate_polygon_vertices: int
    baseline_part_polygon_vertices: int
    candidate_part_polygon_vertices: int
    global_palette_delta: int
    total_part_palette_ratio: float
    max_part_palette_increase: int
    part_palette_growth_relaxed: bool
    edge_energy_retention: float
    subject_color_mae: float
    subject_color_p95: float
    alpha_preserved: bool
    silhouette_preserved: bool


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    analysis_max_side: int = DEFAULT_ANALYSIS_MAX_SIDE
    shading_flatten: ShadingFlattenConfig = field(default_factory=ShadingFlattenConfig)
    shading_flatten_guard: ShadingFlattenGuardConfig = field(
        default_factory=ShadingFlattenGuardConfig
    )
    region_merge: RegionMergeConfig = field(default_factory=RegionMergeConfig)
    contour: ContourSimplificationConfig = field(default_factory=ContourSimplificationConfig)
    primitive: PrimitiveFitConfig = field(default_factory=PrimitiveFitConfig)
    palette: PaletteConfig = field(default_factory=PaletteConfig)
    detail_budget: DetailBudgetConfig = field(default_factory=DetailBudgetConfig)
    facet: PlanarFacetConfig = field(default_factory=PlanarFacetConfig)
    facet_gate: PlanarFacetGateConfig = field(default_factory=PlanarFacetGateConfig)
    layered_person: LayeredPersonConfig = field(default_factory=LayeredPersonConfig)
    cut_policies: Mapping[str, CutPolicy] | None = None


@dataclass(frozen=True, slots=True)
class PresetPipelineResult:
    preset: str
    selection: RegionSelection
    contour: ContourSimplificationResult
    primitives: PrimitiveFittingResult
    palette: PaletteConsolidationResult
    detail_budget: DetailBudgetResult
    facet_reconstruction: PlanarFacetResult
    facet_render_plan: PlanarFacetRenderPlan
    scene: SceneModel

    def __post_init__(self) -> None:
        if self.preset != self.selection.preset:
            raise ValueError("preset result must match RegionSelection preset")
        expected = set(self.selection.region_ids)
        if set(self.contour.contours) != expected:
            raise ValueError("contour regions must match preset selection")
        if set(self.primitives.primitives) != expected:
            raise ValueError("primitive regions must match preset selection")
        if set(self.palette.region_to_palette) != expected:
            raise ValueError("palette regions must match preset selection")
        if set(self.detail_budget.shape_info) != expected:
            raise ValueError("detail-budget regions must match preset selection")
        if not set(self.facet_reconstruction.candidates) <= expected:
            raise ValueError("facet candidates must belong to preset selection")
        if set(self.facet_render_plan.overlays) - set(self.facet_reconstruction.candidates):
            raise ValueError("accepted facet overlays must come from facet candidates")


@dataclass(frozen=True, slots=True)
class MinimalizerV2Result:
    bundle: ImageBundle
    characteristic: CharacteristicContext | None
    region_merge: RegionMergeResult
    cut_family: HierarchyCutFamily
    presets: Mapping[str, PresetPipelineResult]
    person_parts: PersonPartPartition | None = None
    person_part_presets: Mapping[str, Mapping[str, PresetPipelineResult]] = field(default_factory=dict)
    shading_flatten_decision: ShadingFlattenDecision | None = None

    def __post_init__(self) -> None:
        presets = dict(self.presets)
        if not presets:
            raise ValueError("MinimalizerV2Result requires at least one preset")
        unknown = set(presets) - set(_CANONICAL_PRESETS)
        if unknown:
            raise ValueError(f"unknown pipeline presets: {sorted(unknown)}")
        if any(name != result.preset for name, result in presets.items()):
            raise ValueError("preset mapping keys must match result presets")
        object.__setattr__(self, "presets", MappingProxyType(presets))
        part_presets = {
            name: MappingProxyType(dict(items))
            for name, items in self.person_part_presets.items()
        }
        if self.person_parts is None and part_presets:
            raise ValueError("person_part_presets require person_parts")
        object.__setattr__(self, "person_part_presets", MappingProxyType(part_presets))


def _scene_from_results(
    bundle: ImageBundle,
    primitives: PrimitiveFittingResult,
    palette: PaletteConsolidationResult,
    detail_budget: DetailBudgetResult,
    facet_render_plan: PlanarFacetRenderPlan,
) -> SceneModel:
    shapes: list[SceneShape] = []
    for region_id in sorted(primitives.primitives):
        primitive = primitives.primitives[region_id]
        action = detail_budget.actions[region_id]
        palette_id = detail_budget.effective_palette_by_region[region_id]
        shapes.append(
            SceneShape(
                region_id=region_id,
                geometry=primitive.selected.geometry,
                palette_id=palette_id,
                visible=action != HIDE_OVERLAY,
            )
        )
    palette_entries = tuple(
        palette.entries[palette_id]
        for palette_id in sorted(palette.entries)
    )
    height, width = bundle.analysis_rgb.shape[:2]
    return SceneModel(
        width=int(width),
        height=int(height),
        shapes=tuple(shapes),
        palette=palette_entries,
        facet_overlays=tuple(facet_render_plan.overlays[rid] for rid in sorted(facet_render_plan.overlays)),
    )


def _cut_for_preset(family: HierarchyCutFamily, preset: str) -> HierarchyCut:
    if preset not in _CANONICAL_PRESETS:
        raise ValueError(f"unknown preset: {preset}")
    return getattr(family, preset)


def _validate_presets(presets: tuple[str, ...]) -> tuple[str, ...]:
    if not presets:
        raise ValueError("at least one preset is required")
    if len(presets) != len(set(presets)):
        raise ValueError("preset names must be unique")
    unknown = set(presets) - set(_CANONICAL_PRESETS)
    if unknown:
        raise ValueError(f"unknown presets: {sorted(unknown)}")
    return presets
def _run_preset_pipeline(
    bundle: ImageBundle,
    merge_result: RegionMergeResult,
    cut: HierarchyCut,
    *,
    characteristic: CharacteristicContext | None,
    config: PipelineConfig,
    observer: TimingObserver | None,
) -> PresetPipelineResult:
    preset = cut.preset
    selection = _timed(
        observer,
        f"{preset}.hierarchy_cut_materialize",
        lambda: materialize_region_selection(merge_result, cut),
    )
    contour = _timed(
        observer,
        f"{preset}.contour",
        lambda: simplify_region_contours(
            bundle, merge_result, selection, config=config.contour
        ),
    )
    primitives = _timed(
        observer,
        f"{preset}.primitive",
        lambda: fit_region_primitives(
            bundle, selection, contour, config=config.primitive
        ),
    )
    palette = _timed(
        observer,
        f"{preset}.palette",
        lambda: consolidate_palette(
            bundle,
            selection,
            contour,
            primitives,
            characteristic=characteristic,
            config=config.palette,
        ),
    )
    shape_info = _timed(
        observer,
        f"{preset}.importance",
        lambda: analyze_shape_importance(
            bundle,
            selection,
            contour,
            primitives,
            palette,
            config=config.detail_budget,
        ),
    )
    detail_budget = _timed(
        observer,
        f"{preset}.detail_budget",
        lambda: apply_detail_budget(
            shape_info,
            palette,
            policy=config.detail_budget.policy_for(preset),
            config=config.detail_budget,
        ),
    )
    facet_reconstruction = _timed(
        observer,
        f"{preset}.facet_reconstruction",
        lambda: build_planar_facets(
            bundle, selection, primitives, palette, detail_budget,
            preset=preset, config=config.facet,
        ),
    )
    facet_render_plan = _timed(
        observer, f"{preset}.facet_gate",
        lambda: build_facet_render_plan(selection.labels.shape, primitives, palette, detail_budget, facet_reconstruction, preset=preset, config=config.facet_gate),
    )
    scene = _timed(
        observer, f"{preset}.scene",
        lambda: _scene_from_results(bundle, primitives, palette, detail_budget, facet_render_plan),
    )
    return PresetPipelineResult(
        preset=preset,
        selection=selection,
        contour=contour,
        primitives=primitives,
        palette=palette,
        detail_budget=detail_budget,
        facet_reconstruction=facet_reconstruction,
        facet_render_plan=facet_render_plan,
        scene=scene,
    )


def run_preset_pipeline(
    bundle: ImageBundle,
    merge_result: RegionMergeResult,
    cut: HierarchyCut,
    *,
    characteristic: CharacteristicContext | None,
    config: PipelineConfig,
) -> PresetPipelineResult:
    return _run_preset_pipeline(
        bundle,
        merge_result,
        cut,
        characteristic=characteristic,
        config=config,
        observer=None,
    )
def _person_part_cut_policies(part_name: str) -> dict[str, CutPolicy]:
    base = default_cut_policies()
    # Per-part budgets keep the layered result coarse instead of multiplying
    # the whole-person 40-shape Minimal ceiling by six.
    budgets = {
        "head": (18, 10, 6, 4),
        "torso": (16, 9, 5, 3),
        "left_arm": (10, 6, 3, 2),
        "right_arm": (10, 6, 3, 2),
        "left_leg": (10, 6, 3, 2),
        "right_leg": (10, 6, 3, 2),
    }
    detailed, balanced, minimal, ultra = budgets.get(part_name, (24, 18, 10, 6))
    targets = {
        "detailed": (max(1, detailed - 8), detailed),
        "balanced": (max(1, balanced - 6), balanced),
        "minimal": (max(1, minimal - 4), minimal),
        "ultra_minimal": (max(1, ultra - 3), ultra),
    }
    return {
        name: replace(policy, target_min=targets[name][0], target_max=targets[name][1])
        for name, policy in base.items()
    }


def _person_part_contour_config(base: ContourSimplificationConfig) -> ContourSimplificationConfig:
    # Semantic body-part masks tolerate much stronger contour abstraction than
    # a whole scene. Keep the silhouette angular and low-vertex.
    return replace(
        base,
        detailed_epsilon_ratio=max(base.detailed_epsilon_ratio, 0.018),
        balanced_epsilon_ratio=max(base.balanced_epsilon_ratio, 0.030),
        minimal_epsilon_ratio=max(base.minimal_epsilon_ratio, 0.050),
        ultra_minimal_epsilon_ratio=max(base.ultra_minimal_epsilon_ratio, 0.070),
        epsilon_max_px=max(base.epsilon_max_px, 28.0),
        max_area_change=max(base.max_area_change, 0.18),
        min_iou=min(base.min_iou, 0.80),
        max_centroid_shift_ratio=max(base.max_centroid_shift_ratio, 0.08),
        max_directional_loss=max(base.max_directional_loss, 0.25),
    )


def _person_part_primitive_config(part_name: str, base: PrimitiveFitConfig) -> PrimitiveFitConfig:
    # Person parts are semantically isolated, so favor bold geometry over contour fidelity.
    common = dict(
        min_iou=0.62, max_undercoverage=0.38, max_overcoverage=0.32,
        max_centroid_shift_ratio=0.14, max_directional_under_loss=0.42,
        max_directional_over_loss=0.42, max_boundary_distance=0.18,
        max_protected_boundary_error=0.18, min_contact_retention=0.35,
        minimum_complexity_gain=0.12, adoption_margin=0.0, complexity_reward=0.34,
        # Approved references favor angular color planes. Rounded primitives
        # remain possible only when they are substantially better fits.
        rectangle_complexity=0.78, trapezoid_complexity=0.82,
        ellipse_complexity=2.20, capsule_complexity=2.60,
    )
    if part_name in {"left_arm", "right_arm", "left_leg", "right_leg"}:
        common.update(min_iou=0.55, max_undercoverage=0.45, max_overcoverage=0.40)
    elif part_name == "head":
        common.update(min_iou=0.68, max_undercoverage=0.32, max_overcoverage=0.28)
    return replace(base, **common)


def _quantize_polygon_geometry(
    geometry: PrimitiveGeometry,
    *,
    max_vertices: int = 6,
    max_loops: int | None = None,
) -> PrimitiveGeometry:
    if geometry.kind != "polygon" or not geometry.loops:
        return geometry
    loops: list[NDArray[np.float32]] = []
    for loop in geometry.loops:
        points = np.asarray(loop, dtype=np.float32)
        if len(points) <= max_vertices:
            loops.append(points)
            continue
        contour = points.reshape((-1, 1, 2))
        perimeter = float(cv2.arcLength(contour, True))
        best = points
        # Deterministic ladder: stop at the first low-vertex contour that still
        # describes the same angular mass.
        for ratio in (0.02, 0.03, 0.04, 0.055, 0.075, 0.10, 0.14):
            approx = cv2.approxPolyDP(contour, max(0.75, perimeter * ratio), True)
            candidate = approx.reshape((-1, 2)).astype(np.float32)
            if 3 <= len(candidate) <= max_vertices:
                best = candidate
                break
        if len(best) > max_vertices:
            hull = cv2.convexHull(contour).reshape((-1, 2)).astype(np.float32)
            if len(hull) > max_vertices:
                indices = np.linspace(0, len(hull) - 1, max_vertices, dtype=int)
                hull = hull[indices]
            best = hull if len(hull) >= 3 else points
        loops.append(best)
    if max_loops is not None and len(loops) > max_loops:
        loops.sort(key=lambda loop: abs(cv2.contourArea(loop.astype(np.float32))), reverse=True)
        loops = loops[:max_loops]
    return replace(geometry, loops=tuple(loops))


def _person_part_polygon_budget(part_name: str) -> tuple[int, int]:
    if part_name in {"left_arm", "right_arm", "left_leg", "right_leg"}:
        return (4, 1)
    if part_name == "torso":
        return (5, 1)
    if part_name == "head":
        return (6, 1)
    return (6, 1)


def _quantized_geometry_metrics(
    original: PrimitiveGeometry,
    candidate: PrimitiveGeometry,
    *,
    canvas_shape: tuple[int, int],
) -> tuple[float, float, float]:
    """Return IoU, undercoverage and overcoverage for one geometry candidate."""
    from minimalize_engine.v2.primitive.scoring import rasterize_geometry

    original_mask = np.asarray(
        rasterize_geometry(original, canvas_shape, origin=(0, 0), scale=2),
        dtype=np.bool_,
    )
    candidate_mask = np.asarray(
        rasterize_geometry(candidate, canvas_shape, origin=(0, 0), scale=2),
        dtype=np.bool_,
    )
    original_pixels = max(int(np.count_nonzero(original_mask)), 1)
    intersection = int(np.count_nonzero(original_mask & candidate_mask))
    union_pixels = int(np.count_nonzero(original_mask | candidate_mask))
    iou = intersection / max(union_pixels, 1)
    under = int(np.count_nonzero(original_mask & ~candidate_mask)) / float(original_pixels)
    over = int(np.count_nonzero(candidate_mask & ~original_mask)) / float(original_pixels)
    return (float(iou), float(under), float(over))


def _quantized_geometry_is_safe(
    original: PrimitiveGeometry,
    candidate: PrimitiveGeometry,
    *,
    canvas_shape: tuple[int, int],
    min_iou: float = 0.75,
    max_undercoverage: float = 0.15,
    max_overcoverage: float = 0.20,
) -> bool:
    """Guard low-vertex quantization against destructive silhouette loss."""
    iou, under, over = _quantized_geometry_metrics(
        original,
        candidate,
        canvas_shape=canvas_shape,
    )
    return (
        iou >= float(min_iou)
        and under <= float(max_undercoverage)
        and over <= float(max_overcoverage)
    )


def _polygon_angularity_score(geometry: PrimitiveGeometry) -> float:
    """Reward clear corners and penalize nearly collinear low-vertex contours."""
    strengths: list[float] = []
    for loop in geometry.loops:
        points = np.asarray(loop, dtype=np.float32)
        if len(points) < 3:
            continue
        for index in range(len(points)):
            prev = points[index - 1] - points[index]
            nxt = points[(index + 1) % len(points)] - points[index]
            prev_norm = float(np.linalg.norm(prev))
            next_norm = float(np.linalg.norm(nxt))
            if prev_norm <= 1e-6 or next_norm <= 1e-6:
                continue
            cosine = float(
                np.clip(np.dot(prev, nxt) / (prev_norm * next_norm), -1.0, 1.0)
            )
            interior = float(np.arccos(cosine))
            strength = min(abs(np.pi - interior) / (np.pi / 2.0), 1.0)
            strengths.append(float(strength))
    return float(np.mean(strengths)) if strengths else 0.0


def _quantize_polygon_geometry_candidates(
    geometry: PrimitiveGeometry,
    *,
    max_vertices: int,
    max_loops: int | None,
) -> tuple[PrimitiveGeometry, ...]:
    """Enumerate deterministic low-vertex epsilon candidates without early exit."""
    if geometry.kind != "polygon" or not geometry.loops:
        return ()

    source_loops = [np.asarray(loop, dtype=np.float32) for loop in geometry.loops]
    if max_loops is not None and len(source_loops) > max_loops:
        source_loops.sort(
            key=lambda loop: abs(cv2.contourArea(loop.astype(np.float32))),
            reverse=True,
        )
        source_loops = source_loops[:max_loops]

    ratios = (
        0.004, 0.006, 0.008, 0.010, 0.012, 0.016,
        0.020, 0.030, 0.040, 0.055, 0.075, 0.10, 0.14,
    )
    candidates: list[PrimitiveGeometry] = []
    signatures: set[tuple[bytes, ...]] = set()
    for ratio in ratios:
        loops: list[NDArray[np.float32]] = []
        for points in source_loops:
            if len(points) <= max_vertices:
                candidate = points
            else:
                contour = points.reshape((-1, 1, 2))
                perimeter = float(cv2.arcLength(contour, True))
                approx = cv2.approxPolyDP(
                    contour,
                    max(0.75, perimeter * ratio),
                    True,
                )
                candidate = approx.reshape((-1, 2)).astype(np.float32)
            if not 3 <= len(candidate) <= max_vertices:
                loops = []
                break
            loops.append(candidate)
        if not loops:
            continue
        signature = tuple(np.round(loop, 4).astype(np.float32).tobytes() for loop in loops)
        if signature in signatures:
            continue
        signatures.add(signature)
        candidates.append(replace(geometry, loops=tuple(loops)))
    return tuple(candidates)


def _select_quantized_geometry_candidate(
    original: PrimitiveGeometry,
    candidates: tuple[PrimitiveGeometry, ...],
    *,
    canvas_shape: tuple[int, int],
    min_iou: float = 0.75,
    max_undercoverage: float = 0.15,
    max_overcoverage: float = 0.20,
) -> PrimitiveGeometry:
    """Choose the simplest safe candidate, then the strongest geometric fit."""
    original_vertices = max(sum(len(loop) for loop in original.loops), 1)
    ranked: list[tuple[int, float, int, PrimitiveGeometry]] = []
    for order, candidate in enumerate(candidates):
        iou, under, over = _quantized_geometry_metrics(
            original,
            candidate,
            canvas_shape=canvas_shape,
        )
        if (
            iou < float(min_iou)
            or under > float(max_undercoverage)
            or over > float(max_overcoverage)
        ):
            continue
        vertices = sum(len(loop) for loop in candidate.loops)
        simplicity = max(0.0, 1.0 - (vertices / float(original_vertices)))
        angularity = _polygon_angularity_score(candidate)
        score = (
            iou
            - 1.35 * under
            - 0.55 * over
            + 0.08 * angularity
            + 0.06 * simplicity
        )
        ranked.append((vertices, -float(score), order, candidate))
    if not ranked:
        return original
    ranked.sort(key=lambda item: (item[0], item[1], item[2]))
    return ranked[0][3]


def _quantize_person_part_geometry(
    geometry: PrimitiveGeometry,
    *,
    canvas_shape: tuple[int, int],
    max_vertices: int,
    max_loops: int | None,
) -> PrimitiveGeometry:
    """Use strict low-vertex candidates first, then a bounded safe fallback."""
    candidates = _quantize_polygon_geometry_candidates(
        geometry,
        max_vertices=max_vertices,
        max_loops=max_loops,
    )
    selected = _select_quantized_geometry_candidate(
        geometry,
        candidates,
        canvas_shape=canvas_shape,
    )
    if selected is not geometry:
        return selected

    soft_max_vertices = max(max_vertices, min(12, max_vertices * 3))
    if soft_max_vertices <= max_vertices:
        return geometry
    soft_candidates = _quantize_polygon_geometry_candidates(
        geometry,
        max_vertices=soft_max_vertices,
        max_loops=max_loops,
    )
    return _select_quantized_geometry_candidate(
        geometry,
        soft_candidates,
        canvas_shape=canvas_shape,
        max_undercoverage=0.08,
    )


def _quantize_person_part_polygons(
    result: PresetPipelineResult,
    *,
    max_vertices: int = 6,
    max_loops: int | None = None,
) -> PresetPipelineResult:
    canvas_shape = (result.scene.height, result.scene.width)
    shapes: list[SceneShape] = []
    for shape in result.scene.shapes:
        if not shape.visible or shape.geometry.kind != "polygon":
            shapes.append(shape)
            continue
        selected = _quantize_person_part_geometry(
            shape.geometry,
            canvas_shape=canvas_shape,
            max_vertices=max_vertices,
            max_loops=max_loops,
        )
        shapes.append(replace(shape, geometry=selected))
    return replace(
        result,
        scene=replace(result.scene, shapes=tuple(shapes), facet_overlays=()),
    )


def _semantic_part_paint_coverage(
    result: PresetPipelineResult,
    part_mask: NDArray[np.bool_],
) -> float:
    """Return visible non-background paint retained inside one semantic part."""
    target = np.asarray(part_mask, dtype=bool)
    target_pixels = int(np.count_nonzero(target))
    if target_pixels <= 0:
        return 0.0
    if target.shape != (result.scene.height, result.scene.width):
        raise ValueError("part mask shape must match scene dimensions")

    rendered = _render_scene_primitives(result.scene)
    painted = np.any(rendered != 255, axis=2)
    return float(np.count_nonzero(painted & target) / target_pixels)


def _semantic_part_coverage_is_safe(
    baseline_coverage: float,
    candidate_coverage: float,
    *,
    min_retention: float = 0.72,
    max_absolute_loss: float = 0.14,
    zero_floor: float = 0.01,
    meaningful_baseline: float = 0.08,
) -> bool:
    """Reject only destructive semantic-paint loss, not ordinary simplification."""
    baseline = max(0.0, min(1.0, float(baseline_coverage)))
    candidate = max(0.0, min(1.0, float(candidate_coverage)))
    if candidate >= baseline:
        return True
    if baseline >= meaningful_baseline and candidate <= zero_floor:
        return False
    loss = baseline - candidate
    retention = candidate / max(baseline, 1e-9)
    return not (
        loss > float(max_absolute_loss)
        and retention < float(min_retention)
    )


def _guard_semantic_part_coverage(
    baseline: PresetPipelineResult,
    candidate: PresetPipelineResult,
    part_mask: NDArray[np.bool_],
) -> PresetPipelineResult:
    """Rollback a semantic refinement stage if it erases too much of the part."""
    before = _semantic_part_paint_coverage(baseline, part_mask)
    after = _semantic_part_paint_coverage(candidate, part_mask)
    if _semantic_part_coverage_is_safe(before, after):
        return candidate
    return baseline


def _semantic_plane_clusters(
    masks: list[NDArray[np.bool_]],
    colors: list[NDArray[np.float32]],
    *,
    color_distance: float = 48.0,
    adjacency_radius: int = 2,
) -> tuple[tuple[int, ...], ...]:
    """Group spatially touching near-color planes without merging distant accents."""
    if len(masks) < 2:
        return ()
    radius = max(int(adjacency_radius), 1)
    kernel = np.ones((2 * radius + 1, 2 * radius + 1), dtype=np.uint8)
    expanded = [
        cv2.dilate(mask.astype(np.uint8), kernel, iterations=1) > 0
        for mask in masks
    ]
    parents = list(range(len(masks)))

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(a: int, b: int) -> None:
        ra, rb = root(a), root(b)
        if ra != rb:
            parents[max(ra, rb)] = min(ra, rb)

    for i in range(len(masks)):
        if not np.any(masks[i]):
            continue
        for j in range(i + 1, len(masks)):
            if not np.any(masks[j]):
                continue
            if float(np.linalg.norm(colors[i] - colors[j])) > float(color_distance):
                continue
            if np.any(expanded[i] & masks[j]) or np.any(expanded[j] & masks[i]):
                union(i, j)

    grouped: dict[int, list[int]] = {}
    for index in range(len(masks)):
        grouped.setdefault(root(index), []).append(index)
    clusters = [
        tuple(indices)
        for indices in grouped.values()
        if len(indices) >= 2
    ]
    clusters.sort(key=lambda indices: (-sum(int(np.count_nonzero(masks[i])) for i in indices), indices))
    return tuple(clusters)


def _fit_semantic_plane_polygon(
    cluster_mask: NDArray[np.bool_],
    part_mask: NDArray[np.bool_],
    *,
    max_vertices: int,
) -> NDArray[np.float32] | None:
    """Refit one cluster as a bold low-vertex polygon, guarded by semantic support."""
    target = np.asarray(cluster_mask, dtype=bool) & np.asarray(part_mask, dtype=bool)
    target_pixels = int(np.count_nonzero(target))
    if target_pixels < 8:
        return None

    bridge = cv2.morphologyEx(
        target.astype(np.uint8),
        cv2.MORPH_CLOSE,
        np.ones((3, 3), dtype=np.uint8),
    )
    bridge &= part_mask.astype(np.uint8)
    contours, _ = cv2.findContours(bridge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    if float(cv2.contourArea(contour)) < 4.0:
        return None

    perimeter = max(float(cv2.arcLength(contour, True)), 1.0)
    candidates: list[NDArray[np.float32]] = []
    for ratio in (0.010, 0.016, 0.024, 0.034, 0.048, 0.066, 0.090, 0.120, 0.160):
        approx = cv2.approxPolyDP(contour, max(0.65, perimeter * ratio), True)
        polygon = approx.reshape((-1, 2)).astype(np.float32)
        if 3 <= len(polygon) <= max_vertices:
            candidates.append(polygon)
    if max_vertices >= 4:
        rectangle = cv2.boxPoints(cv2.minAreaRect(contour)).astype(np.float32)
        candidates.append(rectangle)
    if not candidates:
        return None

    best: tuple[float, NDArray[np.float32]] | None = None
    for polygon in candidates:
        candidate = np.zeros(target.shape, dtype=np.uint8)
        cv2.fillPoly(candidate, [np.rint(polygon).astype(np.int32)], 1)
        candidate_bool = candidate > 0
        candidate_pixels = int(np.count_nonzero(candidate_bool))
        if candidate_pixels == 0:
            continue
        intersection = int(np.count_nonzero(candidate_bool & target))
        union_pixels = int(np.count_nonzero(candidate_bool | target))
        iou = intersection / max(union_pixels, 1)
        under = int(np.count_nonzero(target & ~candidate_bool)) / target_pixels
        over = int(np.count_nonzero(candidate_bool & ~target)) / target_pixels
        outside = int(np.count_nonzero(candidate_bool & ~part_mask)) / candidate_pixels
        if iou < 0.68 or under > 0.30 or over > 0.36 or outside > 0.12:
            continue
        score = iou - 0.08 * over - 0.16 * outside + 0.008 * (max_vertices - len(polygon))
        if best is None or score > best[0]:
            best = (score, polygon)
    return None if best is None else best[1]


def _refit_semantic_planes(
    result: PresetPipelineResult,
    *,
    part_name: str,
    part_mask: NDArray[np.bool_],
    color_distance: float = 48.0,
    adjacency_radius: int = 2,
) -> PresetPipelineResult:
    """Rebuild adjacent near-color fragments as one semantic plane."""
    from minimalize_engine.v2.primitive.scoring import rasterize_geometry

    shapes = list(result.scene.shapes)
    visible_indices = [index for index, shape in enumerate(shapes) if shape.visible]
    if len(visible_indices) < 2:
        return result
    palette_rgb = {
        entry.palette_id: np.asarray(entry.rgb, dtype=np.float32)
        for entry in result.scene.palette
    }
    masks: list[NDArray[np.bool_]] = []
    colors: list[NDArray[np.float32]] = []
    for index in visible_indices:
        shape = shapes[index]
        mask = rasterize_geometry(shape.geometry, part_mask.shape, origin=(0, 0), scale=2)
        masks.append(np.asarray(mask, dtype=bool) & part_mask)
        colors.append(palette_rgb[shape.palette_id])

    clusters = _semantic_plane_clusters(
        masks,
        colors,
        color_distance=color_distance,
        adjacency_radius=adjacency_radius,
    )
    if not clusters:
        return result
    max_vertices, _ = _person_part_polygon_budget(part_name)
    for cluster in clusters:
        active = [local for local in cluster if shapes[visible_indices[local]].visible]
        if len(active) < 2:
            continue
        union_mask = np.zeros(part_mask.shape, dtype=bool)
        for local in active:
            union_mask |= masks[local]
        polygon = _fit_semantic_plane_polygon(
            union_mask,
            part_mask,
            max_vertices=max_vertices,
        )
        if polygon is None:
            continue
        anchor_local = max(active, key=lambda local: int(np.count_nonzero(masks[local])))
        anchor_index = visible_indices[anchor_local]
        palette_support: dict[int, int] = {}
        for local in active:
            shape = shapes[visible_indices[local]]
            palette_support[shape.palette_id] = (
                palette_support.get(shape.palette_id, 0)
                + int(np.count_nonzero(masks[local]))
            )
        dominant_palette = max(palette_support, key=lambda palette_id: (palette_support[palette_id], -palette_id))
        shapes[anchor_index] = replace(
            shapes[anchor_index],
            geometry=PrimitiveGeometry(kind="polygon", loops=(polygon,)),
            palette_id=dominant_palette,
        )
        for local in active:
            index = visible_indices[local]
            if index != anchor_index:
                shapes[index] = replace(shapes[index], visible=False)
    return replace(result, scene=replace(result.scene, shapes=tuple(shapes), facet_overlays=()))


def _consolidate_semantic_planes(
    result: PresetPipelineResult,
    *,
    color_distance: float = 54.0,
) -> PresetPipelineResult:
    """Hide smaller near-color planes when a larger plane can carry the same visual role."""
    shapes = list(result.scene.shapes)
    if len(shapes) < 2:
        return result
    palette_rgb = {entry.palette_id: np.asarray(entry.rgb, dtype=np.float32) for entry in result.scene.palette}

    def area(shape: SceneShape) -> float:
        geometry = shape.geometry
        if geometry.kind == "polygon":
            return float(sum(abs(cv2.contourArea(loop.astype(np.float32))) for loop in geometry.loops))
        if geometry.points is not None:
            return float(abs(cv2.contourArea(geometry.points.astype(np.float32))))
        if geometry.kind == "ellipse" and geometry.axes is not None:
            return float(np.pi * geometry.axes[0] * geometry.axes[1])
        if geometry.kind == "capsule" and geometry.radius is not None and geometry.segment_start is not None and geometry.segment_end is not None:
            length = float(np.linalg.norm(np.asarray(geometry.segment_end) - np.asarray(geometry.segment_start)))
            return float(2.0 * geometry.radius * length + np.pi * geometry.radius ** 2)
        return 0.0

    visible = [i for i, shape in enumerate(shapes) if shape.visible]
    visible.sort(key=lambda i: area(shapes[i]), reverse=True)
    if not visible:
        return result
    largest_area = max(area(shapes[i]) for i in visible)
    # Preserve one small, high-contrast accent plane. Approved references often
    # retain a ribbon/trim/hair accent even when neighboring near-colors merge.
    accent_index: int | None = None
    if largest_area > 0.0:
        base_rgb = palette_rgb.get(shapes[visible[0]].palette_id)
        candidates: list[tuple[float, int]] = []
        if base_rgb is not None:
            for index in visible[1:]:
                candidate_area = area(shapes[index])
                rgb = palette_rgb.get(shapes[index].palette_id)
                if rgb is None or candidate_area < largest_area * 0.05 or candidate_area > largest_area * 0.42:
                    continue
                contrast = float(np.linalg.norm(rgb - base_rgb))
                if contrast >= color_distance * 1.25:
                    candidates.append((contrast, index))
        if candidates:
            accent_index = max(candidates)[1]

    kept: list[int] = []
    for index in visible:
        shape = shapes[index]
        rgb = palette_rgb.get(shape.palette_id)
        redundant = False
        if rgb is not None:
            for prior in kept:
                prior_rgb = palette_rgb.get(shapes[prior].palette_id)
                if prior_rgb is None:
                    continue
                if float(np.linalg.norm(rgb - prior_rgb)) <= color_distance and area(shape) <= area(shapes[prior]) * 0.42:
                    redundant = True
                    break
        if redundant and index != accent_index:
            shapes[index] = replace(shape, visible=False)
        else:
            kept.append(index)
    return replace(result, scene=replace(result.scene, shapes=tuple(shapes), facet_overlays=()))


def _semantic_part_shape_limit(part_name: str, preset: str) -> int:
    limits = {
        "head": {"detailed": 10, "balanced": 7, "minimal": 5, "ultra_minimal": 3},
        "torso": {"detailed": 8, "balanced": 6, "minimal": 3, "ultra_minimal": 2},
        "left_arm": {"detailed": 6, "balanced": 4, "minimal": 3, "ultra_minimal": 2},
        "right_arm": {"detailed": 6, "balanced": 4, "minimal": 3, "ultra_minimal": 2},
        "left_leg": {"detailed": 6, "balanced": 4, "minimal": 3, "ultra_minimal": 2},
        "right_leg": {"detailed": 6, "balanced": 4, "minimal": 3, "ultra_minimal": 2},
    }
    return limits.get(part_name, {}).get(preset, 6)


def _semantic_budget_keep_ids(
    scored: list[tuple[int, int, SceneShape]],
    palette_rgb: Mapping[int, NDArray[np.float32]],
    *,
    part_name: str,
    limit: int,
) -> set[int]:
    ranked = sorted(scored, reverse=True)
    if len(ranked) <= limit:
        return {shape.region_id for _, _, shape in ranked}
    if part_name != "torso" or limit < 2:
        return {
            shape.region_id
            for _, _, shape in ranked[:limit]
        }

    largest_support, _, largest_shape = ranked[0]
    base_rgb = palette_rgb.get(largest_shape.palette_id)
    accent: tuple[float, int, int, SceneShape] | None = None
    if base_rgb is not None and largest_support > 0:
        for support, neg_order, shape in ranked[1:]:
            rgb = palette_rgb.get(shape.palette_id)
            if rgb is None:
                continue
            ratio = support / float(largest_support)
            if ratio < 0.05 or ratio > 0.55:
                continue
            contrast = float(np.linalg.norm(rgb - base_rgb))
            if contrast < 70.0:
                continue
            candidate = (contrast, support, neg_order, shape)
            if accent is None or candidate[:3] > accent[:3]:
                accent = candidate

    selected: list[SceneShape] = [largest_shape]
    if accent is not None:
        selected.append(accent[3])
    for _, _, shape in ranked[1:]:
        if len(selected) >= limit:
            break
        if any(item.region_id == shape.region_id for item in selected):
            continue
        selected.append(shape)
    return {shape.region_id for shape in selected[:limit]}


def _safe_semantic_two_plane_keep_ids(
    scored: list[tuple[int, int, SceneShape]],
    palette_rgb: Mapping[int, NDArray[np.float32]],
    part_mask: NDArray[np.bool_],
    *,
    min_coverage: float = 0.94,
    accent_support_ratio: float = 0.05,
    accent_contrast: float = 70.0,
) -> set[int] | None:
    """Return two semantic planes only when silhouette and color accents survive."""
    if len(scored) <= 2:
        return {shape.region_id for _, _, shape in scored}

    from itertools import combinations
    from minimalize_engine.v2.primitive.scoring import rasterize_geometry

    items: list[tuple[SceneShape, NDArray[np.bool_], int, NDArray[np.float32]]] = []
    full = np.zeros(part_mask.shape, dtype=bool)
    for support, _, shape in scored:
        mask = np.asarray(
            rasterize_geometry(
                shape.geometry,
                part_mask.shape,
                origin=(0, 0),
                scale=2,
            ),
            dtype=bool,
        ) & part_mask
        if not np.any(mask):
            continue
        rgb = palette_rgb.get(shape.palette_id)
        if rgb is None:
            continue
        items.append((shape, mask, support, rgb))
        full |= mask
    if len(items) <= 2:
        return {item[0].region_id for item in items}

    full_pixels = max(int(np.count_nonzero(full)), 1)
    best: tuple[float, float, set[int]] | None = None
    for left, right in combinations(range(len(items)), 2):
        kept = (items[left], items[right])
        pair_mask = kept[0][1] | kept[1][1]
        coverage = int(np.count_nonzero(pair_mask & full)) / full_pixels
        if coverage < min_coverage:
            continue

        kept_colors = (kept[0][3], kept[1][3])
        loses_accent = False
        for index, item in enumerate(items):
            if index in (left, right):
                continue
            support_ratio = item[2] / float(full_pixels)
            contrast = min(
                float(np.linalg.norm(item[3] - color))
                for color in kept_colors
            )
            if (
                support_ratio >= accent_support_ratio
                and contrast >= accent_contrast
            ):
                loses_accent = True
                break
        if loses_accent:
            continue

        pair_contrast = float(np.linalg.norm(kept[0][3] - kept[1][3]))
        keep_ids = {kept[0][0].region_id, kept[1][0].region_id}
        candidate = (coverage, pair_contrast, keep_ids)
        if best is None or candidate[:2] > best[:2]:
            best = candidate
    return None if best is None else best[2]


def _reduce_safe_head_to_two_planes(
    result: PresetPipelineResult,
    part_mask: NDArray[np.bool_],
) -> PresetPipelineResult:
    """Reduce a finalized minimal head to two planes only when detail is redundant."""
    if result.preset != "minimal":
        return result

    from minimalize_engine.v2.primitive.scoring import rasterize_geometry

    scored: list[tuple[int, int, SceneShape]] = []
    for order, shape in enumerate(result.scene.shapes):
        if not shape.visible:
            continue
        geometry_mask = rasterize_geometry(
            shape.geometry,
            part_mask.shape,
            origin=(0, 0),
            scale=2,
        )
        support = int(np.count_nonzero(geometry_mask & part_mask))
        if support:
            scored.append((support, -order, shape))
    if len(scored) <= 2:
        return result

    palette_rgb = {
        entry.palette_id: np.asarray(entry.rgb, dtype=np.float32)
        for entry in result.scene.palette
    }
    keep_ids = _safe_semantic_two_plane_keep_ids(
        scored,
        palette_rgb,
        part_mask,
        min_coverage=0.94,
        accent_support_ratio=0.04,
        accent_contrast=70.0,
    )
    if keep_ids is None:
        return result

    shapes = tuple(
        replace(shape, visible=shape.visible and shape.region_id in keep_ids)
        for shape in result.scene.shapes
    )
    return replace(
        result,
        scene=replace(result.scene, shapes=shapes, facet_overlays=()),
    )


def _apply_semantic_shape_budget(
    result: PresetPipelineResult,
    *,
    part_name: str,
    part_mask: NDArray[np.bool_],
) -> PresetPipelineResult:
    """Keep only the dominant painted color planes inside a semantic body part."""
    limit = _semantic_part_shape_limit(part_name, result.preset)
    from minimalize_engine.v2.primitive.scoring import rasterize_geometry

    scored: list[tuple[int, int, SceneShape]] = []
    for order, shape in enumerate(result.scene.shapes):
        if not shape.visible:
            continue
        geometry_mask = rasterize_geometry(
            shape.geometry, part_mask.shape, origin=(0, 0), scale=2
        )
        support = int(np.count_nonzero(geometry_mask & part_mask))
        if support:
            scored.append((support, -order, shape))
    palette_rgb = {
        entry.palette_id: np.asarray(entry.rgb, dtype=np.float32)
        for entry in result.scene.palette
    }
    limb_names = {"left_arm", "right_arm", "left_leg", "right_leg"}
    limb_keep_ids: set[int] | None = None
    if (
        result.preset == "minimal"
        and part_name in limb_names
        and len(scored) > 2
    ):
        limb_keep_ids = _safe_semantic_two_plane_keep_ids(
            scored,
            palette_rgb,
            part_mask,
        )
    if limb_keep_ids is not None:
        keep_ids = limb_keep_ids
    else:
        if len(scored) <= limit:
            return result
        keep_ids = _semantic_budget_keep_ids(
            scored,
            palette_rgb,
            part_name=part_name,
            limit=limit,
        )
    shapes = tuple(
        replace(shape, visible=shape.visible and shape.region_id in keep_ids)
        for shape in result.scene.shapes
    )
    return replace(
        result,
        scene=replace(result.scene, shapes=shapes, facet_overlays=()),
    )


def _semantic_dead_plane_ids(
    shapes: Sequence[SceneShape],
    part_mask: NDArray[np.bool_],
    *,
    max_support_pixels: int = 4,
    max_support_ratio: float = 0.002,
) -> set[int]:
    """Find visible planes with effectively no support inside their semantic part."""
    from minimalize_engine.v2.primitive.scoring import rasterize_geometry

    supported: list[tuple[int, int]] = []
    part_pixels = max(int(np.count_nonzero(part_mask)), 1)
    for index, shape in enumerate(shapes):
        if not shape.visible:
            continue
        mask = np.asarray(
            rasterize_geometry(
                shape.geometry,
                part_mask.shape,
                origin=(0, 0),
                scale=2,
            ),
            dtype=bool,
        )
        support = int(np.count_nonzero(mask & part_mask))
        supported.append((index, support))
    if len(supported) <= 1:
        return set()

    anchor_index, anchor_support = max(
        supported,
        key=lambda item: (item[1], -item[0]),
    )
    if anchor_support <= 0:
        return set()

    dead: set[int] = set()
    for index, support in supported:
        if index == anchor_index:
            continue
        ratio = support / float(part_pixels)
        if support <= max_support_pixels and ratio <= max_support_ratio:
            dead.add(shapes[index].region_id)
    return dead


def _remove_semantic_dead_planes(
    result: PresetPipelineResult,
    part_mask: NDArray[np.bool_],
) -> PresetPipelineResult:
    """Hide final planes that carry no meaningful semantic pixels."""
    dead_ids = _semantic_dead_plane_ids(result.scene.shapes, part_mask)
    if not dead_ids:
        return result
    shapes = tuple(
        replace(
            shape,
            visible=shape.visible and shape.region_id not in dead_ids,
        )
        for shape in result.scene.shapes
    )
    return replace(
        result,
        scene=replace(result.scene, shapes=shapes, facet_overlays=()),
    )


def _render_scene_primitives(
    scene: SceneModel,
    *,
    hidden_ids: set[int] | None = None,
) -> NDArray[np.uint8]:
    """Render primitive scene shapes without facets for exact visibility checks."""
    from minimalize_engine.v2.primitive.scoring import rasterize_geometry

    hidden = hidden_ids or set()
    entries = {entry.palette_id: entry for entry in scene.palette}
    canvas = np.full((scene.height, scene.width, 3), 255, dtype=np.uint8)
    for shape in sorted(scene.shapes, key=lambda item: item.region_id):
        if not shape.visible or shape.region_id in hidden:
            continue
        mask = rasterize_geometry(
            shape.geometry,
            (scene.height, scene.width),
            origin=(0, 0),
            scale=2,
        )
        canvas[mask] = entries[shape.palette_id].rgb
    return canvas


def _render_dead_plane_ids(scene: SceneModel) -> set[int]:
    """Find planes that do not contribute a single pixel to the final render."""
    hidden_ids: set[int] = set()
    while True:
        visible_ids = [
            shape.region_id
            for shape in scene.shapes
            if shape.visible and shape.region_id not in hidden_ids
        ]
        if len(visible_ids) <= 1:
            break

        baseline = _render_scene_primitives(scene, hidden_ids=hidden_ids)
        removable: int | None = None
        for region_id in visible_ids:
            candidate = _render_scene_primitives(
                scene,
                hidden_ids=hidden_ids | {region_id},
            )
            if np.array_equal(candidate, baseline):
                removable = region_id
                break
        if removable is None:
            break
        hidden_ids.add(removable)
    return hidden_ids


def _remove_render_dead_planes(
    result: PresetPipelineResult,
) -> PresetPipelineResult:
    """Hide planes whose removal leaves the final primitive render unchanged."""
    if result.preset != "minimal":
        return result

    hidden_ids = _render_dead_plane_ids(result.scene)
    if not hidden_ids:
        return result
    cleaned = tuple(
        replace(
            shape,
            visible=shape.visible and shape.region_id not in hidden_ids,
        )
        for shape in result.scene.shapes
    )
    return replace(
        result,
        scene=replace(result.scene, shapes=cleaned, facet_overlays=()),
    )


def _render_negligible_plane_ids(
    scene: SceneModel,
    *,
    max_changed_pixels: int = 4,
    max_changed_ratio: float = 0.005,
) -> set[int]:
    """Find planes whose visible contribution is only a few output pixels."""
    hidden_ids: set[int] = set()
    while True:
        visible_ids = [
            shape.region_id
            for shape in scene.shapes
            if shape.visible and shape.region_id not in hidden_ids
        ]
        if len(visible_ids) <= 1:
            break

        baseline = _render_scene_primitives(scene, hidden_ids=hidden_ids)
        foreground_pixels = max(
            int(np.count_nonzero(np.any(baseline != 255, axis=2))),
            1,
        )
        removable: int | None = None
        for region_id in visible_ids:
            candidate = _render_scene_primitives(
                scene,
                hidden_ids=hidden_ids | {region_id},
            )
            changed_pixels = int(
                np.count_nonzero(np.any(candidate != baseline, axis=2))
            )
            changed_ratio = changed_pixels / float(foreground_pixels)
            if (
                changed_pixels <= max_changed_pixels
                and changed_ratio <= max_changed_ratio
            ):
                removable = region_id
                break
        if removable is None:
            break
        hidden_ids.add(removable)
    return hidden_ids


def _remove_render_negligible_planes(
    result: PresetPipelineResult,
) -> PresetPipelineResult:
    """Hide final planes whose rendered contribution is only micro-pixel noise."""
    if result.preset != "minimal":
        return result

    hidden_ids = _render_negligible_plane_ids(result.scene)
    if not hidden_ids:
        return result
    cleaned = tuple(
        replace(
            shape,
            visible=shape.visible and shape.region_id not in hidden_ids,
        )
        for shape in result.scene.shapes
    )
    return replace(
        result,
        scene=replace(result.scene, shapes=cleaned, facet_overlays=()),
    )


def _reduce_safe_angular_vertices(
    result: PresetPipelineResult,
    *,
    part_name: str,
    min_iou: float = 0.95,
    max_under: float = 0.04,
    max_over: float = 0.05,
    max_render_change: float = 0.05,
) -> PresetPipelineResult:
    """Drop one redundant polygon corner when the final angular mass is preserved."""
    if result.preset != "minimal" or part_name not in {"head", "torso"}:
        return result

    from minimalize_engine.v2.primitive.scoring import rasterize_geometry

    target_vertices = 5 if part_name == "head" else 4
    scene = result.scene
    baseline = _render_scene_primitives(scene)
    foreground_pixels = max(
        int(np.count_nonzero(np.any(baseline != 255, axis=2))),
        1,
    )
    shapes = list(scene.shapes)
    changed = False

    for shape_index, shape in enumerate(shapes):
        if (
            not shape.visible
            or shape.geometry.kind != "polygon"
            or len(shape.geometry.loops) != 1
        ):
            continue
        points = np.asarray(shape.geometry.loops[0], dtype=np.float32)
        if len(points) != target_vertices + 1:
            continue

        target_mask = np.asarray(
            rasterize_geometry(
                shape.geometry,
                (scene.height, scene.width),
                origin=(0, 0),
                scale=2,
            ),
            dtype=bool,
        )
        target_pixels = max(int(np.count_nonzero(target_mask)), 1)
        best: tuple[float, PrimitiveGeometry] | None = None

        for remove_index in range(len(points)):
            candidate_points = np.delete(points, remove_index, axis=0)
            candidate_geometry = PrimitiveGeometry(
                kind="polygon",
                loops=(candidate_points,),
            )
            candidate_mask = np.asarray(
                rasterize_geometry(
                    candidate_geometry,
                    (scene.height, scene.width),
                    origin=(0, 0),
                    scale=2,
                ),
                dtype=bool,
            )
            intersection = int(np.count_nonzero(target_mask & candidate_mask))
            union_pixels = int(np.count_nonzero(target_mask | candidate_mask))
            iou = intersection / max(union_pixels, 1)
            under = (
                int(np.count_nonzero(target_mask & ~candidate_mask))
                / target_pixels
            )
            over = (
                int(np.count_nonzero(candidate_mask & ~target_mask))
                / target_pixels
            )
            if iou < min_iou or under > max_under or over > max_over:
                continue

            trial_shapes = tuple(
                replace(item, geometry=candidate_geometry)
                if item.region_id == shape.region_id
                else item
                for item in shapes
            )
            trial_scene = replace(
                scene,
                shapes=trial_shapes,
                facet_overlays=(),
            )
            trial_render = _render_scene_primitives(trial_scene)
            render_change = (
                int(
                    np.count_nonzero(
                        np.any(trial_render != baseline, axis=2)
                    )
                )
                / foreground_pixels
            )
            if render_change > max_render_change:
                continue

            score = (
                iou
                - 0.55 * render_change
                - 0.08 * over
                - 0.06 * under
            )
            if best is None or score > best[0]:
                best = (score, candidate_geometry)

        if best is None:
            continue

        shapes[shape_index] = replace(shape, geometry=best[1])
        scene = replace(
            scene,
            shapes=tuple(shapes),
            facet_overlays=(),
        )
        baseline = _render_scene_primitives(scene)
        foreground_pixels = max(
            int(np.count_nonzero(np.any(baseline != 255, axis=2))),
            1,
        )
        changed = True

    if not changed:
        return result
    return replace(result, scene=scene)


def _minimalize_person_parts(
    bundle: ImageBundle,
    partition: PersonPartPartition,
    *,
    presets: tuple[str, ...],
    config: PipelineConfig,
) -> dict[str, Mapping[str, PresetPipelineResult]]:
    results: dict[str, Mapping[str, PresetPipelineResult]] = {}
    source = bundle.analysis_rgb
    for name, mask in partition.part_masks.items():
        if not mask.any():
            continue
        isolated = np.full_like(source, 255)
        isolated[mask] = source[mask]
        probability = mask.astype(np.float32)
        confidence = np.ones(mask.shape, dtype=np.float32)
        part_guidance = AnalysisGuidance(
            subject_prob=probability,
            subject_confidence=confidence,
            alpha=probability,
            subject_provider="minimalizer",
            subject_model=f"person-part:{name}",
        )
        part_config = replace(
            config,
            # A second, alpha-bounded pass is intentional for hierarchical
            # person-part processing: scene shading is flattened first, then
            # each isolated semantic part gets one local consolidation pass.
            shading_flatten=(
                config.shading_flatten
                if config.shading_flatten.hierarchical_parts
                else replace(config.shading_flatten, enabled=False)
            ),
            layered_person=replace(config.layered_person, enabled=False),
            cut_policies=_person_part_cut_policies(name),
            contour=_person_part_contour_config(config.contour),
            primitive=(
                _person_part_primitive_config(name, config.primitive)
                if config.layered_person.coarse_part_primitives
                else config.primitive
            ),
        )
        part_result = _minimalize_v2_impl(
            isolated,
            presets=presets,
            config=part_config,
            characteristic=None,
            observer=None,
            guidance=part_guidance,
        )
        if config.layered_person.semantic_shape_budget:
            polygon_vertices, polygon_loops = _person_part_polygon_budget(name)

            def finalize_semantic_part(
                preset_result: PresetPipelineResult,
            ) -> PresetPipelineResult:
                def guarded(
                    baseline: PresetPipelineResult,
                    candidate: PresetPipelineResult,
                ) -> PresetPipelineResult:
                    if not config.layered_person.semantic_coverage_guard:
                        return candidate
                    return _guard_semantic_part_coverage(
                        baseline,
                        candidate,
                        mask,
                    )

                refined = preset_result
                candidate = _apply_semantic_shape_budget(
                    refined,
                    part_name=name,
                    part_mask=mask,
                )
                refined = guarded(refined, candidate)

                candidate = _quantize_person_part_polygons(
                    refined,
                    max_vertices=polygon_vertices,
                    max_loops=polygon_loops,
                )
                refined = guarded(refined, candidate)

                if config.layered_person.semantic_plane_refit:
                    candidate = _refit_semantic_planes(
                        refined,
                        part_name=name,
                        part_mask=mask,
                    )
                    refined = guarded(refined, candidate)

                candidate = _consolidate_semantic_planes(refined)
                refined = guarded(refined, candidate)

                if name == "head":
                    candidate = _reduce_safe_head_to_two_planes(
                        refined,
                        mask,
                    )
                    refined = guarded(refined, candidate)

                candidate = _remove_semantic_dead_planes(
                    refined,
                    mask,
                )
                refined = guarded(refined, candidate)

                candidate = _reduce_safe_angular_vertices(
                    refined,
                    part_name=name,
                )
                refined = guarded(refined, candidate)

                candidate = _remove_render_dead_planes(refined)
                refined = guarded(refined, candidate)

                candidate = _remove_render_negligible_planes(refined)
                return guarded(refined, candidate)

            results[name] = {
                preset: finalize_semantic_part(preset_result)
                for preset, preset_result in part_result.presets.items()
            }
        else:
            results[name] = part_result.presets
    return results


def _minimalize_v2_impl(
    source_rgb: NDArray[np.uint8],
    *,
    presets: tuple[str, ...],
    config: PipelineConfig,
    characteristic: CharacteristicContext | None,
    observer: TimingObserver | None,
    guidance: AnalysisGuidance | None = None,
) -> MinimalizerV2Result:
    active_presets = _validate_presets(presets)
    if guidance is not None:
        guidance.validate_source_shape(source_rgb.shape[:2])
    bundle = _timed(
        observer,
        "preprocessing",
        lambda: build_image_bundle(
            source_rgb,
            subject_prob=guidance.subject_prob if guidance is not None else None,
            subject_confidence=guidance.subject_confidence if guidance is not None else None,
            alpha=guidance.alpha if guidance is not None else None,
            analysis_max_side=config.analysis_max_side,
            shading_flatten=config.shading_flatten,
        ),
    )
    segmentation = _timed(
        observer,
        "oversegmentation",
        lambda: oversegment(
            bundle,
            iterations=config.region_merge.slic_iterations,
            edge_coverage_threshold=config.region_merge.edge_coverage_threshold,
            retry_scale=config.region_merge.retry_scale,
            max_retry_target_factor=config.region_merge.max_retry_target_factor,
            provider=config.region_merge.slic_provider,
        ),
    )
    def project_guidance():
        active = guidance or AnalysisGuidance()
        return (
            semantic_regions_from_guide(
                bundle,
                segmentation.labels,
                active.semantic,
            ),
            structural_regions_from_guide(
                bundle,
                segmentation.labels,
                active.structural,
            ),
            line_support_from_guide(
                bundle,
                active.line,
            ),
        )

    semantic_regions, structural_regions, line_support = _timed(
        observer,
        "analysis_guidance",
        project_guidance,
    )
    person_parts = None
    if config.layered_person.enabled:
        if guidance is None:
            raise ValueError("layered person mode requires analysis guidance")
        person_parts = _timed(
            observer,
            "person_part_partition",
            lambda: resize_person_part_partition(
                build_person_part_partition(
                    guidance,
                    config=config.layered_person.parts,
                ),
                bundle.analysis_rgb.shape[:2],
            ),
        )
    annotations = _timed(
        observer,
        "initial_annotations",
        lambda: annotate_initial_regions(
            bundle,
            segmentation.labels,
            characteristic=characteristic,
            semantic=semantic_regions,
            structural=structural_regions,
        ),
    )
    graph = _timed(
        observer,
        "initial_rag",
        lambda: build_region_graph(
            bundle,
            segmentation.labels,
            annotations=annotations,
            line_support=line_support,
            gradient_bins=config.region_merge.gradient_bins,
        ),
    )
    merge_result = _timed(
        observer,
        "region_merge",
        lambda: run_region_merge_from_graph(
            graph,
            config=config.region_merge,
        ),
    )
    cut_family = _timed(
        observer,
        "hierarchy_cut_family",
        lambda: build_cut_family(merge_result, policies=config.cut_policies),
    )
    preset_results: dict[str, PresetPipelineResult] = {}
    for preset in active_presets:
        cut = _cut_for_preset(cut_family, preset)
        preset_results[preset] = _run_preset_pipeline(
            bundle,
            merge_result,
            cut,
            characteristic=characteristic,
            config=config,
            observer=observer,
        )
    person_part_presets: dict[str, Mapping[str, PresetPipelineResult]] = {}
    if (
        person_parts is not None
        and config.layered_person.independent_parts
    ):
        person_part_presets = _timed(
            observer,
            "person_part_pipelines",
            lambda: _minimalize_person_parts(
                bundle,
                person_parts,
                presets=active_presets,
                config=config,
            ),
        )
    return MinimalizerV2Result(
        bundle=bundle,
        characteristic=characteristic,
        region_merge=merge_result,
        cut_family=cut_family,
        presets=preset_results,
        person_parts=person_parts,
        person_part_presets=person_part_presets,
    )


def _shading_result_complexity(
    result: MinimalizerV2Result,
) -> tuple[int, int]:
    polygon_vertices = 0
    visible_shapes = 0
    for preset_result in result.presets.values():
        shapes, vertices = _semantic_scene_complexity(preset_result)
        visible_shapes += shapes
        polygon_vertices += vertices
    return visible_shapes, polygon_vertices


def _shading_part_complexity(
    result: MinimalizerV2Result,
) -> tuple[int, int]:
    polygon_vertices = 0
    visible_shapes = 0
    for presets in result.person_part_presets.values():
        for preset_result in presets.values():
            shapes, vertices = _semantic_scene_complexity(preset_result)
            visible_shapes += shapes
            polygon_vertices += vertices
    return visible_shapes, polygon_vertices


def _shading_palette_stats(
    baseline: MinimalizerV2Result,
    candidate: MinimalizerV2Result,
) -> tuple[int, float, int]:
    global_deltas: list[int] = []
    for name in set(baseline.presets) | set(candidate.presets):
        before = baseline.presets.get(name)
        after = candidate.presets.get(name)
        if before is None or after is None:
            return 10**9, float("inf"), 10**9
        global_deltas.append(
            abs(len(after.scene.palette) - len(before.scene.palette))
        )

    baseline_part_total = 0
    candidate_part_total = 0
    max_part_increase = 0
    part_names = set(baseline.person_part_presets) | set(
        candidate.person_part_presets
    )
    for part_name in part_names:
        before_presets = baseline.person_part_presets.get(part_name)
        after_presets = candidate.person_part_presets.get(part_name)
        if before_presets is None or after_presets is None:
            return 10**9, float("inf"), 10**9
        for name in set(before_presets) | set(after_presets):
            before = before_presets.get(name)
            after = after_presets.get(name)
            if before is None or after is None:
                return 10**9, float("inf"), 10**9
            before_count = len(before.scene.palette)
            after_count = len(after.scene.palette)
            baseline_part_total += before_count
            candidate_part_total += after_count
            max_part_increase = max(
                max_part_increase,
                after_count - before_count,
            )

    if baseline_part_total <= 0:
        total_part_ratio = 1.0 if candidate_part_total <= 0 else float("inf")
    else:
        total_part_ratio = candidate_part_total / float(baseline_part_total)

    return (
        max(global_deltas, default=0),
        total_part_ratio,
        max(0, max_part_increase),
    )


def _shading_part_palette_growth_is_safe(
    *,
    total_part_palette_ratio: float,
    max_part_palette_increase: int,
    part_polygon_reduction: float,
    config: ShadingFlattenGuardConfig,
) -> tuple[bool, bool]:
    if total_part_palette_ratio > config.max_total_part_palette_ratio:
        return False, False
    if max_part_palette_increase <= config.max_single_part_palette_increase:
        return True, False

    relaxed = (
        part_polygon_reduction
        >= config.palette_growth_relax_part_reduction_ratio
        and max_part_palette_increase
        <= config.max_relaxed_single_part_palette_increase
    )
    return relaxed, relaxed


def _shading_color_drift(
    baseline: MinimalizerV2Result,
    candidate: MinimalizerV2Result,
) -> tuple[float, float]:
    before = baseline.bundle.analysis_rgb.astype(np.float32)
    after = candidate.bundle.analysis_rgb.astype(np.float32)
    if before.shape != after.shape:
        return float("inf"), float("inf")

    mask: NDArray[np.bool_]
    if baseline.bundle.alpha is not None:
        mask = baseline.bundle.alpha > 0.01
    elif baseline.bundle.subject_prob is not None:
        mask = baseline.bundle.subject_prob > 0.20
    else:
        mask = np.ones(before.shape[:2], dtype=np.bool_)
    if not mask.any():
        mask = np.ones(before.shape[:2], dtype=np.bool_)

    pixel_mae = np.mean(np.abs(after - before), axis=2) / 255.0
    values = pixel_mae[mask]
    return float(values.mean()), float(np.percentile(values, 95.0))


def _shading_alpha_preserved(
    baseline: MinimalizerV2Result,
    candidate: MinimalizerV2Result,
) -> bool:
    before = baseline.bundle.alpha
    after = candidate.bundle.alpha
    if before is None or after is None:
        return before is None and after is None
    return bool(np.array_equal(before, after))


def _shading_silhouette_preserved(
    baseline: MinimalizerV2Result,
    candidate: MinimalizerV2Result,
) -> bool:
    before = baseline.person_parts
    after = candidate.person_parts
    if before is None or after is None:
        return before is None and after is None
    return (
        np.array_equal(before.subject_mask, after.subject_mask)
        and set(before.part_masks) == set(after.part_masks)
        and all(
            np.array_equal(before.part_masks[name], after.part_masks[name])
            for name in before.part_masks
        )
    )


def _safe_complexity_ratio(candidate: int, baseline: int) -> float:
    if baseline <= 0:
        return 1.0 if candidate <= 0 else float("inf")
    return candidate / float(baseline)


def _reduction_ratio(candidate: int, baseline: int) -> float:
    if baseline <= 0:
        return 0.0
    return (baseline - candidate) / float(baseline)


def _evaluate_shading_flatten_guard(
    baseline: MinimalizerV2Result,
    candidate: MinimalizerV2Result,
    *,
    config: ShadingFlattenGuardConfig,
) -> ShadingFlattenDecision:
    _baseline_shapes, baseline_vertices = _shading_result_complexity(baseline)
    _candidate_shapes, candidate_vertices = _shading_result_complexity(candidate)
    _baseline_part_shapes, baseline_part_vertices = _shading_part_complexity(baseline)
    _candidate_part_shapes, candidate_part_vertices = _shading_part_complexity(candidate)

    baseline_regions = int(baseline.region_merge.initial_region_count)
    candidate_regions = int(candidate.region_merge.initial_region_count)
    (
        global_palette_delta,
        total_part_palette_ratio,
        max_part_palette_increase,
    ) = _shading_palette_stats(baseline, candidate)

    before_edge = float(np.mean(baseline.bundle.edge_raw))
    after_edge = float(np.mean(candidate.bundle.edge_raw))
    edge_retention = (
        1.0 if before_edge <= 1.0e-9 else after_edge / before_edge
    )
    color_mae, color_p95 = _shading_color_drift(baseline, candidate)
    alpha_preserved = _shading_alpha_preserved(baseline, candidate)
    silhouette_preserved = _shading_silhouette_preserved(baseline, candidate)

    part_polygon_reduction = _reduction_ratio(
        candidate_part_vertices,
        baseline_part_vertices,
    )
    (
        part_palette_growth_safe,
        palette_growth_relaxed,
    ) = _shading_part_palette_growth_is_safe(
        total_part_palette_ratio=total_part_palette_ratio,
        max_part_palette_increase=max_part_palette_increase,
        part_polygon_reduction=part_polygon_reduction,
        config=config,
    )

    reasons: list[str] = []
    if _safe_complexity_ratio(candidate_vertices, baseline_vertices) > config.max_polygon_vertex_ratio:
        reasons.append("polygon_vertices")
    if (
        _safe_complexity_ratio(candidate_part_vertices, baseline_part_vertices)
        > config.max_part_polygon_vertex_ratio
    ):
        reasons.append("part_polygon_vertices")
    if _safe_complexity_ratio(candidate_regions, baseline_regions) > config.max_initial_region_ratio:
        reasons.append("initial_regions")
    if global_palette_delta > config.max_global_palette_delta:
        reasons.append("global_palette_delta")
    if total_part_palette_ratio > config.max_total_part_palette_ratio:
        reasons.append("part_palette_total")
    elif not part_palette_growth_safe:
        reasons.append("part_palette_growth")
    if edge_retention < config.min_edge_energy_retention:
        reasons.append("edge_retention")
    if color_mae > config.max_subject_color_mae:
        reasons.append("subject_color_mae")
    if color_p95 > config.max_subject_color_p95:
        reasons.append("subject_color_p95")
    if not alpha_preserved:
        reasons.append("alpha")
    if not silhouette_preserved:
        reasons.append("silhouette")

    meaningful = (
        _reduction_ratio(candidate_regions, baseline_regions)
        >= config.min_region_reduction_ratio
        or _reduction_ratio(candidate_vertices, baseline_vertices)
        >= config.min_polygon_reduction_ratio
        or _reduction_ratio(candidate_part_vertices, baseline_part_vertices)
        >= config.min_part_polygon_reduction_ratio
    )
    if not meaningful:
        reasons.append("no_meaningful_simplification")

    return ShadingFlattenDecision(
        accepted=not reasons,
        reasons=tuple(reasons),
        baseline_initial_regions=baseline_regions,
        candidate_initial_regions=candidate_regions,
        baseline_polygon_vertices=baseline_vertices,
        candidate_polygon_vertices=candidate_vertices,
        baseline_part_polygon_vertices=baseline_part_vertices,
        candidate_part_polygon_vertices=candidate_part_vertices,
        global_palette_delta=global_palette_delta,
        total_part_palette_ratio=total_part_palette_ratio,
        max_part_palette_increase=max_part_palette_increase,
        part_palette_growth_relaxed=palette_growth_relaxed,
        edge_energy_retention=edge_retention,
        subject_color_mae=color_mae,
        subject_color_p95=color_p95,
        alpha_preserved=alpha_preserved,
        silhouette_preserved=silhouette_preserved,
    )


def minimalize_v2(
    source_rgb: NDArray[np.uint8],
    *,
    presets: tuple[str, ...] = ("minimal",),
    config: PipelineConfig | None = None,
    guidance: AnalysisGuidance | None = None,
) -> MinimalizerV2Result:
    active_config = config or PipelineConfig()
    guard = active_config.shading_flatten_guard
    if active_config.shading_flatten.enabled and guard.enabled:
        baseline_config = replace(
            active_config,
            shading_flatten=replace(active_config.shading_flatten, enabled=False),
            shading_flatten_guard=replace(guard, enabled=False),
        )
        candidate_config = replace(
            active_config,
            shading_flatten_guard=replace(guard, enabled=False),
        )
        baseline = _minimalize_v2_impl(
            source_rgb,
            presets=presets,
            config=baseline_config,
            characteristic=None,
            observer=None,
            guidance=guidance,
        )
        candidate = _minimalize_v2_impl(
            source_rgb,
            presets=presets,
            config=candidate_config,
            characteristic=None,
            observer=None,
            guidance=guidance,
        )
        decision = _evaluate_shading_flatten_guard(
            baseline,
            candidate,
            config=guard,
        )
        selected = candidate if decision.accepted else baseline
        return replace(selected, shading_flatten_decision=decision)

    return _minimalize_v2_impl(
        source_rgb,
        presets=presets,
        config=active_config,
        characteristic=None,
        observer=None,
        guidance=guidance,
    )
