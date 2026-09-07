from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene(name: str, **overrides):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=34,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        **overrides,
    )
    return minimalize(CORPUS / name, cfg)


def test_hand_primitives_render_at_most_one_shape_per_hand():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")
    meta = scene.metadata["character"]["details"]["hands"]
    hand_shapes = [s for s in scene.shapes if s.source_role == "character_hand_base"]

    assert meta["enabled"] is True
    assert meta["rendering"]["enabled"] is True
    assert len(hand_shapes) == meta["shape_count"]
    assert 1 <= len(hand_shapes) <= 2
    assert len({s.side_hint for s in hand_shapes}) == len(hand_shapes)
    assert all(s.shape_type == "polygon" for s in hand_shapes)
    assert all(s.layer_name == "character_body_detail" for s in hand_shapes)
    assert all(s.semantic_type.startswith("character_hand_") for s in hand_shapes)


def test_hand_primitive_switch_only_removes_dedicated_hand_shapes():
    on = _scene("Mizumiya-Su_pr-img_01_a.png")
    off = _scene("Mizumiya-Su_pr-img_01_a.png", enable_hand_primitives=False)

    assert on.metadata["character"]["details"]["hands"]["rendering_changed"] is True
    assert off.metadata["character"]["details"]["hands"]["rendering_changed"] is False
    assert off.metadata["character"]["details"]["hands"]["analysis"] is not None
    assert not any(s.source_role == "character_hand_base" for s in off.shapes)
    assert any(s.source_role == "character_hand_base" for s in on.shapes)


def test_hand_primitives_respect_confidence_gate():
    scene = _scene(
        "Isaki-Riona_pr-img_01_a.png",
        character_hand_min_confidence=0.99,
    )
    meta = scene.metadata["character"]["details"]["hands"]
    assert meta["analysis"]["diagnostics"]["detected_hand_count"] >= 1
    assert meta["shape_count"] == 0
    assert not any(s.source_role == "character_hand_base" for s in scene.shapes)


def test_hand_primitives_can_be_disabled_without_disabling_analysis():
    scene = _scene(
        "Juufuutei-Raden_pr-img_01_a.webp",
        enable_hand_primitives=False,
    )
    meta = scene.metadata["character"]["details"]["hands"]
    assert meta["enabled"] is True
    assert meta["analysis"] is not None
    assert meta["rendering"]["enabled"] is False
    assert meta["shape_count"] == 0
