import assert from "node:assert/strict";
import "../../web/static/opencv-fill-raster.js";
import {VERSION,initialize,sourceOwnerInput,viewportClip,auditShapes}
  from "../../web/static/public-clipper2-research.mjs";

const raster=globalThis.MinimalizerOpenCvRaster;
let passed=0;
function check(name,test){test();passed++;console.log("PASS",name);}
const square={rgb:[12,80,156],rings:[[[2,2],[20,2],[20,20],[2,20]]]};
const cut={rgb:[12,80,156],rings:[[[-4,3],[18,3],[18,19],[-4,19]]]};
const donut={rgb:[9,20,30],rings:[
  [[1,1],[23,1],[23,23],[1,23]],
  [[6,6],[6,17],[17,17],[17,6]]
]};
const module=await initialize();
check("official Clipper2 WASM executes Intersection64",()=>{
  assert.equal(typeof module.Intersect64,"function");
  const source=sourceOwnerInput(square);
  const candidate=viewportClip(module,source.flat,24,24);
  assert.equal(candidate.length,1);
  assert.equal(candidate[0].length,4);
  const orig=raster.rasterizeLoops(source.loops,24,24,2);
  const post=raster.rasterizeLoops(candidate,24,24,2);
  assert.deepEqual(post,orig);
});
check("external owner clips to viewport with unchanged source mask",()=>{
 const src=sourceOwnerInput(cut);
 const candidate=viewportClip(module,src.flat,24,24);
 assert.equal(candidate.length,1);
 assert.deepEqual(raster.rasterizeLoops(candidate,24,24,2),
   raster.rasterizeLoops(src.loops,24,24,2));
});
check("even-odd polygon hole remains raster-exact",()=>{
 const src=sourceOwnerInput(donut);
 const candidate=viewportClip(module,src.flat,24,24);
 assert.equal(candidate.length,2);
 assert.deepEqual(raster.rasterizeLoops(candidate,24,24,2),
   raster.rasterizeLoops(src.loops,24,24,2));
});
check("invalid, non-grid and unsafe values fail closed",()=>{
 assert.equal(sourceOwnerInput({rings:[[[0,0],[3,0],[NaN,2]]]}),null);
 assert.equal(sourceOwnerInput({rings:[[[0,0],[3,0],[.001,2]]]}),null);
 assert.equal(sourceOwnerInput({rings:[[[0,0],[3,0],[1e10,2]]]}),null);
 assert.equal(sourceOwnerInput({rings:[[[0,0],[3,0]]]}),null);
});
check("source untouched and poly ownership not applied",()=>{
 const source=[square,cut,donut];
 const before=JSON.stringify(source);
 assert.equal(sourceOwnerInput(square).vertices,4);
 assert.equal(JSON.stringify(source),before);
});
const sample=await auditShapes([square,cut,donut],24,24,raster);
check("bounded whole-source raster-gate returns metrics",()=>{
 assert.equal(sample.status,"ok");
 assert.equal(sample.auditedShapes,3);
 assert.equal(sample.exactShapes,3);
 assert.equal(sample.rasterDifferentPixels,0);
 assert.equal(sample.rejectedShapes,0);
 assert.equal(sample.applied,false);
 assert.equal(sample.candidateRings,4);
});
const cap=await auditShapes(Array.from({length:12},()=>square),24,24,raster);
check("shape cap truncates diagnostics not output",()=>{
 assert.equal(cap.status,"truncated");
 assert.equal(cap.auditedShapes,8);
 assert.equal(cap.exactShapes,8);
 assert.equal(cap.applied,false);
});
const bad=await auditShapes([square],500,500,raster);
const missing=await auditShapes([square],24,24,null);
check("invalid bounds and missing raster fail-closed",()=>{
 assert.equal(bad.status,"invalid-input");
 assert.equal(missing.status,"unavailable");
 assert.equal(bad.applied,false);
 assert.equal(missing.applied,false);
});
let calls=0;
const deliberatelyDifferent={rasterizeLoops(...args){
  const out=raster.rasterizeLoops(...args);
  calls++;
  if(calls%2===0)out[0]=out[0]===0?1:0;
  return out;
}};
const mismatch=await auditShapes([square],24,24,deliberatelyDifferent);
check("falsified candidate mask rejected instead of silently accepted",()=>{
 assert.equal(mismatch.status,"ok");
 assert.equal(mismatch.exactShapes,0);
 assert.equal(mismatch.rejectedShapes,1);
 assert.equal(mismatch.rasterDifferentPixels,1);
 assert.equal(mismatch.applied,false);
});
console.log(passed+" scenarios PASS");
