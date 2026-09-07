from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.hand_quality import evaluate_hand_quality

ASSETS = Path(__file__).parent / "assets" / "corpus"


def _scene(name: str, **overrides):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        **overrides,
    )
    return minimalize(ASSETS / name, cfg)


def test_hand_quality_is_reported_for_character_scene():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")
    cq = scene.metadata["character_quality"]
    assert "hand_quality_score" in cq
    assert "hands" in cq["diagnostics"]
    assert scene.metadata["engine_version"] == "0.3.0"


def test_hand_quality_can_be_disabled_without_reenabling_it():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png", enable_hand_quality=False)
    cq = scene.metadata["character_quality"]
    assert cq["hand_applicable"] is False
    assert cq["diagnostics"]["hands"]["disabled_by_config"] is True


def test_limb_refine_never_changes_body_shape_count():
    off = _scene("Kikirara-Vivi_pr-img_01_a.webp", enable_limb_geometry_refine=False)
    on = _scene("Kikirara-Vivi_pr-img_01_a.webp", enable_limb_geometry_refine=True)
    off_body = off.metadata["character"]["details"]["body"]
    on_body = on.metadata["character"]["details"]["body"]
    assert on_body["shape_count"] == off_body["shape_count"]
    assert on_body["limb_refine"] is not None
    assert on_body["limb_refine"]["diagnostics"]["shape_count_changed"] is False


def test_hair_body_guard_is_local_and_bounded():
    scene = _scene("Nerissa-Ravencroft_pr-img_01.webp", enable_hair_body_guard=True)
    hair = scene.metadata["character"]["details"]["hair"]
    guard = hair["body_guard"]
    assert guard is not None
    if guard["applied"]:
        assert guard["hair_pixels_after"] >= guard["hair_pixels_before"] * 0.88
        assert guard["overlap_after"] <= guard["overlap_before"]


def test_hand_quality_helper_handles_no_hand_metadata():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png", enable_hand_analysis=False)
    report = evaluate_hand_quality(scene)
    assert report.applicable is False
    assert report.score == 1.0
