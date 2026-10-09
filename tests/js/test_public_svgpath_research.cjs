"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "../..");
const source = fs.readFileSync(path.join(root, "web/static/vendor/svg-path-commander/index.min.js"), "utf8");
const scope = {};
vm.runInNewContext(source, scope, {timeout: 1000});
globalThis.SVGPathCommander = scope.SVGPathCommander;
assert.equal(typeof scope.SVGPathCommander, "function");
const audit = require(path.join(root, "web/static/public-svgpath-research.js"));

const square = {rings:[[[2,2],[12,2],[12,10],[2,10]]]};
const before = JSON.stringify(square);
const a = audit.auditShapes([square], 24, 24);
assert.equal(a.status,"ok");
assert.equal(a.parsedRings,1);
assert.equal(a.bboxMatches,1);
assert.equal(a.bboxMismatches,0);
assert.equal(a.measuredLength,36);
assert.equal(a.sourceVertices,4);
assert.equal(a.geometryApplied,false);
assert.equal(JSON.stringify(square),before, "cannot mutate source geometry");

const holed = audit.auditShapes([{rings:[
 [[2,2],[21,2],[21,21],[2,21]],
 [[8,8],[14,8],[14,14],[8,14]],
]}],24,24);
assert.equal(holed.status,"ok");
assert.equal(holed.parsedRings,2);
assert.equal(holed.bboxMatches,2);

const jagged = audit.auditShapes([{rings:[
 [[1.25,2.5],[14.75,3.25],[11.5,20.875],[1.25,2.5]],
]}],24,24);
assert.equal(jagged.status,"ok");
assert.equal(jagged.bboxMatches,1);

const invalid = audit.auditShapes([{rings:[[[0,0],[NaN,5],[8,8]]]}],24,24);
assert.equal(invalid.invalidRings,1);
assert.equal(invalid.parsedRings,0);

const bounded = audit.auditShapes(Array.from({length:10},()=>square),24,24);
assert.equal(bounded.status,"truncated");
assert.equal(bounded.shapesAudited,8);

assert.equal(audit.auditShapes([square],1000,1000).status,"invalid-input");
delete globalThis.SVGPathCommander;
const missing = audit.auditShapes([square],24,24);
assert.equal(missing.status,"unavailable");
assert.equal(missing.geometryApplied,false);

console.log("Public SVGPathCommander path audit: 7 scenarios PASS",JSON.stringify({
  bboxMatches:a.bboxMatches,perimeter:a.measuredLength,holeRings:holed.parsedRings
}));
