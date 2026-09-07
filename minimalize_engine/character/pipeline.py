from __future__ import annotations

import numpy as np

from ..models import Region, Shape
from .models import CharacterStructure, CharacterShapeBudget
from .detect import detect_character_structure
from .pose_proxy import build_pose_proxy
from .refine import refine_character_structure, apply_character_part_hints
from .budget import make_character_shape_budget
from .adaptive_budget import rebalance_character_budget
from .prop_rules import refresh_prop_parts
from .primitives import (
    build_character_detail_shapes as _build_character_detail_shapes,
    character_structure_to_shapes,
    suppress_generic_character_shapes,
)


def analyze_character_structure(
    image_rgb: np.ndarray,
    alpha_mask: np.ndarray,
    regions: list[Region],
    *,
    preset: str = "auto",
    total_shape_budget: int = 36,
    enable_pose_proxy: bool = True,
    enable_prop_rules: bool = True,
    enable_face_validation: bool = True,
    face_validation_threshold: float = 0.52,
    enable_face_contour_fit: bool = True,
    face_contour_shrink_strength: float = 0.22,
    face_contour_chin_trim_strength: float = 0.18,
    face_contour_forehead_expand_strength: float = 0.10,
    face_contour_width_scale: float = 1.00,
    face_contour_height_scale: float = 1.00,
    face_contour_center_x_shift_ratio: float = 0.00,
    face_contour_center_y_shift_ratio: float = 0.00,
    enable_face_boundary_guard: bool = True,
    face_boundary_guard_strength: float = 0.65,
    face_boundary_eye_protect_strength: float = 0.80,
    face_boundary_cheek_protect_strength: float = 0.72,
    face_boundary_chin_protect_strength: float = 0.85,
    face_boundary_forehead_allowance: float = 0.18,
    prop_source_rgb: np.ndarray | None = None,
    prop_source_alpha: np.ndarray | None = None,
    importance_strength: float = 0.12,
    enable_adaptive_character_budget: bool = True,
) -> tuple[CharacterStructure, CharacterShapeBudget, list[Region]]:
    structure = detect_character_structure(
        regions,
        alpha_mask,
        image_rgb.shape,
        image_rgb=image_rgb,
        preset=preset,  # type: ignore[arg-type]
        enable_face_validation=enable_face_validation,
        face_validation_threshold=face_validation_threshold,
        enable_face_contour_fit=enable_face_contour_fit,
        face_contour_shrink_strength=face_contour_shrink_strength,
        face_contour_chin_trim_strength=face_contour_chin_trim_strength,
        face_contour_forehead_expand_strength=face_contour_forehead_expand_strength,
        face_contour_width_scale=face_contour_width_scale,
        face_contour_height_scale=face_contour_height_scale,
        face_contour_center_x_shift_ratio=face_contour_center_x_shift_ratio,
        face_contour_center_y_shift_ratio=face_contour_center_y_shift_ratio,
        enable_face_boundary_guard=enable_face_boundary_guard,
        face_boundary_guard_strength=face_boundary_guard_strength,
        face_boundary_eye_protect_strength=face_boundary_eye_protect_strength,
        face_boundary_cheek_protect_strength=face_boundary_cheek_protect_strength,
        face_boundary_chin_protect_strength=face_boundary_chin_protect_strength,
        face_boundary_forehead_allowance=face_boundary_forehead_allowance,
    )
    structure = refine_character_structure(
        structure,
        regions,
        image_rgb.shape,
    )

    if enable_prop_rules:
        refresh_prop_parts(
            image_rgb,
            structure,
            regions,
            source_rgb=prop_source_rgb,
            source_alpha=prop_source_alpha,
        )

    if enable_pose_proxy:
        structure.pose_graph = build_pose_proxy(structure)

    budget = make_character_shape_budget(
        structure,
        total_shape_budget,
        preset=preset,  # type: ignore[arg-type]
    )
    budget, adaptive_report = rebalance_character_budget(
        budget,
        structure,
        enabled=enable_adaptive_character_budget,
    )
    structure.metadata["adaptive_budget"] = adaptive_report.to_dict()
    regions = apply_character_part_hints(
        regions,
        structure,
        importance_strength=importance_strength,
    )
    return structure, budget, regions


# Backwards compatibility for alpha2-alpha4 callers.
def build_character_detail_shapes(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    budget: CharacterShapeBudget,
    regions: list[Region],
    *,
    enable_body_primitives: bool = True,
    enable_face_rules: bool = True,
    enable_hair_rules: bool = True,
    enable_outfit_rules: bool = True,
    enable_prop_rules: bool = True,
    start_id: int = 700000,
) -> tuple[list[Shape], dict]:
    return _build_character_detail_shapes(
        image_rgb,
        structure,
        budget,
        regions,
        enable_body_primitives=enable_body_primitives,
        enable_face_rules=enable_face_rules,
        enable_hair_rules=enable_hair_rules,
        enable_outfit_rules=enable_outfit_rules,
        enable_prop_rules=enable_prop_rules,
        start_id=start_id,
    )


def suppress_replaced_character_shapes(
    shapes: list[Shape],
    character_detail_metadata: dict,
) -> list[Shape]:
    """
    Legacy compatibility shim.

    New code should call `suppress_generic_character_shapes()` with a
    CharacterShapeResult. This shim keeps older external imports working by
    applying the same metadata thresholds without reintroducing the old
    generation pipeline.
    """
    body_parts = {"torso", "left_arm", "right_arm", "left_leg", "right_leg"}
    replace_body = character_detail_metadata.get("body", {}).get("shape_count", 0) > 0
    replace_face = character_detail_metadata.get("face", {}).get("shape_count", 0) > 0
    replace_hair = character_detail_metadata.get("hair", {}).get("shape_count", 0) > 0
    replace_outfit = character_detail_metadata.get("outfit", {}).get("shape_count", 0) > 0
    replace_props = character_detail_metadata.get("props", {}).get("shape_count", 0) > 0

    prop_region_ids = set()
    for d in character_detail_metadata.get("props", {}).get("descriptors", []):
        prop_region_ids.update(d.get("source_region_ids") or [])

    out = []
    for shape in shapes:
        if replace_body and shape.character_part in body_parts and shape.part_confidence >= 0.16:
            continue
        if replace_face and shape.character_part == "face" and shape.part_confidence >= 0.18:
            continue
        if replace_hair and shape.character_part == "hair" and shape.part_confidence >= 0.20:
            continue
        if replace_outfit and shape.character_part == "outfit" and shape.part_confidence >= 0.18:
            continue
        if (
            replace_props
            and (
                (shape.character_part == "prop" and shape.part_confidence >= 0.18)
                or (
                    shape.source_region_id is not None
                    and shape.source_region_id in prop_region_ids
                )
            )
        ):
            continue
        out.append(shape)
    return out
