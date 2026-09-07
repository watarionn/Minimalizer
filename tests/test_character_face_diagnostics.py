from pathlib import Path

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.face_diagnostics import build_face_diagnostics_report


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene(name: str, **overrides):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=180,
        target_max_shapes=28,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
        **overrides,
    )
    return minimalize(CORPUS / name, cfg)


def test_phase106_consolidates_face_pipeline_without_changing_rendering():
    scene = _scene("Rindo-Chihaya_pr-img_01_a.png")
    report = scene.metadata["face_diagnostics"]
    face = scene.metadata["character"]["details"]["face"]

    assert scene.metadata["engine_version"] == "0.3.0"
    assert report["diagnostics"]["phase"] == "10.6"
    assert report["diagnostics"]["rendering_changed"] is False
    assert report["available"] is True
    assert report["status"] in {"healthy", "watch", "repair"}
    assert report["actual_shape_count"] == face["shape_count"]
    assert report["rendered_roles"] == face["identity_rendering"]["rendered_roles"]
    assert scene.metadata["character"]["face_diagnostics"] == report


def test_phase106_reports_selected_and_omitted_identity_cues():
    scene = _scene("Isaki-Riona_pr-img_01_a.png")
    report = scene.metadata["face_diagnostics"]

    assert "face_base" in report["selected_features"]
    assert set(report["selected_features"]).isdisjoint(report["omitted_features"])
    assert report["planned_shape_count"] >= 1
    assert report["actual_shape_count"] >= 1
    assert report["identity_score"] is not None
    assert report["face_geometry_score"] is not None
    assert report["face_boundary_score"] is not None


def test_diagnostics_handles_missing_face_gracefully():
    report = build_face_diagnostics_report({}, {})
    data = report.to_dict()
    assert data["available"] is False
    assert data["status"] == "unavailable"
    assert data["diagnostics"]["phase"] == "10.6"


def test_debug_mode_writes_phase106_dashboard(tmp_path):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=180,
        target_max_shapes=28,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
        debug_mode=True,
        debug_output_dir=str(tmp_path),
    )
    minimalize(CORPUS / "Rindo-Chihaya_pr-img_01_a.png", cfg)

    json_path = tmp_path / "17_face_diagnostics.json"
    png_path = tmp_path / "17_face_diagnostics.png"
    assert json_path.exists()
    assert png_path.exists()
    assert '"phase": "10.6"' in json_path.read_text(encoding="utf-8")
    assert png_path.stat().st_size > 0
