import test from "node:test";
import assert from "node:assert/strict";
import {pixelRectangles,clippedSignedSvg} from "./source_signed_clip.mjs";

const w=9,h=8,mask=new Uint8Array(w*h),rgb=new Uint8Array(w*h*3);
for(let y=1;y<7;y++)for(let x=1;x<5;x++)mask[y*w+x]=1;
mask[3*w+3]=0;mask[4*w+3]=0;mask[2*w+7]=1;
for(let i=0;i<mask.length;i++){rgb[3*i]=100;rgb[3*i+1]=80;rgb[3*i+2]=140;}
const svg='<svg xmlns="http://www.w3.org/2000/svg" width="9" height="8" viewBox="0 0 9 8"><polygon points="1,1 8,1 4,7" fill="rgb(100,80,140)"/></svg>';
const args={mask,rgb,w,h,trianglesSvg:svg,sourceSha:"a".repeat(64),maskSha:"b".repeat(64)};

test("exact run rectangle union retains islands and holes",()=>{
 const proof=new Uint8Array(w*h);
 for(const rect of pixelRectangles(mask,w,h))
  for(let y=rect.y;y<rect.y+rect.height;y++)
   for(let x=rect.x;x<rect.x+rect.width;x++){
    assert.equal(proof[y*w+x],0);proof[y*w+x]=1;
   }
 assert.deepEqual(proof,mask);
});
test("source medoid undercoat is still a research-only candidate",()=>{
 const trial=clippedSignedSvg({...args,undercoat:true});
 assert.match(trial.svg,/<clipPath/);
 assert.equal(trial.metrics.maskPixels,mask.reduce((a,v)=>a+v,0));
 assert.equal(trial.metrics.productionEligible,false);
 assert.equal(trial.svg,clippedSignedSvg({...args,undercoat:true}).svg);
});
test("clip-only never inserts undercoat",()=>{
 const p=clippedSignedSvg(args);
 assert.equal(p.metrics.mode,"clip_only");
 assert.ok(p.metrics.shapes<pixelRectangles(mask,w,h).length+2);
});
test("fail closed on source or SVG mismatch",()=>{
 for(const v of [svg.replace("100,80,140","200,1,4"),svg.replace("</svg>","<image href='x'/></svg>"),svg.replace('width="9"','width="10"')])
  assert.throws(()=>clippedSignedSvg({...args,trianglesSvg:v}));
 assert.throws(()=>clippedSignedSvg({...args,maskSha:"fake"}));
 const wrong=mask.slice();wrong[0]=2;
 assert.throws(()=>clippedSignedSvg({...args,mask:wrong}));
});
