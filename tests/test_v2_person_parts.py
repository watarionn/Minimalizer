import cv2
import numpy as np
import pytest

from minimalize_engine.v2.analysis_guidance import AnalysisGuidance, StructuralGuide
from minimalize_engine.v2.person_parts import (
    PERSON_PART_NAMES,
    PersonPartConfig,
    build_person_part_partition,
)


def _guidance() -> AnalysisGuidance:
    h, w = 20, 16
    subject = np.zeros((h, w), dtype=np.float32)
    subject[2:19, 3:13] = 0.95
    labels = (
        "torso",
        "left_upper_arm",
        "left_forearm",
        "right_upper_arm",
        "right_forearm",
        "left_thigh",
        "left_shin",
        "right_thigh",
        "right_shin",
    )
    maps = np.zeros((len(labels), h, w), dtype=np.float32)
    maps[0, 7:14, 6:10] = 0.9
    maps[1, 8:11, 3:7] = 0.8
    maps[2, 10:14, 3:6] = 0.8
    maps[3, 8:11, 9:13] = 0.8
    maps[4, 10:14, 10:13] = 0.8
    maps[5, 13:17, 6:8] = 0.8
    maps[6, 16:19, 5:8] = 0.8
    maps[7, 13:17, 8:10] = 0.8
    maps[8, 16:19, 9:12] = 0.8
    structural = StructuralGuide(labels=labels, confidence_maps=maps, provider="test", model="pose")
    return AnalysisGuidance(
        subject_prob=subject,
        subject_confidence=np.ones_like(subject),
        structural=structural,
        subject_provider="test",
        subject_model="mask",
    )


def test_partition_separates_background_and_six_coarse_parts():
    partition = build_person_part_partition(_guidance())
    assert set(partition.part_masks) == set(PERSON_PART_NAMES)
    assert np.array_equal(partition.background_mask, ~partition.subject_mask)
    assert partition.part_masks["head"].any()
    for name in PERSON_PART_NAMES[1:]:
        assert partition.part_masks[name].any()
        assert not np.any(partition.part_masks[name] & partition.background_mask)


def test_partition_without_pose_uses_silhouette_body_fallback():
    guidance = _guidance()
    guidance = AnalysisGuidance(
        subject_prob=guidance.subject_prob,
        subject_confidence=guidance.subject_confidence,
        subject_provider="test",
        subject_model="mask",
    )
    partition = build_person_part_partition(guidance)
    assert partition.part_masks["head"].any()
    assert partition.part_masks["torso"].any()
    assert partition.part_masks["left_leg"].any()
    assert partition.part_masks["right_leg"].any()


def test_partition_requires_subject_guidance():
    with pytest.raises(ValueError, match="subject_prob"):
        build_person_part_partition(AnalysisGuidance())


def test_partition_config_rejects_invalid_thresholds():
    with pytest.raises(ValueError):
        PersonPartConfig(subject_threshold=0.0)


def test_pipeline_exposes_partition_only_when_layered_mode_is_enabled():
    from minimalize_engine.v2.pipeline import LayeredPersonConfig, PipelineConfig, minimalize_v2

    guidance = _guidance()
    image = np.full((20, 16, 3), 240, dtype=np.uint8)
    image[2:19, 3:13] = (120, 80, 60)
    result = minimalize_v2(
        image,
        config=PipelineConfig(
            analysis_max_side=20,
            layered_person=LayeredPersonConfig(enabled=True),
        ),
        guidance=guidance,
    )
    assert result.person_parts is not None
    assert result.person_parts.part_masks["torso"].any()

    baseline = minimalize_v2(
        image,
        config=PipelineConfig(analysis_max_side=20),
        guidance=guidance,
    )
    assert baseline.person_parts is None


def test_resize_partition_projects_masks_to_analysis_resolution():
    from minimalize_engine.v2.person_parts import resize_person_part_partition

    partition = build_person_part_partition(_guidance())
    resized = resize_person_part_partition(partition, (10, 8))
    assert resized.subject_mask.shape == (10, 8)
    assert resized.background_mask.shape == (10, 8)
    assert all(mask.shape == (10, 8) for mask in resized.part_masks.values())
    assert not np.any(resized.subject_mask & resized.background_mask)
    occupied = np.zeros((10, 8), dtype=np.uint8)
    for mask in resized.part_masks.values():
        assert not np.any((occupied > 0) & mask)
        occupied[mask] += 1


def test_sparse_pose_support_falls_back_to_complete_silhouette_partition():
    guidance = _guidance()
    maps = np.zeros_like(guidance.structural.confidence_maps)
    # A detector may return one convincing limb while the rest of the pose is unusable.
    maps[1, 8:12, 3:7] = 0.9
    sparse = AnalysisGuidance(
        subject_prob=guidance.subject_prob,
        subject_confidence=guidance.subject_confidence,
        structural=StructuralGuide(
            labels=guidance.structural.labels,
            confidence_maps=maps,
            provider="test",
            model="sparse-pose",
        ),
        subject_provider="test",
        subject_model="mask",
    )
    partition = build_person_part_partition(
        sparse,
        config=PersonPartConfig(structural_min_part_pixels=4),
    )
    for name in PERSON_PART_NAMES:
        assert partition.part_masks[name].any()


def test_partition_config_rejects_invalid_structural_coverage():
    with pytest.raises(ValueError):
        PersonPartConfig(structural_min_coverage_ratio=0.0)


def test_person_part_primitive_config_is_deliberately_coarser_for_limbs():
    from minimalize_engine.v2.pipeline import _person_part_primitive_config
    from minimalize_engine.v2.primitive import PrimitiveFitConfig

    base = PrimitiveFitConfig()
    limb = _person_part_primitive_config("left_arm", base)
    head = _person_part_primitive_config("head", base)
    assert limb.min_iou < base.min_iou
    assert limb.max_overcoverage > base.max_overcoverage
    assert limb.complexity_reward > base.complexity_reward
    assert limb.rectangle_complexity < limb.ellipse_complexity
    assert limb.trapezoid_complexity < limb.capsule_complexity
    assert head.ellipse_complexity > base.ellipse_complexity
    assert head.min_iou > limb.min_iou


