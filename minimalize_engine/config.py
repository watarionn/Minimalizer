from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class ImportanceWeights:
    area: float = 0.45
    contrast: float = 0.25
    rarity: float = 0.20
    structure: float = 0.10


@dataclass(frozen=True)
class MinimalizeConfig:
    abstraction_level: int = 4
    analysis_max_side: int = 640
    pre_smoothing: float = 0.70
    palette_colors: int = 6
    min_region_area_ratio: float = 0.003
    contour_epsilon_ratio: float = 0.025
    merge_distance_ratio: float = 0.015
    merge_color_delta_e: float = 12.0
    target_max_shapes: int = 50
    preserve_accents: bool = True
    accent_repeat_min: int = 3
    importance_weights: ImportanceWeights = field(default_factory=ImportanceWeights)
    rectangle_fit_threshold: float = 0.85
    circle_fit_threshold: float = 0.78

    # v0.1.1 shape-quality controls
    split_large_regions: bool = True
    large_region_area_ratio: float = 0.020
    split_open_radius_ratio: float = 0.006

    role_aware_consolidation: bool = True
    structure_close_ratio_x: float = 0.018
    structure_close_ratio_y: float = 0.010
    water_close_ratio_x: float = 0.028
    water_close_ratio_y: float = 0.008

    enable_silhouette_reconstruction: bool = True
    skyline_merge_ratio_x: float = 0.040
    skyline_merge_ratio_y: float = 0.020
    water_band_merge_ratio_x: float = 0.080
    water_band_merge_ratio_y: float = 0.020
    boat_merge_ratio_x: float = 0.020
    boat_merge_ratio_y: float = 0.012

    # v0.1.5 composition-layer controls
    enable_layer_composition: bool = True
    enable_macro_underlays: bool = True
    accent_layer_ratio: float = 0.16
    foreground_layer_ratio: float = 0.18
    water_layer_ratio: float = 0.10
    skyline_layer_ratio: float = 0.24
    midground_layer_ratio: float = 0.32
    water_underlay_strength: float = 0.24
    skyline_underlay_strength: float = 0.88

    # v0.1.6 composition-skeleton controls
    enable_composition_skeleton: bool = True
    skeleton_center_min_ratio: float = 0.30
    skeleton_center_max_ratio: float = 0.70
    skeleton_min_corridor_ratio: float = 0.08
    skeleton_max_corridor_ratio: float = 0.24
    skeleton_valley_ratio: float = 0.72
    skeleton_balance_layers: bool = True
    skeleton_clip_skyline: bool = True
    skeleton_water_corridor: bool = True

    # v0.2.0 quality bundle
    respect_source_alpha: bool = True
    enable_multiscale_analysis: bool = True
    multiscale_weight: float = 0.18
    enable_pseudo_semantics: bool = True
    enable_design_primitives: bool = True
    enable_design_palette: bool = True
    palette_harmony_strength: float = 0.20
    enable_pattern_recognition: bool = True
    pattern_min_count: int = 3
    pattern_alignment_tolerance: float = 0.10
    enable_quality_evaluation: bool = True
    enable_auto_retry: bool = True
    auto_retry_max: int = 2
    quality_min_score: float = 0.58
    quality_target_tiny_shape_ratio: float = 0.34
    quality_target_vertex_per_shape: float = 9.0

    # Phase 14 Global Minimal Shape Cleanup
    enable_global_shape_cleanup: bool = True
    cleanup_thin_aspect_ratio: float = 8.0
    cleanup_thin_short_side_ratio: float = 0.022
    cleanup_thin_max_area_ratio: float = 0.0045
    cleanup_thin_rectangle_short_side_ratio: float = 0.012
    cleanup_thin_rectangle_aspect_ratio: float = 4.5
    cleanup_thin_rectangle_max_area_ratio: float = 0.0060
    cleanup_thin_rectangle_max_importance: float = 0.97
    cleanup_micro_area_ratio: float = 0.00016
    cleanup_micro_max_importance: float = 0.52
    cleanup_remove_duplicates: bool = False
    cleanup_duplicate_overlap: float = 0.97
    cleanup_duplicate_color_distance: float = 4.0
    cleanup_merge_adjacent: bool = True
    cleanup_merge_gap_ratio: float = 0.008
    cleanup_merge_color_distance: float = 7.0
    cleanup_merge_max_area_ratio: float = 0.018
    cleanup_merge_max_hull_inflation: float = 1.08
    cleanup_role_fragment_merge: bool = False
    cleanup_role_fragment_gap_ratio: float = 0.002
    cleanup_role_fragment_color_distance: float = 3.0
    cleanup_role_fragment_max_area_ratio: float = 0.010
    cleanup_role_fragment_max_combined_area_ratio: float = 0.080
    cleanup_role_fragment_max_hull_inflation: float = 1.070
    cleanup_simplify_polygons: bool = True
    cleanup_simplify_epsilon_ratio: float = 0.012
    cleanup_simplify_max_area_error: float = 0.045
    cleanup_simplify_min_iou: float = 0.985
    cleanup_promote_primitives: bool = True
    cleanup_promote_rectangle_iou: float = 0.985
    cleanup_promote_ellipse_iou: float = 0.945
    cleanup_promote_max_area_ratio: float = 0.080
    cleanup_remove_isolated: bool = True
    cleanup_isolated_max_area_ratio: float = 0.0008
    cleanup_isolated_min_distance_ratio: float = 0.075
    cleanup_isolated_max_importance: float = 0.38

    # Phase 14.3 Global Shape Value
    enable_global_shape_value: bool = True
    shape_value_min_score: float = 0.400
    shape_value_max_remove_area_ratio: float = 0.006
    shape_value_max_remove_importance: float = 0.64
    shape_value_neighbor_distance_ratio: float = 0.035
    shape_value_redundancy_overlap: float = 0.82
    shape_value_redundancy_color_distance: float = 16.0
    shape_value_near_background_max_color_distance: float = 12.0
    shape_value_near_background_max_area_ratio: float = 0.007
    shape_value_near_background_max_importance: float = 0.40

    # v0.3.0 Character Structure Engine
    enable_character_structure: bool = True
    enable_body_primitives: bool = True
    enable_hand_analysis: bool = True
    enable_hand_primitives: bool = True
    character_hand_max_shapes: int = 2
    character_hand_min_confidence: float = 0.30
    enable_hand_geometry_validation: bool = True
    character_hand_geometry_min_connection: float = 0.72
    character_hand_geometry_min_direction: float = 0.58
    character_hand_geometry_min_holding_contact: float = 0.45
    enable_hand_validation: bool = True
    character_hand_validation_min_score: float = 0.42
    character_hand_validation_unknown_min_score: float = 0.42
    enable_hand_quality: bool = True
    character_quality_min_hand: float = 0.72
    character_quality_min_hand_retention: float = 0.72
    character_quality_min_hand_geometry: float = 0.72
    enable_limb_geometry_refine: bool = True
    character_limb_refine_min_iou: float = 0.46
    enable_hair_body_guard: bool = True
    character_hair_body_overlap_trigger: float = 0.44
    character_hair_body_max_remove_ratio: float = 0.12
    enable_pose_proxy: bool = True
    enable_face_rules: bool = True
    # Dedicated face-part rendering is opt-in from rc2. Face analysis can stay on
    # without drawing a floating face ellipse / eyes / mouth.
    enable_face_primitives: bool = False
    enable_face_validation: bool = True
    enable_face_geometry_quality: bool = True
    enable_face_contour_fit: bool = True
    enable_face_boundary_guard: bool = True
    enable_face_identity_analysis: bool = True
    enable_face_identity_budget: bool = True
    enable_face_identity_validation: bool = True
    face_identity_min_score: float = 0.72
    enable_hair_rules: bool = True
    enable_outfit_rules: bool = True
    enable_prop_rules: bool = True

    # Finishing-phase character optimization
    enable_adaptive_character_budget: bool = True
    enable_outfit_structure_quality: bool = True
    character_quality_min_outfit_structure: float = 0.46
    enable_prop_symbol_quality: bool = True
    character_quality_min_prop_symbol: float = 0.64
    enable_character_wide_identity: bool = True
    character_quality_min_wide_identity: float = 0.68

    enable_character_layout: bool = True
    enable_character_quality: bool = True
    enable_character_auto_retry: bool = True
    character_preset: str = "auto"

    character_face_priority: float = 1.25
    character_hair_priority: float = 1.15
    character_prop_priority: float = 1.10

    character_face_abstraction: float = 0.65
    character_hair_abstraction: float = 0.75
    character_body_abstraction: float = 0.85
    character_limb_abstraction: float = 0.95
    character_accessory_abstraction: float = 1.15

    character_min_face_shapes: int = 3
    character_face_validation_threshold: float = 0.52
    character_min_hair_shapes: int = 3

    # Phase 9 Character-specific Quality / Retry
    character_retry_threshold: float = 0.76
    character_max_retries: int = 1
    character_quality_min_face_retention: float = 0.72
    character_quality_min_face_geometry: float = 0.72
    face_geometry_area_ratio_tolerance: float = 0.30
    face_geometry_center_tolerance: float = 0.18
    face_geometry_aspect_tolerance: float = 0.28
    face_geometry_eye_span_tolerance: float = 0.30
    face_geometry_mouth_offset_tolerance: float = 0.26
    face_contour_shrink_strength: float = 0.22
    face_contour_chin_trim_strength: float = 0.18
    face_contour_forehead_expand_strength: float = 0.10

    # Phase 10.4 Face-aware Retry correction knobs. Defaults are neutral.
    # Retry may change these deterministically from Face Geometry diagnostics.
    face_contour_width_scale: float = 1.00
    face_contour_height_scale: float = 1.00
    face_contour_center_x_shift_ratio: float = 0.00
    face_contour_center_y_shift_ratio: float = 0.00

    character_quality_min_face_boundary: float = 0.72
    face_boundary_guard_strength: float = 0.65
    face_boundary_eye_protect_strength: float = 0.80
    face_boundary_cheek_protect_strength: float = 0.72
    face_boundary_chin_protect_strength: float = 0.85
    face_boundary_forehead_allowance: float = 0.18
    character_quality_min_body_readability: float = 0.80
    character_quality_min_limb_separation: float = 0.62
    character_quality_min_prop_retention: float = 0.72
    character_quality_min_layout: float = 0.72
    character_quality_min_geometry_fidelity: float = 0.40
    character_retry_analysis_scale: float = 1.18
    character_retry_shape_growth: float = 1.10
    character_limb_width_scale: float = 1.00

    character_hint_importance_strength: float = 0.12

    # Phase 8 Character Layout
    character_layout_headroom_ratio: float = 0.055
    character_layout_footroom_ratio: float = 0.040
    character_layout_side_margin_ratio: float = 0.050
    character_layout_visual_center_strength: float = 0.72
    character_layout_pose_bias_strength: float = 0.060
    character_layout_max_scale_up: float = 1.10
    character_layout_safety_margin_ratio: float = 0.012

    major_shape_iou_target: float = 0.80
    medium_shape_iou_target: float = 0.72
    small_shape_iou_target: float = 0.62
    max_major_epsilon_ratio: float = 0.015

    line_mode: str = "low"       # none / low / standard
    background_mode: str = "source"  # source / white / transparent / custom
    background_color: tuple[int, int, int] = (245, 242, 233)
    canvas_padding: float = 0.05
    random_seed: int = 42
    debug_mode: bool = False
    debug_output_dir: str | None = None

    @classmethod
    def from_level(cls, level: int, **overrides) -> "MinimalizeConfig":
        if level not in {1, 2, 3, 4, 5}:
            raise ValueError("abstraction_level must be 1..5")

        table = {
            1: dict(analysis_max_side=1024, pre_smoothing=0.20, palette_colors=16,
                    min_region_area_ratio=0.0003, contour_epsilon_ratio=0.004,
                    merge_distance_ratio=0.002, merge_color_delta_e=4.0,
                    target_max_shapes=180, line_mode="standard"),
            2: dict(analysis_max_side=896, pre_smoothing=0.35, palette_colors=12,
                    min_region_area_ratio=0.0007, contour_epsilon_ratio=0.008,
                    merge_distance_ratio=0.004, merge_color_delta_e=6.0,
                    target_max_shapes=120, line_mode="standard"),
            3: dict(analysis_max_side=768, pre_smoothing=0.50, palette_colors=8,
                    min_region_area_ratio=0.0015, contour_epsilon_ratio=0.015,
                    merge_distance_ratio=0.008, merge_color_delta_e=9.0,
                    target_max_shapes=80, line_mode="low"),
            4: dict(analysis_max_side=640, pre_smoothing=0.70, palette_colors=6,
                    min_region_area_ratio=0.0030, contour_epsilon_ratio=0.025,
                    merge_distance_ratio=0.015, merge_color_delta_e=12.0,
                    target_max_shapes=50, line_mode="low"),
            5: dict(analysis_max_side=512, pre_smoothing=0.85, palette_colors=4,
                    min_region_area_ratio=0.0060, contour_epsilon_ratio=0.040,
                    merge_distance_ratio=0.025, merge_color_delta_e=16.0,
                    target_max_shapes=30, line_mode="none"),
        }
        values = dict(abstraction_level=level, **table[level])
        values.update(overrides)
        return cls(**values)

    def with_overrides(self, **kwargs) -> "MinimalizeConfig":
        return replace(self, **kwargs)
