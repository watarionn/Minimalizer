from __future__ import annotations
from pathlib import Path
import json
import cv2, numpy as np
from .config import MinimalizeConfig
from .models import Scene
from .io.image_loader import load_image_data, composite_alpha
from .preprocess.resize import resize_for_analysis
from .preprocess.smoothing import apply_smoothing
from .palette.quantize import quantize_colors
from .palette.design_palette import build_design_palette, apply_design_palette
from .regions.extract import extract_regions
from .regions.importance import calculate_importance
from .regions.merge import merge_similar_regions
from .regions.split import split_large_regions
from .regions.cleanup import filter_regions
from .regions.roles import assign_region_roles, filter_reflection_noise
from .regions.consolidate import consolidate_regions_by_role
from .regions.reconstruct import reconstruct_silhouettes
from .geometry.contours import attach_contours
from .geometry.primitives import regions_to_shapes
from .geometry.lines import detect_structural_lines
from .composition.background import choose_background_region, choose_background_like_region_ids, resolve_background
from .composition.layers import assign_layers
from .composition.layer_plan import assign_composition_layers, make_layer_budget, select_regions_by_layer, count_layers
from .composition.macro_layers import build_macro_layer_shapes
from .composition.subject_base import build_subject_base_shape
from .composition.skeleton import detect_composition_skeleton, detect_subject_skeleton
from .composition.padding import apply_padding
from .analysis.multiscale import analyze_multiscale, apply_multiscale_scores
from .analysis.semantics import classify_pseudo_semantics
from .analysis.patterns import detect_patterns, regularize_pattern_shapes
from .analysis.quality import evaluate_scene
from .analysis.shape_cleanup import cleanup_minimal_shapes
from .analysis.shape_value import evaluate_global_shape_value
from .utils.debug import debug_dir, save_rgb
from .character.pipeline import analyze_character_structure
from .character.primitives import (
    character_structure_to_shapes,
    suppress_generic_character_shapes,
)
from .character.layout import (
    plan_character_layout,
    apply_character_layout,
    layout_metrics,
    render_character_layout_preview,
    transform_layout_reference,
)
from .character.quality import (
    evaluate_character_scene,
    character_retry_needed,
    character_selection_score,
)
from .character.retry import suggest_character_retry_config
from .character.face_boundary import render_face_boundary_structure_overlay
from .character.debug import save_character_debug_overlay, save_character_detail_debug_overlay, save_character_outfit_debug_overlay, save_character_prop_debug_overlay, save_character_body_debug_overlay, save_face_diagnostics_overlay, save_character_hand_debug_overlay, save_character_hand_geometry_overlay, save_character_hand_validation_overlay
from .character.face_diagnostics import build_face_diagnostics_report
from .character.outfit_quality import evaluate_outfit_quality
from .character.prop_symbol_quality import evaluate_prop_symbol_quality
from .character.whole_identity import evaluate_character_wide_identity
from .character.rinka_macro import RinkaMacroReport, build_rinka_macro_partition

def _prepare_source(image_or_path,config):
    if isinstance(image_or_path,(str,Path)):
        d=load_image_data(image_or_path);raw=d.rgb;alpha=d.alpha
    else:
        a=np.asarray(image_or_path)
        if a.ndim!=3 or a.shape[2] not in {3,4}:raise ValueError("image array must be HxWx3 or HxWx4")
        # Keep RGB input zero-copy here. The pipeline only reads this array,
        # and resize/smoothing create their own working buffers. Avoiding an
        # eager duplicate matters for 4K/8K inputs.
        raw=a[:,:,:3];alpha=a[:,:,3].copy() if a.shape[2]==4 else None
    has=config.respect_source_alpha and alpha is not None and bool(np.any(alpha<250))
    source=composite_alpha(raw,alpha,config.background_color) if has else raw
    return raw,source,alpha if has else None,has