def test_layered_person_can_disable_coarse_part_primitive_policy():
    from minimalize_engine.v2.pipeline import LayeredPersonConfig

    assert LayeredPersonConfig().coarse_part_primitives is True
    assert LayeredPersonConfig(coarse_part_primitives=False).coarse_part_primitives is False


def test_person_part_minimal_cut_budgets_are_bold():
    from minimalize_engine.v2.pipeline import _person_part_cut_policies

    expected_max = {
        "head": 6,
        "torso": 5,
        "left_arm": 3,
        "right_arm": 3,
        "left_leg": 3,
        "right_leg": 3,
    }
    for name, ceiling in expected_max.items():
        assert _person_part_cut_policies(name)["minimal"].target_max == ceiling


def test_structural_partition_expands_pose_corridors_across_subject():
    partition = build_person_part_partition(_guidance(), config=PersonPartConfig(structural_min_part_pixels=4))
    covered = np.zeros_like(partition.subject_mask)
    for mask in partition.part_masks.values():
        covered |= mask
    assert np.array_equal(covered, partition.subject_mask)


def test_semantic_part_shape_limits_match_approved_coarse_budget():
    from minimalize_engine.v2.pipeline import _semantic_part_shape_limit

    assert _semantic_part_shape_limit("head", "minimal") == 5
    assert _semantic_part_shape_limit("torso", "minimal") == 3
    for name in ("left_arm", "right_arm", "left_leg", "right_leg"):
        assert _semantic_part_shape_limit(name, "minimal") == 3


def test_person_part_contours_are_more_aggressively_simplified():
    from minimalize_engine.v2.contour import ContourSimplificationConfig
    from minimalize_engine.v2.pipeline import _person_part_contour_config

    base = ContourSimplificationConfig()
    coarse = _person_part_contour_config(base)
    assert coarse.minimal_epsilon_ratio > base.minimal_epsilon_ratio
    assert coarse.ultra_minimal_epsilon_ratio > coarse.minimal_epsilon_ratio
    assert coarse.min_iou < base.min_iou
    assert coarse.max_area_change > base.max_area_change


def test_person_part_polygon_quantization_caps_vertex_count():
    from minimalize_engine.v2.pipeline import _quantize_polygon_geometry
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    angles = np.linspace(0.0, 2.0 * np.pi, 20, endpoint=False)
    loop = np.column_stack((20.0 + 10.0 * np.cos(angles), 20.0 + 7.0 * np.sin(angles))).astype(np.float32)
    geometry = PrimitiveGeometry(kind="polygon", loops=(loop,))
    quantized = _quantize_polygon_geometry(geometry, max_vertices=6)
    assert quantized.kind == "polygon"
    assert 3 <= len(quantized.loops[0]) <= 6


def test_semantic_plane_consolidation_is_available_on_layered_path():
    from minimalize_engine.v2.pipeline import LayeredPersonConfig

    # The consolidation stage is gated by the existing semantic-shape-budget
    # switch, so the layered experiment remains fully reversible.
    assert LayeredPersonConfig().semantic_shape_budget is True
    assert LayeredPersonConfig(semantic_shape_budget=False).semantic_shape_budget is False


def test_person_part_polygon_quantization_supports_quadrilateral_limbs():
    from minimalize_engine.v2.pipeline import _quantize_polygon_geometry
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    angles = np.linspace(0.0, 2.0 * np.pi, 16, endpoint=False)
    loop = np.column_stack((24.0 + 12.0 * np.cos(angles), 30.0 + 5.0 * np.sin(angles))).astype(np.float32)
    geometry = PrimitiveGeometry(kind="polygon", loops=(loop,))
    quantized = _quantize_polygon_geometry(geometry, max_vertices=4)
    assert 3 <= len(quantized.loops[0]) <= 4


def test_person_part_polygon_quantization_can_drop_secondary_loops():
    from minimalize_engine.v2.pipeline import _quantize_polygon_geometry
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    outer = np.array([[0,0],[20,0],[20,20],[0,20]], dtype=np.float32)
    inner = np.array([[7,7],[13,7],[13,13],[7,13]], dtype=np.float32)
    geometry = PrimitiveGeometry(kind="polygon", loops=(outer, inner))
    quantized = _quantize_polygon_geometry(geometry, max_vertices=4, max_loops=1)
    assert len(quantized.loops) == 1
    assert len(quantized.loops[0]) <= 4


def test_person_part_polygon_budget_keeps_head_angular_but_single_loop():
    from minimalize_engine.v2.pipeline import _person_part_polygon_budget

    assert _person_part_polygon_budget("head") == (6, 1)
    assert _person_part_polygon_budget("torso") == (5, 1)
    assert _person_part_polygon_budget("left_arm") == (4, 1)


def test_semantic_plane_refit_clusters_only_adjacent_near_colors():
    from minimalize_engine.v2.pipeline import _semantic_plane_clusters

    masks = [np.zeros((24, 24), dtype=bool) for _ in range(4)]
    masks[0][4:10, 3:8] = True
    masks[1][4:10, 8:13] = True
    masks[2][16:20, 16:20] = True
    masks[3][4:10, 13:18] = True
    colors = [
        np.array((100, 90, 80), dtype=np.float32),
        np.array((112, 96, 84), dtype=np.float32),
        np.array((105, 92, 82), dtype=np.float32),
        np.array((220, 40, 40), dtype=np.float32),
    ]
    clusters = _semantic_plane_clusters(
        masks, colors, color_distance=32.0, adjacency_radius=1
    )
    assert clusters == ((0, 1),)


