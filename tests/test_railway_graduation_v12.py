from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "web" / "static" / "app.js"
INDEX_HTML = ROOT / "web" / "static" / "index.html"
BROWSER_ENGINE = ROOT / "web" / "static" / "browser-fallback.js"
COLOR_STRIP = ROOT / "web" / "static" / "browser-color-strip.js"
FEATURE_PALETTE = ROOT / "web" / "static" / "browser-feature-palette.js"
SHIN_BUILDER = ROOT / "scripts" / "build_shin_static.py"
ORIGIN_SETTER = ROOT / "scripts" / "set_local_worker_origin.ps1"
START_WORKER = ROOT / "scripts" / "start_local_worker.ps1"


def test_static_runtime_has_no_railway_or_hosted_api_dependency():
    source = APP_JS.read_text(encoding="utf-8")
    assert "Railway" not in source
    assert "railway.app" not in source
    assert 'fetch("/api/v2/minimalize"' not in source
    assert 'fetch("/api/minimalize"' not in source
    assert 'fetch("/health")' not in source
    assert 'window.MinimalizerBrowserFallback' in source
    assert 'window.MinimalizerBrowserColorStrip' in source


def test_static_index_loads_all_browser_engines_before_app():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert '/docs' not in html
    assert html.index('/static/browser-fallback.js') < html.index('/static/browser-feature-palette.js')
    assert html.index('/static/browser-feature-palette.js') < html.index('/static/browser-color-strip.js')
    assert html.index('/static/browser-color-strip.js') < html.index('/static/app.js')


def test_browser_color_strip_is_self_hosted_and_network_free():
    source = COLOR_STRIP.read_text(encoding="utf-8")
    assert 'browser-color-strip-v1' in source
    assert 'X-Minimalizer-Compute' in source
    assert '"browser"' in source
    assert 'fetch(' not in source
    assert 'WebSocket' not in source
    feature_source = FEATURE_PALETTE.read_text(encoding="utf-8")
    assert 'browser-feature-palette-v1' in feature_source
    assert 'fetch(' not in feature_source
    assert 'WebSocket' not in feature_source
    assert 'onnx' not in source.lower()
    assert 'rembg' not in source.lower()
    assert 'rtmlib' not in source.lower()


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_large_source_sampling_gate_is_deterministic():
    script = r"""
const api = require(process.argv[1]);
const config = api.DEFAULTS;
process.stdout.write(JSON.stringify({
  large: api._core.shouldUseLargeSourceSampling(5000, 3000, 100, 60, config),
  ordinary: api._core.shouldUseLargeSourceSampling(1200, 800, 400, 267, config),
  noResize: api._core.shouldUseLargeSourceSampling(5000, 3000, 5000, 3000, config),
  nativeLimit: config.nativeRgbaMaxPixels,
  hardLimit: config.sourcePixelHardLimit,
  fileLimit: config.sourceFileByteLimit,
}));
"""
    completed = subprocess.run(
        ["node", "-e", script, str(BROWSER_ENGINE)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["large"] is True
    assert payload["ordinary"] is False
    assert payload["noResize"] is False
    assert payload["nativeLimit"] == 12_000_000
    assert payload["hardLimit"] == 100_000_000
    assert payload["fileLimit"] == 64 * 1024 * 1024


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_browser_color_strip_geometry_contract():
    script = r"""
const api = require(process.argv[1]);
const equal = api._core.equalBounds(4, 100);
const proportional = api._core.proportionalBounds([
  {share: 0.50}, {share: 0.25}, {share: 0.15}, {share: 0.10}
], 100);
const white = api._core.rgbToLab([255,255,255]);
const black = api._core.rgbToLab([0,0,0]);
process.stdout.write(JSON.stringify({equal, proportional, white, black}));
"""
    completed = subprocess.run(
        ["node", "-e", script, str(COLOR_STRIP)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["equal"] == [[0, 25], [25, 50], [50, 75], [75, 100]]
    assert payload["proportional"][0][0] == 0
    assert payload["proportional"][-1][1] == 100
    assert payload["white"][0] == pytest.approx(100.0, abs=0.01)
    assert payload["black"][0] == pytest.approx(0.0, abs=0.01)


def test_shin_builder_produces_static_document_root(tmp_path):
    spec = importlib.util.spec_from_file_location("build_shin_static", SHIN_BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DESTINATION = tmp_path / "shin"

    output = module.build()
    assert output == module.DESTINATION
    assert (output / "index.html").is_file()
    assert (output / "static" / "app.js").is_file()
    assert (output / "static" / "browser-fallback.js").is_file()
    assert (output / "static" / "browser-color-strip.js").is_file()
    assert (output / "static" / "browser-feature-palette.js").is_file()
    assert (output / "static" / "models" / "u2netp.onnx").is_file()
    assert (
        output / "static" / "vendor" / "onnxruntime" / "ort.wasm.min.mjs"
    ).is_file()
    assert (
        output / "static" / "vendor" / "onnxruntime" / "ort-wasm-simd-threaded.wasm"
    ).is_file()
    assert not (output / "static" / "index.html").exists()

    app_source = (output / "static" / "app.js").read_text(encoding="utf-8")
    assert "Railway" not in app_source
    assert 'fetch("/api/' not in app_source
    assert 'fetch("/health")' not in app_source


def test_local_worker_origin_is_configured_outside_repository():
    start = START_WORKER.read_text(encoding="utf-8")
    setter = ORIGIN_SETTER.read_text(encoding="utf-8")
    assert "public-origin.txt" in start
    assert "MINIMALIZER_LOCAL_ALLOWED_ORIGINS" in start
    assert "public-origin.txt" in setter
    assert "LOCALAPPDATA" in setter
    assert "https://" in setter
