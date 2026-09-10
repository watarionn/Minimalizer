from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

import web.app as web_app_module
from web.app import app
from web.service import build_config, build_rinka_config

client = TestClient(app)


def _sample_png() -> bytes:
    image = Image.new("RGB", (64, 48), (242, 238, 228))
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 32, 40), fill=(45, 75, 120))
    draw.ellipse((36, 12, 56, 32), fill=(210, 100, 80))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _sample_gif() -> bytes:
    image = Image.new("RGB", (16, 16), (120, 80, 50))
    buffer = BytesIO()
    image.save(buffer, format="GIF")
    return buffer.getvalue()


def test_phase2_root_serves_browser_workspace():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'id="drop-zone"' in response.text
    assert 'id="source-preview"' in response.text
    assert 'id="result-preview"' in response.text
    assert 'id="download-svg"' in response.text
    assert 'id="download-png"' in response.text
    assert 'name="mode" value="standard" checked' in response.text
    assert 'name="mode" value="rinka_reference"' in response.text
    assert 'name="mode" value="color_strip"' in response.text
    assert 'id="rinka-preset-control"' in response.text
    assert 'id="rinka-preset-select"' in response.text
    assert 'value="geometric_poster" selected' in response.text
    assert 'value="faceless_subject"' in response.text
    assert "凛夏プリセット" in response.text
    assert "幾何学ポスター" in response.text
    assert "人物ミニマル" in response.text
    assert 'id="color-strip-controls"' in response.text
    assert 'id="color-similarity-range"' in response.text
    assert 'id="color-strip-options"' in response.text
    assert 'id="strip-selection-mode-select"' in response.text
    assert 'id="strip-size-mode-select"' in response.text
    assert 'id="strip-order-select"' in response.text
    assert 'id="strip-orientation-select"' in response.text
    assert 'id="mode-description"' in response.text


def test_phase2_static_assets_are_served():
    css = client.get("/static/styles.css")
    color_strip_css = client.get("/static/color-strip.css")
    javascript = client.get("/static/app.js")
    assert css.status_code == 200
    assert color_strip_css.status_code == 200
    assert javascript.status_code == 200
    assert ".drop-zone" in css.text
    assert "[hidden] { display: none !important; }" in css.text
    assert ".color-strip-controls" in color_strip_css.text
    assert 'fetch("/api/minimalize"' in javascript.text
    assert 'form.append("mode", mode)' in javascript.text
    assert 'form.append("rinka_preset", elements.rinkaPreset.value)' in javascript.text
    assert 'form.append("color_similarity", elements.colorSimilarity.value)' in javascript.text
    assert 'form.append("color_selection_mode", elements.stripSelectionMode.value)' in javascript.text
    assert 'form.append("color_size_mode", elements.stripSizeMode.value)' in javascript.text
    assert 'form.append("color_order", elements.stripOrder.value)' in javascript.text
    assert 'form.append("color_orientation", elements.stripOrientation.value)' in javascript.text
    assert ".mode-switch" in css.text


def test_service_info_reports_web_engine_and_limits():
    response = client.get("/api/info")
    assert response.status_code == 200
    assert response.json() == {
        "service": "Minimalizer Web",
        "web_version": "0.10.0",
        "engine_version": "0.3.0",
        "docs": "/docs",
        "max_upload_mb": 20,
        "max_image_pixels": 64_000_000,
        "max_image_side": 16_384,
        "max_analysis_side": 640,
        "max_concurrent_jobs": 2,
        "supported_modes": ["standard", "rinka_reference", "color_strip"],
        "rinka_reference_version": "phase12",
        "rinka_reference_default_preset": "geometric_poster",
        "rinka_reference_presets": ["geometric_poster", "faceless_subject"],
        "color_strip_version": "v0.3",
        "color_strip_default_colors": 5,
        "color_strip_default_similarity": 18.0,
        "color_strip_default_size_mode": "equal",
        "color_strip_default_order": "least_first",
        "color_strip_default_orientation": "vertical",
        "color_strip_default_selection_mode": "dominant",
        "color_strip_size_modes": ["equal", "proportional"],
        "color_strip_orders": ["least_first", "most_first"],
        "color_strip_orientations": ["vertical", "horizontal"],
        "color_strip_selection_modes": ["dominant", "featured"],
    }


