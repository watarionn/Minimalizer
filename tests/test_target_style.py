from minimalize_engine.analysis.shape_cleanup import cleanup_minimal_shapes
from minimalize_engine.models import Scene, Shape
import numpy as np

from minimalize_engine.target_hierarchy import OpaqueSubjectHierarchy, estimate_opaque_subject_zones, estimate_structure_subject_zones
from minimalize_engine.target_style import (
    _merge_mass_pair,
    apply_rinka_reference_style,
    rinka_reference_config,
)


def _rect(
    i,
    x,
    y,
    w,
    h,
    *,
    importance=0.4,
    semantic="generic",
    part="unknown",
    role="misc",
    layer="foreground",
    fill_color=(80, 90, 100),
):
    return Shape(
        id=i,
        shape_type="rectangle",
        fill_color=fill_color,
        x=x,
        y=y,
        width=w,
        height=h,
        importance=importance,
        semantic_type=semantic,
        character_part=part,
        source_role=role,
        layer_name=layer,
    )


def test_rinka_reference_config_is_opt_in_and_more_geometric():
    overridden = rinka_reference_config(4, target_max_shapes=50, line_mode="low")
    assert overridden.target_max_shapes == 50
    assert overridden.line_mode == "low"

    cfg = rinka_reference_config(4)
    assert cfg.target_max_shapes == 28
    assert cfg.palette_colors == 6
    assert cfg.line_mode == "none"
    assert cfg.enable_face_primitives is False
    assert cfg.character_hand_max_shapes == 1
    assert cfg.cleanup_remove_duplicates is True
    assert cfg.cleanup_role_fragment_merge is True
    assert cfg.enable_auto_retry is False
    assert cfg.enable_character_auto_retry is False
    assert cfg.contour_epsilon_ratio >= 0.040


def test_stable_cleanup_still_protects_thin_hair_fragment():
    hair = _rect(
        1,
        10,
        10,
        2,
        14,
        importance=0.3,
        semantic="character_hair_strand",
        part="hair",
        role="character_hair",
    )
    out, report = cleanup_minimal_shapes([hair], 220, 220)
    assert [s.id for s in out] == [1]
    assert report.protected_count == 1


def test_rinka_style_removes_low_value_hair_sliver_but_keeps_major_hair_mass():
    major_hair = _rect(
        1,
        12,
        15,
        44,
        70,
        importance=0.92,
        semantic="character_hair_mass",
        part="hair",
        role="character_hair",
    )
    hair_sliver = _rect(
        2,
        60,
        20,
        2,
        16,
        importance=0.30,
        semantic="character_hair_strand",
        part="hair",
        role="character_hair",
    )
    scene = Scene(220, 220, (240, 240, 235), [major_hair, hair_sliver])

    out = apply_rinka_reference_style(scene)

    assert [s.id for s in out.shapes] == [1]
    assert out.metadata["target_style"]["name"] == "rinka_reference"
    assert out.metadata["target_style"]["version"] == "phase4"
    assert out.metadata["target_style"]["shape_count_before"] == 2
    assert out.metadata["target_style"]["shape_count_after"] == 1


def test_rinka_style_can_reduce_small_hand_fragment_without_losing_large_hand_mass():
    palm = _rect(
        1,
        20,
        20,
        20,
        16,
        importance=0.91,
        semantic="character_hand_palm",
        part="left_hand",
        role="character_hand",
    )
    finger = _rect(
        2,
        40,
        23,
        2,
        13,
        importance=0.35,
        semantic="character_hand_finger",
        part="left_hand",
        role="character_hand",
    )
    scene = Scene(220, 220, (245, 245, 240), [palm, finger])

    out = apply_rinka_reference_style(scene)

    assert [s.id for s in out.shapes] == [1]


