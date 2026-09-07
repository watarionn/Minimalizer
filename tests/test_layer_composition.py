from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def test_layer_composition_metadata_and_budget():
    path = Path(__file__).parents[1] / "examples" / "input.webp"
    if not path.exists():
        return

    cfg = MinimalizeConfig.from_level(4, line_mode="none", enable_auto_retry=False)
    scene = minimalize(path, cfg)
    layers = scene.metadata.get("layer_counts", {})

    assert scene.metadata.get("engine_version") == "0.3.0"
    assert scene.metadata.get("macro_shape_count", 0) <= 5
    assert sum(layers.values()) == scene.metadata.get("region_count")
    assert layers.get("accents", 0) <= 8
    assert scene.metadata.get("shape_count", 0) <= cfg.target_max_shapes + 4


def test_layer_composition_can_be_disabled():
    path = Path(__file__).parents[1] / "examples" / "input.webp"
    if not path.exists():
        return

    cfg = MinimalizeConfig.from_level(
        4,
        enable_auto_retry=False,
        line_mode="none",
        enable_layer_composition=False,
        enable_macro_underlays=False,
    )
    scene = minimalize(path, cfg)
    assert scene.metadata.get("macro_shape_count", 0) == 0