def _minimalize_once(image_or_path,config):
    raw,source,alpha,has_alpha=_prepare_source(image_or_path,config)
    working,scale=resize_for_analysis(source,config.analysis_max_side);h,w=working.shape[:2]
    valid=None;work_alpha=None;subject=False
    if has_alpha:
        work_alpha=cv2.resize(alpha,(w,h),interpolation=cv2.INTER_AREA);valid=(work_alpha>=16).astype(np.uint8)*255
        occ=float((valid>0).mean());subject=.025<=occ<=.96

    ddir=debug_dir(config)
    if ddir:save_rgb(ddir/"01_resized.png",working)
    smoothed=apply_smoothing(working,config.pre_smoothing)
    if ddir:save_rgb(ddir/"02_smoothed.png",smoothed)
    quantized,labels,palette=quantize_colors(smoothed,config.palette_colors,config.random_seed,valid_mask=valid)
    if ddir:save_rgb(ddir/"03_quantized.png",quantized)

    regions=extract_regions(labels,palette,valid_mask=valid)
    regions=calculate_importance(regions,palette,config.importance_weights,config.preserve_accents,config.min_region_area_ratio,config.accent_repeat_min)
    multi=None
    if config.enable_multiscale_analysis:
        multi=analyze_multiscale(smoothed);regions=apply_multiscale_scores(regions,multi,config.multiscale_weight)
    regions=merge_similar_regions(regions,working.shape,config.merge_distance_ratio,config.merge_color_delta_e)
    if config.split_large_regions:
        regions=split_large_regions(regions,working.shape,area_ratio_threshold=config.large_region_area_ratio,open_radius_ratio=config.split_open_radius_ratio,min_piece_ratio=max(.0008,config.min_region_area_ratio*.5))

    if subject:
        background_ids=set()
        background=None if config.background_mode in {"source","transparent"} else (255,255,255) if config.background_mode=="white" else tuple(config.background_color)
    else:
        br=choose_background_region(regions);background_ids=choose_background_like_region_ids(regions,working.shape,br);background=resolve_background(config.background_mode,br,config.background_color)

    regions=assign_region_roles(regions,working.shape,subject_mode=subject)
    skeleton=None
    if config.enable_composition_skeleton:
        if subject and work_alpha is not None:skeleton=detect_subject_skeleton(valid,working.shape)
        else:
            sr=[r for r in regions if r.id not in background_ids]
            skeleton=detect_composition_skeleton(sr,working.shape,center_min_ratio=config.skeleton_center_min_ratio,center_max_ratio=config.skeleton_center_max_ratio,min_corridor_ratio=config.skeleton_min_corridor_ratio,max_corridor_ratio=config.skeleton_max_corridor_ratio,valley_ratio=config.skeleton_valley_ratio)

    if config.role_aware_consolidation:
        regions=consolidate_regions_by_role(regions,working.shape,structure_close_ratio_x=config.structure_close_ratio_x,structure_close_ratio_y=config.structure_close_ratio_y,water_close_ratio_x=config.water_close_ratio_x,water_close_ratio_y=config.water_close_ratio_y)
        regions=assign_region_roles(regions,working.shape,subject_mode=subject)
        if multi is not None:regions=apply_multiscale_scores(regions,multi,config.multiscale_weight)

    if config.enable_pseudo_semantics:regions=classify_pseudo_semantics(regions,working.shape,subject_mode=subject)
    pal_entries=[];pal_map={}
    if config.enable_design_palette:
        pal_entries,pal_map=build_design_palette(palette,harmony_strength=config.palette_harmony_strength,has_background=not subject)
        regions=apply_design_palette(regions,pal_map)

    macro_source=list(regions)
    if config.enable_silhouette_reconstruction and not subject:
        macro_source=reconstruct_silhouettes(list(regions),working.shape,skyline_merge_ratio_x=config.skyline_merge_ratio_x,skyline_merge_ratio_y=config.skyline_merge_ratio_y,water_band_merge_ratio_x=config.water_band_merge_ratio_x,water_band_merge_ratio_y=config.water_band_merge_ratio_y,boat_merge_ratio_x=config.boat_merge_ratio_x,boat_merge_ratio_y=config.boat_merge_ratio_y,min_area_ratio=max(.001,config.min_region_area_ratio*.6))
        macro_source=assign_region_roles(macro_source,working.shape,subject_mode=False)
        if config.enable_pseudo_semantics:macro_source=classify_pseudo_semantics(macro_source,working.shape,subject_mode=False)
        if pal_map:macro_source=apply_design_palette(macro_source,pal_map)

    regions=assign_region_roles(regions,working.shape,subject_mode=subject)
    if config.enable_pseudo_semantics:regions=classify_pseudo_semantics(regions,working.shape,subject_mode=subject)

    character_structure=None
    character_budget=None
    if subject and valid is not None and config.enable_character_structure:
        character_structure,character_budget,regions=analyze_character_structure(
            working,
            valid,
            regions,
            preset=config.character_preset,
            total_shape_budget=max(12,config.target_max_shapes),
            enable_pose_proxy=config.enable_pose_proxy,
            enable_prop_rules=config.enable_prop_rules,
            enable_face_validation=config.enable_face_validation,
            face_validation_threshold=config.character_face_validation_threshold,
            enable_face_contour_fit=config.enable_face_contour_fit,
            face_contour_shrink_strength=config.face_contour_shrink_strength,
            face_contour_chin_trim_strength=config.face_contour_chin_trim_strength,
            face_contour_forehead_expand_strength=config.face_contour_forehead_expand_strength,
            face_contour_width_scale=config.face_contour_width_scale,
            face_contour_height_scale=config.face_contour_height_scale,
            face_contour_center_x_shift_ratio=config.face_contour_center_x_shift_ratio,
            face_contour_center_y_shift_ratio=config.face_contour_center_y_shift_ratio,
            enable_face_boundary_guard=config.enable_face_boundary_guard,
            face_boundary_guard_strength=config.face_boundary_guard_strength,
            face_boundary_eye_protect_strength=config.face_boundary_eye_protect_strength,
            face_boundary_cheek_protect_strength=config.face_boundary_cheek_protect_strength,
            face_boundary_chin_protect_strength=config.face_boundary_chin_protect_strength,
            face_boundary_forehead_allowance=config.face_boundary_forehead_allowance,
            prop_source_rgb=source,
            prop_source_alpha=alpha if has_alpha else None,
            importance_strength=config.character_hint_importance_strength,
            enable_adaptive_character_budget=config.enable_adaptive_character_budget,
        )
        if ddir:
            save_character_debug_overlay(
                ddir/"04_character_parts.png",
                working,
                character_structure,
            )
            boundary_meta = character_structure.metadata.get("face_boundary") or {}
            if boundary_meta.get("enabled", False):
                save_rgb(
                    ddir/"11_face_boundary.png",
                    render_face_boundary_structure_overlay(
                        working,
                        character_structure,
                    ),
                )
                (ddir/"11_face_boundary.json").write_text(
                    json.dumps(boundary_meta, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

    if not subject:
        pbr=choose_background_region(regions);background_ids=choose_background_like_region_ids(regions,working.shape,pbr);regions=filter_reflection_noise(regions,target_keep=3)

    line_budget={"none":0,"low":8,"standard":14}.get(config.line_mode,8);macro_allowed=config.enable_layer_composition and config.enable_macro_underlays and not subject
    character_detail_reserved=0
    if character_budget is not None:
        adaptive_meta = (character_budget.metadata or {}).get("adaptive") or {}
        legacy_reservation = adaptive_meta.get("before") or {}
        # Adaptive part budgeting must not silently convert every freed
        # character-detail slot into generic fragments. Keep the composition
        # reservation anchored to the pre-adaptive plan while the dedicated
        # builders are free to use fewer identity-bearing Shapes.
        reserve_face = int(legacy_reservation.get("face", character_budget.reserved_face))
        reserve_hair = int(legacy_reservation.get("hair", character_budget.reserved_hair))
        reserve_outfit = int(legacy_reservation.get("outfit", character_budget.reserved_outfit))
        reserve_props = int(legacy_reservation.get("prop", character_budget.reserved_props))
        if config.enable_body_primitives:
            character_detail_reserved+=character_budget.reserved_body
            if config.enable_hand_analysis and config.enable_hand_primitives:
                character_detail_reserved+=max(0, int(config.character_hand_max_shapes))
        if config.enable_face_rules and config.enable_face_primitives:
            character_detail_reserved+=reserve_face
        if config.enable_hair_rules:
            character_detail_reserved+=reserve_hair
        if config.enable_outfit_rules:
            character_detail_reserved+=reserve_outfit
        if config.enable_prop_rules:
            character_detail_reserved+=reserve_props
    region_budget=max(5,config.target_max_shapes-line_budget-(5 if macro_allowed else 0)-character_detail_reserved)
    regions=filter_regions(regions,config.min_region_area_ratio,max(region_budget,region_budget*2),background_ids)
    regions=assign_composition_layers(regions,working.shape);macro_source=assign_composition_layers(macro_source,working.shape)
    if config.enable_layer_composition:
        lb=make_layer_budget(region_budget,skyline_ratio=.08 if subject else config.skyline_layer_ratio,midground_ratio=.48 if subject else config.midground_layer_ratio,water_ratio=.04 if subject else config.water_layer_ratio,foreground_ratio=.24 if subject else config.foreground_layer_ratio,accent_ratio=.16 if subject else config.accent_layer_ratio)
        regions=select_regions_by_layer(regions,lb,skeleton,balance_sides=config.skeleton_balance_layers and not subject)

    patterns=detect_patterns(regions,working.shape,min_count=config.pattern_min_count,alignment_tolerance=config.pattern_alignment_tolerance) if config.enable_pattern_recognition else []
    regions=attach_contours(regions)
    shapes=regions_to_shapes(regions,config.contour_epsilon_ratio,config.rectangle_fit_threshold,config.circle_fit_threshold,major_iou_target=config.major_shape_iou_target,medium_iou_target=config.medium_shape_iou_target,small_iou_target=config.small_shape_iou_target,max_major_epsilon_ratio=config.max_major_epsilon_ratio,enable_design_primitives=config.enable_design_primitives)
    if patterns:shapes=regularize_pattern_shapes(shapes,patterns)

    character_detail_shapes=[]
    character_detail_metadata={}
    character_shape_result=None
    if character_structure is not None and character_budget is not None:
        character_shape_result=character_structure_to_shapes(
            working,
            character_structure,
            regions,
            character_budget,
            enable_body_primitives=config.enable_body_primitives,
            enable_hand_analysis=config.enable_hand_analysis,
            enable_hand_primitives=config.enable_hand_primitives,
            hand_max_shapes=config.character_hand_max_shapes,
            hand_min_confidence=config.character_hand_min_confidence,
            enable_hand_geometry_validation=config.enable_hand_geometry_validation,
            hand_geometry_min_connection=config.character_hand_geometry_min_connection,
            hand_geometry_min_direction=config.character_hand_geometry_min_direction,
            hand_geometry_min_holding_contact=config.character_hand_geometry_min_holding_contact,
            enable_hand_validation=config.enable_hand_validation,
            hand_validation_min_score=config.character_hand_validation_min_score,
            hand_validation_unknown_min_score=config.character_hand_validation_unknown_min_score,
            enable_limb_geometry_refine=config.enable_limb_geometry_refine,
            limb_refine_min_iou=config.character_limb_refine_min_iou,
            enable_hair_body_guard=config.enable_hair_body_guard,
            hair_body_overlap_trigger=config.character_hair_body_overlap_trigger,
            hair_body_max_remove_ratio=config.character_hair_body_max_remove_ratio,
            limb_width_scale=config.character_limb_width_scale,
            enable_face_rules=config.enable_face_rules,
            enable_face_primitives=config.enable_face_primitives,
            enable_face_identity_analysis=config.enable_face_identity_analysis,
            enable_face_identity_budget=config.enable_face_identity_budget,
            enable_face_identity_validation=config.enable_face_identity_validation,
            face_identity_min_score=config.face_identity_min_score,
            abstraction_level=config.abstraction_level,
            enable_hair_rules=config.enable_hair_rules,
            enable_outfit_rules=config.enable_outfit_rules,
            enable_prop_rules=config.enable_prop_rules,
        )
        character_detail_shapes=character_shape_result.shapes
        character_detail_metadata=character_shape_result.metadata
        if character_detail_shapes:
            shapes=suppress_generic_character_shapes(
                shapes,
                character_shape_result,
            )
            shapes.extend(character_detail_shapes)
        if ddir:
            save_character_detail_debug_overlay(
                ddir/"05_character_face_hair.png",
                working,
                character_detail_metadata,
            )
            identity_signals = (
                character_detail_metadata.get("face", {}).get("identity_signals")
            )
            if identity_signals is not None:
                (ddir/"13_face_identity_signals.json").write_text(
                    json.dumps(identity_signals, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            identity_budget = (
                character_detail_metadata.get("face", {}).get("identity_budget")
            )
            if identity_budget is not None:
                (ddir/"14_face_identity_budget.json").write_text(
                    json.dumps(identity_budget, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            identity_rendering = (
                character_detail_metadata.get("face", {}).get("identity_rendering")
            )
            if identity_rendering is not None:
                (ddir/"15_face_identity_primitives.json").write_text(
                    json.dumps(identity_rendering, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            identity_validation = (
                character_detail_metadata.get("face", {}).get("identity_validation")
            )
            if identity_validation is not None:
                (ddir/"16_face_identity_validation.json").write_text(
                    json.dumps(identity_validation, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            save_character_outfit_debug_overlay(
                ddir/"06_character_outfit.png",
                working,
                character_detail_metadata,
            )
            save_character_prop_debug_overlay(
                ddir/"07_character_props.png",
                working,
                character_detail_metadata,
            )
            save_character_body_debug_overlay(
                ddir/"08_character_body.png",
                working,
                character_detail_metadata,
            )
            hand_analysis = (
                character_detail_metadata.get("hands", {}).get("analysis")
            )
            if hand_analysis is not None:
                (ddir/"18_character_hands.json").write_text(
                    json.dumps(hand_analysis, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                save_character_hand_debug_overlay(
                    ddir/"18_character_hands.png",
                    working,
                    character_detail_metadata,
                )
            hand_rendering = (
                character_detail_metadata.get("hands", {}).get("rendering")
            )
            if hand_rendering is not None:
                (ddir/"19_character_hand_primitives.json").write_text(
                    json.dumps(hand_rendering, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            hand_geometry = (character_detail_metadata.get("hands") or {}).get("geometry_validation")
            if hand_geometry is not None:
                (ddir/"20_character_hand_geometry.json").write_text(
                    json.dumps(hand_geometry, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                save_character_hand_geometry_overlay(
                    ddir/"20_character_hand_geometry.png",
                    working,
                    character_detail_metadata,
                )
            hand_validation = (character_detail_metadata.get("hands") or {}).get("candidate_validation")
            if hand_validation is not None:
                (ddir/"21_character_hand_validation.json").write_text(
                    json.dumps(hand_validation, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                save_character_hand_validation_overlay(
                    ddir/"21_character_hand_validation.png",
                    working,
                    character_detail_metadata,
                )

    rinka_macro_report = RinkaMacroReport()
    rinka_macro_active = (
        character_structure is not None
        and config.enable_rinka_macro_partition
        and (not config.rinka_macro_rescue_only or config.rinka_macro_rescue_active)
    )
    if rinka_macro_active and character_structure is not None:
        shapes, rinka_macro_report = build_rinka_macro_partition(
            working,
            character_structure,
            shapes,
        )

    macro_shapes=[];subject_base=[]
    if subject and valid is not None and not rinka_macro_report.enabled:
        subject_base=build_subject_base_shape(valid,[e.output_rgb for e in pal_entries] if pal_entries else [p.rgb for p in palette]);shapes.extend(subject_base)
    if macro_allowed:
        macro_shapes=build_macro_layer_shapes(macro_source,working.shape,background,water_strength=config.water_underlay_strength,skyline_strength=config.skyline_underlay_strength,skeleton=skeleton,clip_skyline=config.skeleton_clip_skyline,water_corridor=config.skeleton_water_corridor);shapes.extend(macro_shapes)
    shapes.extend(detect_structural_lines(smoothed,config.line_mode));shapes=assign_layers(shapes)

    character_layout_plan=None
    character_layout_metrics={}
    quality_reference=working
    quality_subject_mask=valid if subject else None

    if (
        subject
        and character_structure is not None
        and config.enable_character_layout
    ):
        character_layout_plan=plan_character_layout(
            character_structure,
            shapes,
            w,
            h,
            headroom_ratio=config.character_layout_headroom_ratio,
            footroom_ratio=config.character_layout_footroom_ratio,
            side_margin_ratio=max(
                config.character_layout_side_margin_ratio,
                config.canvas_padding,
            ),
            visual_center_strength=config.character_layout_visual_center_strength,
            pose_bias_strength=config.character_layout_pose_bias_strength,
            max_scale_up=config.character_layout_max_scale_up,
            safety_margin_ratio=config.character_layout_safety_margin_ratio,
        )
        shapes=apply_character_layout(
            shapes,
            character_layout_plan,
        )
        character_layout_metrics=layout_metrics(
            character_layout_plan,
            w,
            h,
        )
        if valid is not None:
            quality_reference,quality_subject_mask=transform_layout_reference(
                working,
                valid,
                character_layout_plan,
            )
        if ddir:
            save_rgb(
                ddir/"09_character_layout.png",
                render_character_layout_preview(
                    working,
                    character_structure,
                    character_layout_plan,
                ),
            )
    else:
        shapes=apply_padding(shapes,w,h,config.canvas_padding)

    # Global Shape Value: remove generic shapes that contribute too little to
    # the image as a whole. This is conservative and semantic-protected.
    shapes, shape_value_report = evaluate_global_shape_value(
        shapes,
        w,
        h,
        background,
        enable=config.enable_global_shape_value,
        min_value=config.shape_value_min_score,
        max_remove_area_ratio=config.shape_value_max_remove_area_ratio,
        max_remove_importance=config.shape_value_max_remove_importance,
        neighbor_distance_ratio=config.shape_value_neighbor_distance_ratio,
        redundancy_overlap=config.shape_value_redundancy_overlap,
        redundancy_color_distance=config.shape_value_redundancy_color_distance,
        near_background_max_color_distance=config.shape_value_near_background_max_color_distance,
        near_background_max_area_ratio=config.shape_value_near_background_max_area_ratio,
        near_background_max_importance=config.shape_value_near_background_max_importance,
    )
    if ddir:
        (ddir/"22_global_shape_value.json").write_text(
            json.dumps(shape_value_report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # Final global minimalization pass. This runs after value pruning so it can
    # remove slivers and simplify the remaining geometry.
    shapes, shape_cleanup_report = cleanup_minimal_shapes(
        shapes,
        w,
        h,
        enable=config.enable_global_shape_cleanup,
        thin_aspect_ratio=config.cleanup_thin_aspect_ratio,
        thin_short_side_ratio=config.cleanup_thin_short_side_ratio,
        thin_max_area_ratio=config.cleanup_thin_max_area_ratio,
        thin_rectangle_short_side_ratio=config.cleanup_thin_rectangle_short_side_ratio,
        thin_rectangle_aspect_ratio=config.cleanup_thin_rectangle_aspect_ratio,
        thin_rectangle_max_area_ratio=config.cleanup_thin_rectangle_max_area_ratio,
        thin_rectangle_max_importance=config.cleanup_thin_rectangle_max_importance,
        micro_area_ratio=config.cleanup_micro_area_ratio,
        micro_max_importance=config.cleanup_micro_max_importance,
        remove_duplicates=config.cleanup_remove_duplicates,
        duplicate_overlap=config.cleanup_duplicate_overlap,
        duplicate_color_distance=config.cleanup_duplicate_color_distance,
        merge_adjacent=config.cleanup_merge_adjacent,
        merge_gap_ratio=config.cleanup_merge_gap_ratio,
        merge_color_distance=config.cleanup_merge_color_distance,
        merge_max_area_ratio=config.cleanup_merge_max_area_ratio,
        merge_max_hull_inflation=config.cleanup_merge_max_hull_inflation,
        role_fragment_merge=config.cleanup_role_fragment_merge,
        role_fragment_gap_ratio=config.cleanup_role_fragment_gap_ratio,
        role_fragment_color_distance=config.cleanup_role_fragment_color_distance,
        role_fragment_max_area_ratio=config.cleanup_role_fragment_max_area_ratio,
        role_fragment_max_combined_area_ratio=config.cleanup_role_fragment_max_combined_area_ratio,
        role_fragment_max_hull_inflation=config.cleanup_role_fragment_max_hull_inflation,
        simplify_polygons=config.cleanup_simplify_polygons,
        simplify_epsilon_ratio=config.cleanup_simplify_epsilon_ratio,
        simplify_max_area_error=config.cleanup_simplify_max_area_error,
        simplify_min_iou=config.cleanup_simplify_min_iou,
        promote_primitives=config.cleanup_promote_primitives,
        promote_rectangle_iou=config.cleanup_promote_rectangle_iou,
        promote_ellipse_iou=config.cleanup_promote_ellipse_iou,
        promote_max_area_ratio=config.cleanup_promote_max_area_ratio,
        remove_isolated=config.cleanup_remove_isolated,
        isolated_max_area_ratio=config.cleanup_isolated_max_area_ratio,
        isolated_min_distance_ratio=config.cleanup_isolated_min_distance_ratio,
        isolated_max_importance=config.cleanup_isolated_max_importance,
    )
    if ddir:
        (ddir/"23_global_shape_cleanup.json").write_text(
            json.dumps(shape_cleanup_report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    roles={};sems={}
    for r in regions:roles[r.role]=roles.get(r.role,0)+1;sems[r.semantic_type]=sems.get(r.semantic_type,0)+1
    scene=Scene(w,h,background,shapes,metadata={
        "engine_version":"0.3.0","subject_mode":subject,"source_has_alpha":has_alpha,
        "composition_skeleton":skeleton.to_dict() if skeleton is not None else {"active":False,"mode":"none","confidence":0},
        "role_counts":roles,"semantic_counts":sems,"layer_counts":count_layers(regions),
        "pattern_groups":[{"id":p.id,"count":len(p.region_ids),"orientation":p.orientation,"spacing":p.spacing,"palette_id":p.palette_id} for p in patterns],
        "design_palette":[{"palette_id":e.palette_id,"role":e.role,"source_rgb":e.source_rgb,"output_rgb":e.output_rgb} for e in pal_entries],
        "multiscale_enabled":multi is not None,"macro_shape_count":len(macro_shapes),"subject_base_shape_count":len(subject_base),
        "global_shape_value":shape_value_report.to_dict(),
        "global_shape_cleanup":shape_cleanup_report.to_dict(),
        "rinka_macro_partition":rinka_macro_report.to_dict(),
        "character":(
            {
                "enabled":True,
                "structure":character_structure.to_dict(),
                "budget":character_budget.to_dict() if character_budget is not None else {},
                "details":character_detail_metadata,
                "shape_result":(
                    character_shape_result.to_dict()
                    if character_shape_result is not None
                    else {}
                ),
                "layout":(
                    {
                        **character_layout_plan.to_dict(),
                        "metrics":character_layout_metrics,
                    }
                    if character_layout_plan is not None
                    else {"enabled":False}
                ),
            }
            if character_structure is not None
            else {"enabled":False}
        ),
        "abstraction_level":config.abstraction_level,"analysis_scale":scale,"palette_colors":config.palette_colors,"region_count":len(regions),"shape_count":len(shapes),"source_width":raw.shape[1],"source_height":raw.shape[0]})
    if config.enable_quality_evaluation:
        q=evaluate_scene(
            scene,
            quality_reference,
            target_max_shapes=config.target_max_shapes,
            target_tiny_ratio=config.quality_target_tiny_shape_ratio,
            target_vertex_per_shape=config.quality_target_vertex_per_shape,
            subject_mask=quality_subject_mask,
        )
        scene.metadata["quality"]=q.to_dict()

    if (
        subject
        and character_structure is not None
        and config.enable_character_quality
    ):
        cq=evaluate_character_scene(
            scene,
            character_structure,
            enable_body_primitives=config.enable_body_primitives,
            enable_face_rules=(config.enable_face_rules and config.enable_face_primitives),
            enable_face_geometry_quality=config.enable_face_geometry_quality,
            enable_face_boundary_guard=config.enable_face_boundary_guard,
            enable_prop_rules=config.enable_prop_rules,
            enable_hand_quality=config.enable_hand_quality,
            enable_character_layout=config.enable_character_layout,
            min_score=config.character_retry_threshold,
            min_face_retention=config.character_quality_min_face_retention,
            min_face_geometry=config.character_quality_min_face_geometry,
            min_face_boundary=config.character_quality_min_face_boundary,
            min_face_identity=config.face_identity_min_score,
            face_geometry_area_ratio_tolerance=config.face_geometry_area_ratio_tolerance,
            face_geometry_center_tolerance=config.face_geometry_center_tolerance,
            face_geometry_aspect_tolerance=config.face_geometry_aspect_tolerance,
            face_geometry_eye_span_tolerance=config.face_geometry_eye_span_tolerance,
            face_geometry_mouth_offset_tolerance=config.face_geometry_mouth_offset_tolerance,
            canvas_padding=config.canvas_padding,
            min_body_readability=config.character_quality_min_body_readability,
            min_limb_separation=config.character_quality_min_limb_separation,
            min_prop_retention=config.character_quality_min_prop_retention,
            min_hand_score=config.character_quality_min_hand,
            min_hand_retention=config.character_quality_min_hand_retention,
            min_hand_geometry=config.character_quality_min_hand_geometry,
            min_hand_holding_contact=config.character_hand_geometry_min_holding_contact,
            min_layout_score=config.character_quality_min_layout,
            min_geometry_fidelity=config.character_quality_min_geometry_fidelity,
        )
        cq_dict=cq.to_dict()

        outfit_q = evaluate_outfit_quality(
            scene,
            character_structure,
            min_score=config.character_quality_min_outfit_structure,
        ) if (config.enable_outfit_structure_quality and config.enable_outfit_rules) else None
        prop_symbol_q = evaluate_prop_symbol_quality(
            scene,
            character_structure,
            min_score=config.character_quality_min_prop_symbol,
        ) if (config.enable_prop_symbol_quality and config.enable_prop_rules) else None

        if outfit_q is not None:
            outfit_q_dict=outfit_q.to_dict()
            scene.metadata["outfit_quality"]=outfit_q_dict
            scene.metadata["character"]["outfit_quality"]=outfit_q_dict
            cq_dict["outfit_structure_score"]=outfit_q.score
            cq_dict["outfit_structure_applicable"]=outfit_q.applicable
            cq_dict["retry_reasons"].extend(outfit_q.retry_reasons)
        if prop_symbol_q is not None:
            prop_q_dict=prop_symbol_q.to_dict()
            scene.metadata["prop_symbol_quality"]=prop_q_dict
            scene.metadata["character"]["prop_symbol_quality"]=prop_q_dict
            cq_dict["prop_symbol_score"]=prop_symbol_q.score
            cq_dict["prop_symbol_applicable"]=prop_symbol_q.applicable
            cq_dict["retry_reasons"].extend(prop_symbol_q.retry_reasons)

        if config.enable_character_wide_identity:
            wide=evaluate_character_wide_identity(
                generic_quality=scene.metadata.get("quality", {}),
                character_quality=cq_dict,
                outfit_quality=outfit_q.to_dict() if outfit_q is not None else None,
                prop_quality=prop_symbol_q.to_dict() if prop_symbol_q is not None else None,
                min_score=config.character_quality_min_wide_identity,
            )
            wide_dict=wide.to_dict()
            scene.metadata["character_wide_identity"]=wide_dict
            scene.metadata["character"]["wide_identity"]=wide_dict
            cq_dict["character_wide_identity_score"]=wide.score
            cq_dict["retry_reasons"].extend(wide.retry_reasons)

        cq_dict["retry_reasons"]=list(dict.fromkeys(cq_dict.get("retry_reasons") or []))
        scene.metadata["character_quality"]=cq_dict
        scene.metadata["character"]["quality"]=cq_dict
        scene.metadata["retry_selection_score"]=character_selection_score(
            cq_dict,
            scene.metadata.get("quality", {}),
        )
        face_diag = build_face_diagnostics_report(
            character_detail_metadata,
            cq_dict,
        )
        face_diag_dict = face_diag.to_dict()
        scene.metadata["face_diagnostics"] = face_diag_dict
        scene.metadata["character"]["face_diagnostics"] = face_diag_dict
        if ddir:
            (ddir/"10_character_quality.json").write_text(
                json.dumps(cq_dict, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (ddir/"17_face_diagnostics.json").write_text(
                json.dumps(face_diag_dict, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            save_face_diagnostics_overlay(
                ddir/"17_face_diagnostics.png",
                working,
                character_detail_metadata,
                face_diag_dict,
            )
            finishing = {
                "adaptive_budget": character_structure.metadata.get("adaptive_budget"),
                "outfit_quality": scene.metadata.get("outfit_quality"),
                "prop_symbol_quality": scene.metadata.get("prop_symbol_quality"),
                "character_wide_identity": scene.metadata.get("character_wide_identity"),
            }
            (ddir/"22_character_finishing.json").write_text(
                json.dumps(finishing, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    else:
        scene.metadata["retry_selection_score"]=float(
            scene.metadata.get("quality", {}).get("score", 0.0)
        )
    return scene

def _suggest_retry_config(config,q,attempt):
    u={};tiny=float(q.get("tiny_shape_ratio",0));identity=float(q.get("identity_score",0));complexity=float(q.get("complexity_score",1));minimal=float(q.get("minimality_score",1))
    if tiny>config.quality_target_tiny_shape_ratio or complexity<.68:u={"target_max_shapes":max(14,int(config.target_max_shapes*.86)),"min_region_area_ratio":min(.02,config.min_region_area_ratio*1.18),"contour_epsilon_ratio":min(.06,config.contour_epsilon_ratio*1.12)}
    elif identity<.48:u={"target_max_shapes":min(120,int(config.target_max_shapes*1.12)),"contour_epsilon_ratio":max(.004,config.contour_epsilon_ratio*.86),"palette_colors":min(16,config.palette_colors+2)}
    elif minimal<.58:u={"target_max_shapes":max(14,int(config.target_max_shapes*.9)),"palette_harmony_strength":min(.45,config.palette_harmony_strength+.05)}
    else:u={"contour_epsilon_ratio":max(.004,config.contour_epsilon_ratio*.92)}
    if attempt>=1 and config.line_mode=="standard":u["line_mode"]="low"
    return config.with_overrides(**u)

def minimalize(image_or_path,config=None):
    config=config or MinimalizeConfig.from_level(4)
    first=_minimalize_once(image_or_path,config)

    generic_enabled=(
        config.enable_auto_retry
        and config.enable_quality_evaluation
        and config.auto_retry_max>0
    )
    character_enabled=(
        first.metadata.get("subject_mode")
        and config.enable_character_auto_retry
        and config.enable_character_quality
        and config.character_max_retries>0
    )

    if not generic_enabled and not character_enabled:
        first.metadata["auto_retry_attempts"]=0
        first.metadata["character_retry_attempts"]=0
        first.metadata["face_retry_attempts"]=0
        first.metadata["retry_history"]=[]
        first.metadata["face_retry_history"]=[]
        return first

    q=first.metadata.get("quality",{})
    cq=first.metadata.get("character_quality",{})

    generic_need=False
    if generic_enabled:
        generic_need=(
            float(q.get("score",1))<config.quality_min_score
            or float(q.get("tiny_shape_ratio",0))>config.quality_target_tiny_shape_ratio*1.15
            or float(q.get("complexity_score",1))<.72
            or int(q.get("shape_count",0))>int(config.target_max_shapes*1.08)
            or (
                first.metadata.get("subject_mode")
                and float(q.get("silhouette_similarity",1))<.62
            )
        )

    character_need=(
        character_enabled
        and character_retry_needed(cq)
    )

    if not generic_need and not character_need:
        first.metadata["auto_retry_attempts"]=0
        first.metadata["character_retry_attempts"]=0
        first.metadata["face_retry_attempts"]=0
        first.metadata["retry_history"]=[]
        first.metadata["face_retry_history"]=[]
        first.metadata["auto_retry_selected_score"]=float(
            first.metadata.get("retry_selection_score", q.get("score", 0.0))
        )
        return first

    best=first
    best_score=float(
        first.metadata.get(
            "retry_selection_score",
            q.get("score",0.0),
        )
    )
    rc=config
    retry_history=[]
    generic_attempts=0
    character_attempts=0

    max_attempts=max(
        config.auto_retry_max if generic_enabled else 0,
        config.character_max_retries if character_enabled else 0,
    )

    for attempt in range(max_attempts):
        current_q=best.metadata.get("quality",{})
        current_cq=best.metadata.get("character_quality",{})

        use_character=(
            character_enabled
            and character_attempts<config.character_max_retries
            and character_retry_needed(current_cq)
        )

        if use_character:
            rc,info=suggest_character_retry_config(
                rc,
                current_cq,
                current_q,
                character_attempts,
            )
            character_attempts+=1
            info["mode"]="character"
        elif generic_enabled and generic_attempts<config.auto_retry_max:
            rc=_suggest_retry_config(
                rc,
                current_q,
                generic_attempts,
            )
            generic_attempts+=1
            info={
                "mode":"generic",
                "attempt":generic_attempts,
                "reasons":["generic_quality_retry"],
                "strategy":["generic_quality_tuning"],
                "updates":{},
            }
        else:
            break

        info["before_face_geometry_score"]=current_cq.get("face_geometry_score")
        info["before_face_boundary_score"]=current_cq.get("face_boundary_score")
        info["before_face_retention_score"]=current_cq.get("face_retention_score")

        cand=_minimalize_once(image_or_path,rc)
        cs=float(
            cand.metadata.get(
                "retry_selection_score",
                cand.metadata.get("quality",{}).get("score",0.0),
            )
        )
        info["candidate_selection_score"]=cs
        info["candidate_character_score"]=float(
            cand.metadata.get("character_quality",{}).get("score",0.0)
        )
        info["candidate_generic_score"]=float(
            cand.metadata.get("quality",{}).get("score",0.0)
        )
        candidate_cq=cand.metadata.get("character_quality",{})
        info["candidate_face_geometry_score"]=candidate_cq.get("face_geometry_score")
        info["candidate_face_boundary_score"]=candidate_cq.get("face_boundary_score")
        info["candidate_face_retention_score"]=candidate_cq.get("face_retention_score")

        face_reason_names={
            "false_face_generated",
            "face_retention_low",
            "face_geometry_low",
            "face_boundary_low",
            "face_feature_balance_low",
        }
        before_face_reasons=[
            r for r in (current_cq.get("retry_reasons") or [])
            if r in face_reason_names
        ]
        after_face_reasons=[
            r for r in (candidate_cq.get("retry_reasons") or [])
            if r in face_reason_names
        ]
        info["before_face_reasons"]=before_face_reasons
        info["candidate_face_reasons"]=after_face_reasons

        face_issue_improved=(
            bool(before_face_reasons)
            and len(after_face_reasons)<len(before_face_reasons)
        )
        candidate_face_safe=float(candidate_cq.get("face_safety_score",1.0))>=0.99
        selected=cs>best_score
        selection_reason="selection_score" if selected else "not_selected"
        if (
            not selected
            and face_issue_improved
            and candidate_face_safe
            and cs>=best_score-0.035
        ):
            selected=True
            selection_reason="face_issue_resolved"

        info["selected"]=selected
        info["selection_reason"]=selection_reason
        retry_history.append(info)

        if selected:
            best,best_score=cand,cs

    face_retry_history=[
        item for item in retry_history
        if any(
            str(reason).startswith("face_")
            or reason=="false_face_generated"
            for reason in item.get("reasons",[])
        )
    ]
    best.metadata["auto_retry_attempts"]=generic_attempts
    best.metadata["character_retry_attempts"]=character_attempts
    best.metadata["face_retry_attempts"]=len(face_retry_history)
    best.metadata["retry_history"]=retry_history
    best.metadata["face_retry_history"]=face_retry_history
    best.metadata["auto_retry_selected_score"]=best_score

    if config.debug_mode and config.debug_output_dir and face_retry_history:
        retry_debug=Path(config.debug_output_dir)/"12_face_retry.json"
        retry_debug.parent.mkdir(parents=True,exist_ok=True)
        retry_debug.write_text(
            json.dumps(
                {
                    "attempts":len(face_retry_history),
                    "selected_face_geometry_score":best.metadata.get("character_quality",{}).get("face_geometry_score"),
                    "selected_face_boundary_score":best.metadata.get("character_quality",{}).get("face_boundary_score"),
                    "selected_face_retention_score":best.metadata.get("character_quality",{}).get("face_retention_score"),
                    "history":face_retry_history,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return best
