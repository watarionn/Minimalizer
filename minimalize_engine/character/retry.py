from __future__ import annotations

from ..config import MinimalizeConfig


def _normalize_character_retry_reasons(reasons: list[str]) -> list[str]:
    """Deduplicate retry reasons while preserving diagnostic priority."""
    out: list[str] = []
    for reason in reasons:
        if reason and reason not in out:
            out.append(reason)
    return out


def _face_geometry_diagnostics(character_quality: dict) -> dict:
    return (
        character_quality.get("diagnostics", {})
        .get("face_geometry", {})
        or {}
    )


def _apply_face_geometry_retry(
    config: MinimalizeConfig,
    character_quality: dict,
    updates: dict,
    strategy: list[str],
) -> None:
    """Translate Face Geometry diagnostics into deterministic contour changes."""
    metrics = _face_geometry_diagnostics(character_quality)
    diagnostic = metrics.get("diagnostics", {}) or {}

    # Respect explicit feature switches. A retry may tune an enabled feature,
    # but it must not silently re-enable a contour fitter the user turned off.
    if not config.enable_face_contour_fit:
        updates["analysis_max_side"] = min(
            1400,
            max(
                config.analysis_max_side + 32,
                int(round(config.analysis_max_side * 1.12)),
            ),
        )
        strategy.append("recheck_face_geometry")
        return

    width_scale = float(config.face_contour_width_scale)
    height_scale = float(config.face_contour_height_scale)
    shift_x = float(config.face_contour_center_x_shift_ratio)
    shift_y = float(config.face_contour_center_y_shift_ratio)

    area_ratio = float(diagnostic.get("generated_to_source_area_ratio", 1.0))
    if area_ratio > 1.06:
        common = max(0.88, min(0.985, (1.0 / area_ratio) ** 0.42))
        width_scale *= common
        height_scale *= common
        updates["face_contour_shrink_strength"] = min(
            0.52,
            config.face_contour_shrink_strength + 0.06 + min(0.08, (area_ratio - 1.0) * 0.18),
        )
        strategy.append("face_geometry_shrink")
    elif area_ratio < 0.94:
        common = min(1.14, max(1.015, (1.0 / max(area_ratio, 1e-6)) ** 0.38))
        width_scale *= common
        height_scale *= common
        updates["face_contour_shrink_strength"] = max(
            0.0,
            config.face_contour_shrink_strength - 0.07,
        )
        strategy.append("face_geometry_expand")

    source_aspect = float(diagnostic.get("source_bbox_aspect", 0.0) or 0.0)
    generated_aspect = float(diagnostic.get("generated_bbox_aspect", 0.0) or 0.0)
    if source_aspect > 0.0 and generated_aspect > 0.0:
        aspect_ratio = generated_aspect / source_aspect
        if aspect_ratio > 1.08 or aspect_ratio < 0.92:
            aspect_correction = float(max(0.84, min(1.18, (1.0 / aspect_ratio) ** 0.60)))
            width_scale *= aspect_correction
            # A small opposite height correction preserves approximate area.
            height_scale *= float(max(0.93, min(1.07, aspect_ratio ** 0.18)))
            strategy.append("face_geometry_aspect")

    # Eye span is especially useful because eye coordinates do not move when
    # only the face ellipse is resized. It gives a direct width correction.
    source_eye = metrics.get("source_eye_span_ratio")
    generated_eye = metrics.get("generated_eye_span_ratio")
    if source_eye is not None and generated_eye is not None:
        source_eye = float(source_eye)
        generated_eye = float(generated_eye)
        if source_eye > 1e-6:
            eye_ratio = generated_eye / source_eye
            if eye_ratio > 1.10 or eye_ratio < 0.90:
                width_scale *= float(max(0.88, min(1.12, eye_ratio)))
                strategy.append("face_geometry_eye_span")

    source_center = metrics.get("source_face_center")
    generated_center = metrics.get("generated_face_center")
    source_bbox = metrics.get("source_face_bbox")
    if source_center and generated_center and source_bbox and len(source_bbox) == 4:
        sw = max(float(source_bbox[2]), 1.0)
        sh = max(float(source_bbox[3]), 1.0)
        dx = (float(source_center[0]) - float(generated_center[0])) / sw
        dy = (float(source_center[1]) - float(generated_center[1])) / sh
        if abs(dx) > 0.025 or abs(dy) > 0.025:
            shift_x += float(max(-0.10, min(0.10, dx * 0.72)))
            shift_y += float(max(-0.10, min(0.10, dy * 0.72)))
            strategy.append("face_geometry_recenter")

    source_mouth = metrics.get("source_mouth_relative")
    generated_mouth = metrics.get("generated_mouth_relative")
    if source_mouth and generated_mouth:
        mouth_dy = float(generated_mouth[1]) - float(source_mouth[1])
        if abs(mouth_dy) > 0.07:
            # If the mouth sits too low relative to the generated oval, move the
            # oval downward. The mouth itself remains anchored to source evidence.
            shift_y += float(max(-0.055, min(0.055, mouth_dy * 0.30)))
            strategy.append("face_geometry_mouth_align")

    updates["face_contour_width_scale"] = float(max(0.76, min(1.26, width_scale)))
    updates["face_contour_height_scale"] = float(max(0.76, min(1.26, height_scale)))
    updates["face_contour_center_x_shift_ratio"] = float(max(-0.16, min(0.16, shift_x)))
    updates["face_contour_center_y_shift_ratio"] = float(max(-0.16, min(0.16, shift_y)))
    updates["analysis_max_side"] = min(
        1400,
        max(
            config.analysis_max_side + 24,
            int(round(config.analysis_max_side * 1.08)),
        ),
    )
    strategy.append("repair_face_geometry")


