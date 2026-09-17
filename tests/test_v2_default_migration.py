from io import BytesIO
from types import SimpleNamespace

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

import web.app as web_app_module
from web.app import app
from web.service import minimalize_v2_path

client = TestClient(app)
BROWSER_HEADERS = {"X-Minimalizer-Browser-Default": "v2"}


def _opaque_png() -> bytes:
    image = Image.new("RGB", (64, 48), (242, 238, 228))
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 32, 40), fill=(45, 75, 120))
    draw.ellipse((36, 12, 56, 32), fill=(210, 100, 80))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _transparent_png() -> bytes:
    image = Image.new("RGBA", (64, 48), (242, 238, 228, 255))
    ImageDraw.Draw(image).rectangle((8, 8, 32, 40), fill=(45, 75, 120, 180))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_browser_default_standard_png_routes_to_v2_with_hosted_cap(tmp_path):
    source = _opaque_png()
    source_path = tmp_path / "sample.png"
    source_path.write_bytes(source)
    direct = minimalize_v2_path(
        source_path,
        preset="minimal",
        include_facets=True,
        analysis_max_side_cap=400,
    )

    response = client.post(
        "/api/minimalize",
        headers=BROWSER_HEADERS,
        files={"file": ("sample.png", source, "image/png")},
        data={
            "mode": "standard",
            "level": "4",
            "output_format": "png",
            "background": "white",
        },
    )
    assert response.status_code == 200
    assert response.content == direct.content
    assert response.headers["x-minimalizer-route"] == "v2"
    assert response.headers["x-minimalizer-mode"] == "standard"
    assert response.headers["x-minimalizer-configured-analysis-max-side"] == "400"
    assert response.headers["x-minimalizer-v2-png-sha256"] == direct.metadata.png_sha256


def test_browser_default_svg_stays_legacy():
    response = client.post(
        "/api/minimalize",
        headers=BROWSER_HEADERS,
        files={"file": ("sample.png", _opaque_png(), "image/png")},
        data={"mode": "standard", "level": "4", "output_format": "svg", "background": "white"},
    )
    assert response.status_code == 200
    assert response.headers["x-minimalizer-route"] == "legacy"


def test_browser_default_transparency_stays_legacy():
    response = client.post(
        "/api/minimalize",
        headers=BROWSER_HEADERS,
        files={"file": ("transparent.png", _transparent_png(), "image/png")},
        data={"mode": "standard", "level": "4", "output_format": "png", "background": "white"},
    )
    assert response.status_code == 200
    assert response.headers["x-minimalizer-route"] == "legacy"


def test_browser_default_custom_level_stays_legacy():
    response = client.post(
        "/api/minimalize",
        headers=BROWSER_HEADERS,
        files={"file": ("sample.png", _opaque_png(), "image/png")},
        data={"mode": "standard", "level": "5", "output_format": "png", "background": "white"},
    )
    assert response.status_code == 200
    assert response.headers["x-minimalizer-route"] == "legacy"


def test_browser_default_source_background_stays_legacy():
    response = client.post(
        "/api/minimalize",
        headers=BROWSER_HEADERS,
        files={"file": ("sample.png", _opaque_png(), "image/png")},
        data={"mode": "standard", "level": "4", "output_format": "png", "background": "source"},
    )
    assert response.status_code == 200
    assert response.headers["x-minimalizer-route"] == "legacy"


def test_browser_default_custom_color_count_stays_legacy():
    response = client.post(
        "/api/minimalize",
        headers=BROWSER_HEADERS,
        files={"file": ("sample.png", _opaque_png(), "image/png")},
        data={
            "mode": "standard",
            "level": "4",
            "output_format": "png",
            "background": "white",
            "colors": "6",
        },
    )
    assert response.status_code == 200
    assert response.headers["x-minimalizer-route"] == "legacy"


def test_direct_api_without_browser_marker_remains_legacy():
    response = client.post(
        "/api/minimalize",
        files={"file": ("sample.png", _opaque_png(), "image/png")},
        data={"mode": "standard", "level": "4", "output_format": "png", "background": "white"},
    )
    assert response.status_code == 200
    assert response.headers["x-minimalizer-route"] == "legacy"


def test_browser_default_specialized_mode_remains_legacy():
    response = client.post(
        "/api/minimalize",
        headers=BROWSER_HEADERS,
        files={"file": ("sample.png", _opaque_png(), "image/png")},
        data={"mode": "rinka_reference", "level": "4", "output_format": "png"},
    )
    assert response.status_code == 200
    assert response.headers["x-minimalizer-route"] == "legacy"


def test_v2_default_error_is_not_silently_retried_on_legacy(monkeypatch):
    legacy_called = False

    def fail_v2(*args, **kwargs):
        raise ValueError("expected V2 failure")

    def unexpected_legacy(*args, **kwargs):
        nonlocal legacy_called
        legacy_called = True
        raise AssertionError("legacy fallback must not run")

    monkeypatch.setattr(web_app_module, "minimalize_v2_path", fail_v2)
    monkeypatch.setattr(web_app_module, "minimalize_path", unexpected_legacy)
    response = client.post(
        "/api/minimalize",
        headers=BROWSER_HEADERS,
        files={"file": ("sample.png", _opaque_png(), "image/png")},
        data={"mode": "standard", "level": "4", "output_format": "png", "background": "white"},
    )
    assert response.status_code == 400
    assert legacy_called is False


def test_rollback_state_returns_browser_default_endpoint_to_legacy(monkeypatch):
    monkeypatch.setattr(
        web_app_module,
        "build_browser_migration_contract",
        lambda: SimpleNamespace(current_state="legacy_default"),
    )
    response = client.post(
        "/api/minimalize",
        headers=BROWSER_HEADERS,
        files={"file": ("sample.png", _opaque_png(), "image/png")},
        data={"mode": "standard", "level": "4", "output_format": "png", "background": "white"},
    )
    assert response.status_code == 200
    assert response.headers["x-minimalizer-route"] == "legacy"
