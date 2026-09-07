from pathlib import Path
from minimalize_engine import MinimalizeConfig, minimalize


def test_smoke_example():
    path = Path(__file__).parents[1] / "examples" / "input.webp"
    if not path.exists():
        return
    scene = minimalize(path, MinimalizeConfig.from_level(4, line_mode="none", enable_auto_retry=False))
    assert scene.width <= 640
    assert scene.height <= 640
    assert len(scene.shapes) > 0
    assert len(scene.shapes) <= 50
