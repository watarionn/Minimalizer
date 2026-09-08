from minimalize_engine.analysis.shape_cleanup import cleanup_minimal_shapes
from minimalize_engine.models import Scene, Shape
from minimalize_engine.target_style import (
    apply_rinka_reference_style,
    rinka_reference_config,
)


def _rect(i, x, y, w, h, *, importance=0.4, semantic="generic", part="unknown", role="misc"):
    return Shape(
        id=i,
        shape_type="rectangle",
        fill_color=(80, 90, 100),
        x=x,
        y=y,
        width=w,
        height=h,
        importance=importance,
        semantic_type=semantic,
        character_part=part,
        source_role=role,
        layer_name="foreground",
    )


def test_rinka_reference_config_is_opt_in_and_more_geometric():
    stable = rinka_reference_config(4, target_max_shapes=50, line_mode="low")
    assert stable.target_max_shapes == 50
    assert stable.line_mode == "low"

    cfg = rinka_reference_config(4)
    assert cfg.target_max_shapes == 38
    assert cfg.palette_colors == 6
    assert cfg.line_mode == "none"
    assert cfg.enable_face_primitives is False
    assert cfg.character_hand_max_shapes == 1
    assert cfg.cleanup_remove_duplicates is True
    assert cfg.cleanup_role_fragment_merge is True
    assert cfg.enable_auto_retry is False
    assert cfg.enable_character_auto_retry is False
    assert cfg.contour_epsilon_ratio >= 0.032


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
