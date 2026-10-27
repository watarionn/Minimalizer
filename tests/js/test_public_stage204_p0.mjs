import test from 'node:test';
import assert from 'node:assert/strict';
import {buildExactObservedBoundary, VERSION} from '../../web/static/public-stage204-source-exact-contour-p0.mjs';
function verify(caseId,width,height,mask){
 const r=buildExactObservedBoundary({caseId,width,height,mask});
 assert.equal(r.sourcePixels,mask.filter(v=>v===255).length);
 assert.equal(r.exactRasterReplay,true);assert.equal(r.spilledPixels,0);assert.equal(r.lostPixels,0);
 assert.equal(r.releaseAuthorized,false);assert.equal(r.semanticGolden,false);
 assert.equal(r.unknownPixelsFilled,0);assert.equal(r.independentlyCertifiedSemanticPixels,0);
 assert.equal(r.fillRule,'evenodd');assert.equal(r.version,VERSION);
 assert.ok(r.explicitVertices>=4*r.loops);
 return r;
}
test('204 empty source mask does not invent shapes',()=>{const a=verify('GC001',8,8,new Uint8Array(64));assert.equal(a.loops,0);assert.equal(a.pathD,'')});
test('204 1px square uses four vertices',()=>{const a=verify('Raden',1,1,new Uint8Array([255]));assert.equal(a.explicitVertices,4);assert.equal(a.loops,1)});
test('204 long clean bar has four vertices',()=>{const a=verify('GC001',60,2,new Uint8Array(120).fill(255));assert.equal(a.explicitVertices,4);assert.equal(a.boundaryEdges,124)});
test('204 diagonally touching pixels remain two closed loops',()=>{
 const r=verify('GC001',2,2,new Uint8Array([255,0,0,255]));assert.equal(r.loops,2);assert.equal(r.explicitVertices,8)
});
test('204 donut preserves hole, not filled',()=>{
 const m=new Uint8Array(25).fill(255);m[12]=0;const r=verify('GC001',5,5,m);assert.equal(r.loops,2);assert.equal(r.explicitVertices,8)
});
test('204 hole with winding and diagonal-touch ambiguity preserves source',()=>{
 const m=new Uint8Array(7*7).fill(255);for(let y=2;y<=4;y++)for(let x=2;x<=4;x++)m[y*7+x]=0;m[3*7+3]=255;
 verify('Raden',7,7,m)
});
test('204 all 512 3x3 binary combinations replay exactly without spill',()=>{
 for(let mask=0;mask<512;mask++){
  const pix=new Uint8Array(9);for(let i=0;i<9;i++)if(mask&(1<<i))pix[i]=255;
  verify('GC001',3,3,pix)
 }
});
test('204 randomized 16x16 patterns replay exact and bounded by input',()=>{
 let seed=1;const next=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed};
 for(let k=0;k<48;k++){
  const m=new Uint8Array(16*16);for(let i=0;i<m.length;i++)m[i]=next()%100<45?255:0;
  verify('Raden',16,16,m)
 }
});
test('204 checkerboard remains source exact and cannot pass Golden',()=>{
 const w=100,h=80,m=new Uint8Array(w*h);for(let y=0;y<h;y++)for(let x=0;x<w;x++)if((x+y)%2)m[y*w+x]=255;
 const r=verify('GC001',w,h,m);assert.equal(r.loops,4000);assert.equal(r.explicitVertices,16000);
 assert.equal(r.withinHistoricNumericBudget,false)
});
test('204 rejects malformed cases, masks, nonbinary inputs',()=>{
 assert.throws(()=>buildExactObservedBoundary({caseId:'Unknown',width:2,height:2,mask:new Uint8Array(4)}),/UNKNOWN_CASE/);
 assert.throws(()=>buildExactObservedBoundary({caseId:'GC001',width:2,height:2,mask:new Uint8Array(3)}),/INVALID_SOURCE_MASK/);
 assert.throws(()=>buildExactObservedBoundary({caseId:'GC001',width:2,height:2,mask:new Uint8Array([255,0,2,0])}),/NONBINARY/);
});
