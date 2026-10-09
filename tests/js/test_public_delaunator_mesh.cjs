"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const repo = path.resolve(__dirname, "../..");
const source = fs.readFileSync(path.join(repo, "web/static/vendor/delaunator/delaunator.min.js"), "utf8");
const sandbox = {};
vm.runInNewContext(source, sandbox, { timeout: 1000 });
assert.equal(typeof sandbox.Delaunator, "function", "actual bundled Delaunator is executable");

globalThis.Delaunator = sandbox.Delaunator;
globalThis.MinimalizerOpenCvRaster = require(path.join(repo, "web/static/opencv-fill-raster.js"));
const adapter = require(path.join(repo, "web/static/public-mesh-research.js"));

const square = [[2, 2], [20, 2], [20, 20], [2, 20]];
const oneShape = { rings: [square] };
const old = JSON.stringify(oneShape);
const plain = adapter.auditShapes([oneShape], 24, 24);
assert.equal(plain.status, "ok");
assert.equal(plain.shapesAudited, 1);
assert.equal(plain.candidateTriangles, 2);
assert.equal(plain.acceptedTriangles, 2);
assert.equal(plain.rejectedTriangles, 0);
assert.equal(plain.geometryApplied, false);
assert.equal(JSON.stringify(oneShape), old, "observer must never mutate original shapes");

const hole = { rings: [
 square,
 [[7, 7], [15, 7], [15, 15], [7, 15]],
]};
const holed = adapter.auditShapes([hole], 24, 24);
assert.equal(holed.status, "ok");
assert.ok(holed.candidateTriangles >= 2);
assert.ok(holed.rejectedTriangles > 0, JSON.stringify(holed));
assert.equal(holed.geometryApplied, false);

const concave = { rings: [[[2,2],[20,2],[20,8],[8,8],[8,20],[2,20]]] };
const notched = adapter.auditShapes([concave], 24, 24);
assert.equal(notched.status, "ok");
assert.ok(notched.rejectedTriangles > 0, JSON.stringify(notched));

const bound = adapter.auditShapes(Array.from({ length: 12 }, () => oneShape), 24, 24);
assert.equal(bound.status, "truncated");
assert.equal(bound.shapesAudited, 8);

const invalid = adapter.auditShapes([oneShape], 1000, 1000);
assert.equal(invalid.status, "invalid-input");
const nanShape = adapter.auditShapes([{ rings: [[[0,0],[NaN,1],[5,5]]] }], 24, 24);
assert.equal(nanShape.skippedShapes, 1);

delete globalThis.Delaunator;
const missing = adapter.auditShapes([oneShape], 24, 24);
assert.equal(missing.status, "unavailable");
assert.equal(missing.acceptedTriangles, 0);

console.log("Public Delaunator original-owner mesh research: 7 scenarios PASS",
  JSON.stringify({ solidAccepted: plain.acceptedTriangles,
    holedRejected: holed.rejectedTriangles,
    concaveRejected: notched.rejectedTriangles }));
