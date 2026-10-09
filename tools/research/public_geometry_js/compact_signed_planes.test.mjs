import test from "node:test";
import assert from "node:assert/strict";
import {exactSourceBoundary,optimizeSignedColorPlanes} from "./compact_signed_planes.mjs";
const w=12,h=12,mask=new Uint8Array(w*h),rgb=new Uint8Array(w*h*3);
for(let y=1;y<11;y++)for(let x=1;x<10;x++)mask[y*w+x]=1;
mask[5*w+5]=0;mask[5*w+6]=0;mask[11*w+11]=1;
for(let i=0;i<w*h;i++){rgb[i*3]=i%w<6?25:240;rgb[i*3+1]=100;rgb[i*3+2]=130;}
const signed={mask,rgb,w,h,sourceSha:"a".repeat(64),maskSha:"b".repeat(64)};
test("mask contour retains separated island and internal hole",()=>{
 const out=exactSourceBoundary(mask,w,h);
 assert.equal(out.loops,3);
 assert.ok(out.vertices<out.perimeterCellEdges);
});
test("requested local shape budgets are never exceeded",()=>{
 for(const budget of [2,8,24,40,60,80]){
  const p=optimizeSignedColorPlanes({...signed,budget});
  assert.ok(p.metrics.shapes<=budget);
  assert.equal(p.metrics.clipSourceLoops,3);
  assert.equal(p.svg,optimizeSignedColorPlanes({...signed,budget}).svg);
  for(const plane of p.planes){
   assert.ok(plane.fill.every(Number.isInteger));
  }
 }
});
test("unsigned mask, invalid RGB or out-of-bound budget fails closed",()=>{
 assert.throws(()=>optimizeSignedColorPlanes({...signed,maskSha:"invalid"}));
 assert.throws(()=>optimizeSignedColorPlanes({...signed,rgb:new Uint8Array(3)}));
 assert.throws(()=>optimizeSignedColorPlanes({...signed,budget:1}));
 const bad=mask.slice();bad[0]=2;
 assert.throws(()=>optimizeSignedColorPlanes({...signed,mask:bad}));
});
