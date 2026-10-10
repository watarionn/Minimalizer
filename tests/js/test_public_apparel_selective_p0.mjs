import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {replaySelectiveApparel} from '../../web/static/public-apparel-selective-p0.mjs';
const H=20,W=20,N=H*W;
const sha=b=>createHash('sha256').update(b).digest('hex');
function fixture(){
 const src=new Uint8Array(N*4),base=new Uint8Array(N*4);
 const parent=new Uint8Array(N),prot=new Uint8Array(N),pm=new Uint8Array(N);
 for(let i=0;i<N;i++){
  const c=(i%W>5&&i%W<15&&Math.floor(i/W)>5&&Math.floor(i/W)<15)?[251,252,253]:[35,40,70];
  src.set([...c,255],i*4);base.set([60,65,74,255],i*4);
  if(i>=W*3&&i<W*17&&i%W>=2&&i%W<18)parent[i]=255;
  if(i>=W*6&&i<W*15&&i%W>5&&i%W<15)pm[i]=255;
 }
 const panel={material:'white_shirt',owner:'lower_body',mask:pm,maskSha256:sha(pm),
  colorRgbObserved:[251,252,253],vertexCount:4,evidenceRef:'synthetic-verified',semanticApproval:false};
 const args={width:W,height:H,sourceRgba:src,sourceRgbaSha256:sha(src),
  baselineRgba:base,baselineRgbaSha256:sha(base),parentMask:parent,parentMaskSha256:sha(parent),
  protectedMask:prot,protectedMaskSha256:sha(prot),panels:[panel]};
 return args;
}
let count=0;async function test(name,fn){await fn();console.log('PASS',++count,name);}
const clone=x=>({ ...x, panels:[...x.panels] });
const rejects=async(x,pat)=>assert.rejects(replaySelectiveApparel(x),pat);
await test('source colors and positive quality increase',async()=>{
 const a=fixture(),v=await replaySelectiveApparel(a);
 assert.equal(v.audit.panels[0].accepted,true);
 assert(v.audit.changedPixels>0);assert(v.audit.sourceSquaredErrorAfter<v.audit.sourceSquaredErrorBefore);
 assert.equal(v.audit.productPromotionAuthorized,false);
 for(let i=0;i<N;i++)if(!a.panels[0].mask[i])assert.deepEqual([...v.rgba.slice(4*i,4*i+4)],[...a.baselineRgba.slice(4*i,4*i+4)]);
});
await test('read only source and reproducible replay',async()=>{
 const a=fixture(),old=Buffer.from(a.sourceRgba),a1=await replaySelectiveApparel(a),a2=await replaySelectiveApparel(a);
 assert.deepEqual(a1,a2);assert.deepEqual(Buffer.from(a.sourceRgba),old);
});
await test('no-op control with zero proposals',async()=>{
 const a=fixture();a.panels=[];const x=await replaySelectiveApparel(a);
 assert.deepEqual([...x.rgba],[...a.baselineRgba]);assert.equal(x.audit.changedPixels,0);
});
await test('unverified source hash rejected',async()=>{const a=fixture();a.sourceRgbaSha256='0'.repeat(64);await rejects(a,/SHA256_mismatch/);});
await test('unverified parent hash rejected',async()=>{const a=fixture();a.parentMaskSha256='a'.repeat(64);await rejects(a,/SHA256_mismatch/);});
await test('mask SHA mutation rejected',async()=>{const a=fixture();a.panels[0]={...a.panels[0],maskSha256:'b'.repeat(64)};await rejects(a,/SHA256_mismatch/);});
await test('face owner collision rejected',async()=>{const a=fixture();a.protectedMask[a.panels[0].mask.indexOf(255)]=255;a.protectedMaskSha256=sha(a.protectedMask);await rejects(a,/outside_source_owned_boundary/);});
await test('background owner exclusion rejected',async()=>{const a=fixture();a.parentMask[a.panels[0].mask.indexOf(255)]=0;a.parentMaskSha256=sha(a.parentMask);await rejects(a,/outside_source_owned_boundary/);});
await test('transparent source rejected',async()=>{const a=fixture();const i=a.panels[0].mask.indexOf(255);a.sourceRgba[i*4+3]=25;a.sourceRgbaSha256=sha(a.sourceRgba);await rejects(a,/outside_source_owned_boundary/);});
await test('invented source RGB rejected',async()=>{const a=fixture();a.panels[0]={...a.panels[0],colorRgbObserved:[238,249,253]};await rejects(a,/source_RGB_color_not_present/);});
await test('wrong material class rejected',async()=>{const a=fixture();a.panels[0]={...a.panels[0],material:'green_necktie'};await rejects(a,/source_RGB_color_not_present|source_color_precision/);});
await test('over-budget geometry rejected',async()=>{const a=fixture();a.maxAdditionalVertices=3;await rejects(a,/vertex_budget_exceeded/);});
await test('regressing valid material abstains',async()=>{
 const a=fixture();for(let i=0;i<N;i++)if(a.panels[0].mask[i])a.baselineRgba.set(a.sourceRgba.slice(i*4,i*4+4),i*4);
 a.baselineRgbaSha256=sha(a.baselineRgba);const z=await replaySelectiveApparel(a);
 assert.equal(z.audit.panels[0].accepted,false);assert.equal(z.audit.changedPixels,0);
});
await test('unsupported parts are not inferred',async()=>{const a=fixture();a.panels=[{...a.panels[0],material:'corset_lacing'}];await rejects(a,/unknown_material/);});
await test('owner claims do not permit automatic production promotion',async()=>{const a=fixture();a.panels[0]={...a.panels[0],semanticApproval:true};await rejects(a,/unsigned_semantic_authority/);});
console.log('ALL',count,'STAGE3_TESTS_PASSED');