def test_rinka_style_polygonizes_circle_and_ellipse_into_straight_edges():
    circle = Shape(
        id=1,
        shape_type="circle",
        fill_color=(220, 210, 180),
        cx=50,
        cy=50,
        rx=12,
        ry=12,
        importance=0.9,
        layer_name="foreground",
    )
    ellipse = Shape(
        id=2,
        shape_type="ellipse",
        fill_color=(100, 130, 120),
        cx=120,
        cy=100,
        rx=18,
        ry=10,
        importance=0.9,
        layer_name="foreground",
    )
    scene = Scene(220, 220, (20, 30, 30), [circle, ellipse])

    out = apply_rinka_reference_style(scene, curve_polygon_sides=8)

    assert len(out.shapes) == 2
    assert all(s.shape_type == "polygon" for s in out.shapes)
    assert all(len(s.points) == 8 for s in out.shapes)
    assert all(s.cx is None and s.cy is None and s.rx is None and s.ry is None for s in out.shapes)


def test_high_importance_character_fragment_remains_protected_in_target_style():
    important_strand = _rect(
        1,
        10,
        10,
        2,
        14,
        importance=0.95,
        semantic="character_hair_signature_lock",
        part="hair",
        role="character_hair",
    )
    scene = Scene(220, 220, (240, 240, 235), [important_strand])

    out = apply_rinka_reference_style(scene)

    assert [s.id for s in out.shapes] == [1]


def test_phase2_merges_nearby_similar_garment_shapes_into_one_mass():
    a = _rect(
        1, 20, 30, 28, 32,
        importance=0.78,
        semantic="character_outfit_main",
        part="outfit",
        role="character_outfit",
        fill_color=(42, 44, 48),
    )
    b = _rect(
        2, 49, 34, 24, 26,
        importance=0.62,
        semantic="character_outfit_fold",
        part="outfit",
        role="character_outfit",
        fill_color=(50, 49, 53),
    )
    scene = Scene(220, 220, (240, 240, 235), [a, b])

    out = apply_rinka_reference_style(scene)

    assert len(out.shapes) == 1
    assert out.shapes[0].shape_type == "polygon"
    assert out.metadata["target_style"]["mass_merges"] == 1


def test_phase2_faceless_suppression_removes_small_internal_face_fragments():
    carrier = _rect(
        1, 42, 35, 28, 30,
        importance=0.82,
        semantic="skin_mass",
        fill_color=(232, 202, 184),
    )
    eye_like = _rect(
        2, 48, 45, 7, 5,
        importance=0.55,
        semantic="generic_accent",
        fill_color=(80, 70, 70),
    )
    mouth_like = _rect(
        3, 57, 55, 8, 4,
        importance=0.50,
        semantic="generic_accent",
        fill_color=(180, 90, 90),
    )
    metadata = {
        "subject_mode": True,
        "character": {
            "structure": {
                "parts": [
                    {"part_type": "face", "bbox": [40, 32, 34, 38]},
                ]
            }
        },
    }
    scene = Scene(120, 120, (245, 245, 240), [carrier, eye_like, mouth_like], metadata)

    out = apply_rinka_reference_style(scene)

    assert [s.id for s in out.shapes] == [1]
    assert out.metadata["target_style"]["face_fragments_removed"] == 2


