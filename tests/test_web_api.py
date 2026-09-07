from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

import web.app as web_app_module
from web.app import app

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


def test_phase2_static_assets_are_served():
    css = client.get("/static/styles.css")
    javascript = client.get("/static/app.js")
    assert css.status_code == 200
    assert javascript.status_code == 200
    assert ".drop-zone" in css.text
    assert 'fetch("/api/minimalize"' in javascript.text


def test_service_info_reports_web_engine_and_limits():
    response = client.get("/api/info")
    assert response.status_code == 200
    assert response.json() == {
        "service": "Minimalizer Web",
        "web_version": "0.4.0",
        "engine_version": "0.3.0",
        "docs": "/docs",
        "max_upload_mb": 20,
        "max_image_pixels": 64_000_000,
        "max_image_side": 16_384,
        "max_concurrent_jobs": 2,
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
    assert int(response.headers["x-minimalizer-shape-count"]) >= 1
    assert "x" in response.headers["x-minimalizer-analysis-size"]
    assert response.headers["x-minimalizer-source-size"] == "64x48"
    assert response.headers["x-minimalizer-validated-source-size"] == "64x48"
    assert response.headers["x-minimalizer-source-format"] == "PNG"
    assert float(response.headers["x-minimalizer-processing-ms"]) >= 0.0
    assert len(response.headers["x-request-id"]) == 32


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
