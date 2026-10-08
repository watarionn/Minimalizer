from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "web/static/weighted-visvalingam.js"
CONTOUR = ROOT / "web/static/canonical-contour.js"
ENGINE = ROOT / "web/static/browser-fallback.js"
APP = ROOT / "web/static/app.js"
HTML = ROOT / "web/static/index.html"


def _node(source: str) -> dict:
    completed = subprocess.run(
        ["node", "-e", source, str(MODULE), str(CONTOUR), str(ENGINE)],
        check=True, text=True, capture_output=True, timeout=45,
    )
    return json.loads(completed.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_weighted_visvalingam_removes_jitter_without_moving_anchors():
    out = _node(r"""
const {simplifyOpen} = require(process.argv[1]);
const points = [[0,0],[1,0.12],[2,-0.13],[3,0.08],[4,0],[5,-0.07],[6,0],[7,0.10],[8,0]];
const weak = simplifyOpen(points, 0.1);
const strong = simplifyOpen(points, 1.5);
const repeated = simplifyOpen(points, 1.5);
process.stdout.write(JSON.stringify({points, weak, strong, repeated, zero:simplifyOpen(points,0)}));
""")
    assert len(out["strong"]) < len(out["weak"]) <= len(out["points"])
    assert out["strong"][0] == out["points"][0]
    assert out["strong"][-1] == out["points"][-1]
    assert out["strong"] == out["repeated"]
    assert out["zero"] == out["points"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_geo_contour_keeps_topology_and_region_fidelity_guards():
    result = _node(r"""
require(process.argv[1]);
const contour = require(process.argv[2]);
const width = 64, height = 48;
const labels = new Int32Array(width * height);
for (let y = 0; y < height; y += 1) {
  const boundary = 30 + (y % 8 < 4 ? 1 : -1);
  for (let x = 0; x < width; x += 1) labels[y * width + x] = x < boundary ? 0 : 1;
}
const baseline = contour.simplifyLabels(labels, width, height, 2);
const geometric = contour.simplifyLabels(labels, width, height, 2, {
  simplifier:"weighted-visvalingam",
});
process.stdout.write(JSON.stringify({
  original:baseline.metrics.originalVertexCount,
  defaultSimplifier:baseline.metrics.simplifier,
  geometricSimplifier:geometric.metrics.simplifier,
  baseline:baseline.metrics,
  geometric:geometric.metrics,
  loopCounts:geometric.loopsByRegion.map(loops=>loops.length),
}));
""")
    assert result["defaultSimplifier"] == "opencv-dp"
    assert result["geometricSimplifier"] == "weighted-visvalingam"
    assert result["baseline"]["originalVertexCount"] == result["geometric"]["originalVertexCount"]
    assert result["geometric"]["minRegionIoU"] >= 0.90
    assert result["geometric"]["simplifiedVertexCount"] <= result["original"]
    assert all(count >= 1 for count in result["loopCounts"])


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_geo_fails_closed_when_plugin_missing():
    result = _node(r"""
const contour = require(process.argv[2]);
const labels = new Int32Array([0,0,1,1]);
let error = "";
try {
  contour.simplifyLabels(labels, 2, 2, 2, {simplifier:"weighted-visvalingam"});
} catch (caught) { error = String(caught.message); }
process.stdout.write(JSON.stringify({error}));
""")
    assert "unavailable" in result["error"]


def test_geo_is_explicit_opt_in_with_browser_only_dependencies():
    html = HTML.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    engine = ENGINE.read_text(encoding="utf-8")
    js = MODULE.read_text(encoding="utf-8")
    assert html.index("weighted-visvalingam.js") < html.index("canonical-contour.js")
    assert 'browserFallbackQualityParam === "geo"' in app
    assert 'contourSimplifier: window.localStorage.getItem' in app
    assert 'contourSimplifier: "opencv-dp"' in engine
    assert 'X-Minimalizer-Contour-Simplifier' in engine
    assert 'module.exports' in js
    assert "fetch(" not in js
    assert "WebSocket" not in js
    assert "onnx" not in js.lower()
