from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize

ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"

def _scene(**overrides):
    cfg = MinimalizeConfig.from_level(
        4, analysis_max_side=220, target_max_shapes=30, line_mode="none",
        enable_auto_retry=False, enable_character_auto_retry=False, **overrides
    )
    return minimalize(CORPUS / "Rindo-Chihaya_pr-img_01_a.png", cfg)

def test_face_primitives_are_off_by_default_but_analysis_stays_on():
    scene = _scene()
    face = scene.metadata["character"]["details"]["face"]
    assert scene.metadata["engine_version"] == "0.3.0"
    assert face["enabled"] is True
    assert face["rendering_enabled"] is False
    assert face["shape_count"] == 0
    assert face["layout"] is not None
    assert face["identity_signals"] is not None
    assert scene.metadata["character_quality"]["face_applicable"] is False

def test_face_primitives_can_be_opted_in_explicitly():
    scene = _scene(enable_face_primitives=True)
    face = scene.metadata["character"]["details"]["face"]
    assert face["rendering_enabled"] is True
    assert face["shape_count"] >= 1
