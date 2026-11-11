import assert from "node:assert/strict";
import {
  VTRACER_DEFAULTS, normalizeVTracerSettings,
  readVTracerControls, writeVTracerControls
} from "../../local_worker/frontend/vtracer-demo-options.mjs";

const base = normalizeVTracerSettings();
assert.deepEqual(base, VTRACER_DEFAULTS);
assert.equal(base.binary, false);
assert.equal(base.mode, "spline");
assert.equal(base.hierarchical, "stacked");
const keys = new Map([
  ["color-mode","color"],["hierarchical","stacked"],["mode","spline"],
  ["filter-speckle","4"],["color-precision","6"],["gradient-step","16"],
  ["corner-threshold","60"],["segment-length","4"],["splice-threshold","45"],
  ["path-precision","4"]
]);
const root = {
  getElementById(id) {
    const key=id.replace("vtracer-","");
    assert(keys.has(key), "missing setting " + key);
    return {
      get value() {return keys.get(key)},
      set value(x) {keys.set(key,String(x))}
    };
  }
};
assert.deepEqual(readVTracerControls(root),base);
writeVTracerControls(root,{
  ...base,binary:true,hierarchical:"cutout",mode:"pixel",
  filterSpeckle:12,colorPrecision:4,layerDifference:40,
  cornerThreshold:155,lengthThreshold:6.5,spliceThreshold:83,pathPrecision:2
});
const updated = readVTracerControls(root);
assert.deepEqual(updated,{
  binary:true,hierarchical:"cutout",mode:"pixel",filterSpeckle:12,
  colorPrecision:4,layerDifference:40,cornerThreshold:155,
  lengthThreshold:6.5,maxIterations:10,spliceThreshold:83,pathPrecision:2
});
assert.equal(keys.get("color-mode"),"bw");
assert.equal(keys.get("mode"),"pixel");
writeVTracerControls(root,{...base,mode:"polygon"});
assert.equal(readVTracerControls(root).mode,"polygon");
assert.throws(()=>normalizeVTracerSettings({filterSpeckle:0}),RangeError);
assert.throws(()=>normalizeVTracerSettings({lengthThreshold:10.5}),RangeError);
assert.throws(()=>normalizeVTracerSettings({colorPrecision:Infinity}),RangeError);
assert.throws(()=>normalizeVTracerSettings({spliceThreshold:"broken"}),RangeError);
assert.equal(normalizeVTracerSettings({mode:"ignored",extra:"bad"}).mode,"spline");
console.log("LOCAL_VTRACER_DEMO_OPTIONS_PASS");
