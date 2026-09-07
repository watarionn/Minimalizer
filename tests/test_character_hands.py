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


def test_hand_analysis_is_attached_without_rendering_changes():
    on = _scene("Isaki-Riona_pr-img_01_a.png", enable_hand_primitives=False)
    off = _scene("Isaki-Riona_pr-img_01_a.png", enable_hand_analysis=False, enable_hand_primitives=False)

    hands = on.metadata["character"]["details"]["hands"]
    assert hands["enabled"] is True
    assert hands["rendering_changed"] is False
    assert hands["analysis"]["diagnostics"]["phase"] == "11.1"

    # Phase 11.1 is analysis-only. Turning it off must not change shapes.
    sig_on = [(s.shape_type, s.character_part, s.source_role, s.side_hint) for s in on.shapes]
    sig_off = [(s.shape_type, s.character_part, s.source_role, s.side_hint) for s in off.shapes]
    assert sig_on == sig_off


def test_hand_analysis_reports_coarse_intents_for_detected_arm_tips():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")
    analysis = scene.metadata["character"]["details"]["hands"]["analysis"]

    assert analysis["diagnostics"]["detected_hand_count"] >= 1
    valid = {"open", "compact", "extended", "holding", "unknown"}
    for hand in analysis["hands"]:
        assert hand["intent"] in valid
        assert hand["side"] in {"left", "right"}
        assert 0.0 <= hand["confidence"] <= 1.0
        assert hand["bbox"][2] > 0 and hand["bbox"][3] > 0


def test_hand_analysis_can_be_disabled_independently():
    scene = _scene("Mizumiya-Su_pr-img_01_a.png", enable_hand_analysis=False)
    hands = scene.metadata["character"]["details"]["hands"]
    assert hands["enabled"] is False
    assert hands["analysis"] is None
