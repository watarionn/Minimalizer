from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from minimalize_engine.v2.preprocessing import l0_gradient_smooth


ROOT = Path(__file__).resolve().parents[1]
SPECTRAL = ROOT / "web" / "static" / "spectral-fft.js"
BROWSER_ENGINE = ROOT / "web" / "static" / "browser-fallback.js"


def _node(script: str, *args: str) -> dict:
    completed = subprocess.run(
        ["node", "-e", script, str(SPECTRAL), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_bluestein_matches_direct_dft_for_prime_and_composite_lengths():
    payload = _node(r"""
const api = require(process.argv[1]);
function direct(real, imag) {
  const n = real.length;
  const outR = new Float64Array(n);
  const outI = new Float64Array(n);
  for (let k = 0; k < n; k += 1) {
    let rr = 0, ii = 0;
    for (let j = 0; j < n; j += 1) {
      const angle = -2 * Math.PI * j * k / n;
      const c = Math.cos(angle), s = Math.sin(angle);
      rr += real[j] * c - imag[j] * s;
      ii += real[j] * s + imag[j] * c;
    }
    outR[k] = rr;
    outI[k] = ii;
  }
  return [outR, outI];
}
const rows = [];
for (const n of [7, 10, 13, 16]) {
  const real = new Float64Array(n);
  const imag = new Float64Array(n);
  for (let i = 0; i < n; i += 1) {
    real[i] = Math.sin(i * 0.37) + i * 0.1;
    imag[i] = Math.cos(i * 0.23) * 0.25;
  }
  const expected = direct(real, imag);
  const actualR = new Float64Array(real);
  const actualI = new Float64Array(imag);
  api.fftAny(actualR, actualI, false);
  let maxError = 0;
  for (let i = 0; i < n; i += 1) {
    maxError = Math.max(
      maxError,
      Math.abs(actualR[i] - expected[0][i]),
      Math.abs(actualI[i] - expected[1][i]),
    );
  }
  rows.push({n, maxError});
}
process.stdout.write(JSON.stringify(rows));
""")
    assert max(row["maxError"] for row in payload) < 1.0e-9


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_arbitrary_size_fft2_roundtrip():
    payload = _node(r"""
const api = require(process.argv[1]);
const width = 7, height = 5, n = width * height;
const real = new Float64Array(n);
const imag = new Float64Array(n);
for (let i = 0; i < n; i += 1) {
  real[i] = Math.sin(i * 0.17) + (i % width) * 0.03;
  imag[i] = Math.cos(i * 0.11) * 0.07;
}
const originalR = new Float64Array(real);
const originalI = new Float64Array(imag);
api.fft2(real, imag, width, height, false);
api.fft2(real, imag, width, height, true);
let maxError = 0;
for (let i = 0; i < n; i += 1) {
  maxError = Math.max(
    maxError,
    Math.abs(real[i] - originalR[i]),
    Math.abs(imag[i] - originalI[i]),
  );
}
process.stdout.write(JSON.stringify({maxError}));
""")
    assert payload["maxError"] < 1.0e-9


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_exact_spectral_l0_matches_python_small_fixture(tmp_path):
    height, width = 11, 13
    yy, xx = np.indices((height, width))
    rgb = np.zeros((height, width, 3), dtype=np.uint8)
    rgb[..., 0] = (30 + xx * 13 + yy * 5) % 256
    rgb[..., 1] = (70 + yy * 17 + xx * 3) % 256
    rgb[..., 2] = (180 + xx * 7 - yy * 9) % 256
    rgba = np.empty((height, width, 4), dtype=np.uint8)
    rgba[:, :, :3] = rgb
    rgba[:, :, 3] = 255

    expected = l0_gradient_smooth(rgb)
    input_path = tmp_path / "rgba.bin"
    output_path = tmp_path / "out.bin"
    input_path.write_bytes(rgba.tobytes())

    script = r"""
const fs = require("fs");
const api = require(process.argv[1]);
const input = process.argv[2];
const output = process.argv[3];
const width = 13, height = 11;
const raw = fs.readFileSync(input);
const rgba = new Uint8ClampedArray(raw.buffer, raw.byteOffset, width * height * 4);
const result = api.exactL0StructuralRgba(rgba, width, height);
fs.writeFileSync(output, Buffer.from(result.buffer, result.byteOffset, result.byteLength));
process.stdout.write(JSON.stringify({bytes:result.byteLength}));
"""
    payload = _node(script, str(input_path), str(output_path))
    assert payload["bytes"] == height * width * 4

    actual = np.frombuffer(output_path.read_bytes(), dtype=np.uint8).reshape(height, width, 4)
    diff = np.abs(actual[:, :, :3].astype(np.int16) - expected.astype(np.int16))
    assert int(diff.max()) <= 1
    assert float(diff.mean()) <= 0.05


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_browser_v5_exact_mode_reports_structural_profile():
    completed = subprocess.run(
        [
            "node",
            "-e",
            r"""
global.MinimalizerSpectralFFT = require(process.argv[1]);
const api = require(process.argv[2]);
const width = 12, height = 10;
const rgba = new Uint8ClampedArray(width * height * 4);
for (let y = 0; y < height; y += 1) {
  for (let x = 0; x < width; x += 1) {
    const i = y * width + x;
    rgba[i * 4] = (x * 19 + y * 7) % 256;
    rgba[i * 4 + 1] = (y * 23 + x * 5) % 256;
    rgba[i * 4 + 2] = (180 + x * 3 - y * 9 + 256) % 256;
    rgba[i * 4 + 3] = 255;
  }
}
const result = api._core.analyzeRgba(rgba, width, height, {
  ...api.DEFAULTS,
  structuralMode: "spectral-exact",
  slicIterations: 2,
  slicTargetMin: 4,
  slicTargetMax: 4,
  slicMinAverageArea: 4,
  maxShapes: 2,
  hierarchyTargetMin: 2,
  hierarchyTargetMax: 2,
  paletteTarget: 2,
});
process.stdout.write(JSON.stringify({
  version: result.version,
  structuralPreprocess: result.metrics.structuralPreprocess,
}));
""",
            str(SPECTRAL),
            str(BROWSER_ENGINE),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["version"] == "browser-fallback-v11"
    assert payload["structuralPreprocess"] == "spectral-exact"
