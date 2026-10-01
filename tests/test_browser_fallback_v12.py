from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest
import numpy as np

from minimalize_engine.io.image_loader import load_image
from minimalize_engine.v2.contour.validation import rasterize_loops
from minimalize_engine.v2.pipeline import minimalize_v2
from minimalize_engine.v2.preprocessing import build_image_bundle, lab_edge_map, rgb_to_canonical_lab
from minimalize_engine.v2.region_merge.cost import RegionMergeConfig
from minimalize_engine.v2.region_merge.cut import _build_cut, default_cut_policies, materialize_region_selection
from minimalize_engine.v2.region_merge.graph import build_region_graph_from_arrays
from minimalize_engine.v2.region_merge.hierarchy import run_region_merge_from_graph
from minimalize_engine.v2.region_merge.segmentation import (
    _run_numpy_slico,
    split_disconnected_labels,
)


ROOT = Path(__file__).resolve().parents[1]
BROWSER_ENGINE = ROOT / "web" / "static" / "browser-fallback.js"
APP_JS = ROOT / "web" / "static" / "app.js"
INDEX_HTML = ROOT / "web" / "static" / "index.html"
CANONICAL_CONTOUR = ROOT / "web" / "static" / "canonical-contour.js"
OPENCV_RASTER = ROOT / "web" / "static" / "opencv-fill-raster.js"


