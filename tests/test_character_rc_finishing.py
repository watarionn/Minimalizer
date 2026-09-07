from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.whole_identity import evaluate_character_wide_identity
from minimalize_engine.character.retry import suggest_character_retry_config

ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene(name: str, **overrides):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        **overrides,
    )
    return minimalize(CORPUS / name, cfg)


def test_adaptive_budget_releases_capacity_without_breaking_total():
    scene = _scene("Isaki-Riona_pr-img_01_a.png")
    budget = scene.metadata["character"]["budget"]
    adaptive = budget["metadata"]["adaptive"]
    assert adaptive["enabled"] is True
    assert adaptive["released_slots"] >= 1
    assert sum(budget["per_part"].values()) == budget["total"]
    assert budget["per_part"].get("unknown", 0) == adaptive["released_slots"]
    assert budget["reserved_outfit"] >= 4


def test_adaptive_budget_can_be_disabled():
    scene = _scene("Isaki-Riona_pr-img_01_a.png", enable_adaptive_character_budget=False)
    adaptive = scene.metadata["character"]["budget"]["metadata"].get("adaptive")
    assert adaptive is None or adaptive["enabled"] is False


def test_finishing_quality_reports_are_attached():
    scene = _scene("Isaki-Riona_pr-img_01_a.png")
    assert scene.metadata["outfit_quality"]["applicable"] is True
    assert scene.metadata["outfit_quality"]["score"] > 0.40
    assert scene.metadata["character_wide_identity"]["score"] >= 0.68
    assert "character_wide_identity_score" in scene.metadata["character_quality"]


def test_prop_symbol_quality_is_minimal_and_retained_when_applicable():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")
    report = scene.metadata["prop_symbol_quality"]
    assert report["applicable"] is True
    assert report["retention"] >= 0.90
    assert report["compactness"] >= 0.75
    assert report["score"] >= 0.64


def test_character_wide_identity_flags_low_composite_and_retry_knows_it():
    wide = evaluate_character_wide_identity(
        generic_quality={"silhouette_similarity": 0.30, "minimality_score": 0.80},
        character_quality={
            "geometry_fidelity_score": 0.30,
            "face_identity_score": 0.40,
            "hand_quality_score": 0.50,
            "layout_score": 0.55,
        },
        outfit_quality={"score": 0.35},
        prop_quality={"score": 0.45},
        min_score=0.70,
    )
    assert wide.score < 0.70
    assert wide.retry_reasons == ["character_wide_identity_low"]

    cfg = MinimalizeConfig.from_level(4)
    new_cfg, info = suggest_character_retry_config(
        cfg,
        {"retry_reasons": ["character_wide_identity_low"]},
        {"identity_score": 0.45, "complexity_score": 0.90},
        0,
    )
    assert "recover_character_wide_identity" in info["strategy"]
    assert new_cfg.analysis_max_side > cfg.analysis_max_side