def test_semantic_plane_refit_rebuilds_adjacent_mass_as_low_vertex_polygon():
    import cv2
    from minimalize_engine.v2.pipeline import _fit_semantic_plane_polygon

    part = np.zeros((30, 30), dtype=bool)
    part[4:24, 4:24] = True
    target = np.zeros_like(part)
    target[8:16, 6:12] = True
    target[8:16, 12:20] = True

    polygon = _fit_semantic_plane_polygon(target, part, max_vertices=4)
    assert polygon is not None
    assert 3 <= len(polygon) <= 4

    rendered = np.zeros_like(part, dtype=np.uint8)
    cv2.fillPoly(rendered, [np.rint(polygon).astype(np.int32)], 1)
    candidate = rendered > 0
    iou = np.count_nonzero(candidate & target) / np.count_nonzero(candidate | target)
    assert iou >= 0.85


def test_semantic_plane_refit_has_independent_layered_toggle():
    from minimalize_engine.v2.pipeline import LayeredPersonConfig

    assert LayeredPersonConfig().semantic_plane_refit is True
    assert LayeredPersonConfig(semantic_plane_refit=False).semantic_plane_refit is False


def test_torso_semantic_budget_preserves_small_high_contrast_accent():
    from minimalize_engine.v2.pipeline import SceneShape, _semantic_budget_keep_ids
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    geometry = PrimitiveGeometry(
        kind="polygon",
        loops=(np.array([[0,0],[4,0],[4,4],[0,4]], dtype=np.float32),),
    )
    shapes = [
        SceneShape(region_id=1, geometry=geometry, palette_id=0),
        SceneShape(region_id=2, geometry=geometry, palette_id=1),
        SceneShape(region_id=3, geometry=geometry, palette_id=2),
        SceneShape(region_id=4, geometry=geometry, palette_id=3),
    ]
    scored = [
        (1000, 0, shapes[0]),
        (500, -1, shapes[1]),
        (400, -2, shapes[2]),
        (100, -3, shapes[3]),
    ]
    palette = {
        0: np.array((100,100,100), dtype=np.float32),
        1: np.array((110,110,110), dtype=np.float32),
        2: np.array((120,120,120), dtype=np.float32),
        3: np.array((230,30,30), dtype=np.float32),
    }

    torso_ids = _semantic_budget_keep_ids(
        scored, palette, part_name="torso", limit=3
    )
    arm_ids = _semantic_budget_keep_ids(
        scored, palette, part_name="left_arm", limit=3
    )

    assert torso_ids == {1, 2, 4}
    assert arm_ids == {1, 2, 3}


