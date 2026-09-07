from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize


def test_scene_contains_macro_roles():
    path = Path(__file__).parents[1] / "examples" / "input.webp"
    if not path.exists():
        return

    scene = minimalize(path, MinimalizeConfig.from_level(4, line_mode="none", enable_auto_retry=False))
    roles = scene.metadata.get("role_counts", {})
    assert roles.get("structure", 0) >= 1
    assert roles.get("water", 0) >= 1
    assert roles.get("boat", 0) >= 1
