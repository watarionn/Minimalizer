import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import initVTracer from "../../web/static/vendor/vtracer-wasm/vtracer.mjs";
import {VERSION,sampleSize,compareRgba,traceCandidate,auditCanvas}
  from "../../web/static/public-vtracer-research.mjs";

const wasmBytes=readFileSync(new URL(
  "../../web/static/vendor/vtracer-wasm/vtracer.wasm",import.meta.url));
await initVTracer({module_or_path:new Uint8Array(wasmBytes)});
let tests=0;
function check(name,fn){fn();tests++;console.log("PASS",name);}
check("sample sizing limits and 96px max side",()=>{
  assert.deepEqual(sampleSize(32,16),{width:32,height:16,downsampled:false});
  assert.deepEqual(sampleSize(400,200),{width:96,height:48,downsampled:true});
  assert.equal(sampleSize(0,25),null);
  assert.equal(sampleSize(99999,1),null);
});
check("RGBA comparator observes all 4 channels",()=>{
 const a=new Uint8ClampedArray([1,2,3,255,30,20,10,0]);
 const b=new Uint8ClampedArray(a);
 assert.equal(compareRgba(a,b).pixelExact,true);
 b[7]=1;b[1]=4;
 assert.equal(compareRgba(a,b).changedPixels,2);
 assert.equal(compareRgba(a,b).maxChannelDelta,2);
 assert.equal(compareRgba(a,[0,0,0,0]),null);
});
const w=20,h=20,pixels=new Uint8Array(w*h*4);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=4*(y*w+x),bright=!(x>=3&&x<17&&y>=4&&y<16);
 pixels[i]=bright?234:40;pixels[i+1]=bright?242:90;
 pixels[i+2]=bright?241:200;pixels[i+3]=255;
}
const before=new Uint8Array(pixels);
const svg=traceCandidate(pixels,w,h);
check("genuine third-party browser WASM raster to SVG",()=>{
 assert.match(VERSION,/vtracer/);
 assert.ok(svg.includes("<svg")&&svg.includes("</svg>"));
 assert.ok(svg.includes("<path"));
 assert.ok(svg.length>100);
 assert.deepEqual(pixels,before);
});
check("candidate is deterministic for same bounded input",()=>{
 assert.equal(traceCandidate(pixels,w,h),svg);
});
check("original owner's face/color/pixel state never applied",()=>{
 assert.equal(before.length,pixels.length);
 assert.deepEqual(pixels,before);
 assert.equal(typeof svg,"string");
});
check("oversize buffers and dimensions are rejected before tracing",()=>{
 assert.throws(()=>traceCandidate(pixels,w,h+1));
 assert.throws(()=>traceCandidate(pixels,500,500));
 assert.throws(()=>traceCandidate(new Uint8Array(0),0,0));
});
const fail=await auditCanvas({width:20,height:20});
check("no browser canvas means audit fails closed, never applies SVG",()=>{
 assert.equal(fail.status,"error");
 assert.equal(fail.applied,false);
 assert.equal(fail.tracedSvgBytes,0);
});
const wrong=await auditCanvas({width:-1,height:20});
check("invalid source dimensions fail closed",()=>{
 assert.equal(wrong.status,"invalid-input");
 assert.equal(wrong.applied,false);
});
assert.equal(tests,8);
console.log("8 scenarios PASS");