def test_phase2_background_compression_keeps_fewer_low_value_background_shapes():
    shapes = []
    for i in range(12):
        shapes.append(
            _rect(
                i + 1,
                4 + (i % 4) * 24,
                4 + (i // 4) * 24,
                16,
                16,
                importance=0.30 + i * 0.01,
                semantic="generic_panel",
                role="background_panel",
                layer="background",
                fill_color=(20 + i * 12, 30, 40),
            )
        )
    scene = Scene(120, 120, (245, 245, 240), shapes, {"subject_mode": False})

    out = apply_rinka_reference_style(scene)

    assert len(out.shapes) <= 10
    assert out.metadata["target_style"]["background_removed"] >= 2


def test_phase2_final_cap_enforces_target_shape_budget():
    shapes = [
        _rect(
            i + 1,
            5 + i * 12,
            20,
            8,
            18,
            importance=0.30 + i * 0.08,
            semantic="generic",
            layer="foreground",
            fill_color=(30 + i * 20, 60, 90),
        )
        for i in range(6)
    ]
    scene = Scene(120, 120, (245, 245, 240), shapes)

    out = apply_rinka_reference_style(scene, target_max_shapes=3)

    assert len(out.shapes) == 3
    assert out.metadata["target_style"]["cap_removed"] == 3



def test_phase4_opaque_zones_are_recorded_and_can_suppress_head_micro_fragment():
    mask = np.zeros((140, 120), dtype=np.uint8)
    mask[12:132, 30:90] = 1
    hierarchy = OpaqueSubjectHierarchy(True, 0.84, float(mask.mean()), (30, 12, 90, 132), "accepted", mask)
    base_scene = Scene(120, 140, (245, 245, 240), [], {"subject_mode": False})
    zones = estimate_opaque_subject_zones(hierarchy, base_scene)
    carrier = _rect(1, 46, 20, 28, 24, importance=0.94, semantic="skin_mass", fill_color=(224, 190, 170))
    micro = _rect(2, 55, 27, 5, 4, importance=0.45, semantic="generic_accent", fill_color=(70, 60, 60))
    torso = _rect(3, 44, 60, 32, 42, importance=0.80, semantic="generic_body", fill_color=(55, 70, 90))
    scene = Scene(120, 140, (245, 245, 240), [carrier, micro, torso], {"subject_mode": False})

    out = apply_rinka_reference_style(scene, opaque_hierarchy=hierarchy, opaque_zones=zones)

    meta = out.metadata["target_style"]["opaque_zones"]
    assert meta["enabled"] is True
    assert meta["head_shapes"] >= 1
    assert meta["torso_shapes"] >= 1
    fragment = next((shape for shape in out.shapes if shape.id == 2), None)
    assert fragment is None or fragment.semantic_type == "target_zone_head_fragment"
    assert out.metadata["target_style"]["face_fragments_removed"] >= 1


def test_phase4_refines_hair_clothing_and_merges_nearby_arm_blocks():
    mask = np.zeros((140, 120), dtype=np.uint8)
    mask[12:132, 30:90] = 1
    hierarchy = OpaqueSubjectHierarchy(True, 0.90, float(mask.mean()), (30, 12, 90, 132), "accepted", mask)
    base_scene = Scene(120, 140, (245, 245, 240), [], {"subject_mode": False})
    zones = estimate_opaque_subject_zones(hierarchy, base_scene)

    face = _rect(1, 50, 20, 20, 20, importance=0.93, semantic="generic", fill_color=(224, 190, 170))
    hair = _rect(2, 44, 14, 30, 18, importance=0.82, semantic="generic", fill_color=(55, 48, 58))
    clothing = _rect(3, 45, 54, 30, 32, importance=0.82, semantic="generic", fill_color=(50, 72, 96))
    left_a = _rect(4, 31, 56, 5, 14, importance=0.82, semantic="generic", fill_color=(224, 190, 170))
    left_b = _rect(5, 38, 56, 5, 14, importance=0.80, semantic="generic", fill_color=(224, 190, 170))
    right = _rect(6, 79, 56, 10, 18, importance=0.84, semantic="generic", fill_color=(224, 190, 170))
    scene = Scene(120, 140, (245, 245, 240), [face, hair, clothing, left_a, left_b, right], {"subject_mode": False})

    out = apply_rinka_reference_style(scene, opaque_hierarchy=hierarchy, opaque_zones=zones)
    meta = out.metadata["target_style"]["opaque_zones"]

    assert meta["face_reference_source"] == "bilateral_arms"
    assert meta["inferred_hair_shapes"] >= 1
    assert meta["inferred_clothing_shapes"] >= 1
    assert meta["hair_shapes"] >= 1
    assert meta["clothing_shapes"] >= 1
    assert out.metadata["target_style"]["mass_merges"] >= 1
    roles = [shape.source_role for shape in out.shapes]
    assert any("opaque_zone:hair:" in role for role in roles)
    assert any("opaque_zone:clothing:" in role for role in roles)


def test_phase4_can_infer_light_hair_from_geometry_when_dark_contrast_is_absent():
    mask = np.zeros((140, 120), dtype=np.uint8)
    mask[12:132, 30:90] = 1
    hierarchy = OpaqueSubjectHierarchy(True, 0.90, float(mask.mean()), (30, 12, 90, 132), "accepted", mask)
    zones = estimate_opaque_subject_zones(hierarchy, Scene(120, 140, (245, 245, 240), [], {"subject_mode": False}))
    face = _rect(1, 50, 24, 20, 20, importance=0.93, fill_color=(224, 190, 170))
    light_hair = _rect(2, 45, 14, 30, 18, importance=0.84, fill_color=(244, 222, 112))
    left = _rect(3, 31, 56, 10, 18, importance=0.84, fill_color=(224, 190, 170))
    right = _rect(4, 79, 56, 10, 18, importance=0.84, fill_color=(224, 190, 170))
    torso = _rect(5, 46, 55, 28, 28, importance=0.84, fill_color=(62, 80, 104))
    scene = Scene(120, 140, (245, 245, 240), [face, light_hair, left, right, torso], {"subject_mode": False})

    out = apply_rinka_reference_style(scene, opaque_hierarchy=hierarchy, opaque_zones=zones)
    meta = out.metadata["target_style"]["opaque_zones"]

    assert meta["inferred_hair_mode"] == "geometry_contrast"
    assert meta["inferred_hair_shapes"] == 1
    assert any(shape.id == 2 and "opaque_zone:hair:" in shape.source_role for shape in out.shapes)


def test_phase4_propagates_clothing_to_nearby_same_mass_piece():
    mask = np.zeros((140, 120), dtype=np.uint8)
    mask[12:132, 30:90] = 1
    hierarchy = OpaqueSubjectHierarchy(True, 0.90, float(mask.mean()), (30, 12, 90, 132), "accepted", mask)
    zones = estimate_opaque_subject_zones(hierarchy, Scene(120, 140, (245, 245, 240), [], {"subject_mode": False}))
    face = _rect(1, 50, 24, 20, 20, importance=0.93, fill_color=(224, 190, 170))
    left = _rect(2, 31, 56, 10, 18, importance=0.84, fill_color=(224, 190, 170))
    right = _rect(3, 79, 56, 10, 18, importance=0.84, fill_color=(224, 190, 170))
    garment_a = _rect(4, 46, 55, 28, 24, importance=0.84, fill_color=(54, 78, 108))
    garment_b = _rect(5, 48, 78, 24, 10, importance=0.81, fill_color=(58, 82, 112))
    scene = Scene(120, 140, (245, 245, 240), [face, left, right, garment_a, garment_b], {"subject_mode": False})

    out = apply_rinka_reference_style(scene, opaque_hierarchy=hierarchy, opaque_zones=zones)
    meta = out.metadata["target_style"]["opaque_zones"]

    assert meta["inferred_clothing_shapes"] >= 2
    assert meta["propagated_clothing_shapes"] >= 1


def test_phase4_arm_mass_merge_preserves_left_right_sides():
    left = _rect(1, 20, 20, 10, 14, importance=0.84, role="opaque_zone:arm:test", fill_color=(220, 190, 170))
    right = _rect(2, 31, 20, 10, 14, importance=0.84, role="opaque_zone:arm:test", fill_color=(220, 190, 170))
    left.side_hint = "left"
    right.side_hint = "right"

    assert _merge_mass_pair(left, right, 120.0) is None
    right.side_hint = "left"
    assert _merge_mass_pair(left, right, 120.0) is not None


def test_phase4_structure_bridge_keeps_character_base_and_relaxes_generic_head_fragment():
    parts = [
        {"part_type": "subject", "bbox": [20, 5, 80, 130], "confidence": 1.0},
        {"part_type": "head", "bbox": [42, 20, 38, 42], "confidence": 0.76},
        {"part_type": "face", "bbox": [50, 31, 20, 20], "confidence": 0.78},
        {"part_type": "hair", "bbox": [36, 18, 50, 55], "confidence": 0.68},
        {"part_type": "torso", "bbox": [43, 58, 36, 34], "confidence": 0.72},
        {"part_type": "outfit", "bbox": [38, 58, 46, 55], "confidence": 0.77},
        {"part_type": "left_arm", "bbox": [24, 56, 16, 42], "confidence": 0.56},
        {"part_type": "right_arm", "bbox": [82, 56, 16, 42], "confidence": 0.56},
        {"part_type": "left_leg", "bbox": [42, 94, 18, 40], "confidence": 0.60},
        {"part_type": "right_leg", "bbox": [62, 94, 18, 40], "confidence": 0.60},
    ]
    metadata = {"subject_mode": True, "character": {"structure": {"parts": parts}}}
    hair_base = _rect(1, 38, 20, 45, 34, importance=0.95, semantic="character_hair", part="hair", role="character_hair_base", layer="character_hair_base", fill_color=(55, 48, 58))
    face_fragment = _rect(2, 55, 37, 3, 3, importance=0.45, semantic="subject_detail", part="head", role="misc", layer="midground", fill_color=(80, 70, 70))
    torso = _rect(3, 46, 62, 30, 28, importance=0.98, semantic="character_torso", part="torso", role="character_torso_base", layer="character_body_base", fill_color=(80, 90, 110))
    scene = Scene(120, 140, (245, 245, 240), [hair_base, face_fragment, torso], metadata)
    zones = estimate_structure_subject_zones(scene)

    out = apply_rinka_reference_style(scene, opaque_zones=zones)
    meta = out.metadata["target_style"]["opaque_zones"]

    assert meta["enabled"] is True
    assert meta["zone_source"] == "character_structure"
    assert 1 in [shape.id for shape in out.shapes]
    fragment = next((shape for shape in out.shapes if shape.id == 2), None)
    assert fragment is None or fragment.semantic_type == "target_zone_head_fragment"


def test_phase4_structure_prunes_only_redundant_low_value_clothing_candidates():
    parts = [
        {"part_type": "subject", "bbox": [20, 5, 80, 130], "confidence": 1.0},
        {"part_type": "head", "bbox": [42, 20, 38, 42], "confidence": 0.76},
        {"part_type": "face", "bbox": [50, 31, 20, 20], "confidence": 0.78},
        {"part_type": "hair", "bbox": [36, 18, 50, 55], "confidence": 0.68},
        {"part_type": "torso", "bbox": [43, 58, 36, 34], "confidence": 0.72},
        {"part_type": "outfit", "bbox": [38, 58, 46, 55], "confidence": 0.77},
    ]
    metadata = {"subject_mode": True, "character": {"structure": {"parts": parts}}}
    outfit = _rect(1, 40, 60, 42, 50, importance=0.98, semantic="character_outfit_torso", part="outfit", role="character_outfit_torso", layer="character_outfit_base", fill_color=(70, 90, 120))
    redundant = _rect(2, 48, 70, 6, 10, importance=0.40, semantic="generic", role="vertical", layer="accents", fill_color=(110, 120, 135))
    strong = _rect(3, 60, 70, 6, 10, importance=0.80, semantic="generic", role="vertical", layer="accents", fill_color=(120, 130, 145))
    face_detail = _rect(4, 55, 35, 5, 5, importance=0.30, semantic="subject_detail", part="head", role="vertical", layer="accents", fill_color=(100, 80, 80))
    scene = Scene(120, 140, (245, 245, 240), [outfit, redundant, strong, face_detail], metadata)
    zones = estimate_structure_subject_zones(scene)

    out = apply_rinka_reference_style(scene, opaque_zones=zones)
    ids = {shape.id for shape in out.shapes}

    assert out.metadata["target_style"]["structure_redundant_removed"] == 1
    assert 2 not in ids
    assert 3 in ids