def test_health_reports_engine_version():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "engine_version": "0.3.0"}


def test_security_and_request_metadata_headers_are_present():
    response = client.get("/api/info")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert len(response.headers["x-request-id"]) == 32
    assert response.headers["server-timing"].startswith("app;dur=")


def test_web_analysis_cap_preserves_level_detail_controls():
    detailed = build_config(1, analysis_max_side_cap=640)
    medium = build_config(3, analysis_max_side_cap=640)
    abstract = build_config(5, analysis_max_side_cap=640)

    assert detailed.analysis_max_side == 640
    assert detailed.palette_colors == 16
    assert detailed.target_max_shapes == 180
    assert detailed.line_mode == "standard"

    assert medium.analysis_max_side == 640
    assert medium.palette_colors == 8
    assert medium.target_max_shapes == 80

    assert abstract.analysis_max_side == 512
    assert abstract.palette_colors == 4
    assert abstract.target_max_shapes == 30


def test_rinka_config_is_frozen_and_respects_hosted_analysis_cap():
    config = build_rinka_config(analysis_max_side_cap=400)
    assert config.analysis_max_side == 400
    assert config.palette_colors == 6
    assert config.target_max_shapes == 28
    assert config.line_mode == "none"
    assert config.enable_face_primitives is False


def test_rinka_reference_svg_upload_uses_frozen_web_mode():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={"mode": "rinka_reference", "level": "4", "output_format": "svg"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.content.startswith(b"<svg")
    assert response.headers["x-minimalizer-mode"] == "rinka_reference"
    assert response.headers["x-minimalizer-level"] == "4"
    assert response.headers["x-minimalizer-rinka-preset"] == "geometric_poster"
    assert response.headers["x-minimalizer-configured-analysis-max-side"] == "640"
    assert int(response.headers["x-minimalizer-shape-count"]) >= 1


def test_rinka_reference_accepts_faceless_subject_preset():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={
            "mode": "rinka_reference",
            "level": "4",
            "rinka_preset": "faceless_subject",
            "output_format": "svg",
        },
    )

    assert response.status_code == 200
    assert response.headers["x-minimalizer-rinka-preset"] == "faceless_subject"


def test_standard_mode_rejects_rinka_preset():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={
            "mode": "standard",
            "level": "4",
            "rinka_preset": "geometric_poster",
            "output_format": "svg",
        },
    )

    assert response.status_code == 400
    assert "only available in Rinka Reference mode" in response.json()["detail"]


def test_rinka_reference_rejects_custom_detail_settings():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={"mode": "rinka_reference", "level": "5", "output_format": "svg"},
    )
    assert response.status_code == 400
    assert "frozen level-4 profile" in response.json()["detail"]


def test_color_strip_svg_upload_uses_color_only_pipeline():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={
            "mode": "color_strip",
            "colors": "3",
            "color_similarity": "18",
            "output_format": "svg",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.content.startswith(b"<svg")
    assert response.content.count(b"<rect ") == 3
    assert response.headers["content-disposition"] == 'attachment; filename="color-strip.svg"'
    assert response.headers["x-minimalizer-mode"] == "color_strip"
    assert response.headers["x-minimalizer-level"] == "n/a"
    assert response.headers["x-minimalizer-color-count"] == "3"
    assert response.headers["x-minimalizer-color-similarity"] == "18"
    assert response.headers["x-minimalizer-color-selection-mode"] == "dominant"
    assert response.headers["x-minimalizer-color-size-mode"] == "equal"
    assert response.headers["x-minimalizer-color-order"] == "least_first"
    assert response.headers["x-minimalizer-color-orientation"] == "vertical"
    assert response.headers["x-minimalizer-shape-count"] == "3"
    assert response.headers["x-minimalizer-source-size"] == "64x48"


def test_color_strip_accepts_selection_and_layout_options():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={
            "mode": "color_strip",
            "colors": "3",
            "color_similarity": "18",
            "color_selection_mode": "featured",
            "color_size_mode": "proportional",
            "color_order": "most_first",
            "color_orientation": "horizontal",
            "output_format": "svg",
        },
    )

    assert response.status_code == 200
    assert response.headers["x-minimalizer-color-selection-mode"] == "featured"
    assert response.headers["x-minimalizer-color-size-mode"] == "proportional"
    assert response.headers["x-minimalizer-color-order"] == "most_first"
    assert response.headers["x-minimalizer-color-orientation"] == "horizontal"
    assert b'y="0" width="' in response.content
    assert b'height="48"' in response.content


