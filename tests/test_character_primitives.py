from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene(name: str, **overrides):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=260,
        target_max_shapes=34,
        line_mode="none",
        enable_auto_retry=False,
        **overrides,
    )
    return minimalize(CORPUS / name, cfg)


def test_integrated_character_shape_result_contains_body_face_hair_outfit():
    scene = _scene("Isaki-Riona_pr-img_01_a.png", enable_face_primitives=True)
    ch = scene.metadata["character"]
    result = ch["shape_result"]

    assert scene.metadata["engine_version"] == "0.3.0"
    assert result["body_shape_count"] >= 4
    assert result["face_shape_count"] >= 3
    assert result["hair_shape_count"] >= 2
    assert result["outfit_shape_count"] >= 3
    assert result["shape_count"] == (
        result["body_shape_count"]
        + result["hand_shape_count"]
        + result["face_shape_count"]
        + result["hair_shape_count"]
        + result["outfit_shape_count"]
        + result["prop_shape_count"]
    )


def test_body_primitives_emit_torso_and_both_legs_for_fullbody():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")

    body_shapes = [
        s for s in scene.shapes
        if s.layer_name == "character_body_base"
    ]
    parts = {s.character_part for s in body_shapes}

    assert "torso" in parts
    assert "left_leg" in parts
    assert "right_leg" in parts
    assert all(s.shape_type == "polygon" for s in body_shapes)


def test_body_budget_reserves_only_one_big_shape_per_detected_body_part():
    scene = _scene("Koganei-Niko_pr-img_01_a.png")
    ch = scene.metadata["character"]

    reserve = ch["budget"]["reserved_body"]
    body_count = ch["details"]["body"]["shape_count"]

    assert 3 <= reserve <= 5
    assert body_count == reserve


def test_generic_high_confidence_body_shapes_are_suppressed():
    scene = _scene("Isaki-Riona_pr-img_01_a.png")
    body_parts = {"torso", "left_arm", "right_arm", "left_leg", "right_leg"}

    # Dedicated shapes have no source Region id. Any surviving generic body
    # detail should be deliberately low confidence.
    generic_body = [
        s for s in scene.shapes
        if s.source_region_id is not None and s.character_part in body_parts
    ]
    assert all(s.part_confidence < 0.16 for s in generic_body)


def test_body_primitives_can_be_disabled_without_disabling_character_engine():
    scene = _scene(
        "Isaki-Riona_pr-img_01_a.png",
        enable_body_primitives=False,
    )
    ch = scene.metadata["character"]

    assert ch["enabled"] is True
    assert ch["details"]["body"]["enabled"] is False
    assert ch["details"]["body"]["shape_count"] == 0
    assert ch["shape_result"]["body_shape_count"] == 0
