import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {replaySourceFeatureSurfaces as run} from './public-source-feature-preservation-p0.mjs';
if(!globalThis.crypto)globalThis.crypto=webcrypto;
const sha=x=>createHash('sha256').update(x).digest('hex');
function sample(){
 const width=30,height=30,n=width*height;
 const src=new Uint8Array(n*4),base=new Uint8Array(n*4),face=new Uint8Array(n),m=new Uint8Array(n);
 for(let i=0;i<n;i++){
  const o=i*4;src.set([48,44,58,255],o);base.set([178,64,13,255],o);
 }
 for(let y=8;y<14;y++)for(let x=10;x<16;x++){
  const i=y*width+x,o=i*4;m[i]=255;src.set([230,232,239,255],o);
 }
 face[19*width+15]=255;
 const f={id:'goggles',role:'eyewear',colorClass:'high_neutral',evidenceLevel:'research_observation',
  evidenceRef:'frozen-p0-fixture-only-not-human-attestation',bbox:[8,6,18,15],mask:m,maskSha256:sha(m),maxPixels:100};
 const args={width,height,sourceRgba:src,sourceRgbaSha256:sha(src),baselineRgba:base,baselineRgbaSha256:sha(base),faceMask:face,faceMaskSha256:sha(face),features:[f],maxChangedPixels:100};
 return args;
}
const reject=async(fn,needle)=>assert.rejects(fn,new RegExp(needle));
test('goggles: only observed RGBA medoid inside exact owner; rest and alpha unchanged',async()=>{
 const x=sample(),s=x.sourceRgba.slice(),b=x.baselineRgba.slice(),m=x.features[0].mask.slice();
 const r=await run(x);assert.equal(r.audit.pixelsChanged,36);
 assert.deepEqual(r.audit.features[0].rgbSourceMedoid,[230,232,239]);
 for(let i=0;i<900;i++){
  const o=i*4;assert.equal(r.rgba[o+3],255);
  if(m[i])assert.deepEqual([...r.rgba.slice(o,o+3)],[230,232,239]);
  else assert.deepEqual([...r.rgba.slice(o,o+3)],[...b.slice(o,o+3)]);
 }
 assert.deepEqual(x.sourceRgba,s);assert.deepEqual(x.baselineRgba,b);
 assert.equal(r.audit.productPromotionAuthorized,false);
});
test('deterministic with same output and audit',async()=>{const x=sample(),a=await run(x),b=await run(x);assert.deepEqual(a,b);});
test('reject tampered source SHA',async()=>{const x=sample();x.sourceRgba[1]++;await reject(()=>run(x),'source:SHA_mismatch');});
test('reject tampered mask SHA',async()=>{const x=sample();x.features[0].maskSha256='0'.repeat(64);await reject(()=>run(x),'goggles:SHA_mismatch');});
test('reject tampered face mask',async()=>{const x=sample();x.faceMask[0]=255;await reject(()=>run(x),'face:SHA_mismatch');});
test('reject fake color class',async()=>{const x=sample();x.features[0].colorClass='low_dark';await reject(()=>run(x),'not_original_source_color_class');});
test('reject face crossing',async()=>{const x=sample();x.features[0].mask[19*30+15]=255;x.features[0].maskSha256=sha(x.features[0].mask);x.features[0].bbox=[9,8,17,20];await reject(()=>run(x),'facial_feature_guard');});
test('reject mask outside ROI',async()=>{const x=sample();x.features[0].bbox=[0,0,11,11];await reject(()=>run(x),'pixel_outside_source_roi');});
test('reject unsupported alpha',async()=>{const x=sample();x.sourceRgba[8*30*4+10*4+3]=0;x.sourceRgbaSha256=sha(x.sourceRgba);await reject(()=>run(x),'unsupported_alpha');});
test('reject nonbinary mask',async()=>{const x=sample();x.features[0].mask[0]=1;await reject(()=>run(x),'nonbinary_mask');});
test('reject masked source color not observed',async()=>{const x=sample();const i=8*30+10;x.sourceRgba.set([23,44,67,255],i*4);x.sourceRgbaSha256=sha(x.sourceRgba);await reject(()=>run(x),'not_original_source_color_class');});
test('reject duplicate owner ids',async()=>{const x=sample();x.features.push({...x.features[0]});await reject(()=>run(x),'invalid_role_or_id');});
test('reject overlapping masks with explicit other owner',async()=>{const x=sample();x.features.push({...x.features[0],id:'bow',role:'bow'});await reject(()=>run(x),'feature_overlap_unresolved');});
test('reject maxChanged budget',async()=>{const x=sample();x.maxChangedPixels=20;await reject(()=>run(x),'total_pixel_budget_exceeded');});
test('reject unsigned semantic authority',async()=>{const x=sample();x.features[0].evidenceLevel='independently_attested';await reject(()=>run(x),'unsigned_feature_evidence');});
test('research no-change when original and baseline colors same',async()=>{const x=sample();for(let i=0;i<900;i++)if(x.features[0].mask[i])x.baselineRgba.set(x.sourceRgba.slice(i*4,i*4+4),i*4);x.baselineRgbaSha256=sha(x.baselineRgba);const r=await run(x);assert.equal(r.audit.pixelsChanged,0);assert.equal(r.audit.features[0].reason,'ABSTAIN_NO_RGB_GAIN');});
test('even an abstained observation reserves overlap for fail-closed ownership',async()=>{
 const x=sample();for(let i=0;i<900;i++)if(x.features[0].mask[i])x.baselineRgba.set(x.sourceRgba.slice(i*4,i*4+4),i*4);
 x.baselineRgbaSha256=sha(x.baselineRgba);x.features.push({...x.features[0],id:'other',role:'bow'});
 await reject(()=>run(x),'feature_overlap_unresolved');
});
