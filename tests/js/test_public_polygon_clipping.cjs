"use strict";

const assert = require("node:assert/strict");
const path = require("node:path");
const root = path.resolve(__dirname, "../..");
const clipping = require(path.join(root, "web/static/vendor/polygon-clipping/polygon-clipping.umd.min.js"));
globalThis.polygonClipping = clipping;
const adapter = require(path.join(root, "web/static/public-polygon-geometry.js"));

assert.equal(typeof clipping.intersection, "function", "vendored library is real");
assert.equal(adapter.VERSION, "public-polygon-clipping-v1");

const square = [[2, 2], [12, 2], [12, 12], [2, 12]];
const result = adapter.auditShapes([{ rings: [square] }], 10, 10);
assert.equal(result.status, "ok");
assert.equal(result.testedRings, 1);
assert.equal(result.visibleRingCount, 1);
assert.equal(result.clippedAreaSum, 64);

const outside = adapter.auditShapes([{ rings: [[[20, 20], [30, 20], [30, 30], [20, 30]]] }], 10, 10);
assert.equal(outside.status, "ok");
assert.equal(outside.visibleRingCount, 0);
assert.equal(outside.clippedAreaSum, 0);

const invalid = adapter.auditShapes([{ rings: [[[1, 1], [2, 2]]] }], 10, 10);
assert.equal(invalid.invalidRings, 1);
assert.equal(invalid.testedRings, 0);

const raw = JSON.stringify([{ rings: [square] }]);
adapter.auditShapes([{ rings: [square] }], 10, 10);
assert.equal(JSON.stringify([{ rings: [square] }]), raw, "diagnostic cannot mutate original geometry");

delete globalThis.polygonClipping;
const missing = adapter.auditShapes([{ rings: [square] }], 10, 10);
assert.equal(missing.status, "unavailable", "non-authoritative missing dependency must fail open");

console.log("Public polygon-clipping adapter: 5 scenarios PASS");
