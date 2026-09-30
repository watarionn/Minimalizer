from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BROWSER_ENGINE = ROOT / "web" / "static" / "browser-fallback.js"
APP_JS = ROOT / "web" / "static" / "app.js"
INDEX_HTML = ROOT / "web" / "static" / "index.html"


def test_browser_fallback_v0_is_loaded_before_app():
    html = INDEX_HTML.read_text(encoding="utf-8")
    browser_index = html.index('/static/browser-fallback.js')
    app_index = html.index('/static/app.js')
    assert browser_index < app_index


def test_browser_fallback_v0_has_no_network_or_model_runtime_dependency():
    source = BROWSER_ENGINE.read_text(encoding="utf-8")
    assert 'browser-fallback-v0' in source
    assert 'deterministic-js' in source
    assert 'fetch(' not in source
    assert 'WebSocket' not in source
    assert 'onnx' not in source.lower()
    assert 'transformers' not in source.lower()
    assert 'rembg' not in source.lower()
    assert 'rtmlib' not in source.lower()


def test_browser_fallback_is_opt_in_and_railway_remains_default():
    source = APP_JS.read_text(encoding="utf-8")
    assert 'minimalizer.browserFallbackMode' in source
    assert 'browserFallbackParam === "1"' in source
    assert 'browserFallbackParam === "force"' in source
    assert 'browserFallbackParam === "0"' in source
    assert 'function browserFallbackEnabled()' in source
    assert 'function browserFallbackForced()' in source
    assert 'window.MinimalizerBrowserFallback' in source
    assert 'compute: "browser"' in source
    assert 'fetch("/api/v2/minimalize"' in source


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_browser_fallback_core_is_deterministic_on_synthetic_image():
    script = r"""
const api = require(process.argv[1]);
const width = 8;
const height = 8;
const rgba = new Uint8ClampedArray(width * height * 4);
for (let y = 0; y < height; y += 1) {
  for (let x = 0; x < width; x += 1) {
    const offset = (y * width + x) * 4;
    const left = x < 4;
    rgba[offset] = left ? 220 : 30;
    rgba[offset + 1] = left ? 40 : 80;
    rgba[offset + 2] = left ? 40 : 220;
    rgba[offset + 3] = 255;
  }
}
const options = {
  paletteSize: 2,
  kmeansIterations: 4,
  smoothPasses: 0,
  minComponentRatio: 0.01,
  maxShapes: 4,
};
const first = api._core.analyzeRgba(rgba, width, height, options);
const second = api._core.analyzeRgba(rgba, width, height, options);
process.stdout.write(JSON.stringify({first, second}));
"""
    completed = subprocess.run(
        ["node", "-e", script, str(BROWSER_ENGINE)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["first"] == payload["second"]
    assert payload["first"]["version"] == "browser-fallback-v0"
    assert len(payload["first"]["centers"]) == 2
    assert len(payload["first"]["shapes"]) == 2
    assert all(len(shape["polygon"]) >= 3 for shape in payload["first"]["shapes"])
