from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

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


def test_health_reports_engine_version():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "engine_version": "0.3.0"}


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
