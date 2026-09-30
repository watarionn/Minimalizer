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


def _node(script: str) -> dict:
    completed = subprocess.run(
        ["node", "-e", script, str(BROWSER_ENGINE)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_browser_fallback_v2_is_loaded_before_app():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert html.index('/static/browser-fallback.js') < html.index('/static/app.js')


def test_browser_fallback_v2_has_no_network_or_model_runtime_dependency():
    source = BROWSER_ENGINE.read_text(encoding="utf-8")
    assert 'browser-fallback-v2' in source
    assert 'deterministic-js' in source
    assert 'runSlicoLite' in source
    assert 'oversegmentSpatial' in source
    assert 'edgeCoverageThreshold: 0.75' in source
    assert 'workMaxSide: 400' in source
    assert 'slicIterations: 10' in source
    assert 'paletteTarget: 8' in source
    assert 'retryScale: 0.80' in source
    assert 'mergeSpatialGroupsToBudget' in source
    assert 'consolidateShapePalette' in source
    assert 'boundaryRings' in source
    assert 'fetch(' not in source
    assert 'WebSocket' not in source
    assert 'onnx' not in source.lower()
    assert 'transformers' not in source.lower()
    assert 'rembg' not in source.lower()
    assert 'rtmlib' not in source.lower()
    assert 'convexHull' not in source


def test_browser_fallback_is_opt_in_and_railway_remains_default():
    source = APP_JS.read_text(encoding="utf-8")
    assert 'minimalizer.browserFallbackMode' in source
    assert 'browserFallbackParam === "1"' in source
    assert 'browserFallbackParam === "force"' in source
    assert 'browserFallbackParam === "0"' in source
    assert 'window.MinimalizerBrowserFallback' in source
    assert 'compute: "browser"' in source
    assert 'fetch("/api/v2/minimalize"' in source
    assert 'Minimalizer Browser Fallback v2' in source
    assert 'workMaxSide: 400' in source
    assert 'slicIterations: 10' in source
    assert 'paletteTarget: 8' in source


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_rgb_to_lab_has_expected_neutral_endpoints():
    payload = _node(r"""
const api = require(process.argv[1]);
const white = api._core.rgbToLab(255, 255, 255);
const black = api._core.rgbToLab(0, 0, 0);
process.stdout.write(JSON.stringify({white, black}));
""")
    assert payload["white"][0] == pytest.approx(100.0, abs=0.01)
    assert payload["white"][1] == pytest.approx(0.0, abs=0.02)
    assert payload["white"][2] == pytest.approx(0.0, abs=0.02)
    assert payload["black"][0] == pytest.approx(0.0, abs=0.01)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_slico_lite_is_deterministic_and_spatially_connected():
    payload = _node(r"""
const api = require(process.argv[1]);
const width = 48;
const height = 32;
const rgba = new Uint8ClampedArray(width * height * 4);
for (let y = 0; y < height; y += 1) {
  for (let x = 0; x < width; x += 1) {
    const i = y * width + x;
    const o = i * 4;
    const left = x < width / 2;
    rgba[o] = left ? 225 : 35;
    rgba[o + 1] = left ? 45 : 65;
    rgba[o + 2] = left ? 45 : 220;
    rgba[o + 3] = 255;
  }
}
const lab = api._core.rgbaToLab(rgba, width, height);
const edge = api._core.structuralEdgeMap(lab, width, height);
const first = api._core.runSlicoLite(lab, edge, width, height, 6, 4);
const second = api._core.runSlicoLite(lab, edge, width, height, 6, 4);
const equal = first.labels.every((value, index) => value === second.labels[index]);
const seen = new Set(first.labels);
let connected = true;
for (const label of seen) {
  let start = -1;
  let count = 0;
  for (let i = 0; i < first.labels.length; i += 1) {
    if (first.labels[i] === label) {
      if (start < 0) start = i;
      count += 1;
    }
  }
  const visited = new Uint8Array(first.labels.length);
  const queue = [start];
  visited[start] = 1;
  let reached = 0;
  while (queue.length) {
    const i = queue.pop();
    reached += 1;
    const x = i % width;
    const y = Math.floor(i / width);
    const neighbors = [];
    if (x > 0) neighbors.push(i - 1);
    if (x + 1 < width) neighbors.push(i + 1);
    if (y > 0) neighbors.push(i - width);
    if (y + 1 < height) neighbors.push(i + width);
    for (const n of neighbors) {
      if (!visited[n] && first.labels[n] === label) {
        visited[n] = 1;
        queue.push(n);
      }
    }
  }
  if (reached !== count) connected = false;
}
const coverage = api._core.structuralEdgeCoverageJs(first.labels, edge, width, height);
process.stdout.write(JSON.stringify({
  equal,
  connected,
  regionCount: first.regionCount,
  coverage,
}));
""")
    assert payload["equal"] is True
    assert payload["connected"] is True
    assert payload["regionCount"] >= 20
    assert payload["coverage"] >= 0.75


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_v2_pipeline_enforces_spatial_shape_and_palette_budgets():
    payload = _node(r"""
const api = require(process.argv[1]);
const width = 40;
const height = 40;
const rgba = new Uint8ClampedArray(width * height * 4);
for (let y = 0; y < height; y += 1) {
  for (let x = 0; x < width; x += 1) {
    const i = y * width + x;
    const o = i * 4;
    const qx = x < 20 ? 0 : 1;
    const qy = y < 20 ? 0 : 1;
    const colors = [
      [220, 50, 50],
      [50, 90, 220],
      [235, 210, 70],
      [60, 170, 105],
    ];
    const c = colors[qy * 2 + qx];
    rgba[o] = c[0] + ((x + y) % 3);
    rgba[o + 1] = c[1];
    rgba[o + 2] = c[2];
    rgba[o + 3] = 255;
  }
}
const options = {
  slicIterations: 4,
  slicTargetMin: 24,
  slicTargetMax: 24,
  slicMinAverageArea: 4,
  maxShapes: 8,
  paletteTarget: 4,
  contourFidelity: 0.94,
};
const first = api._core.analyzeRgba(rgba, width, height, options);
const second = api._core.analyzeRgba(rgba, width, height, options);
process.stdout.write(JSON.stringify({first, second}));
""")
    first = payload["first"]
    second = payload["second"]
    assert first == second
    assert first["version"] == "browser-fallback-v2"
    assert first["metrics"]["initialRegionCount"] >= 8
    assert first["metrics"]["componentCount"] == 8
    assert first["metrics"]["paletteCount"] == 4
    assert first["metrics"]["edgeCoverage"] >= 0.75
    assert first["metrics"]["meanContourIoU"] >= 0.94
    assert len(first["shapes"]) == 8
    assert len({tuple(shape["rgb"]) for shape in first["shapes"]}) <= 4


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_concave_component_keeps_v1_mask_fidelity_contract():
    payload = _node(r"""
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
const geometry = api._core.componentGeometry(
  built.components[0],
  built.componentIds,
  width,
  height,
  0.94
);
process.stdout.write(JSON.stringify({
  contourIoU: geometry.contourIoU,
  ringLength: geometry.rings[0].length,
}));
""")
    assert payload["contourIoU"] >= 0.94
    assert payload["ringLength"] >= 6


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_adaptive_slic_retry_is_deterministic_and_bounded():
    payload = _node(r"""
const api = require(process.argv[1]);
const width = 64;
const height = 64;
const rgba = new Uint8ClampedArray(width * height * 4);
for (let y = 0; y < height; y += 1) {
  for (let x = 0; x < width; x += 1) {
    const i = y * width + x;
    const o = i * 4;
    const stripe = Math.floor(x / 4) % 2;
    rgba[o] = stripe ? 235 : 20;
    rgba[o + 1] = stripe ? 235 : 40;
    rgba[o + 2] = stripe ? 235 : 180;
    rgba[o + 3] = 255;
  }
}
const lab = api._core.rgbaToLab(rgba, width, height);
const edge = api._core.structuralEdgeMap(lab, width, height);
const config = {
  ...api.DEFAULTS,
  slicIterations: 4,
  slicTargetMin: 32,
  slicTargetMax: 32,
  slicMinAverageArea: 4,
  edgeCoverageThreshold: 0.95,
  retryScale: 0.5,
  maxRetryTargetFactor: 2.5,
};
const first = api._core.oversegmentSpatial(lab, edge, width, height, config);
const second = api._core.oversegmentSpatial(lab, edge, width, height, config);
process.stdout.write(JSON.stringify({
  equal: first.labels.every((value, index) => value === second.labels[index]),
  regionCount: first.regionCount,
  targetCount: first.targetCount,
  retried: first.retried,
  edgeCoverage: first.edgeCoverage,
  initialEdgeCoverage: first.initialEdgeCoverage,
  bounded: first.regionCount <= Math.max(
    first.initialRegionCountBeforeRetry || first.regionCount,
    Math.ceil(first.targetCount * config.maxRetryTargetFactor)
  )
}));
""")
    assert payload["equal"] is True
    assert payload["bounded"] is True
    assert payload["regionCount"] > 0
    assert payload["edgeCoverage"] >= payload["initialEdgeCoverage"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_large_400px_region_map_does_not_use_argument_spread():
    payload = _node(r"""
const api = require(process.argv[1]);
const width = 400;
const height = 311;
const count = width * height;
const labels = new Int32Array(count);
const rgba = new Uint8ClampedArray(count * 4);
const lab = new Float32Array(count * 3);
const edge = new Float32Array(count);
for (let y = 0; y < height; y += 1) {
  for (let x = 0; x < width; x += 1) {
    const i = y * width + x;
    labels[i] = Math.floor(y / 16) * 25 + Math.floor(x / 16);
    rgba[i * 4] = 120;
    rgba[i * 4 + 1] = 100;
    rgba[i * 4 + 2] = 80;
    rgba[i * 4 + 3] = 255;
    lab[i * 3] = 50;
  }
}
const groups = api._core.buildSpatialGroups(labels, rgba, lab, edge, width, height);
process.stdout.write(JSON.stringify({
  groups: groups.length,
  pixels: groups.reduce((sum, group) => sum + group.count, 0),
}));
""")
    assert payload["groups"] > 0
    assert payload["pixels"] == 400 * 311
