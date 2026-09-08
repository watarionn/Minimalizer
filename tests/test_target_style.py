from minimalize_engine.analysis.shape_cleanup import cleanup_minimal_shapes
from minimalize_engine.models import Scene, Shape
from minimalize_engine.target_style import (
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
    assert out.metadata["target_style"]["version"] == "phase2.1"
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