def test_safe_limb_two_plane_budget_rejects_meaningful_color_accent():
    from minimalize_engine.v2.pipeline import (
        SceneShape,
        _safe_semantic_two_plane_keep_ids,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    def polygon(points):
        return PrimitiveGeometry(
            kind="polygon",
            loops=(np.asarray(points, dtype=np.float32),),
        )

    main = SceneShape(
        region_id=1,
        geometry=polygon([[2,5],[24,5],[24,20],[2,20]]),
        palette_id=0,
    )
    secondary = SceneShape(
        region_id=2,
        geometry=polygon([[24,5],[42,5],[42,20],[24,20]]),
        palette_id=1,
    )
    overlay = SceneShape(
        region_id=3,
        geometry=polygon([[8,8],[13,8],[13,16],[8,16]]),
        palette_id=2,
    )
    scored = [(400, 0, main), (300, -1, secondary), (60, -2, overlay)]
    part = np.ones((30, 50), dtype=bool)

    neutral_palette = {
        0: np.array((100,100,100), dtype=np.float32),
        1: np.array((110,110,110), dtype=np.float32),
        2: np.array((115,115,115), dtype=np.float32),
    }
    accent_palette = {
        **neutral_palette,
        2: np.array((230,30,30), dtype=np.float32),
    }

    assert _safe_semantic_two_plane_keep_ids(
        scored, neutral_palette, part
    ) == {1, 2}
    assert _safe_semantic_two_plane_keep_ids(
        scored, accent_palette, part
    ) is None


def test_head_two_plane_budget_protects_smaller_color_accent():
    from minimalize_engine.v2.pipeline import (
        SceneShape,
        _safe_semantic_two_plane_keep_ids,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry
    from minimalize_engine.v2.primitive.scoring import rasterize_geometry

    def polygon(points):
        return PrimitiveGeometry(
            kind="polygon",
            loops=(np.asarray(points, dtype=np.float32),),
        )

    main = SceneShape(
        region_id=11,
        geometry=polygon([[2,5],[24,5],[24,20],[2,20]]),
        palette_id=0,
    )
    secondary = SceneShape(
        region_id=12,
        geometry=polygon([[24,5],[42,5],[42,20],[24,20]]),
        palette_id=1,
    )
    small_accent = SceneShape(
        region_id=13,
        geometry=polygon([[8,8],[12,8],[12,13],[8,13]]),
        palette_id=2,
    )
    part = np.ones((30, 50), dtype=bool)
    main_mask = np.asarray(
        rasterize_geometry(main.geometry, part.shape, origin=(0, 0), scale=2),
        dtype=bool,
    )
    secondary_mask = np.asarray(
        rasterize_geometry(secondary.geometry, part.shape, origin=(0, 0), scale=2),
        dtype=bool,
    )
    full_pixels = int(np.count_nonzero((main_mask | secondary_mask) & part))
    accent_support = max(1, int(round(full_pixels * 0.045)))
    scored = [
        (400, 0, main),
        (300, -1, secondary),
        (accent_support, -2, small_accent),
    ]
    palette = {
        0: np.array((100,100,100), dtype=np.float32),
        1: np.array((110,110,110), dtype=np.float32),
        2: np.array((230,30,30), dtype=np.float32),
    }

    limb_like = _safe_semantic_two_plane_keep_ids(
        scored,
        palette,
        part,
        accent_support_ratio=0.05,
    )
    head_like = _safe_semantic_two_plane_keep_ids(
        scored,
        palette,
        part,
        accent_support_ratio=0.04,
    )

    assert limb_like == {11, 12}
    assert head_like is None


def test_semantic_dead_plane_cleanup_only_flags_negligible_support():
    from minimalize_engine.v2.pipeline import SceneShape, _semantic_dead_plane_ids
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    def polygon(points):
        return PrimitiveGeometry(
            kind="polygon",
            loops=(np.asarray(points, dtype=np.float32),),
        )

    anchor = SceneShape(
        region_id=21,
        geometry=polygon([[2,2],[18,2],[18,18],[2,18]]),
        palette_id=0,
    )
    outside = SceneShape(
        region_id=22,
        geometry=polygon([[30,30],[34,30],[34,34],[30,34]]),
        palette_id=1,
    )
    small_but_real = SceneShape(
        region_id=23,
        geometry=polygon([[20,2],[24,2],[24,6],[20,6]]),
        palette_id=2,
    )
    part = np.zeros((28, 28), dtype=bool)
    part[1:27, 1:27] = True

    dead = _semantic_dead_plane_ids(
        [anchor, outside, small_but_real],
        part,
    )

    assert dead == {22}


def test_render_dead_plane_cleanup_flags_only_fully_hidden_plane():
    from minimalize_engine.v2.palette import PaletteEntry
    from minimalize_engine.v2.pipeline import (
        SceneModel,
        SceneShape,
        _render_dead_plane_ids,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    def polygon(points):
        return PrimitiveGeometry(
            kind="polygon",
            loops=(np.asarray(points, dtype=np.float32),),
        )

    covered = SceneShape(
        region_id=1,
        geometry=polygon([[2,2],[12,2],[12,12],[2,12]]),
        palette_id=0,
    )
    covering = SceneShape(
        region_id=2,
        geometry=polygon([[2,2],[12,2],[12,12],[2,12]]),
        palette_id=1,
    )
    visible = SceneShape(
        region_id=3,
        geometry=polygon([[15,2],[22,2],[22,10],[15,10]]),
        palette_id=0,
    )
    red = PaletteEntry(
        0, (1,3), 1, np.asarray([50.0,0.0,0.0]), (220,40,40), (0,0)
    )
    blue = PaletteEntry(
        1, (2,), 2, np.asarray([50.0,0.0,0.0]), (40,40,220), (0,0)
    )
    scene = SceneModel(
        30,
        20,
        (covered, covering, visible),
        (red, blue),
    )

    assert _render_dead_plane_ids(scene) == {1}


def test_render_negligible_cleanup_flags_single_pixel_overlay():
    from minimalize_engine.v2.palette import PaletteEntry
    from minimalize_engine.v2.pipeline import (
        SceneModel,
        SceneShape,
        _render_negligible_plane_ids,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    def polygon(points):
        return PrimitiveGeometry(
            kind="polygon",
            loops=(np.asarray(points, dtype=np.float32),),
        )

    base = SceneShape(
        region_id=10,
        geometry=polygon([[2,2],[27,2],[27,27],[2,27]]),
        palette_id=0,
    )
    pixel = SceneShape(
        region_id=11,
        geometry=polygon([[8,8],[9,8],[9,9],[8,9]]),
        palette_id=1,
    )
    red = PaletteEntry(
        0, (10,), 10, np.asarray([50.0,0.0,0.0]), (220,40,40), (0,0)
    )
    white = PaletteEntry(
        1, (11,), 11, np.asarray([100.0,0.0,0.0]), (255,255,255), (0,0)
    )
    scene = SceneModel(
        40,
        40,
        (base, pixel),
        (red, white),
    )

    assert _render_negligible_plane_ids(scene) == {11}


def test_safe_angular_vertex_reduction_drops_redundant_head_corner():
    from dataclasses import dataclass
    from minimalize_engine.v2.palette import PaletteEntry
    from minimalize_engine.v2.pipeline import (
        SceneModel,
        SceneShape,
        _reduce_safe_angular_vertices,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    @dataclass(frozen=True)
    class DummyResult:
        preset: str
        scene: SceneModel

    geometry = PrimitiveGeometry(
        kind="polygon",
        loops=(
            np.asarray(
                [[2,2],[12,2],[22,2],[22,18],[2,18],[2,10]],
                dtype=np.float32,
            ),
        ),
    )
    shape = SceneShape(region_id=1, geometry=geometry, palette_id=0)
    entry = PaletteEntry(
        0,
        (1,),
        1,
        np.asarray([50.0,0.0,0.0]),
        (120,120,120),
        (0,0),
    )
    result = DummyResult(
        preset="minimal",
        scene=SceneModel(30, 24, (shape,), (entry,)),
    )

    reduced = _reduce_safe_angular_vertices(
        result,
        part_name="head",
    )

    visible = [s for s in reduced.scene.shapes if s.visible]
    assert len(visible) == 1
    assert len(visible[0].geometry.loops[0]) == 5


def test_tiny_structural_leg_repair_restores_bilateral_fallback_without_overlap():
    from minimalize_engine.v2.person_parts import (
        PERSON_PART_NAMES,
        _repair_tiny_structural_legs,
    )

    subject = np.ones((20, 20), dtype=bool)
    parts = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    parts["torso"][:] = True
    parts["left_leg"][19, 0] = True
    parts["right_leg"][19, 19] = True
    parts["torso"][19, 0] = False
    parts["torso"][19, 19] = False

    fallback = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    fallback["left_leg"][12:, :10] = True
    fallback["right_leg"][12:, 10:] = True

    repaired = _repair_tiny_structural_legs(
        subject,
        parts,
        fallback,
        {"left_leg": 40, "right_leg": 40},
        min_subject_ratio=0.02,
        severe_subject_ratio=0.004,
        lower_start_ratio=0.72,
        min_seed_pixels=24,
    )

    assert int(repaired["left_leg"].sum()) >= 60
    assert int(repaired["right_leg"].sum()) >= 60
    assert not np.any(repaired["left_leg"] & repaired["right_leg"])
    assert not np.any(repaired["left_leg"] & repaired["torso"])
    assert not np.any(repaired["right_leg"] & repaired["torso"])
    assert np.logical_or.reduce(list(repaired.values())).all()


def test_tiny_structural_leg_repair_ignores_unilateral_degeneracy():
    from minimalize_engine.v2.person_parts import (
        PERSON_PART_NAMES,
        _repair_tiny_structural_legs,
    )

    subject = np.ones((20, 20), dtype=bool)
    parts = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    parts["torso"][:] = True
    parts["left_leg"][19, 0] = True
    parts["torso"][19, 0] = False
    parts["right_leg"][12:, 10:] = True
    parts["torso"][12:, 10:] = False

    fallback = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    fallback["left_leg"][12:, :10] = True
    fallback["right_leg"][12:, 10:] = True

    repaired = _repair_tiny_structural_legs(
        subject,
        parts,
        fallback,
        {"left_leg": 40, "right_leg": 40},
        min_subject_ratio=0.02,
        severe_subject_ratio=0.004,
        lower_start_ratio=0.72,
        min_seed_pixels=24,
    )

    assert int(repaired["left_leg"].sum()) == 1
    assert np.array_equal(repaired["right_leg"], parts["right_leg"])


def test_tiny_structural_leg_repair_ignores_weak_pose_seed():
    from minimalize_engine.v2.person_parts import (
        PERSON_PART_NAMES,
        _repair_tiny_structural_legs,
    )

    subject = np.ones((20, 20), dtype=bool)
    parts = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    parts["torso"][:] = True
    parts["left_leg"][19, 0] = True
    parts["right_leg"][19, 19] = True
    parts["torso"][19, 0] = False
    parts["torso"][19, 19] = False

    fallback = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    fallback["left_leg"][12:, :10] = True
    fallback["right_leg"][12:, 10:] = True

    repaired = _repair_tiny_structural_legs(
        subject,
        parts,
        fallback,
        {"left_leg": 40, "right_leg": 8},
        min_subject_ratio=0.02,
        severe_subject_ratio=0.004,
        lower_start_ratio=0.72,
        min_seed_pixels=24,
    )

    assert int(repaired["left_leg"].sum()) == 1
    assert int(repaired["right_leg"].sum()) == 1


def test_tiny_structural_leg_repair_only_expands_severe_leg():
    from minimalize_engine.v2.person_parts import (
        PERSON_PART_NAMES,
        _repair_tiny_structural_legs,
    )

    subject = np.ones((20, 20), dtype=bool)
    parts = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    parts["torso"][:] = True
    parts["left_leg"][19, 0] = True
    parts["right_leg"][19, 18:20] = True
    parts["torso"][19, 0] = False
    parts["torso"][19, 18:20] = False

    fallback = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    fallback["left_leg"][12:, :10] = True
    fallback["right_leg"][12:, 10:] = True

    repaired = _repair_tiny_structural_legs(
        subject,
        parts,
        fallback,
        {"left_leg": 40, "right_leg": 40},
        min_subject_ratio=0.02,
        severe_subject_ratio=0.004,
        lower_start_ratio=0.72,
        min_seed_pixels=24,
    )

    assert int(repaired["left_leg"].sum()) >= 60
    assert int(repaired["right_leg"].sum()) == 2
    assert np.array_equal(repaired["right_leg"], parts["right_leg"])
    assert not np.any(repaired["left_leg"] & repaired["torso"])


def test_bilateral_structural_arm_repair_restores_high_confidence_cores():
    from minimalize_engine.v2.person_parts import (
        PERSON_PART_NAMES,
        _repair_bilateral_structural_arms,
    )

    subject = np.ones((100, 100), dtype=bool)
    assigned = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    assigned["head"][0:20, 25:75] = True
    assigned["torso"][40:70, 30:70] = True
    assigned["left_leg"][70:, 30:50] = True
    assigned["right_leg"][70:, 50:70] = True

    seed_parts = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    seed_parts["head"][0:20, 25:75] = True
    seed_parts["torso"][35:70, 35:65] = True
    seed_parts["left_arm"][24:34, 18:24] = True
    seed_parts["right_arm"][24:34, 76:82] = True
    seed_parts["left_leg"][65:95, 35:45] = True
    seed_parts["right_leg"][65:95, 55:65] = True

    left_support = np.zeros(subject.shape, dtype=np.float32)
    right_support = np.zeros(subject.shape, dtype=np.float32)
    left_support[20:30, 28:34] = 0.8
    right_support[20:30, 66:72] = 0.8

    repaired = _repair_bilateral_structural_arms(
        subject,
        assigned,
        seed_parts,
        {"left_arm": left_support, "right_arm": right_support},
        collapse_subject_ratio=0.002,
        min_core_confidence=0.4,
        max_head_core_ratio=0.08,
        min_seed_pixels=4,
        minimum_part_pixels=1,
    )

    assert repaired["left_arm"].any()
    assert repaired["right_arm"].any()
    assert not np.any(repaired["left_arm"] & repaired["right_arm"])
    assert not np.any(repaired["left_arm"] & repaired["head"])
    assert not np.any(repaired["right_arm"] & repaired["head"])


def test_bilateral_structural_arm_repair_ignores_unilateral_collapse():
    from minimalize_engine.v2.person_parts import (
        PERSON_PART_NAMES,
        _repair_bilateral_structural_arms,
    )

    subject = np.ones((100, 100), dtype=bool)
    assigned = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    assigned["head"][0:40, 25:75] = True
    assigned["left_arm"][20:21, 20:21] = True
    assigned["right_arm"][20:30, 80:84] = True

    seed_parts = {name: mask.copy() for name, mask in assigned.items()}
    seed_parts["left_arm"][20:30, 28:34] = True
    left_support = np.zeros(subject.shape, dtype=np.float32)
    right_support = np.zeros(subject.shape, dtype=np.float32)
    left_support[20:30, 28:34] = 0.8
    right_support[20:30, 66:72] = 0.8

    repaired = _repair_bilateral_structural_arms(
        subject,
        assigned,
        seed_parts,
        {"left_arm": left_support, "right_arm": right_support},
        collapse_subject_ratio=0.002,
        min_core_confidence=0.4,
        max_head_core_ratio=0.08,
        min_seed_pixels=4,
        minimum_part_pixels=1,
    )

    assert np.array_equal(repaired["left_arm"], assigned["left_arm"])
    assert np.array_equal(repaired["right_arm"], assigned["right_arm"])


def test_bilateral_structural_arm_repair_rejects_head_overlapping_cores():
    from minimalize_engine.v2.person_parts import (
        PERSON_PART_NAMES,
        _repair_bilateral_structural_arms,
    )

    subject = np.ones((100, 100), dtype=bool)
    assigned = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    assigned["head"][0:40, 25:75] = True
    assigned["torso"][40:70, 30:70] = True

    seed_parts = {name: np.zeros_like(subject) for name in PERSON_PART_NAMES}
    seed_parts["head"][0:40, 25:75] = True
    seed_parts["left_arm"][20:30, 28:34] = True
    seed_parts["right_arm"][20:30, 66:72] = True

    left_support = np.zeros(subject.shape, dtype=np.float32)
    right_support = np.zeros(subject.shape, dtype=np.float32)
    left_support[20:30, 28:34] = 0.8
    right_support[20:30, 66:72] = 0.8

    repaired = _repair_bilateral_structural_arms(
        subject,
        assigned,
        seed_parts,
        {"left_arm": left_support, "right_arm": right_support},
        collapse_subject_ratio=0.002,
        min_core_confidence=0.4,
        max_head_core_ratio=0.08,
        min_seed_pixels=4,
        minimum_part_pixels=1,
    )

    assert np.array_equal(repaired["left_arm"], assigned["left_arm"])
    assert np.array_equal(repaired["right_arm"], assigned["right_arm"])


def test_quantized_geometry_safety_rejects_large_undercoverage():
    from minimalize_engine.v2.pipeline import _quantized_geometry_is_safe
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    original = PrimitiveGeometry(
        kind="polygon",
        loops=(
            np.asarray(
                [[2,2],[18,2],[18,18],[2,18]],
                dtype=np.float32,
            ),
        ),
    )
    candidate = PrimitiveGeometry(
        kind="polygon",
        loops=(
            np.asarray(
                [[2,2],[18,2],[2,18]],
                dtype=np.float32,
            ),
        ),
    )

    assert not _quantized_geometry_is_safe(
        original,
        candidate,
        canvas_shape=(24,24),
    )


def test_quantized_geometry_safety_accepts_redundant_corner_cleanup():
    from minimalize_engine.v2.pipeline import _quantized_geometry_is_safe
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    original = PrimitiveGeometry(
        kind="polygon",
        loops=(
            np.asarray(
                [[2,2],[10,2],[18,2],[18,10],[18,18],[10,18],[2,18],[2,10]],
                dtype=np.float32,
            ),
        ),
    )
    candidate = PrimitiveGeometry(
        kind="polygon",
        loops=(
            np.asarray(
                [[2,2],[18,2],[18,18],[2,18]],
                dtype=np.float32,
            ),
        ),
    )

    assert _quantized_geometry_is_safe(
        original,
        candidate,
        canvas_shape=(24,24),
    )


def test_quantized_candidate_selection_prefers_simplest_safe_geometry():
    from minimalize_engine.v2.pipeline import _select_quantized_geometry_candidate
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    original = PrimitiveGeometry(kind="polygon", loops=(np.asarray(
        [[2,2],[10,2],[18,2],[18,10],[18,18],[10,18],[2,18],[2,10]],
        dtype=np.float32,
    ),))
    five = PrimitiveGeometry(kind="polygon", loops=(np.asarray(
        [[2,2],[18,2],[18,18],[10,18],[2,18]], dtype=np.float32,
    ),))
    four = PrimitiveGeometry(kind="polygon", loops=(np.asarray(
        [[2,2],[18,2],[18,18],[2,18]], dtype=np.float32,
    ),))

    selected = _select_quantized_geometry_candidate(
        original, (five, four), canvas_shape=(24,24)
    )
    assert len(selected.loops[0]) == 4


def test_quantized_candidate_selection_keeps_original_when_all_are_destructive():
    from minimalize_engine.v2.pipeline import _select_quantized_geometry_candidate
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    original = PrimitiveGeometry(kind="polygon", loops=(np.asarray(
        [[2,2],[18,2],[18,18],[2,18]], dtype=np.float32,
    ),))
    triangle = PrimitiveGeometry(kind="polygon", loops=(np.asarray(
        [[2,2],[18,2],[2,18]], dtype=np.float32,
    ),))

    selected = _select_quantized_geometry_candidate(
        original, (triangle,), canvas_shape=(24,24)
    )
    assert selected is original


def test_person_part_quantization_uses_bounded_safe_soft_fallback():
    from minimalize_engine.v2.pipeline import (
        _quantize_person_part_geometry,
        _quantized_geometry_metrics,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    original = PrimitiveGeometry(kind="polygon", loops=(np.asarray(
        [[2,2],[18,2],[18,8],[8,8],[8,18],[2,18]], dtype=np.float32,
    ),))
    selected = _quantize_person_part_geometry(
        original, canvas_shape=(24,24), max_vertices=4, max_loops=1
    )
    iou, under, over = _quantized_geometry_metrics(
        original, selected, canvas_shape=(24,24)
    )
    assert 4 < len(selected.loops[0]) <= 12
    assert iou >= 0.75
    assert under <= 0.15
    assert over <= 0.20


def test_semantic_part_coverage_guard_rejects_catastrophic_loss():
    from minimalize_engine.v2.pipeline import _semantic_part_coverage_is_safe

    assert _semantic_part_coverage_is_safe(0.82, 0.72)
    assert not _semantic_part_coverage_is_safe(0.62, 0.19)
    assert not _semantic_part_coverage_is_safe(0.60, 0.00)
    # Tiny absolute changes should not be rejected just because the ratio is noisy.
    assert _semantic_part_coverage_is_safe(0.10, 0.06)


def test_semantic_part_coverage_guard_rolls_back_destructive_geometry():
    from dataclasses import dataclass
    from minimalize_engine.v2.palette import PaletteEntry
    from minimalize_engine.v2.pipeline import (
        SceneModel,
        SceneShape,
        _guard_semantic_part_coverage,
        _semantic_part_paint_coverage,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    @dataclass(frozen=True)
    class DummyResult:
        preset: str
        scene: SceneModel

    def polygon(points):
        return PrimitiveGeometry(
            kind="polygon",
            loops=(np.asarray(points, dtype=np.float32),),
        )

    entry = PaletteEntry(
        0,
        (1,),
        1,
        np.asarray([50.0, 0.0, 0.0]),
        (220, 80, 120),
        (0, 0),
    )
    baseline = DummyResult(
        preset="minimal",
        scene=SceneModel(
            30,
            30,
            (
                SceneShape(
                    region_id=1,
                    geometry=polygon([[3,3],[23,3],[23,23],[3,23]]),
                    palette_id=0,
                ),
            ),
            (entry,),
        ),
    )
    collapsed = DummyResult(
        preset="minimal",
        scene=SceneModel(
            30,
            30,
            (
                SceneShape(
                    region_id=1,
                    geometry=polygon([[3,3],[8,3],[8,8],[3,8]]),
                    palette_id=0,
                ),
            ),
            (entry,),
        ),
    )
    part = np.zeros((30, 30), dtype=bool)
    part[3:24, 3:24] = True

    before = _semantic_part_paint_coverage(baseline, part)
    after = _semantic_part_paint_coverage(collapsed, part)
    assert before > 0.90
    assert after < 0.10
    assert _guard_semantic_part_coverage(baseline, collapsed, part) is baseline


def test_semantic_coverage_guard_has_independent_layered_toggle():
    from minimalize_engine.v2.pipeline import LayeredPersonConfig

    assert LayeredPersonConfig().semantic_coverage_guard is True
    assert LayeredPersonConfig(semantic_coverage_guard=False).semantic_coverage_guard is False


def test_semantic_part_paint_coverage_ignores_pure_white_background_but_keeps_near_white():
    from dataclasses import dataclass
    from minimalize_engine.v2.palette import PaletteEntry
    from minimalize_engine.v2.pipeline import (
        SceneModel,
        SceneShape,
        _semantic_part_paint_coverage,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    @dataclass(frozen=True)
    class DummyResult:
        preset: str
        scene: SceneModel

    geometry = PrimitiveGeometry(
        kind="polygon",
        loops=(
            np.asarray(
                [[2,2],[17,2],[17,17],[2,17]],
                dtype=np.float32,
            ),
        ),
    )
    part = np.zeros((20,20), dtype=bool)
    part[2:18,2:18] = True

    def result_for(rgb):
        entry = PaletteEntry(
            0,
            (1,),
            1,
            np.asarray([100.0,0.0,0.0]),
            rgb,
            (0,0),
        )
        shape = SceneShape(region_id=1, geometry=geometry, palette_id=0)
        return DummyResult(
            preset="minimal",
            scene=SceneModel(20,20,(shape,),(entry,)),
        )

    assert _semantic_part_paint_coverage(result_for((255,255,255)), part) == 0.0
    assert _semantic_part_paint_coverage(result_for((254,254,254)), part) > 0.85


def test_semantic_geometric_mass_toggle_is_opt_in():
    from minimalize_engine.v2.pipeline import LayeredPersonConfig

    assert LayeredPersonConfig().semantic_geometric_mass is False
    assert LayeredPersonConfig(semantic_geometric_mass=True).semantic_geometric_mass is True


def test_semantic_geometric_mass_builds_bold_torso_and_keeps_accent():
    from dataclasses import dataclass
    from minimalize_engine.v2.palette import PaletteEntry
    from minimalize_engine.v2.pipeline import (
        SceneModel,
        SceneShape,
        _build_semantic_geometric_mass,
        _semantic_part_paint_coverage,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    @dataclass(frozen=True)
    class DummyResult:
        preset: str
        scene: SceneModel

    def polygon(points):
        return PrimitiveGeometry(
            kind="polygon",
            loops=(np.asarray(points, dtype=np.float32),),
        )

    palette = (
        PaletteEntry(
            0, (1,), 1, np.asarray([45.0,0.0,0.0]), (110,110,110), (0,0)
        ),
        PaletteEntry(
            1, (2,), 2, np.asarray([55.0,65.0,45.0]), (220,40,70), (0,0)
        ),
    )
    baseline = DummyResult(
        preset="minimal",
        scene=SceneModel(
            30,
            30,
            (
                SceneShape(
                    region_id=1,
                    geometry=polygon([[5,5],[8,5],[11,5],[14,5],[14,10],[14,15],[14,20],[14,24],[11,24],[8,24],[5,24],[5,15]]),
                    palette_id=0,
                ),
                SceneShape(
                    region_id=2,
                    geometry=polygon([[14,5],[20,5],[20,24],[14,24]]),
                    palette_id=0,
                ),
                SceneShape(
                    region_id=3,
                    geometry=polygon([[16,8],[20,8],[20,15],[16,15]]),
                    palette_id=1,
                ),
            ),
            palette,
        ),
    )
    part = np.zeros((30,30), dtype=bool)
    part[5:25,5:21] = True

    candidate = _build_semantic_geometric_mass(
        baseline,
        part_name="torso",
        part_mask=part,
    )
    visible = [shape for shape in candidate.scene.shapes if shape.visible]

    assert len(visible) == 3
    assert visible[0].palette_id == 0
    assert visible[0].geometry.kind == "polygon"
    assert len(visible[0].geometry.loops[0]) <= 5
    assert any(shape.palette_id == 1 for shape in visible)
    assert _semantic_part_paint_coverage(candidate, part) > 0.80


def test_semantic_geometric_mass_uses_four_vertex_limb_budget():
    from dataclasses import dataclass
    from minimalize_engine.v2.palette import PaletteEntry
    from minimalize_engine.v2.pipeline import SceneModel, SceneShape, _build_semantic_geometric_mass
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    @dataclass(frozen=True)
    class DummyResult:
        preset: str
        scene: SceneModel

    entry = PaletteEntry(
        0, (1,), 1, np.asarray([45.0,0.0,0.0]), (90,120,150), (0,0)
    )
    geom = PrimitiveGeometry(
        kind="polygon",
        loops=(np.asarray([[6,3],[9,3],[12,3],[12,8],[12,14],[12,20],[12,25],[10,25],[8,25],[6,25],[6,18],[6,10]], dtype=np.float32),),
    )
    baseline = DummyResult(
        preset="minimal",
        scene=SceneModel(
            30,
            30,
            (SceneShape(region_id=1, geometry=geom, palette_id=0),),
            (entry,),
        ),
    )
    part = np.zeros((30,30), dtype=bool)
    cv2.fillPoly(
        part.view(np.uint8),
        [np.asarray([[6,3],[9,3],[12,3],[12,8],[12,14],[12,20],[12,25],[10,25],[8,25],[6,25],[6,18],[6,10]], dtype=np.int32)],
        1,
    )

    candidate = _build_semantic_geometric_mass(
        baseline,
        part_name="left_arm",
        part_mask=part,
    )
    visible = [shape for shape in candidate.scene.shapes if shape.visible]
    assert len(visible) == 1
    assert visible[0].geometry.kind == "polygon"
    assert len(visible[0].geometry.loops[0]) <= 4



def test_semantic_geometric_mass_guard_is_stricter_than_general_coverage_guard():
    from minimalize_engine.v2.pipeline import _semantic_geometric_mass_is_safe

    assert _semantic_geometric_mass_is_safe(0.80, 0.76)
    assert _semantic_geometric_mass_is_safe(0.785, 0.738)
    assert not _semantic_geometric_mass_is_safe(0.59, 0.54)
    assert not _semantic_geometric_mass_is_safe(0.23, 0.18)


def test_semantic_mass_cutout_fill_guard_separates_small_cleanup_from_large_cutout_loss():
    from minimalize_engine.v2.pipeline import _semantic_mass_cutout_fill_is_safe

    assert _semantic_mass_cutout_fill_is_safe(1745, 33)
    assert not _semantic_mass_cutout_fill_is_safe(1924, 131)
    assert _semantic_mass_cutout_fill_is_safe(100, 3)


def test_semantic_geometric_mass_final_guard_requires_real_vertex_savings():
    from dataclasses import dataclass
    from minimalize_engine.v2.palette import PaletteEntry
    from minimalize_engine.v2.pipeline import (
        SceneModel, SceneShape, _semantic_geometric_mass_final_is_simpler,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    @dataclass(frozen=True)
    class DummyResult:
        scene: SceneModel

    entry = PaletteEntry(
        0, (1,), 1, np.asarray([45.0,0.0,0.0]), (120,120,120), (0,0)
    )

    def result(points):
        geometry = PrimitiveGeometry(
            kind="polygon",
            loops=(np.asarray(points, dtype=np.float32),),
        )
        return DummyResult(
            SceneModel(
                30, 30,
                (SceneShape(region_id=1, geometry=geometry, palette_id=0),),
                (entry,),
            )
        )

    baseline = result([[2,2],[5,2],[8,2],[11,2],[14,2],[14,8],[14,14],[11,14],[8,14],[5,14],[2,14],[2,8]])
    candidate = result([[2,2],[14,2],[14,14],[2,14]])
    weak = result([[2,2],[8,2],[14,2],[14,14],[8,14],[2,14],[2,8]])

    assert _semantic_geometric_mass_final_is_simpler(baseline, candidate)
    assert not _semantic_geometric_mass_final_is_simpler(baseline, weak)


def test_semantic_geometric_mass_final_guard_rejects_extra_visible_shape():
    from dataclasses import dataclass, replace
    from minimalize_engine.v2.palette import PaletteEntry
    from minimalize_engine.v2.pipeline import (
        SceneModel, SceneShape, _semantic_geometric_mass_final_is_simpler,
    )
    from minimalize_engine.v2.primitive import PrimitiveGeometry

    @dataclass(frozen=True)
    class DummyResult:
        scene: SceneModel

    entry = PaletteEntry(
        0, (1,), 1, np.asarray([45.0,0.0,0.0]), (120,120,120), (0,0)
    )

    def poly(region_id, points):
        return SceneShape(
            region_id=region_id,
            geometry=PrimitiveGeometry(
                kind="polygon",
                loops=(np.asarray(points, dtype=np.float32),),
            ),
            palette_id=0,
        )

    baseline = DummyResult(
        SceneModel(
            30, 30,
            (poly(1, [[2,2],[6,2],[10,2],[14,2],[14,14],[10,14],[6,14],[2,14],[2,8]]),),
            (entry,),
        )
    )
    candidate = DummyResult(
        SceneModel(
            30, 30,
            (
                poly(1, [[2,2],[14,2],[14,14],[2,14]]),
                poly(2, [[16,4],[20,4],[20,8],[16,8]]),
            ),
            (entry,),
        )
    )

    assert not _semantic_geometric_mass_final_is_simpler(baseline, candidate)
