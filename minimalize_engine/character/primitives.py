from __future__ import annotations

import numpy as np

from ..models import Region, Shape
from .models import (
    CharacterShapeBudget,
    CharacterShapeResult,
    CharacterStructure,
)
from .part_types import CharacterPartType
from .body_rules import (
    analyze_body_primitives,
    build_body_shapes,
)
from .face_rules import analyze_face_layout, build_face_shapes
from .face_identity import analyze_face_identity_signals
from .face_identity_budget import build_face_identity_plan, apply_face_identity_budget
from .face_identity_validation import validate_face_identity_loss, apply_single_feature_rollback
from .hair_rules import analyze_hair_flows, build_hair_shapes
from .hand_rules import analyze_hand_primitives, build_hand_shapes
from .hand_geometry import validate_and_refine_hand_geometry
from .hand_validation import validate_hand_candidates, filtered_hand_analysis
from .limb_refine import refine_limb_shapes
from .hair_body_guard import guard_hair_from_body_core
from .outfit_rules import analyze_outfit_structure, build_outfit_shapes
from .prop_rules import analyze_props, build_prop_shapes


def _body_budget(
    structure: CharacterStructure,
    budget: CharacterShapeBudget,
) -> int:
    return int(budget.reserved_body)


def character_structure_to_shapes(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    regions: list[Region],
    budget: CharacterShapeBudget,
    *,
    enable_body_primitives: bool = True,
    enable_hand_analysis: bool = True,
    enable_hand_primitives: bool = True,
    hand_max_shapes: int = 2,
    hand_min_confidence: float = 0.30,
    enable_hand_geometry_validation: bool = True,
    hand_geometry_min_connection: float = 0.72,
    hand_geometry_min_direction: float = 0.58,
    hand_geometry_min_holding_contact: float = 0.45,
    enable_hand_validation: bool = True,
    hand_validation_min_score: float = 0.42,
    hand_validation_unknown_min_score: float = 0.42,
    enable_limb_geometry_refine: bool = True,
    limb_refine_min_iou: float = 0.46,
    enable_hair_body_guard: bool = True,
    hair_body_overlap_trigger: float = 0.44,
    hair_body_max_remove_ratio: float = 0.12,
    limb_width_scale: float = 1.0,
    enable_face_rules: bool = True,
    enable_face_primitives: bool = False,
    enable_face_identity_analysis: bool = True,
    enable_face_identity_budget: bool = True,
    enable_face_identity_validation: bool = True,
    face_identity_min_score: float = 0.72,
    abstraction_level: int = 4,
    enable_hair_rules: bool = True,
    enable_outfit_rules: bool = True,
    enable_prop_rules: bool = True,
    start_id: int = 700000,
) -> CharacterShapeResult:
    """
    Single Character Shape generation entry point.

    Phase 7 unifies torso/limbs, face, hair, outfit and props under one
    deterministic budgeted generator. Generic Region Shapes become fallback
    detail instead of the primary body representation.
    """
    shapes: list[Shape] = []
    body_shapes: list[Shape] = []
    face_shapes: list[Shape] = []
    hair_shapes: list[Shape] = []
    outfit_shapes: list[Shape] = []
    prop_shapes: list[Shape] = []
    hand_shapes: list[Shape] = []
    sid = start_id

    metadata = {
        "body": {
            "enabled": False,
            "shape_count": 0,
            "analysis": None,
            "limb_refine": None,
        },
        "hands": {
            "enabled": False,
            "rendering_changed": False,
            "shape_count": 0,
            "analysis": None,
            "candidate_validation": None,
            "geometry_validation": None,
            "rendering": None,
        },
        "face": {
            "enabled": False,
            "shape_count": 0,
            "layout": None,
            "validation": structure.metadata.get("face_validation"),
            "identity_signals": None,
            "identity_plan": None,
            "identity_budget": None,
            "identity_rendering": None,
            "identity_validation": None,
        },
        "hair": {
            "enabled": False,
            "shape_count": 0,
            "flows": [],
            "body_guard": None,
        },
        "outfit": {
            "enabled": False,
            "shape_count": 0,
            "structure": None,
        },
        "props": {
            "enabled": False,
            "shape_count": 0,
            "descriptors": [],
        },
    }

    if enable_body_primitives:
        body_analysis = analyze_body_primitives(structure)
        body_shapes = build_body_shapes(
            image_rgb,
            structure,
            body_analysis,
            _body_budget(structure, budget),
            start_id=sid,
            limb_width_scale=limb_width_scale,
        )
        limb_refine_report = None
        if body_shapes and enable_limb_geometry_refine:
            body_shapes, limb_refine_report = refine_limb_shapes(
                body_shapes,
                structure,
                min_iou=limb_refine_min_iou,
            )
        shapes.extend(body_shapes)
        sid += len(body_shapes)
        metadata["body"] = {
            "enabled": True,
            "shape_count": len(body_shapes),
            "analysis": body_analysis.to_dict(),
            "limb_refine": limb_refine_report.to_dict() if limb_refine_report is not None else None,
        }
        if enable_hand_analysis:
            hand_analysis = analyze_hand_primitives(
                image_rgb,
                structure,
                body_analysis,
            )
            hand_validation = None
            render_hand_analysis = hand_analysis
            if enable_hand_validation:
                hand_validation_report = validate_hand_candidates(
                    hand_analysis,
                    min_score=hand_validation_min_score,
                    unknown_min_score=hand_validation_unknown_min_score,
                )
                hand_validation = hand_validation_report.to_dict()
                render_hand_analysis = filtered_hand_analysis(hand_analysis, hand_validation_report)
            hand_shapes = (
                build_hand_shapes(
                    image_rgb,
                    render_hand_analysis,
                    start_id=sid,
                    max_shapes=hand_max_shapes,
                    min_confidence=hand_min_confidence,
                )
                if enable_hand_primitives
                else []
            )
            hand_geometry = None
            if hand_shapes and enable_hand_geometry_validation:
                hand_shapes, hand_geometry_report = validate_and_refine_hand_geometry(
                    image_rgb,
                    structure,
                    body_analysis,
                    render_hand_analysis,
                    hand_shapes,
                    min_connection=hand_geometry_min_connection,
                    min_direction=hand_geometry_min_direction,
                    min_holding_contact=hand_geometry_min_holding_contact,
                )
                hand_geometry = hand_geometry_report.to_dict()
            if hand_shapes:
                shapes.extend(hand_shapes)
                sid += len(hand_shapes)
            metadata["hands"] = {
                "enabled": True,
                "rendering_changed": bool(hand_shapes),
                "shape_count": len(hand_shapes),
                "analysis": hand_analysis.to_dict(),
                "candidate_validation": hand_validation,
                "geometry_validation": hand_geometry,
                "rendering": {
                    "enabled": bool(enable_hand_primitives),
                    "max_shapes": int(hand_max_shapes),
                    "min_confidence": float(hand_min_confidence),
                    "rendered_sides": [shape.side_hint for shape in hand_shapes],
                    "rendered_intents": [
                        shape.semantic_type.removeprefix("character_hand_")
                        for shape in hand_shapes
                    ],
                    "shapes": [
                        {
                            "id": shape.id,
                            "side": shape.side_hint,
                            "intent": shape.semantic_type.removeprefix("character_hand_"),
                            "points": [list(p) for p in shape.points],
                            "fill_color": list(shape.fill_color) if shape.fill_color is not None else None,
                        }
                        for shape in hand_shapes
                    ],
                },
            }

    face = structure.first_part(CharacterPartType.FACE)
    if enable_face_rules and face is not None:
        layout = analyze_face_layout(image_rgb, face, regions)
        face_budget = max(
            0,
            budget.per_part.get(CharacterPartType.FACE, 0),
        )
        identity_signals = (
            analyze_face_identity_signals(
                image_rgb,
                structure,
                face,
                layout,
                abstraction_level=abstraction_level,
            )
            if enable_face_identity_analysis
            else None
        )
        identity_plan = (
            build_face_identity_plan(
                identity_signals,
                available_shapes=face_budget,
                abstraction_level=abstraction_level,
            )
            if (enable_face_identity_budget and identity_signals is not None)
            else None
        )
        identity_budget = (
            apply_face_identity_budget(
                identity_plan,
                available_shapes=face_budget,
            )
            if identity_plan is not None
            else None
        )

        identity_reservation = (
            identity_budget.reserved_shapes
            if identity_budget is not None
            else None
        )
        primary_eye_side = (
            identity_signals.primary_eye_side
            if identity_signals is not None
            else "none"
        )
        face_shapes = (
            build_face_shapes(
                image_rgb,
                face,
                layout,
                face_budget,
                start_id=sid,
                identity_reservation=identity_reservation,
                primary_eye_side=primary_eye_side,
            )
            if enable_face_primitives
            else []
        )

        identity_validation = None
        rollback_feature = None
        if (
            enable_face_primitives
            and enable_face_identity_validation
            and identity_signals is not None
            and identity_plan is not None
            and identity_budget is not None
        ):
            identity_validation = validate_face_identity_loss(
                identity_signals,
                identity_plan,
                face_shapes,
                min_score=face_identity_min_score,
                primary_eye_side=primary_eye_side,
            )
            repaired_reservation, rollback_feature = apply_single_feature_rollback(
                identity_reservation or {},
                identity_validation,
                available_shapes=face_budget,
            )
            if rollback_feature is not None:
                face_shapes = build_face_shapes(
                    image_rgb,
                    face,
                    layout,
                    face_budget,
                    start_id=sid,
                    identity_reservation=repaired_reservation,
                    primary_eye_side=primary_eye_side,
                )
                identity_validation = validate_face_identity_loss(
                    identity_signals,
                    identity_plan,
                    face_shapes,
                    min_score=face_identity_min_score,
                    primary_eye_side=primary_eye_side,
                )
                identity_validation.diagnostics["rollback_applied"] = True
                identity_validation.diagnostics["rollback_feature"] = rollback_feature
            elif identity_validation is not None:
                identity_validation.diagnostics["rollback_applied"] = False

        shapes.extend(face_shapes)
        sid += len(face_shapes)
        metadata["face"] = {
            "enabled": True,
            "rendering_enabled": bool(enable_face_primitives),
            "shape_count": len(face_shapes),
            "layout": layout.to_dict(),
            "validation": structure.metadata.get("face_validation"),
            "identity_signals": (
                identity_signals.to_dict()
                if identity_signals is not None
                else None
            ),
            "identity_plan": (
                identity_plan.to_dict()
                if identity_plan is not None
                else None
            ),
            "identity_budget": (
                identity_budget.to_dict()
                if identity_budget is not None
                else None
            ),
            "identity_validation": (
                identity_validation.to_dict()
                if identity_validation is not None
                else None
            ),
            "identity_rendering": (
                {
                    "phase": "10.5-c",
                    "enabled": bool(enable_face_primitives),
                    "rendering_changed": bool(face_shapes),
                    "legacy_face_budget": int(face_budget),
                    "planned_shape_count": int(identity_budget.total_reserved),
                    "actual_shape_count": len(face_shapes),
                    "released_shape_slots": max(0, int(face_budget) - len(face_shapes)),
                    "primary_eye_side": identity_signals.primary_eye_side,
                    "rendered_roles": [s.source_role for s in face_shapes],
                    "rendered_eye_sides": [
                        s.side_hint
                        for s in face_shapes
                        if s.source_role == "character_eye"
                    ],
                    "plan_fulfilled": (
                        len(face_shapes) == int(identity_budget.total_reserved)
                        or rollback_feature is not None
                    ),
                    "adaptive_rollback_feature": rollback_feature,
                    "adaptive_rollback_applied": rollback_feature is not None,
                }
                if identity_budget is not None
                else {
                    "phase": "10.5-c",
                    "enabled": False,
                    "rendering_changed": False,
                    "legacy_face_budget": int(face_budget),
                    "actual_shape_count": len(face_shapes),
                    "reason": (
                        "identity budget disabled or identity signals unavailable"
                    ),
                }
            ),
        }

    hair = structure.first_part(CharacterPartType.HAIR)
    if enable_hair_rules and hair is not None:
        face_part = structure.first_part(CharacterPartType.FACE)
        hair_guard_report = None
        hair_for_render = hair
        if enable_hair_body_guard:
            hair_for_render, hair_guard_report = guard_hair_from_body_core(
                hair,
                structure.first_part(CharacterPartType.TORSO),
                face_part,
                trigger_overlap_ratio=hair_body_overlap_trigger,
                max_remove_ratio=hair_body_max_remove_ratio,
            )
        flows = analyze_hair_flows(
            hair_for_render,
            face_part,
            image_rgb,
            subject_bbox=structure.subject_bbox,
        )
        hair_budget = max(
            0,
            budget.per_part.get(CharacterPartType.HAIR, 0),
        )
        hair_shapes = build_hair_shapes(
            hair_for_render,
            flows,
            image_rgb,
            hair_budget,
            start_id=sid,
        )
        shapes.extend(hair_shapes)
        sid += len(hair_shapes)
        metadata["hair"] = {
            "enabled": True,
            "shape_count": len(hair_shapes),
            "flows": [f.to_dict() for f in flows],
            "body_guard": hair_guard_report.to_dict() if hair_guard_report is not None else None,
        }

    if enable_outfit_rules:
        outfit_structure = analyze_outfit_structure(
            structure,
            regions,
        )
        outfit_budget = max(
            0,
            budget.per_part.get(CharacterPartType.OUTFIT, 0),
        )
        outfit_shapes = build_outfit_shapes(
            outfit_structure,
            image_rgb,
            regions,
            outfit_budget,
            start_id=sid,
        )
        shapes.extend(outfit_shapes)
        sid += len(outfit_shapes)
        metadata["outfit"] = {
            "enabled": True,
            "shape_count": len(outfit_shapes),
            "structure": outfit_structure.to_dict(),
        }

    if enable_prop_rules:
        descriptors = analyze_props(structure)
        prop_budget = max(
            0,
            budget.per_part.get(CharacterPartType.PROP, 0),
        )
        prop_shapes = build_prop_shapes(
            descriptors,
            image_rgb,
            prop_budget,
            start_id=sid,
        )
        shapes.extend(prop_shapes)
        sid += len(prop_shapes)
        metadata["props"] = {
            "enabled": True,
            "shape_count": len(prop_shapes),
            "descriptors": [d.to_dict() for d in descriptors],
        }

    metadata["total_shape_count"] = len(shapes)
    metadata["replaceable_parts"] = sorted({
        s.character_part
        for s in shapes
        if s.character_part not in {"unknown", ""}
    })

    return CharacterShapeResult(
        shapes=shapes,
        body_shapes=body_shapes,
        hand_shapes=hand_shapes,
        face_shapes=face_shapes,
        hair_shapes=hair_shapes,
        outfit_shapes=outfit_shapes,
        prop_shapes=prop_shapes,
        metadata=metadata,
    )


