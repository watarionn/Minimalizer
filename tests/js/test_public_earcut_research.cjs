"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const root = path.resolve(__dirname, "../..");
const browserSource = fs.readFileSync(path.join(root, "web/static/vendor/earcut/earcut.min.js"), "utf8");
const sandbox = {};
vm.runInNewContext(browserSource, sandbox, { timeout: 1000 });
assert.equal(typeof sandbox.earcut.default, "function", "pinned Earcut UMD executes");
globalThis.earcut = sandbox.earcut;
globalThis.MinimalizerOpenCvRaster = require(path.join(root, "web/static/opencv-fill-raster.js"));
const adapter = require(path.join(root, "web/static/public-earcut-research.js"));

const square = [[2, 2], [20, 2], [20, 20], [2, 20]];
const solid = {rings:[square]};
const original = JSON.stringify(solid);
const base = adapter.auditShapes([solid], 24, 24);
assert.equal(base.status, "ok");
assert.equal(base.auditedShapes, 1);
assert.equal(base.candidateTriangles, 2);
assert.equal(base.acceptedTriangles, 2);
assert.equal(base.rejectedTriangles, 0);
assert.equal(base.fullyReconstructedShapes, 1);
assert.equal(base.geometryApplied, false);
assert.equal(JSON.stringify(solid), original, "original source polygon must be immutable");

// Hole geometry is submitted as an explicit polygon-with-hole to Earcut.
// ANY triangle painting forbidden hole pixels is rejected by the source raster gate.
const hole = {rings:[
 square,
 [[7, 7], [15, 7], [15, 15], [7, 15]],
]};
const holes = adapter.auditShapes([hole], 24, 24);
assert.equal(holes.status, "ok");
assert.equal(holes.holeGroups, 1);
assert.ok(holes.candidateTriangles > 2);
assert.equal(holes.geometryApplied, false);

// Concavity: triangulation proposals must not paint outside the original L-mask.
const concave = {rings:[[[2,2],[20,2],[20,8],[8,8],[8,20],[2,20]]]};
const notch = adapter.auditShapes([concave], 24, 24);
assert.equal(notch.status, "ok");
assert.ok(notch.candidateTriangles >= 3);
assert.equal(notch.geometryApplied, false);

// Disconnected "two outer rings" must NOT be silently certified as "hole".
const disconnected = {rings:[
 [[2,2],[8,2],[8,8],[2,8]],
 [[16,16],[22,16],[22,22],[16,22]],
]};
const ambiguous = adapter.auditShapes([disconnected], 24, 24);
assert.equal(ambiguous.status, "ok");
assert.equal(ambiguous.fullyReconstructedShapes, 0);

const bounded = adapter.auditShapes(Array.from({length:10},()=>solid),24,24);
assert.equal(bounded.status, "truncated");
assert.equal(bounded.auditedShapes, 8);

const tooBig = adapter.auditShapes([solid], 1000, 1000);
assert.equal(tooBig.status, "invalid-input");
const malformed = adapter.auditShapes([{rings:[[[0,0],[NaN,1],[4,4]]]}],24,24);
assert.equal(malformed.skippedShapes,1);

delete globalThis.earcut;
const missing = adapter.auditShapes([solid], 24, 24);
assert.equal(missing.status, "unavailable");
assert.equal(missing.acceptedTriangles, 0);

console.log("Public Earcut hole-aware source-mask audit: 8 scenarios PASS", JSON.stringify({
 solidExact:base.fullyReconstructedShapes,
 holeAccepted:holes.acceptedTriangles,
 holeRejected:holes.rejectedTriangles,
 concaveAccepted:notch.acceptedTriangles,
 concaveRejected:notch.rejectedTriangles,
}));
