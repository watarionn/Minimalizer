from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest
import numpy as np

from minimalize_engine.v2.preprocessing import build_image_bundle, lab_edge_map, rgb_to_canonical_lab
from minimalize_engine.v2.region_merge.cost import RegionMergeConfig
from minimalize_engine.v2.region_merge.cut import _build_cut, default_cut_policies, materialize_region_selection
from minimalize_engine.v2.region_merge.graph import build_region_graph_from_arrays
from minimalize_engine.v2.region_merge.hierarchy import run_region_merge_from_graph


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


def test_browser_fallback_v4_is_loaded_before_app():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert html.index('/static/browser-fallback.js') < html.index('/static/app.js')


def test_browser_fallback_v4_has_no_network_or_model_runtime_dependency():
    source = BROWSER_ENGINE.read_text(encoding="utf-8")
    assert 'browser-fallback-v4' in source
    assert 'deterministic-js' in source
    assert 'runSlicoLite' in source
    assert 'oversegmentSpatial' in source
    assert 'workMaxSide: 400' in source
    assert 'slicIterations: 10' in source
    assert 'paletteTarget: 8' in source
    assert 'gradientBins: 32' in source
    assert 'approximateL0StructuralRgba' in source
    assert 'l0Lambda: 0.010' in source
    assert 'l0BetaMax: 100.0' in source
    assert 'l0JacobiIterations: 16' in source
    assert 'buildCanonicalRegionGraph' in source
    assert 'evaluateCanonicalMerge' in source
    assert 'runCanonicalRegionHierarchy' in source
    assert 'cutCanonicalHierarchyToCount' in source
    assert 'canonicalGeometryCost' in source
    assert 'consolidateShapePalette' in source
    assert 'boundaryRings' in source
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
    assert 'window.MinimalizerBrowserFallback' in source
    assert 'compute: "browser"' in source
    assert 'fetch("/api/v2/minimalize"' in source
    assert 'Minimalizer Browser Fallback v4' in source
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
def test_v4_pipeline_enforces_hierarchy_shape_and_palette_budgets():
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
    assert first["version"] == "browser-fallback-v4"
    assert first["metrics"]["initialRegionCount"] >= 8
    assert first["metrics"]["componentCount"] == 8
    assert first["metrics"]["hierarchyCutCount"] == 8
    assert first["metrics"]["finalRootCount"] == 1
    assert first["metrics"]["safeMergeCount"] + first["metrics"]["hierarchyMergeCount"] == first["metrics"]["initialRegionCount"] - 1
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
