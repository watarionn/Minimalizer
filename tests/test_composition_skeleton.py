from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def test_sample_detects_central_composition_corridor():
    path = Path(__file__).parents[1] / "examples" / "input.webp"
    if not path.exists():
        return

    cfg = MinimalizeConfig.from_level(4, line_mode="none", enable_auto_retry=False)
    scene = minimalize(path, cfg)
    skeleton = scene.metadata.get("composition_skeleton", {})

    assert skeleton.get("active") is True
    assert 0 < skeleton.get("corridor_width", 0) < scene.width * 0.30
    assert scene.width * 0.25 < skeleton.get("center_x", 0) < scene.width * 0.75
    assert skeleton.get("corridor_score", 0) >= 0.20


def test_composition_skeleton_can_be_disabled():
    path = Path(__file__).parents[1] / "examples" / "input.webp"
    if not path.exists():
        return

    cfg = MinimalizeConfig.from_level(
        4,
        enable_auto_retry=False,
        line_mode="none",
        enable_composition_skeleton=False,
    )
    scene = minimalize(path, cfg)
    skeleton = scene.metadata.get("composition_skeleton", {})
    assert skeleton.get("active") is False


def test_water_macro_is_corridor_shaped_when_skeleton_active():
    path = Path(__file__).parents[1] / "examples" / "input.webp"
    if not path.exists():
        return

    cfg = MinimalizeConfig.from_level(4, line_mode="none", enable_auto_retry=False)
    scene = minimalize(path, cfg)
    water_bases = [s for s in scene.shapes if s.source_role == "water_base"]
    assert water_bases

    base = water_bases[0]
    assert base.shape_type == "polygon"
    xs = [x for x, _ in base.points]
    # The water base should no longer cover the full canvas width at the top.
    assert min(xs) > 0 or max(xs) < scene.width