def _apply_face_boundary_retry(
    config: MinimalizeConfig,
    character_quality: dict,
    updates: dict,
    strategy: list[str],
) -> None:
    """Tune only the local face/hair guard from boundary diagnostics."""
    if not config.enable_face_boundary_guard:
        # Respect explicit user disable.
        strategy.append("face_boundary_guard_disabled")
        return

    boundary = (
        character_quality.get("diagnostics", {})
        .get("face_boundary", {})
        or {}
    )
    diag = boundary.get("diagnostics", {}) or {}
    conflict_after = int(diag.get("conflict_pixels_after", 0) or 0)
    conflict_before = int(diag.get("conflict_pixels_before", 0) or 0)
    removed = int(diag.get("removed_hair_pixels", 0) or 0)
    hair_before = max(1, int(diag.get("hair_pixels_before", 0) or 0))
    removed_ratio = removed / hair_before

    if conflict_after > 0:
        updates["face_boundary_guard_strength"] = min(
            0.96,
            max(0.72, config.face_boundary_guard_strength + 0.18),
        )
        updates["face_boundary_eye_protect_strength"] = min(
            1.0, config.face_boundary_eye_protect_strength + 0.10
        )
        updates["face_boundary_cheek_protect_strength"] = min(
            1.0, config.face_boundary_cheek_protect_strength + 0.10
        )
        updates["face_boundary_chin_protect_strength"] = min(
            1.0, config.face_boundary_chin_protect_strength + 0.08
        )
        strategy.append("strengthen_face_boundary")
    elif removed_ratio > 0.10 and conflict_before > 0:
        # The guard solved the conflict but paid too much hair mass. Preserve
        # legitimate bangs/side hair while keeping the protection zones.
        updates["face_boundary_guard_strength"] = max(
            0.50, config.face_boundary_guard_strength - 0.06
        )
        updates["face_boundary_forehead_allowance"] = min(
            0.32, config.face_boundary_forehead_allowance + 0.04
        )
        strategy.append("preserve_face_boundary_hair")
    else:
        updates["face_boundary_guard_strength"] = min(
            0.90, config.face_boundary_guard_strength + 0.08
        )
        strategy.append("refine_face_boundary")

    updates["analysis_max_side"] = min(
        1400,
        max(
            int(updates.get("analysis_max_side", config.analysis_max_side)),
            config.analysis_max_side + 24,
        ),
    )


def _apply_face_feature_balance_retry(
    config: MinimalizeConfig,
    updates: dict,
    strategy: list[str],
) -> None:
    """Forward-compatible face-detail retry; Phase 10.5 will reserve slots."""
    updates["analysis_max_side"] = min(
        1400,
        max(
            int(updates.get("analysis_max_side", config.analysis_max_side)),
            int(round(config.analysis_max_side * 1.14)),
        ),
    )
    updates["target_max_shapes"] = min(150, config.target_max_shapes + 3)
    updates["palette_colors"] = min(16, config.palette_colors + 1)
    strategy.append("protect_face_features")


