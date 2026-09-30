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


def test_browser_fallback_v1_is_loaded_before_app():
    html = INDEX_HTML.read_text(encoding="utf-8")
    browser_index = html.index('/static/browser-fallback.js')
    app_index = html.index('/static/app.js')
    assert browser_index < app_index


def test_browser_fallback_v1_has_no_network_or_model_runtime_dependency():
    source = BROWSER_ENGINE.read_text(encoding="utf-8")
    assert 'browser-fallback-v1' in source
    assert 'deterministic-js' in source
    assert 'fetch(' not in source
    assert 'WebSocket' not in source
    assert 'onnx' not in source.lower()
    assert 'transformers' not in source.lower()
    assert 'rembg' not in source.lower()
    assert 'rtmlib' not in source.lower()
    assert 'destination-in' not in source
    assert 'rgb(255,255,255)' in source
    assert 'convexHull' not in source
    assert 'boundaryRings' in source
    assert 'reduceComponentsToBudget' in source


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
    assert payload["first"]["version"] == "browser-fallback-v1"
    assert len(payload["first"]["centers"]) == 2
    assert len(payload["first"]["shapes"]) == 2
    assert payload["first"]["metrics"]["meanContourIoU"] >= 0.94
    assert all(len(shape["rings"]) >= 1 for shape in payload["first"]["shapes"])


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_concave_component_keeps_mask_fidelity_without_convex_hull_fill():
    script = r"""
const api = require(process.argv[1]);
const width = 7;
const height = 7;
const labels = new Int16Array(width * height);
labels.fill(-1);
const rgba = new Uint8ClampedArray(width * height * 4);
for (let i = 0; i < width * height; i += 1) {
  rgba[i * 4] = 160;
  rgba[i * 4 + 1] = 80;
  rgba[i * 4 + 2] = 40;
  rgba[i * 4 + 3] = 255;
}
const pixels = [
  [1,1],[1,2],[1,3],[1,4],[1,5],
  [2,5],[3,5],[4,5],[5,5],
  [5,4],[5,3]
];
for (const [x,y] of pixels) labels[y * width + x] = 0;
const built = api._core.buildComponents(labels, rgba, width, height);
const component = built.components[0];
const geometry = api._core.componentGeometry(
  component,
  built.componentIds,
  width,
  height,
  0.94
);
process.stdout.write(JSON.stringify({
  contourIoU: geometry.contourIoU,
  ringLength: geometry.rings[0].length,
  ringCount: geometry.rings.length,
}));
"""
    completed = subprocess.run(
        ["node", "-e", script, str(BROWSER_ENGINE)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["contourIoU"] >= 0.94
    assert payload["ringCount"] >= 1
    assert payload["ringLength"] >= 6


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_region_budget_merges_adjacent_components_instead_of_dropping_them():
    script = r"""
const api = require(process.argv[1]);
const width = 12;
const height = 6;
const labels = new Int16Array(width * height);
const rgba = new Uint8ClampedArray(width * height * 4);
for (let y = 0; y < height; y += 1) {
  for (let x = 0; x < width; x += 1) {
    const index = y * width + x;
    labels[index] = x;
    rgba[index * 4] = (x * 19) % 255;
    rgba[index * 4 + 1] = (80 + x * 11) % 255;
    rgba[index * 4 + 2] = (180 - x * 7 + 255) % 255;
    rgba[index * 4 + 3] = 255;
  }
}
const reduced = api._core.reduceComponentsToBudget(
  labels,
  rgba,
  width,
  height,
  4
);
process.stdout.write(JSON.stringify({
  componentCount: reduced.built.components.length,
  mergeCount: reduced.mergeCount,
  covered: Array.from(reduced.labels).every((label) => label >= 0),
}));
"""
    completed = subprocess.run(
        ["node", "-e", script, str(BROWSER_ENGINE)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["componentCount"] <= 4
    assert payload["mergeCount"] >= 8
    assert payload["covered"] is True
