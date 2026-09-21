from __future__ import annotations

from dataclasses import dataclass, field, replace
from time import perf_counter
from types import MappingProxyType
from typing import Callable, Mapping

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
from minimalize_engine.v2.preprocessing import DEFAULT_ANALYSIS_MAX_SIDE, build_image_bundle
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
    parts: PersonPartConfig = field(default_factory=PersonPartConfig)


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    analysis_max_side: int = DEFAULT_ANALYSIS_MAX_SIDE
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
        "head": (30, 22, 14, 8),
        "torso": (28, 20, 12, 7),
        "left_arm": (20, 14, 8, 5),
        "right_arm": (20, 14, 8, 5),
        "left_leg": (20, 14, 8, 5),
        "right_leg": (20, 14, 8, 5),
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


def _person_part_primitive_config(part_name: str, base: PrimitiveFitConfig) -> PrimitiveFitConfig:
    # Person parts are semantically isolated, so favor bold geometry over contour fidelity.
    common = dict(
        min_iou=0.62, max_undercoverage=0.38, max_overcoverage=0.32,
        max_centroid_shift_ratio=0.14, max_directional_under_loss=0.42,
        max_directional_over_loss=0.42, max_boundary_distance=0.18,
        max_protected_boundary_error=0.18, min_contact_retention=0.35,
        minimum_complexity_gain=0.12, adoption_margin=0.0, complexity_reward=0.34,
    )
    if part_name in {"left_arm", "right_arm", "left_leg", "right_leg"}:
        common.update(min_iou=0.55, max_undercoverage=0.45, max_overcoverage=0.40)
    elif part_name == "head":
        common.update(min_iou=0.68, max_undercoverage=0.32, max_overcoverage=0.28)
    return replace(base, **common)


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
            subject_provider="minimalizer",
            subject_model=f"person-part:{name}",
        )
        part_config = replace(
            config,
            layered_person=replace(config.layered_person, enabled=False),
            cut_policies=_person_part_cut_policies(name),
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
            analysis_max_side=config.analysis_max_side,
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


def minimalize_v2(
    source_rgb: NDArray[np.uint8],
    *,
    presets: tuple[str, ...] = ("minimal",),
    config: PipelineConfig | None = None,
    guidance: AnalysisGuidance | None = None,
) -> MinimalizerV2Result:
    active_config = config or PipelineConfig()
    return _minimalize_v2_impl(
        source_rgb,
        presets=presets,
        config=active_config,
        characteristic=None,
        observer=None,
        guidance=guidance,
    )
