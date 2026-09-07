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


def test_hand_geometry_report_is_attached_when_hands_render():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")
    hands = scene.metadata["character"]["details"]["hands"]
    report = hands["geometry_validation"]
    assert report is not None
    assert report["diagnostics"]["phase"] == "11.3"
    assert report["hands"]
    assert 0.0 <= report["score"] <= 1.0
    for item in report["hands"]:
        assert 0.0 <= item["connection_score"] <= 1.0
        assert 0.0 <= item["direction_score"] <= 1.0


def test_hand_geometry_never_adds_extra_shapes():
    on = _scene("Isaki-Riona_pr-img_01_a.png")
    off = _scene("Isaki-Riona_pr-img_01_a.png", enable_hand_geometry_validation=False)
    hon = [s for s in on.shapes if s.source_role == "character_hand_base"]
    hoff = [s for s in off.shapes if s.source_role == "character_hand_base"]
    assert len(hon) == len(hoff)
    assert len(hon) <= 2


def test_hand_geometry_can_be_disabled_independently():
    scene = _scene("Mizumiya-Su_pr-img_01_a.png", enable_hand_geometry_validation=False)
    hands = scene.metadata["character"]["details"]["hands"]
    assert hands["analysis"] is not None
    assert hands["rendering"]["enabled"] is True
    assert hands["geometry_validation"] is None


def test_hand_geometry_keeps_arm_connection_readable():
    scene = _scene("Juufuutei-Raden_pr-img_01_a.webp")
    report = scene.metadata["character"]["details"]["hands"]["geometry_validation"]
    assert report is not None
    assert min(item["connection_score"] for item in report["hands"]) >= 0.35
