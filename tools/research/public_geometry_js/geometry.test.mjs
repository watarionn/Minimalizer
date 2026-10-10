import test from "node:test";
import assert from "node:assert/strict";
import { rasterizePolygon, proposePaperContour, proposeDelaunayPart, trianglesToSVG } from "./geometry.mjs";

const W = 32, H = 24;
function rgbFixture() {
  const rgb = new Uint8Array(W * H * 3);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const i = (y * W + x) * 3;
    rgb[i] = x < 16 ? 25 : 220;
    rgb[i + 1] = x < 16 ? 200 : 30;
    rgb[i + 2] = 80;
  }
  return rgb;
}
function partMask(x0, y0, x1, y1) {
  const m = new Uint8Array(W * H);
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) m[y * W + x] = 1;
  return m;
}
test("Paper.js candidate remains independent, deterministic and never auto-promotes", () => {
  const polygon = [[2, 2], [7, 2], [12, 2], [17, 2], [17, 6],
    [17, 12], [12, 12], [7, 12], [2, 12], [2, 7]];
  const snapshot = JSON.stringify(polygon);
  const mask = rasterizePolygon(polygon, W, H);
  const args = { points: polygon, width: W, height: H, sourceMask: mask,
    tolerance: 0.1, protectedIndices: [0, 3, 6, 8], maxMissingPixels: 0 };
  const a = proposePaperContour(args);
  const b = proposePaperContour(args);
  assert.deepEqual(a, b);
  assert.equal(JSON.stringify(polygon), snapshot);
  assert.equal(a.source, "paper@0.12.18");
  assert.equal(a.candidateOnly, true);
  assert.ok(a.pathData.length > 0);
  assert.ok(a.anchorCountAfter >= 2);
  assert.equal(typeof a.accepted, "boolean");
  if (a.accepted) {
    assert.equal(a.addedPixels, 0);
    assert.equal(a.missingPixels, 0);
    assert.equal(a.protectedPreserved, true);
    assert.ok(a.anchorCountAfter < a.anchorCountBefore);
  }
});
test("Paper.js rejects a smoothed silhouette that bulges beyond source pixels", () => {
  const width = 80, height = 60;
  const points = [[6, 6], [20, 6], [40, 6], [58, 6], [66, 6],
    [66, 18], [66, 30], [66, 52], [40, 52], [20, 52], [6, 52], [6, 30]];
  const sourceMask = rasterizePolygon(points, width, height);
  const proposed = proposePaperContour({
    points, width, height, sourceMask, tolerance: 0.1, maxMissingPixels: 0,
    protectedIndices: [0, 4, 7, 10],
  });
  assert.ok(proposed.addedPixels > 0, "curve must be checked for expansion");
  assert.equal(proposed.accepted, false, "expanded contours cannot pass");
  assert.equal(proposed.protectedPreserved, true, "landmark protection is not enough");
});

test("Paper.js rejects unverified input rather than inventing geometry", () => {
  const points = [[0, 0], [8, 0], [0, 8]];
  assert.throws(() => proposePaperContour({ points, width: W, height: H,
    sourceMask: new Uint8Array(3) }), /binary part mask/);
  assert.throws(() => proposePaperContour({ points, width: W, height: H,
    sourceMask: partMask(0, 0, 8, 8), protectedIndices: [99] }), /landmarks/);
});
test("Delaunator never crosses independently supplied part boundaries", () => {
  const left = partMask(2, 2, 14, 20);
  const right = partMask(18, 2, 30, 20);
  const rgb = rgbFixture();
  const a = proposeDelaunayPart({ width: W, height: H, partMask: left, sourceRGB: rgb, step: 3 });
  const b = proposeDelaunayPart({ width: W, height: H, partMask: right, sourceRGB: rgb, step: 3 });
  assert.ok(a.triangles.length > 0 && b.triangles.length > 0);
  for (const [p, mask] of [[a, left], [b, right]]) {
    assert.equal(p.candidateOnly, true);
    assert.equal(p.extraPixels, 0);
    assert.ok(p.coveredPixels > 0 && p.coveredPixels <= p.sourcePixels);
    for (const tri of p.triangles) {
      const [x, y] = tri.colorSample;
      assert.equal(mask[y * W + x], 1);
      assert.deepEqual(tri.rgb, Array.from(rgb.slice((y * W + x) * 3, (y * W + x) * 3 + 3)));
    }
  }
  assert.ok(a.triangles.every(t => t.rgb[0] === 25));
  assert.ok(b.triangles.every(t => t.rgb[0] === 220));
  assert.deepEqual(a, proposeDelaunayPart({ width: W, height: H, partMask: left, sourceRGB: rgb, step: 3 }));
  assert.match(trianglesToSVG(a, W, H), /^<svg /);
});
test("Delaunator rejects triangles that span an observed empty hole", () => {
  const mask = partMask(2, 2, 30, 22);
  for (let y = 7; y < 17; y++) for (let x = 11; x < 21; x++) mask[y * W + x] = 0;
  const out = proposeDelaunayPart({ width: W, height: H,
    partMask: mask, sourceRGB: rgbFixture(), step: 4 });
  assert.ok(out.rejectedOutsideMask > 0);
  assert.equal(out.extraPixels, 0);
  assert.ok(out.coveredPixels > 0);
});
test("Delaunator requires real input provenance and bound size", () => {
  assert.throws(() => proposeDelaunayPart({ width: W, height: H,
    partMask: partMask(0, 0, 4, 4), sourceRGB: [] }), /source RGB/);
  assert.throws(() => proposeDelaunayPart({ width: W, height: H,
    partMask: partMask(0, 0, 30, 20), sourceRGB: rgbFixture(), step: 1, maxPoints: 8 }), /point cap/);
  const empty = proposeDelaunayPart({ width: W, height: H,
    partMask: new Uint8Array(W * H), sourceRGB: rgbFixture() });
  assert.equal(empty.triangles.length, 0);
});
