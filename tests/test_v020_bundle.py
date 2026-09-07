from pathlib import Path
import json

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.io.image_loader import load_image_data


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def test_corpus_manifest_contains_uploaded_images():
    manifest = json.loads((ROOT / "tests/assets/corpus_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 16
    assert all((CORPUS / item["name"]).exists() for item in manifest)


def test_alpha_subject_mode_and_v020_metadata():
    path = CORPUS / "Isaki-Riona_pr-img_01_a.png"
    loaded = load_image_data(path)
    assert loaded.alpha is not None
    assert loaded.has_transparency is True

    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
    )
    scene = minimalize(path, cfg)

    assert scene.metadata["engine_version"] == "0.3.0"
    assert scene.metadata["subject_mode"] is True
    assert scene.metadata["source_has_alpha"] is True
    assert scene.metadata["multiscale_enabled"] is True
    assert scene.metadata["design_palette"]
    assert "quality" in scene.metadata
    assert scene.metadata["quality"]["score"] > 0.55
    assert scene.metadata["subject_base_shape_count"] >= 1


def test_general_thumbnail_stays_general_scene():
    path = CORPUS / "Oozora-Subaru_list_thumb.png"
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=30,
        line_mode="none",
        enable_auto_retry=False,
    )
    scene = minimalize(path, cfg)
    assert scene.metadata["subject_mode"] is False
    assert scene.metadata["quality"]["score"] > 0.50