def suggest_character_retry_config(
    config: MinimalizeConfig,
    character_quality: dict,
    generic_quality: dict,
    attempt: int,
) -> tuple[MinimalizeConfig, dict]:
    reasons = _normalize_character_retry_reasons(list(character_quality.get("retry_reasons") or []))
    updates: dict = {}
    strategy = []

    def grow_analysis(multiplier: float | None = None) -> None:
        mult = multiplier or config.character_retry_analysis_scale
        updates["analysis_max_side"] = min(
            1400,
            max(
                config.analysis_max_side + 32,
                int(round(config.analysis_max_side * mult)),
            ),
        )

    def grow_shapes(extra: int = 0) -> None:
        updates["target_max_shapes"] = min(
            150,
            max(
                config.target_max_shapes + extra,
                int(round(
                    config.target_max_shapes
                    * config.character_retry_shape_growth
                )),
            ),
        )

    if "false_face_generated" in reasons:
        # Never "solve" a false face by making the detector more permissive.
        # Tighten the gate and disable dedicated face redraw for this retry.
        updates["character_face_validation_threshold"] = min(
            0.78,
            config.character_face_validation_threshold + 0.07,
        )
        updates["enable_face_rules"] = False
        strategy.append("tighten_face_gate")

    if "face_retention_low" in reasons:
        grow_analysis(1.16)
        grow_shapes(3)
        updates["palette_colors"] = min(16, config.palette_colors + 1)
        updates["character_face_abstraction"] = max(
            0.50,
            config.character_face_abstraction * 0.90,
        )
        strategy.append("protect_face_detail")

    if "face_geometry_low" in reasons:
        _apply_face_geometry_retry(
            config,
            character_quality,
            updates,
            strategy,
        )

    if "face_boundary_low" in reasons:
        _apply_face_boundary_retry(
            config,
            character_quality,
            updates,
            strategy,
        )

    if "face_feature_balance_low" in reasons:
        _apply_face_feature_balance_retry(
            config,
            updates,
            strategy,
        )

    if "body_readability_low" in reasons:
        grow_analysis(1.20)
        grow_shapes(2)
        updates["character_body_abstraction"] = max(
            0.68,
            config.character_body_abstraction * 0.92,
        )
        strategy.append("recover_body_parts")

    if "limb_separation_low" in reasons:
        updates["character_limb_width_scale"] = max(
            0.68,
            config.character_limb_width_scale * 0.76,
        )
        updates["character_limb_abstraction"] = max(
            0.74,
            config.character_limb_abstraction * 0.92,
        )
        grow_analysis(1.16)
        strategy.append("separate_limbs")

    if "prop_retention_low" in reasons:
        grow_analysis(1.20)
        grow_shapes(3)
        updates["palette_colors"] = min(
            16,
            max(updates.get("palette_colors", config.palette_colors), config.palette_colors + 1),
        )
        strategy.append("protect_props")

    if any(r in reasons for r in {"hand_retention_low", "hand_quality_low"}):
        if config.enable_hand_analysis and config.enable_hand_primitives:
            grow_analysis(1.14)
            updates["character_hand_min_confidence"] = max(
                0.18, config.character_hand_min_confidence - 0.05
            )
            if config.enable_hand_validation:
                updates["character_hand_validation_min_score"] = max(
                    0.34, config.character_hand_validation_min_score - 0.04
                )
                updates["character_hand_validation_unknown_min_score"] = max(
                    0.36, config.character_hand_validation_unknown_min_score - 0.03
                )
            strategy.append("recover_hand_intent")
        else:
            strategy.append("hand_features_disabled")

    if "hand_geometry_low" in reasons:
        if config.enable_hand_geometry_validation:
            grow_analysis(1.10)
            updates["character_hand_geometry_min_connection"] = min(
                0.90, config.character_hand_geometry_min_connection + 0.06
            )
            updates["character_hand_geometry_min_direction"] = min(
                0.82, config.character_hand_geometry_min_direction + 0.06
            )
            strategy.append("repair_hand_geometry")
        else:
            strategy.append("hand_geometry_disabled")

    if "hand_holding_contact_low" in reasons:
        if config.enable_hand_geometry_validation:
            updates["character_hand_geometry_min_holding_contact"] = min(
                0.72, config.character_hand_geometry_min_holding_contact + 0.08
            )
            grow_analysis(1.10)
            strategy.append("restore_hand_prop_contact")
        else:
            strategy.append("hand_geometry_disabled")

    if "geometry_fidelity_low" in reasons:
        grow_analysis(1.16)
        updates["character_limb_width_scale"] = max(
            0.74,
            config.character_limb_width_scale * 0.92,
        )
        updates["character_body_abstraction"] = max(
            0.70,
            config.character_body_abstraction * 0.94,
        )
        updates["character_hair_abstraction"] = max(
            0.64,
            config.character_hair_abstraction * 0.92,
        )
        strategy.append("improve_geometry_fidelity")


    if "outfit_structure_low" in reasons:
        grow_analysis(1.16)
        grow_shapes(2)
        updates["palette_colors"] = min(16, config.palette_colors + 1)
        updates["character_body_abstraction"] = max(0.70, config.character_body_abstraction * 0.94)
        strategy.append("recover_outfit_structure")

    if "prop_symbolization_low" in reasons:
        if config.enable_prop_rules:
            grow_analysis(1.18)
            grow_shapes(2)
            updates["palette_colors"] = min(16, config.palette_colors + 1)
            strategy.append("recover_prop_symbol")
        else:
            strategy.append("prop_rules_disabled")

    if "character_wide_identity_low" in reasons:
        grow_analysis(1.12)
        generic_identity = float(generic_quality.get("identity_score", 0.0))
        if generic_identity < 0.72:
            grow_shapes(2)
            updates["contour_epsilon_ratio"] = max(0.004, config.contour_epsilon_ratio * 0.94)
            updates["palette_colors"] = min(16, config.palette_colors + 1)
            strategy.append("recover_character_wide_identity")
        else:
            strategy.append("refine_character_wide_identity")

    if "layout_low" in reasons:
        updates["character_layout_visual_center_strength"] = min(
            1.0,
            config.character_layout_visual_center_strength + 0.14,
        )
        updates["character_layout_side_margin_ratio"] = min(
            0.10,
            config.character_layout_side_margin_ratio + 0.012,
        )
        updates["character_layout_max_scale_up"] = min(
            1.12,
            config.character_layout_max_scale_up,
        )
        strategy.append("normalize_layout")

    # If only the combined score is low, use generic quality to decide whether
    # to add detail or simplify. This keeps retries targeted rather than random.
    specific = {
        "false_face_generated",
        "face_retention_low",
        "face_geometry_low",
        "face_boundary_low",
        "face_feature_balance_low",
        "body_readability_low",
        "limb_separation_low",
        "prop_retention_low",
        "hand_retention_low",
        "hand_geometry_low",
        "hand_holding_contact_low",
        "hand_quality_low",
        "layout_low",
        "geometry_fidelity_low",
        "outfit_structure_low",
        "prop_symbolization_low",
        "character_wide_identity_low",
    }
    if "character_quality_low" in reasons and not (set(reasons) & specific):
        generic_identity = float(generic_quality.get("identity_score", 0.0))
        generic_complexity = float(generic_quality.get("complexity_score", 1.0))
        if generic_identity < 0.58:
            grow_analysis(1.16)
            grow_shapes(2)
            updates["palette_colors"] = min(16, config.palette_colors + 1)
            strategy.append("recover_identity")
        elif generic_complexity < 0.75:
            updates["target_max_shapes"] = max(
                14,
                int(round(config.target_max_shapes * 0.92)),
            )
            updates["contour_epsilon_ratio"] = min(
                0.06,
                config.contour_epsilon_ratio * 1.08,
            )
            strategy.append("reduce_complexity")
        else:
            grow_analysis(1.08)
            strategy.append("refine_character_analysis")

    if not strategy:
        grow_analysis(1.08)
        strategy.append("safe_refine")

    # A second retry should be more conservative about line clutter.
    if attempt >= 1 and config.line_mode == "standard":
        updates["line_mode"] = "low"

    strategy = _normalize_character_retry_reasons(strategy)
    new_config = config.with_overrides(**updates)
    return new_config, {
        "attempt": attempt + 1,
        "reasons": reasons,
        "strategy": strategy,
        "updates": updates,
    }