def suppress_generic_character_shapes(
    generic_shapes: list[Shape],
    result: CharacterShapeResult,
) -> list[Shape]:
    """
    Dedicated Character primitives own large body parts.

    Generic Shapes are retained only as unresolved low-confidence detail.
    This avoids the old "primitive plus a second fragmented body" double image.
    """
    md = result.metadata
    replace_face = md.get("face", {}).get("shape_count", 0) > 0
    replace_hair = md.get("hair", {}).get("shape_count", 0) > 0
    replace_outfit = md.get("outfit", {}).get("shape_count", 0) > 0
    replace_props = md.get("props", {}).get("shape_count", 0) > 0
    replace_body = md.get("body", {}).get("shape_count", 0) > 0

    body_parts = {
        "torso",
        "left_arm",
        "right_arm",
        "left_leg",
        "right_leg",
    }

    prop_region_ids = set()
    for d in md.get("props", {}).get("descriptors", []):
        prop_region_ids.update(d.get("source_region_ids") or [])

    out = []
    for shape in generic_shapes:
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


# Backwards-compatible alpha2/alpha3 helper.
def build_character_detail_shapes(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    budget: CharacterShapeBudget,
    regions: list[Region],
    *,
    enable_body_primitives: bool = True,
    enable_hand_analysis: bool = True,
    enable_hand_primitives: bool = True,
    hand_max_shapes: int = 2,
    hand_min_confidence: float = 0.30,
    enable_hand_geometry_validation: bool = True,
    hand_geometry_min_connection: float = 0.72,
    hand_geometry_min_direction: float = 0.58,
    hand_geometry_min_holding_contact: float = 0.45,
    enable_hand_validation: bool = True,
    hand_validation_min_score: float = 0.42,
    hand_validation_unknown_min_score: float = 0.42,
    enable_limb_geometry_refine: bool = True,
    limb_refine_min_iou: float = 0.46,
    enable_hair_body_guard: bool = True,
    hair_body_overlap_trigger: float = 0.44,
    hair_body_max_remove_ratio: float = 0.12,
    limb_width_scale: float = 1.0,
    enable_face_rules: bool = True,
    enable_face_primitives: bool = False,
    enable_face_identity_analysis: bool = True,
    enable_face_identity_budget: bool = True,
    abstraction_level: int = 4,
    enable_hair_rules: bool = True,
    enable_outfit_rules: bool = True,
    enable_prop_rules: bool = True,
    start_id: int = 700000,
) -> tuple[list[Shape], dict]:
    result = character_structure_to_shapes(
        image_rgb,
        structure,
        regions,
        budget,
        enable_body_primitives=enable_body_primitives,
        enable_hand_analysis=enable_hand_analysis,
        enable_hand_primitives=enable_hand_primitives,
        hand_max_shapes=hand_max_shapes,
        hand_min_confidence=hand_min_confidence,
        enable_hand_geometry_validation=enable_hand_geometry_validation,
        hand_geometry_min_connection=hand_geometry_min_connection,
        hand_geometry_min_direction=hand_geometry_min_direction,
        hand_geometry_min_holding_contact=hand_geometry_min_holding_contact,
        enable_hand_validation=enable_hand_validation,
        hand_validation_min_score=hand_validation_min_score,
        hand_validation_unknown_min_score=hand_validation_unknown_min_score,
        enable_limb_geometry_refine=enable_limb_geometry_refine,
        limb_refine_min_iou=limb_refine_min_iou,
        enable_hair_body_guard=enable_hair_body_guard,
        hair_body_overlap_trigger=hair_body_overlap_trigger,
        hair_body_max_remove_ratio=hair_body_max_remove_ratio,
        limb_width_scale=limb_width_scale,
        enable_face_rules=enable_face_rules,
        enable_face_primitives=enable_face_primitives,
        enable_face_identity_analysis=enable_face_identity_analysis,
        enable_face_identity_budget=enable_face_identity_budget,
        abstraction_level=abstraction_level,
        enable_hair_rules=enable_hair_rules,
        enable_outfit_rules=enable_outfit_rules,
        enable_prop_rules=enable_prop_rules,
        start_id=start_id,
    )
    return result.shapes, result.metadata