def _node(script: str) -> dict:
    completed = subprocess.run(
        ["node", "-e", script, str(BROWSER_ENGINE)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_browser_fallback_v12_is_loaded_before_app():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert html.index('static/opencv-lab-lut.js') < html.index('static/browser-fallback.js')
    assert html.index('/static/opencv-area-resize.js') < html.index('/static/browser-fallback.js')
    assert html.index('/static/spectral-fft.js') < html.index('/static/opencv-fill-raster.js')
    assert html.index('/static/opencv-fill-raster.js') < html.index('/static/canonical-contour.js')
    assert html.index('/static/canonical-contour.js') < html.index('/static/browser-fallback.js')
    assert html.index('/static/browser-fallback.js') < html.index('static/app.js')


def test_browser_fallback_v12_has_no_network_or_model_runtime_dependency():
    source = BROWSER_ENGINE.read_text(encoding="utf-8")
    raster_source = OPENCV_RASTER.read_text(encoding="utf-8")
    assert 'browser-fallback-v12' in source
    assert 'deterministic-js' in source
    assert 'runSlicoLite' in source
    assert 'new Float64Array(width * height)' in source
    assert 'new Float64Array(clusterCount)' in source
    assert 'oversegmentSpatial' in source
    assert 'workMaxSide: 400' in source
    assert 'slicIterations: 10' in source
    assert 'paletteMedoidCandidateCount: 64' in source
    assert 'consolidateCanonicalPalette' in source
    assert 'canonical-medoid-hierarchy' in source
    assert 'X-Minimalizer-Palette-Method' in source
    assert 'canonicalContourLite: false' in source
    assert 'X-Minimalizer-Contour-Method' in source
    assert 'X-Minimalizer-Raster-Method' in source
    assert 'opencv-fillpoly-2x' in source
    assert 'canonical-shared-chain' in CANONICAL_CONTOUR.read_text(encoding="utf-8")
    assert 'opencv-fillpoly-2x-v1' in raster_source
    assert 'renderShapesRgba' in raster_source
    assert 'fetch(' not in raster_source
    assert 'WebSocket' not in raster_source
    assert 'gradientBins: 32' in source
    assert 'approximateL0StructuralRgba' in source
    assert 'spectral-exact' in source
    assert 'spectralL0BetaMax: 1.0e5' in source
    assert 'structuralPreprocess: analysis.metrics.structuralPreprocess' in source
    assert 'X-Minimalizer-Analysis-Resize' in source
    assert 'analysisResize: resizeMethod' in source
    assert 'l0Lambda: 0.010' in source
    assert 'l0BetaMax: 100.0' in source
    assert 'l0JacobiIterations: 16' in source
    assert 'buildCanonicalRegionGraph' in source
    assert 'evaluateCanonicalMerge' in source
    assert 'runCanonicalRegionHierarchy' in source
    assert 'cutCanonicalHierarchyToCount' in source
    assert 'canonicalGeometryCost' in source
    assert 'consolidateCanonicalPalette' in source
    assert 'ciede2000Scalar' in source
    assert 'repairCanonicalPaletteRelationships' in source
    assert 'boundaryRings' in source
    assert 'fetch(' not in source
    assert 'WebSocket' not in source
    assert 'onnx' not in source.lower()
    assert 'transformers' not in source.lower()
    assert 'rembg' not in source.lower()
    assert 'rtmlib' not in source.lower()


def test_browser_fallback_is_default_after_local_without_railway_runtime():
    source = APP_JS.read_text(encoding="utf-8")
    assert 'minimalizer.browserFallbackMode' in source
    assert 'minimalizer.browserFallbackQuality' in source
    assert 'browserFallbackQualityParam === "exact"' in source
    assert 'browserFallbackQualityParam === "lite"' in source
    assert 'structuralMode: browserFallbackStructuralMode()' in source
    assert 'browserFallbackParam === "1"' in source
    assert 'browserFallbackParam === "force"' in source
    assert 'browserFallbackParam === "0"' in source
    assert 'return mode === "force" ? "force" : "after-local"' in source
    assert 'window.MinimalizerBrowserFallback' in source
    assert 'window.MinimalizerBrowserColorStrip' in source
    assert 'compute: "browser"' in source
    assert 'fetch("/api/v2/minimalize"' not in source
    assert 'fetch("/api/minimalize"' not in source
    assert 'fetch("/health")' not in source
    assert "Railway" not in source
    assert 'Minimalizer Browser Fallback v12' in source
    assert 'workMaxSide: 400' in source
    assert 'slicIterations: 10' in source


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
def test_canonical_color_cost_matches_python_formula():
    payload = _node(r"""
const api = require(process.argv[1]);
const left = {count: 10, lab: [50, 10, -5]};
const right = {count: 30, lab: [60, 4, 1]};
const value = api._core.canonicalColorCost(left, right, api.DEFAULTS);
process.stdout.write(JSON.stringify({value}));
""")
    n_left = 10.0
    n_right = 30.0
    delta_sq = (50 - 60) ** 2 + (10 - 4) ** 2 + (-5 - 1) ** 2
    delta_sse = (n_left * n_right / (n_left + n_right)) * delta_sq
    per_pixel = delta_sse / (n_left + n_right)
    expected = 1.0 - math.exp(-per_pixel / 25.0)
    assert payload["value"] == pytest.approx(expected, abs=1e-12)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_canonical_boundary_cost_uses_histogram_quantiles_not_mean():
    payload = _node(r"""
const api = require(process.argv[1]);
const rawHist = new Int32Array(32);
const structuralHist = new Int32Array(32);
rawHist[1] = 8;
rawHist[31] = 2;
structuralHist[2] = 7;
structuralHist[24] = 3;
const edge = {rawHist, structuralHist, shared: 10};
const cost = api._core.canonicalBoundaryCost(edge);
process.stdout.write(JSON.stringify({cost}));
""")
    assert 0.0 < payload["cost"] <= 1.0
    assert payload["cost"] > 0.4


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_safe_consolidation_contract_is_conservative():
    payload = _node(r"""
const api = require(process.argv[1]);
const config = api.DEFAULTS;
const small = {
  count: 1, lab: [50,0,0], perimeter: 4,
  hull: [[0,0],[1,0],[1,1],[0,1]], hullArea: 1,
};
const near = {
  count: 100, lab: [50.1,0,0], perimeter: 42,
  hull: [[1,0],[11,0],[11,10],[1,10]], hullArea: 100,
};
const hist = new Int32Array(32); hist[0] = 2;
const edge = {shared: 2, rawHist: hist, structuralHist: hist};
const evaluation = api._core.evaluateCanonicalMerge(small, near, edge, 1600, config);
const safe = api._core.canonicalSafeCandidate(small, near, edge, evaluation, 1600, config);
const far = {...near, lab:[90,70,60]};
const farEval = api._core.evaluateCanonicalMerge(small, far, edge, 1600, config);
const farSafe = api._core.canonicalSafeCandidate(small, far, edge, farEval, 1600, config);
process.stdout.write(JSON.stringify({safe, farSafe, evaluation, farEval}));
""")
    assert payload["safe"] is True
    assert payload["farSafe"] is False
    assert payload["farEval"]["colorCost"] > payload["evaluation"]["colorCost"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_l0_lite_reduces_texture_and_preserves_major_edge():
    payload = _node(r"""
const api = require(process.argv[1]);
const width = 40;
const height = 24;
const rgba = new Uint8ClampedArray(width * height * 4);
for (let y = 0; y < height; y += 1) {
  for (let x = 0; x < width; x += 1) {
    const i = y * width + x;
    const o = i * 4;
    const left = x < width / 2;
    const texture = ((x + y) % 2) ? 14 : -14;
    const base = left ? [210, 60, 55] : [45, 75, 215];
    rgba[o] = Math.max(0, Math.min(255, base[0] + texture));
    rgba[o + 1] = Math.max(0, Math.min(255, base[1] + texture));
    rgba[o + 2] = Math.max(0, Math.min(255, base[2] + texture));
    rgba[o + 3] = 255;
  }
}
const first = api._core.approximateL0StructuralRgba(rgba, width, height, api.DEFAULTS);
const second = api._core.approximateL0StructuralRgba(rgba, width, height, api.DEFAULTS);
let deterministic = true;
for (let i = 0; i < first.length; i += 1) {
  if (first[i] !== second[i]) deterministic = false;
}
function stats(buffer, x0, x1) {
  const values = [];
  let meanRgb = [0,0,0];
  let count = 0;
  for (let y = 2; y < height - 2; y += 1) {
    for (let x = x0; x < x1; x += 1) {
      const o = (y * width + x) * 4;
      values.push(buffer[o]);
      meanRgb[0] += buffer[o];
      meanRgb[1] += buffer[o + 1];
      meanRgb[2] += buffer[o + 2];
      count += 1;
    }
  }
  meanRgb = meanRgb.map(v => v / count);
  const mean = values.reduce((a,b)=>a+b,0) / values.length;
  const variance = values.reduce((a,b)=>a+(b-mean)*(b-mean),0) / values.length;
  return {std:Math.sqrt(variance), meanRgb};
}
const beforeLeft = stats(rgba, 2, width/2 - 2);
const afterLeft = stats(first, 2, width/2 - 2);
const afterRight = stats(first, width/2 + 2, width - 2);
const edgeDistance = Math.hypot(
  afterLeft.meanRgb[0] - afterRight.meanRgb[0],
  afterLeft.meanRgb[1] - afterRight.meanRgb[1],
  afterLeft.meanRgb[2] - afterRight.meanRgb[2],
);
process.stdout.write(JSON.stringify({
  deterministic,
  beforeStd: beforeLeft.std,
  afterStd: afterLeft.std,
  edgeDistance,
}));
""")
    assert payload["deterministic"] is True
    assert payload["afterStd"] < payload["beforeStd"]
    assert payload["edgeDistance"] > 120.0


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
process.stdout.write(JSON.stringify({equal, connected, regionCount:first.regionCount, coverage}));
""")
    assert payload["equal"] is True
    assert payload["connected"] is True
    assert payload["regionCount"] >= 20
    assert payload["coverage"] >= 0.75


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_v3_hierarchy_is_deterministic_and_cuts_to_requested_count():
    payload = _node(r"""
const api = require(process.argv[1]);
const width = 32;
const height = 32;
const labels = new Int32Array(width * height);
const rgba = new Uint8ClampedArray(width * height * 4);
for (let y = 0; y < height; y += 1) {
  for (let x = 0; x < width; x += 1) {
    const i = y * width + x;
    const gx = Math.floor(x / 8);
    const gy = Math.floor(y / 8);
    labels[i] = gy * 4 + gx;
    rgba[i * 4] = 30 + gx * 50;
    rgba[i * 4 + 1] = 40 + gy * 45;
    rgba[i * 4 + 2] = 180 - gx * 20 + gy * 5;
    rgba[i * 4 + 3] = 255;
  }
}
const lab = api._core.rgbaToLab(rgba, width, height);
const edge = api._core.structuralEdgeMap(lab, width, height);
const config = {
  ...api.DEFAULTS,
  maxShapes:4,
  hierarchyTargetMin:4,
  hierarchyTargetMax:4,
  gradientBins:32,
};
const first = api._core.runCanonicalRegionHierarchy(labels, rgba, lab, edge, edge, width, height, config);
const second = api._core.runCanonicalRegionHierarchy(labels, rgba, lab, edge, edge, width, height, config);
const digest = (result) => ({
  labels:Array.from(result.labels),
  selected:result.groups.map(g=>({count:g.count,rgb:g.rgb,lab:g.lab})),
  safe:result.safeMergeCount,
  hierarchy:result.hierarchyMergeCount,
  roots:result.finalRootCount,
  cut:result.selectedCount,
});
process.stdout.write(JSON.stringify({first:digest(first), second:digest(second)}));
""")
    assert payload["first"] == payload["second"]
    first = payload["first"]
    assert first["cut"] == 4
    assert first["roots"] == 1
    assert first["safe"] + first["hierarchy"] == 15
    assert len(set(first["labels"])) == 4


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_v12_pipeline_enforces_hierarchy_shape_and_palette_budgets():
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
  hierarchyTargetMin: 8,
  hierarchyTargetMax: 8,
  paletteTargetMin: 4,
  paletteTargetMax: 4,
  contourFidelity: 0.94,
};
const first = api._core.analyzeRgba(rgba, width, height, options);
const second = api._core.analyzeRgba(rgba, width, height, options);
process.stdout.write(JSON.stringify({first, second}));
""")
    first = payload["first"]
    second = payload["second"]
    assert first == second
    assert first["version"] == "browser-fallback-v12"
    assert first["metrics"]["initialRegionCount"] >= 8
    assert first["metrics"]["componentCount"] == 8
    assert first["metrics"]["hierarchyCutCount"] == 8
    assert first["metrics"]["finalRootCount"] == 1
    assert first["metrics"]["safeMergeCount"] + first["metrics"]["hierarchyMergeCount"] == first["metrics"]["initialRegionCount"] - 1
    assert first["metrics"]["paletteCount"] >= 4
    assert first["metrics"]["paletteCount"] <= 8
    assert first["metrics"]["paletteMethod"] == "canonical-medoid-hierarchy"
    assert first["metrics"]["edgeCoverage"] >= 0.75
    assert first["metrics"]["meanContourIoU"] >= 0.94
    assert len(first["shapes"]) == 8
    assert len({tuple(shape["rgb"]) for shape in first["shapes"]}) <= first["metrics"]["paletteCount"]


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
const geometry = api._core.componentGeometry(built.components[0], built.componentIds, width, height, 0.94);
process.stdout.write(JSON.stringify({contourIoU:geometry.contourIoU, ringLength:geometry.rings[0].length}));
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
  equal:first.labels.every((value,index)=>value===second.labels[index]),
  regionCount:first.regionCount,
  targetCount:first.targetCount,
  retried:first.retried,
  edgeCoverage:first.edgeCoverage,
  initialEdgeCoverage:first.initialEdgeCoverage,
  bounded:first.regionCount <= Math.max(
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
def test_large_400px_canonical_region_graph_is_stack_safe():
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
const graph = api._core.buildCanonicalRegionGraph(labels, rgba, lab, edge, edge, width, height, 32);
let pixels = 0;
for (const node of graph.nodes.values()) pixels += node.count;
process.stdout.write(JSON.stringify({groups:graph.nodes.size, pixels, edges:graph.edges.size}));
""")
    assert payload["groups"] > 0
    assert payload["pixels"] == 400 * 311
    assert payload["edges"] > 0


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_canonical_lab_edge_map_matches_python(tmp_path):
    height, width = 17, 23
    yy, xx = np.indices((height, width))
    rgb = np.zeros((height, width, 3), dtype=np.uint8)
    rgb[..., 0] = (xx * 11 + yy * 3) % 256
    rgb[..., 1] = (yy * 17 + xx * 5) % 256
    rgb[..., 2] = ((xx + yy) * 13) % 256
    lab = rgb_to_canonical_lab(rgb).astype(np.float32)
    expected = lab_edge_map(lab).astype(np.float32)

    lab_path = tmp_path / "lab.bin"
    out_path = tmp_path / "edge.bin"
    lab_path.write_bytes(lab.tobytes())

    script = r"""
const fs = require("fs");
const api = require(process.argv[1]);
const input = process.argv[2];
const output = process.argv[3];
const height = 17;
const width = 23;
const count = height * width;
const raw = fs.readFileSync(input);
const lab = new Float32Array(raw.buffer, raw.byteOffset, count * 3);
const edge = api._core.canonicalLabEdgeMap(lab, width, height, 99);
fs.writeFileSync(output, Buffer.from(edge.buffer, edge.byteOffset, edge.byteLength));
"""
    subprocess.run(
        ["node", "-e", script, str(BROWSER_ENGINE), str(lab_path), str(out_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    actual = np.frombuffer(out_path.read_bytes(), dtype=np.float32).reshape(height, width)
    assert np.allclose(actual, expected, atol=1.0e-5)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_canonical_region_hierarchy_matches_python_on_same_inputs(tmp_path):
    height = width = 32
    block = 4
    labels = np.empty((height, width), dtype=np.int32)
    image = np.empty((height, width, 3), dtype=np.uint8)
    region_id = 0
    for gy in range(0, height, block):
        for gx in range(0, width, block):
            labels[gy:gy + block, gx:gx + block] = region_id
            image[gy:gy + block, gx:gx + block] = (
                (40 + gx * 5 + gy * 2) % 256,
                (70 + gy * 4 + gx * 3) % 256,
                (190 - gx * 2 + gy) % 256,
            )
            region_id += 1

    bundle = build_image_bundle(image, analysis_max_side=32)
    graph = build_region_graph_from_arrays(
        labels,
        bundle.analysis_lab,
        bundle.edge_raw,
        bundle.edge_structural,
    )
    merge = run_region_merge_from_graph(graph, config=RegionMergeConfig())
    policy = default_cut_policies()["minimal"]
    cut = _build_cut(
        merge,
        preset="minimal",
        policy=policy,
        atomic_ids=frozenset(),
    )
    selection = materialize_region_selection(merge, cut).labels

    rgba = np.empty((height, width, 4), dtype=np.uint8)
    rgba[:, :, :3] = bundle.analysis_rgb
    rgba[:, :, 3] = 255

    paths = {}
    for name, array in {
        "rgba": rgba,
        "lab": bundle.analysis_lab.astype(np.float32),
        "raw": bundle.edge_raw.astype(np.float32),
        "structural": bundle.edge_structural.astype(np.float32),
        "labels": labels,
    }.items():
        path = tmp_path / f"{name}.bin"
        path.write_bytes(array.tobytes())
        paths[name] = path
    js_labels = tmp_path / "js-labels.bin"

    script = r"""
const fs = require("fs");
const api = require(process.argv[1]);
const width = 32;
const height = 32;
const n = width * height;
function bytes(path) { return fs.readFileSync(path); }
const rgbaRaw = bytes(process.argv[2]);
const labRaw = bytes(process.argv[3]);
const rawRaw = bytes(process.argv[4]);
const structuralRaw = bytes(process.argv[5]);
const labelRaw = bytes(process.argv[6]);
const rgba = new Uint8ClampedArray(rgbaRaw.buffer, rgbaRaw.byteOffset, n * 4);
const lab = new Float32Array(labRaw.buffer, labRaw.byteOffset, n * 3);
const edgeRaw = new Float32Array(rawRaw.buffer, rawRaw.byteOffset, n);
const edgeStructural = new Float32Array(structuralRaw.buffer, structuralRaw.byteOffset, n);
const labels = new Int32Array(labelRaw.buffer, labelRaw.byteOffset, n);
const result = api._core.runCanonicalRegionHierarchy(
  labels, rgba, lab, edgeRaw, edgeStructural, width, height, api.DEFAULTS
);
fs.writeFileSync(
  process.argv[7],
  Buffer.from(result.labels.buffer, result.labels.byteOffset, result.labels.byteLength)
);
process.stdout.write(JSON.stringify({
  safeMergeCount: result.safeMergeCount,
  hierarchyMergeCount: result.hierarchyMergeCount,
  finalRootCount: result.finalRootCount,
  selectedCount: result.selectedCount,
  evaluationCount: result.evaluationCount,
  safeCandidateCount: result.safeCandidateCount,
  cutObjective: result.cutObjective,
  cutNormalizedVisualLoss: result.cutNormalizedVisualLoss,
  cutMaxHeight: result.cutMaxHeight,
}));
"""
    completed = subprocess.run(
        [
            "node", "-e", script, str(BROWSER_ENGINE),
            str(paths["rgba"]), str(paths["lab"]), str(paths["raw"]),
            str(paths["structural"]), str(paths["labels"]), str(js_labels),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    js_metrics = json.loads(completed.stdout)
    actual = np.frombuffer(js_labels.read_bytes(), dtype=np.int32).reshape(height, width)

    assert js_metrics["safeMergeCount"] == merge.safe_merge_count
    assert js_metrics["hierarchyMergeCount"] == merge.hierarchy_merge_count
    assert js_metrics["finalRootCount"] == merge.metrics.final_root_count
    assert js_metrics["selectedCount"] == cut.region_count
    assert js_metrics["evaluationCount"] == merge.metrics.evaluation_count
    assert js_metrics["safeCandidateCount"] == merge.metrics.safe_candidate_count
    assert js_metrics["cutObjective"] == pytest.approx(cut.objective, abs=1e-12)
    assert js_metrics["cutNormalizedVisualLoss"] == pytest.approx(
        cut.normalized_visual_loss, abs=1e-12
    )
    assert js_metrics["cutMaxHeight"] == pytest.approx(
        cut.max_selected_hierarchy_height, abs=1e-12
    )

    def boundary_map(array):
        boundary = np.zeros(array.shape, dtype=bool)
        horizontal = array[:, :-1] != array[:, 1:]
        boundary[:, :-1] |= horizontal
        boundary[:, 1:] |= horizontal
        vertical = array[:-1, :] != array[1:, :]
        boundary[:-1, :] |= vertical
        boundary[1:, :] |= vertical
        return boundary

    assert np.array_equal(boundary_map(actual), boundary_map(selection))


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_browser_slico_matches_python_exactly_on_same_inputs(tmp_path):
    height, width = 29, 31
    yy, xx = np.indices((height, width))
    lab = np.empty((height, width, 3), dtype=np.float32)
    lab[..., 0] = 35.0 + (xx * 1.7 + yy * 0.9) % 55.0
    lab[..., 1] = -28.0 + ((xx * 3 - yy * 2) % 41)
    lab[..., 2] = -22.0 + ((xx * 2 + yy * 5) % 47)
    edge = (
        ((xx * 11 + yy * 7) % 101).astype(np.float32) / 100.0
    ).astype(np.float32)

    region_size = 5
    iterations = 6
    expected_raw = _run_numpy_slico(
        lab,
        edge,
        region_size=region_size,
        iterations=iterations,
    )
    expected = split_disconnected_labels(expected_raw)

    lab_path = tmp_path / "lab.bin"
    edge_path = tmp_path / "edge.bin"
    output_path = tmp_path / "labels.bin"
    lab_path.write_bytes(lab.tobytes())
    edge_path.write_bytes(edge.tobytes())

    script = r"""
const fs = require("fs");
const api = require(process.argv[1]);
const width = 31;
const height = 29;
const count = width * height;
const labRaw = fs.readFileSync(process.argv[2]);
const edgeRaw = fs.readFileSync(process.argv[3]);
const lab = new Float32Array(labRaw.buffer, labRaw.byteOffset, count * 3);
const edge = new Float32Array(edgeRaw.buffer, edgeRaw.byteOffset, count);
const result = api._core.runSlicoLite(lab, edge, width, height, 5, 6);
fs.writeFileSync(
  process.argv[4],
  Buffer.from(result.labels.buffer, result.labels.byteOffset, result.labels.byteLength)
);
process.stdout.write(JSON.stringify({regionCount:result.regionCount}));
"""
    completed = subprocess.run(
        [
            "node", "-e", script, str(BROWSER_ENGINE),
            str(lab_path), str(edge_path), str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    actual = np.frombuffer(output_path.read_bytes(), dtype=np.int32).reshape(height, width)

    assert payload["regionCount"] == int(expected.max()) + 1
    assert np.array_equal(actual, expected)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_opencv_lab_lut_matches_python_exactly(tmp_path):
    from minimalize_engine.v2.preprocessing import rgb_to_canonical_lab

    rng = np.random.default_rng(20260930)
    rgb = rng.integers(0, 256, size=(4096, 3), dtype=np.uint8)
    rgb[:256] = np.stack([np.arange(256, dtype=np.uint8)] * 3, axis=1)
    expected = rgb_to_canonical_lab(rgb.reshape(-1, 1, 3)).reshape(-1, 3)

    rgb_path = tmp_path / "rgb.bin"
    lab_path = tmp_path / "lab.bin"
    rgb_path.write_bytes(rgb.tobytes())

    script = r"""
const fs = require("fs");
const lut = require(process.argv[1]);
const raw = fs.readFileSync(process.argv[2]);
const count = raw.length / 3;
const out = new Float32Array(count * 3);
for (let i = 0; i < count; i += 1) {
  const value = lut.rgbToLab(raw[i*3], raw[i*3+1], raw[i*3+2]);
  out[i*3] = value[0];
  out[i*3+1] = value[1];
  out[i*3+2] = value[2];
}
fs.writeFileSync(process.argv[3], Buffer.from(out.buffer));
"""
    lut_path = ROOT / "web" / "static" / "opencv-lab-lut.js"
    subprocess.run(
        ["node", "-e", script, str(lut_path), str(rgb_path), str(lab_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    actual = np.frombuffer(lab_path.read_bytes(), dtype=np.float32).reshape(-1, 3)
    assert np.array_equal(actual, expected)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_exact_preprocess_to_slic_matches_python_with_same_rgba(tmp_path):
    from minimalize_engine.v2.preprocessing import (
        lab_edge_map,
        l0_gradient_smooth,
        rgb_to_canonical_lab,
    )
    from minimalize_engine.v2.region_merge.segmentation import oversegment
    from minimalize_engine.v2.types import ImageBundle

    height, width = 29, 31
    yy, xx = np.indices((height, width))
    rgb = np.empty((height, width, 3), dtype=np.uint8)
    rgb[..., 0] = (35 + xx * 13 + yy * 5) % 256
    rgb[..., 1] = (70 + yy * 17 + xx * 3) % 256
    rgb[..., 2] = (180 + xx * 7 - yy * 9) % 256
    rgba = np.empty((height, width, 4), dtype=np.uint8)
    rgba[:, :, :3] = rgb
    rgba[:, :, 3] = 255

    structural_rgb = l0_gradient_smooth(rgb)
    analysis_lab = rgb_to_canonical_lab(rgb)
    structural_lab = rgb_to_canonical_lab(structural_rgb)
    edge_raw = lab_edge_map(analysis_lab)
    edge_structural = lab_edge_map(structural_lab)
    bundle = ImageBundle(
        source_rgb=rgb,
        analysis_rgb=rgb,
        structural_rgb=structural_rgb,
        analysis_lab=analysis_lab,
        structural_lab=structural_lab,
        edge_raw=edge_raw,
        edge_structural=edge_structural,
        scale_x=1.0,
        scale_y=1.0,
    )
    expected = oversegment(bundle)

    rgba_path = tmp_path / "rgba.bin"
    labels_path = tmp_path / "labels.bin"
    rgba_path.write_bytes(rgba.tobytes())

    script = r"""
const fs = require("fs");
global.MinimalizerOpenCvLab = require(process.argv[1]);
global.MinimalizerSpectralFFT = require(process.argv[2]);
const api = require(process.argv[3]);
const width = 31, height = 29, count = width * height;
const raw = fs.readFileSync(process.argv[4]);
const rgba = new Uint8ClampedArray(raw.buffer, raw.byteOffset, count * 4);
const structural = global.MinimalizerSpectralFFT.exactL0StructuralRgba(
  rgba, width, height, {lambda:0.010, kappa:2.0, betaMax:1e5}
);
const lab = api._core.rgbaToLab(structural, width, height);
const edge = api._core.canonicalLabEdgeMap(lab, width, height, 99);
const seg = api._core.oversegmentSpatial(lab, edge, width, height, api.DEFAULTS);
fs.writeFileSync(
  process.argv[5],
  Buffer.from(seg.labels.buffer, seg.labels.byteOffset, seg.labels.byteLength)
);
process.stdout.write(JSON.stringify({regionCount:seg.regionCount}));
"""
    lut_path = ROOT / "web" / "static" / "opencv-lab-lut.js"
    spectral_path = ROOT / "web" / "static" / "spectral-fft.js"
    completed = subprocess.run(
        [
            "node", "-e", script, str(lut_path), str(spectral_path),
            str(BROWSER_ENGINE), str(rgba_path), str(labels_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    actual = np.frombuffer(labels_path.read_bytes(), dtype=np.int32).reshape(height, width)
    assert payload["regionCount"] == expected.region_count
    assert np.array_equal(actual, expected.labels)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_opencv_inter_area_resize_matches_python_exactly(tmp_path):
    import cv2

    resize_module = ROOT / "web" / "static" / "opencv-area-resize.js"
    rng = np.random.default_rng(20260930)
    cases = [
        (17, 13, 7, 5),
        (12, 9, 5, 5),
        (31, 29, 13, 11),
        (53, 47, 19, 17),
        (100, 78, 40, 31),
    ]
    records = []
    for index, (width, height, dest_width, dest_height) in enumerate(cases):
        rgb = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
        rgba = np.dstack(
            [rgb, np.full((height, width), 255, dtype=np.uint8)]
        )
        expected = cv2.resize(
            rgb,
            (dest_width, dest_height),
            interpolation=cv2.INTER_AREA,
        )
        source_path = tmp_path / f"{index}.rgba"
        expected_path = tmp_path / f"{index}.expected"
        actual_path = tmp_path / f"{index}.actual"
        source_path.write_bytes(rgba.tobytes())
        expected_path.write_bytes(expected.tobytes())
        records.append(
            {
                "width": width,
                "height": height,
                "dest_width": dest_width,
                "dest_height": dest_height,
                "source": str(source_path),
                "actual": str(actual_path),
            }
        )

    script = r"""
const fs = require("fs");
const api = require(process.argv[1]);
const records = JSON.parse(process.argv[2]);
for (const item of records) {
  const raw = fs.readFileSync(item.source);
  const rgba = new Uint8ClampedArray(raw.buffer, raw.byteOffset, raw.byteLength);
  const resized = api.resizeRgba(
    rgba, item.width, item.height, item.dest_width, item.dest_height
  );
  const rgb = Buffer.alloc(item.dest_width * item.dest_height * 3);
  for (let i = 0; i < item.dest_width * item.dest_height; i += 1) {
    rgb[i*3] = resized[i*4];
    rgb[i*3+1] = resized[i*4+1];
    rgb[i*3+2] = resized[i*4+2];
  }
  fs.writeFileSync(item.actual, rgb);
}
"""
    subprocess.run(
        ["node", "-e", script, str(resize_module), json.dumps(records)],
        check=True,
        capture_output=True,
        text=True,
    )

    for index, (_, _, dest_width, dest_height) in enumerate(cases):
        count = dest_width * dest_height * 3
        expected = np.frombuffer(
            (tmp_path / f"{index}.expected").read_bytes(),
            dtype=np.uint8,
            count=count,
        )
        actual = np.frombuffer(
            (tmp_path / f"{index}.actual").read_bytes(),
            dtype=np.uint8,
            count=count,
        )
        assert np.array_equal(actual, expected)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_canonical_palette_matches_python_subaru_with_relationship_repair(tmp_path):
    source_path = ROOT / "tests" / "assets" / "corpus" / "Oozora-Subaru_list_thumb.png"
    result = minimalize_v2(
        load_image(source_path),
        presets=("minimal",),
        guidance=None,
    )
    preset = result.presets["minimal"]
    bundle = result.bundle
    palette = preset.palette

    region_ids = sorted(preset.selection.region_ids)
    local_id = {region_id: index for index, region_id in enumerate(region_ids)}
    local_labels = np.vectorize(local_id.__getitem__, otypes=[np.int32])(
        preset.selection.labels
    ).astype(np.int32)

    rgba = np.empty((*bundle.analysis_rgb.shape[:2], 4), dtype=np.uint8)
    rgba[:, :, :3] = bundle.analysis_rgb
    rgba[:, :, 3] = 255

    expected_colors = []
    for region_id in region_ids:
        palette_id = palette.region_to_palette[region_id]
        expected_colors.append(list(palette.entries[palette_id].rgb))

    labels_path = tmp_path / "labels.bin"
    rgba_path = tmp_path / "rgba.bin"
    lab_path = tmp_path / "lab.bin"
    labels_path.write_bytes(local_labels.tobytes())
    rgba_path.write_bytes(rgba.tobytes())
    lab_path.write_bytes(bundle.analysis_lab.astype(np.float32).tobytes())

    script = r"""
const fs = require("fs");
global.MinimalizerOpenCvLab = require(process.argv[1]);
const api = require(process.argv[2]);
const width = Number(process.argv[3]);
const height = Number(process.argv[4]);
const count = width * height;
const labelsRaw = fs.readFileSync(process.argv[5]);
const rgbaRaw = fs.readFileSync(process.argv[6]);
const labRaw = fs.readFileSync(process.argv[7]);
const labels = new Int32Array(labelsRaw.buffer, labelsRaw.byteOffset, count);
const rgba = new Uint8ClampedArray(rgbaRaw.buffer, rgbaRaw.byteOffset, count * 4);
const lab = new Float32Array(labRaw.buffer, labRaw.byteOffset, count * 3);
const groups = Array.from({length:40}, (_, id) => ({id}));
const result = api._core.consolidateCanonicalPalette(
  groups, labels, rgba, lab, width, height, api.DEFAULTS
);
process.stdout.write(JSON.stringify({
  colors: result.colors,
  palette: result.palette.map(entry => entry.rgb),
  relationshipCount: result.relationshipCount,
  repairedSplitCount: result.repairedSplitCount,
  method: result.method,
}));
"""
    lut_path = ROOT / "web" / "static" / "opencv-lab-lut.js"
    completed = subprocess.run(
        [
            "node", "-e", script,
            str(lut_path),
            str(BROWSER_ENGINE),
            str(bundle.analysis_rgb.shape[1]),
            str(bundle.analysis_rgb.shape[0]),
            str(labels_path),
            str(rgba_path),
            str(lab_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    actual = json.loads(completed.stdout)

    assert actual["method"] == "canonical-medoid-hierarchy"
    assert actual["relationshipCount"] == palette.metrics.protected_relationship_count
    assert actual["repairedSplitCount"] == palette.metrics.repaired_split_count == 1
    assert len(actual["palette"]) == palette.metrics.palette_count == 8
    assert actual["colors"] == expected_colors


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_canonical_contour_tracks_python_subaru_shared_boundary(tmp_path):
    source_path = ROOT / "tests" / "assets" / "corpus" / "Oozora-Subaru_list_thumb.png"
    result = minimalize_v2(
        load_image(source_path),
        presets=("minimal",),
        guidance=None,
    )
    preset = result.presets["minimal"]
    ids = sorted(preset.selection.region_ids)
    local_id = {region_id: index for index, region_id in enumerate(ids)}
    labels = np.vectorize(local_id.__getitem__, otypes=[np.int32])(
        preset.selection.labels
    ).astype(np.int32)
    labels_path = tmp_path / "labels.bin"
    labels_path.write_bytes(labels.tobytes())

    script = r"""
const fs = require("fs");
global.MinimalizerOpenCvRaster = require(process.argv[2]);
const contour = require(process.argv[1]);
const width = Number(process.argv[3]);
const height = Number(process.argv[4]);
const regionCount = Number(process.argv[5]);
const raw = fs.readFileSync(process.argv[6]);
const labels = new Int32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4);
const result = contour.simplifyLabels(labels, width, height, regionCount);
process.stdout.write(JSON.stringify({
  metrics: result.metrics,
  loopsByRegion: result.loopsByRegion,
}));
"""
    completed = subprocess.run(
        [
            "node", "-e", script,
            str(CANONICAL_CONTOUR),
            str(OPENCV_RASTER),
            str(labels.shape[1]),
            str(labels.shape[0]),
            str(len(ids)),
            str(labels_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    metrics = payload["metrics"]

    assert metrics["originalVertexCount"] == preset.contour.metrics.original_vertex_count
    assert abs(
        metrics["simplifiedVertexCount"]
        - preset.contour.metrics.simplified_vertex_count
    ) <= 3
    assert metrics["fallbackChainCount"] == preset.contour.metrics.fallback_chain_count
    assert metrics["rejectedCandidateCount"] == preset.contour.metrics.rejected_candidate_count
    assert metrics["minRegionIoU"] == pytest.approx(
        preset.contour.metrics.min_region_iou, abs=1e-12
    )

    cross_ious = []
    for local_index, region_id in enumerate(ids):
        python_mask = rasterize_loops(
            preset.contour.contours[region_id].loops,
            preset.selection.labels.shape,
            scale=2,
        )
        browser_loops = tuple(
            np.asarray(loop, dtype=np.float32)
            for loop in payload["loopsByRegion"][local_index]
        )
        browser_mask = rasterize_loops(
            browser_loops,
            preset.selection.labels.shape,
            scale=2,
        )
        intersection = int(np.count_nonzero(python_mask & browser_mask))
        union = int(np.count_nonzero(python_mask | browser_mask))
        cross_ious.append(intersection / max(union, 1))

    assert float(np.mean(cross_ious)) >= 0.998
    assert float(np.percentile(cross_ious, 10)) >= 0.9985
    assert min(cross_ious) >= 0.97


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_v12_exact_uses_canonical_contour_while_lite_keeps_fast_legacy():
    script = r"""
global.MinimalizerOpenCvRaster = require(process.argv[3]);
global.MinimalizerCanonicalContour = require(process.argv[2]);
const api = require(process.argv[1]);
const width = 24, height = 24;
const rgba = new Uint8ClampedArray(width * height * 4);
for (let y = 0; y < height; y += 1) {
  for (let x = 0; x < width; x += 1) {
    const o = (y * width + x) * 4;
    const left = x < 12;
    rgba[o] = left ? 220 : 45;
    rgba[o + 1] = left ? 70 : 105;
    rgba[o + 2] = left ? 65 : 215;
    rgba[o + 3] = 255;
  }
}
const lite = api._core.analyzeRgba(rgba, width, height, {
  ...api.DEFAULTS,
  structuralMode: "l0-lite-jacobi",
  slicTargetMin: 16,
  slicTargetMax: 16,
  slicMinAverageArea: 4,
  hierarchyTargetMin: 4,
  hierarchyTargetMax: 8,
});
const exactProfile = api._core.analyzeRgba(rgba, width, height, {
  ...api.DEFAULTS,
  structuralMode: "l0-lite-jacobi",
  canonicalContourLite: true,
  slicTargetMin: 16,
  slicTargetMax: 16,
  slicMinAverageArea: 4,
  hierarchyTargetMin: 4,
  hierarchyTargetMax: 8,
});
process.stdout.write(JSON.stringify({
  liteMethod: lite.metrics.contourMethod,
  canonicalMethod: exactProfile.metrics.contourMethod,
}));
"""
    completed = subprocess.run(
        [
            "node", "-e", script,
            str(BROWSER_ENGINE),
            str(CANONICAL_CONTOUR),
            str(OPENCV_RASTER),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["liteMethod"] == "legacy-independent-rings"
    assert payload["canonicalMethod"] == "canonical-shared-chain"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_opencv_fill_raster_matches_python_2x_contract_exactly():
    loops = (
        np.asarray(
            [[1, 1], [16, 2], [17, 8], [14, 15], [3, 13], [1, 1]],
            dtype=np.float32,
        )[:-1],
        np.asarray(
            [[6, 5], [12, 6], [10, 11], [7, 10], [6, 5]],
            dtype=np.float32,
        )[:-1],
    )
    expected = (
        rasterize_loops(loops, (17, 19), scale=2)
        .astype(np.uint8)
        .ravel()
        .tolist()
    )
    script = r"""
const raster = require(process.argv[1]);
const loops = [
  [[1,1],[16,2],[17,8],[14,15],[3,13]],
  [[6,5],[12,6],[10,11],[7,10]],
];
const mask = raster.rasterizeLoops(loops, 19, 17, 2);
process.stdout.write(JSON.stringify({
  version: raster.VERSION,
  mask: Array.from(mask),
}));
"""
    completed = subprocess.run(
        ["node", "-e", script, str(OPENCV_RASTER)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["version"] == "opencv-fillpoly-2x-v1"
    assert payload["mask"] == expected


def test_v12_exact_raster_contract_is_explicit_in_renderer():
    source = BROWSER_ENGINE.read_text(encoding="utf-8")
    assert 'analysis.metrics.contourMethod === "canonical-shared-chain"' in source
    assert 'MinimalizerOpenCvRaster.renderShapesRgba' in source
    assert 'rasterMethod: "opencv-fillpoly-2x"' in source
    assert 'rasterMethod: "canvas-evenodd"' in source
