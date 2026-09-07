from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.layout import shapes_bounds


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


def test_fullbody_layout_normalizes_top_and_foot_margins():
    scene = _scene("Isaki-Riona_pr-img_01_a.png")
    layout = scene.metadata["character"]["layout"]

    assert scene.metadata["engine_version"] == "0.3.0"
    assert layout["enabled"] is True
    assert abs(layout["headroom_ratio"] - 0.055) <= 0.012
    assert abs(layout["footroom_ratio"] - 0.040) <= 0.012
    assert layout["metrics"]["clipped"] is False


def test_layout_keeps_all_generated_shapes_inside_canvas():
    scene = _scene("Nerissa-Ravencroft_pr-img_01.webp")
    x0, y0, x1, y1 = shapes_bounds(scene.shapes)

    assert x0 >= -1e-3
    assert y0 >= -1e-3
    assert x1 <= scene.width + 1e-3
    assert y1 <= scene.height + 1e-3


def test_pose_aware_layout_moves_visual_center_toward_target():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")
    layout = scene.metadata["character"]["layout"]

    before = abs(
        layout["visual_center_before"][0]
        - layout["target_visual_center"][0]
    ) / scene.width
    after = layout["metrics"]["center_error"]

    assert after < before
    assert abs(layout["pose_bias_x"]) > 0.1


def test_left_reaching_pose_receives_positive_left_breathing_bias():
    scene = _scene("Isaki-Riona_pr-img_01_a.png")
    layout = scene.metadata["character"]["layout"]

    # Positive bias moves the weighted body core right, leaving more room for
    # the prominently extended left hand.
    assert layout["pose_bias_x"] > 0


def test_character_layout_can_be_disabled_independently():
    scene = _scene(
        "Isaki-Riona_pr-img_01_a.png",
        enable_character_layout=False,
    )
    ch = scene.metadata["character"]

    assert ch["enabled"] is True
    assert ch["layout"]["enabled"] is False


def test_general_scene_is_not_routed_through_character_layout():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
    )
    scene = minimalize(ROOT / "examples" / "input.webp", cfg)

    assert scene.metadata["subject_mode"] is False
    assert scene.metadata["character"]["enabled"] is False
