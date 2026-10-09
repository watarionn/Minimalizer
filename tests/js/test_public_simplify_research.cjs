"use strict";
const assert = require("node:assert/strict");
const path = require("node:path");
const root = path.resolve(__dirname, "../..");

globalThis.simplify = require(path.join(root, "web/static/vendor/simplify-js/simplify.js"));
globalThis.MinimalizerOpenCvRaster = require(path.join(root, "web/static/opencv-fill-raster.js"));
const adapter = require(path.join(root, "web/static/public-simplify-research.js"));
const raster = globalThis.MinimalizerOpenCvRaster;

const rectangle = [[2, 2], [5, 2], [8, 2], [12, 2], [16, 2], [16, 16], [2, 16]];
const shape = { rings: [rectangle] };
const immutable = JSON.stringify(shape);
const a = adapter.auditShapes([shape], 24, 24);
assert.equal(a.status, "ok");
assert.equal(a.auditedShapes, 1);
assert.ok(a.safeSavedVertices >= 1, JSON.stringify(a));
assert.equal(a.geometryApplied, false);
assert.equal(JSON.stringify(shape), immutable, "must never mutate render geometry");

// Source-shape holes are guarded with an exact WHOLE-owner raster, not isolated rings.
const withHole = { rings: [
 rectangle,
 [[7, 7], [10, 7], [10, 10], [7, 10]],
]};
const b = adapter.auditShapes([withHole], 24, 24);
assert.equal(b.status, "ok");
assert.equal(b.geometryApplied, false);
assert.equal(raster.rasterizeLoops(withHole.rings, 24, 24, 2)[8 * 24 + 8], 0);

// A near-pixel-size notch is not safe to discard just because a simplifier
// believes its distance from a straight line is small.
const notch = [[2,2],[21,2],[21,21],[14,21],[14,20],[9,20],[9,21],[2,21]];
const c = adapter.auditShapes([{ rings: [notch] }], 24, 24);
assert.ok(["ok", "truncated"].includes(c.status));
assert.ok(c.rejectedProposals > 0, JSON.stringify(c));

const bound = adapter.auditShapes(Array.from({length: 14}, () => shape), 24, 24);
assert.equal(bound.status, "truncated");
assert.equal(bound.auditedShapes, 12);

const invalid = adapter.auditShapes([shape], 1000, 1000);
assert.equal(invalid.status, "invalid-input");

delete globalThis.simplify;
const missing = adapter.auditShapes([shape], 24, 24);
assert.equal(missing.status, "unavailable");
assert.equal(missing.safeSavedVertices, 0);

console.log("Public Simplify.js exact-mask research: 6 scenarios PASS", JSON.stringify({
 safeSavedVertices: a.safeSavedVertices,
 notchRejected: c.rejectedProposals,
 shapesBounded: bound.auditedShapes,
}));
