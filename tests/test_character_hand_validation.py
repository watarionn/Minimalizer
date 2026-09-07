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


def test_hand_validation_report_is_attached():
    scene = _scene("Koganei-Niko_pr-img_01_a.png")
    report = scene.metadata["character"]["details"]["hands"]["candidate_validation"]
    assert report is not None
    assert report["diagnostics"]["phase"] == "11.4"
    assert report["accepted_count"] + report["rejected_count"] == report["diagnostics"]["input_count"]
    assert all(0.0 <= item["score"] <= 1.0 for item in report["items"])


def test_hand_validation_suppresses_obvious_thin_tip():
    scene = _scene("Koganei-Niko_pr-img_01_a.png")
    report = scene.metadata["character"]["details"]["hands"]["candidate_validation"]
    assert report["rejected_count"] >= 1
    assert any("too_thin_for_hand" in item["reasons"] for item in report["items"] if not item["accepted"])
    assert len([s for s in scene.shapes if s.source_role == "character_hand_base"]) == report["accepted_count"]


def test_holding_prop_can_survive_without_skin_support():
    scene = _scene("Nerissa-Ravencroft_pr-img_01.webp")
    report = scene.metadata["character"]["details"]["hands"]["candidate_validation"]
    holding = [item for item in report["items"] if item["intent"] == "holding"]
    assert holding and holding[0]["accepted"] is True


def test_hand_validation_can_be_disabled_independently():
    on = _scene("Rindo-Chihaya_pr-img_01_a.png")
    off = _scene("Rindo-Chihaya_pr-img_01_a.png", enable_hand_validation=False)
    assert on.metadata["character"]["details"]["hands"]["candidate_validation"] is not None
    assert off.metadata["character"]["details"]["hands"]["candidate_validation"] is None
    assert len([s for s in off.shapes if s.source_role == "character_hand_base"]) >= len([s for s in on.shapes if s.source_role == "character_hand_base"])