def test_color_strip_rejects_color_count_outside_three_to_five():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={"mode": "color_strip", "colors": "2", "output_format": "svg"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Color Strip color count must be between 3 and 5."


def test_standard_rejects_color_strip_only_settings():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={"mode": "standard", "color_selection_mode": "featured", "output_format": "svg"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Color Strip settings are only available in Color Strip mode."


def test_minimalize_svg_upload():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={"level": "5", "output_format": "svg"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.content.startswith(b"<svg")
    assert response.headers["content-disposition"] == 'attachment; filename="minimalized.svg"'
    assert response.headers["x-minimalizer-mode"] == "standard"
    assert response.headers["x-minimalizer-level"] == "5"
    assert response.headers["x-minimalizer-configured-analysis-max-side"] == "512"
    assert int(response.headers["x-minimalizer-shape-count"]) >= 1
    assert "x" in response.headers["x-minimalizer-analysis-size"]
    assert response.headers["x-minimalizer-source-size"] == "64x48"
    assert response.headers["x-minimalizer-validated-source-size"] == "64x48"
    assert response.headers["x-minimalizer-source-format"] == "PNG"
    assert float(response.headers["x-minimalizer-processing-ms"]) >= 0.0
    assert len(response.headers["x-request-id"]) == 32


def test_minimalize_level_one_uses_hosted_analysis_cap():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={"level": "1", "output_format": "svg"},
    )

    assert response.status_code == 200
    assert response.headers["x-minimalizer-level"] == "1"
    assert response.headers["x-minimalizer-configured-analysis-max-side"] == "640"


def test_minimalize_png_upload():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
        data={"level": "5", "output_format": "png"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert response.headers["content-disposition"] == 'attachment; filename="minimalized.png"'


def test_rejects_non_image_upload():
    response = client.post(
        "/api/minimalize",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 415


def test_rejects_spoofed_image_content_type():
    response = client.post(
        "/api/minimalize",
        files={"file": ("fake.png", b"not actually an image", "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is not a readable image."


def test_rejects_unsupported_real_image_format():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.gif", _sample_gif(), "image/gif")},
    )
    assert response.status_code == 415
    assert "Unsupported image format" in response.json()["detail"]


def test_rejects_image_above_pixel_limit(monkeypatch):
    monkeypatch.setattr(web_app_module, "MAX_IMAGE_PIXELS", 1_000)
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _sample_png(), "image/png")},
    )
    assert response.status_code == 413
    assert "pixel limit" in response.json()["detail"]


def test_rejects_when_all_processing_slots_are_busy():
    acquired = 0
    try:
        for _ in range(web_app_module.MAX_CONCURRENT_JOBS):
            assert web_app_module._PROCESS_SLOTS.acquire(blocking=False)
            acquired += 1

        response = client.post(
            "/api/minimalize",
            files={"file": ("sample.png", _sample_png(), "image/png")},
        )
        assert response.status_code == 429
        assert response.headers["retry-after"] == "2"
        assert response.json()["detail"] == "Minimalizer is busy. Please retry shortly."
        assert len(response.headers["x-request-id"]) == 32
    finally:
        for _ in range(acquired):
            web_app_module._PROCESS_SLOTS.release()


def test_env_int_uses_default_and_clamps(monkeypatch):
    monkeypatch.delenv("MINIMALIZER_TEST_INT", raising=False)
    assert web_app_module._env_int("MINIMALIZER_TEST_INT", 3, minimum=1, maximum=5) == 3

    monkeypatch.setenv("MINIMALIZER_TEST_INT", "99")
    assert web_app_module._env_int("MINIMALIZER_TEST_INT", 3, minimum=1, maximum=5) == 5

    monkeypatch.setenv("MINIMALIZER_TEST_INT", "bad")
    assert web_app_module._env_int("MINIMALIZER_TEST_INT", 3, minimum=1, maximum=5) == 3
