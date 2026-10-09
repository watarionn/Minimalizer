import assert from "node:assert/strict";
import {auditShapes, buildSourceSvg, makeCandidate, rgbaDiffPixels, VERSION} from "../../web/static/public-svgo-research.mjs";

let passed = 0;
function scenario(name, fn) {
  fn(); passed++;
  console.log("PASS", name);
}
const rectangle = {rgb: [12, 90, 200],
  rings: [[[2, 2], [12, 2], [12, 10], [2, 10]]]};
const withHole = {rgb: [255, 0, 30],
  rings: [
    [[0, 0], [20, 0], [20, 20], [0, 20]],
    [[5, 5], [5, 15], [15, 15], [15, 5]],
  ]};
scenario("SVGO official browser module and deterministic savings", () => {
  assert.match(VERSION, /svgo/);
  const source = buildSourceSvg([rectangle], 32, 32);
  assert.equal(source.status, "ok");
  assert.equal(source.shapesAudited, 1);
  const candidate = makeCandidate(source.svg);
  assert.equal(candidate, makeCandidate(source.svg));
  assert.ok(candidate.length < source.svg.length);
  assert.ok(candidate.includes("<svg") && candidate.includes("<path"));
  assert.ok(source.svg.includes("<!-- SVGO source-owner diagnostic only -->"));
});
scenario("holes and source owner paint order retained in copy", () => {
  const before = JSON.stringify([rectangle, withHole]);
  const build = buildSourceSvg([rectangle, withHole], 32, 32);
  assert.equal(build.ownerRings, 3);
  assert.equal(build.shapesAudited, 2);
  assert.equal(build.vertices, 12);
  assert.ok(build.svg.indexOf("rgb(12,90,200)") < build.svg.indexOf("rgb(255,0,30)"));
  assert.equal((build.svg.match(/fill-rule="evenodd"/g) || []).length, 2);
  assert.equal(JSON.stringify([rectangle, withHole]), before);
});
scenario("malformed and non-finite source fail closed", () => {
  assert.equal(buildSourceSvg([{}], 24, 24).status, "invalid-shape");
  assert.equal(buildSourceSvg([{...rectangle, rings: [[[0,0],[3,0],[Infinity,4]]]}], 24, 24).status, "invalid-ring");
  assert.equal(buildSourceSvg([rectangle], 0, 24).status, "invalid-input");
});
scenario("limits truncate whole owners and cap raster pixel count", () => {
  assert.equal(buildSourceSvg([rectangle], 401, 400).status, "invalid-input");
  const built = buildSourceSvg(Array.from({length: 12}, () => rectangle), 32, 32);
  assert.equal(built.status, "truncated");
  assert.equal(built.shapesAudited, 8);
  assert.equal(built.ownerRings, 8);
});
scenario("RGBA exact pixel equality is bit exact, incl alpha", () => {
  const a = new Uint8ClampedArray([1, 2, 3, 255, 4, 5, 6, 128]);
  const b = new Uint8ClampedArray(a);
  assert.equal(rgbaDiffPixels(a, b), 0);
  b[7] = 129;
  assert.equal(rgbaDiffPixels(a, b), 1);
  assert.equal(rgbaDiffPixels(a, [1,2]), null);
});
scenario("oversized SVG candidate rejected", () => {
  assert.throws(() => makeCandidate("x".repeat(120002)));
});
const unavailableAudit = await auditShapes([rectangle], 32, 32);
assert.equal(unavailableAudit.status, "error");
assert.equal(unavailableAudit.applied, false);
assert.equal(unavailableAudit.rasterExact, false);
passed++;
console.log("PASS missing browser raster fails closed and never applies");
assert.equal(unavailableAudit.savedBytes, 0);
passed++;
console.log("PASS failed raster never saves candidate bytes");
assert.equal(passed, 8);
console.log("8 scenarios PASS");
