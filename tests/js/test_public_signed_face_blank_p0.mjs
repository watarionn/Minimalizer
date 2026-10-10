import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {blankSignedFace as run} from './public-signed-face-blank-p0.mjs';
if(!globalThis.crypto)globalThis.crypto=webcrypto;
const sha=x=>createHash('sha256').update(x).digest('hex');
function fixture(){const n=30*30;
 const src=new Uint8Array(n*4),base=new Uint8Array(n*4),mask=new Uint8Array(n);
 for(let i=0;i<n;i++){src.set([21,40,52,255],4*i);base.set([56,56,56,255],4*i);}
 for(let y=10;y<17;y++)for(let x=10;x<17;x++){
 const i=y*30+x;mask[i]=255;src.set([228,199,190,255],i*4);base.set([30,70,90,255],i*4);}
 src.set([30,60,90,255],(13*30+13)*4);
 return {width:30,height:30,sourceRgba:src,sourceRgbaSha256:sha(src),baselineRgba:base,
 baselineRgbaSha256:sha(base),signedFaceMask:mask,signedFaceMaskSha256:sha(mask)};
}
const rejects=(f,k)=>assert.rejects(f,new RegExp(k));
test('full signed face is one *original* skin RGB, no eyes, and exterior untouched',async()=>{
 const x=fixture(),r=await run(x),col=r.audit.observedFaceRGB;
 assert.deepEqual(col,[228,199,190]);assert.equal(r.audit.facePixels,49);assert.equal(r.audit.internalFaceColorCount,1);
 assert.equal(r.audit.outsideSignedFaceMicrofeatureSuppressionVerified,false);
 for(let i=0;i<900;i++){
  assert.equal(r.rgba[4*i+3],255);
  assert.deepEqual([...r.rgba.slice(i*4,i*4+3)],x.signedFaceMask[i]?col:[...x.baselineRgba.slice(i*4,i*4+3)]);
 }
 assert.equal(r.audit.productPromotionAuthorized,false);
});
test('stable and never mutates caller inputs',async()=>{const x=fixture(),a=JSON.stringify([...x.sourceRgba]),b=await run(x),c=await run(x);assert.deepEqual(b,c);assert.equal(JSON.stringify([...x.sourceRgba]),a);});
test('bad source SHA denied',async()=>{const x=fixture();x.sourceRgba[7]++;await rejects(()=>run(x),'source:SHA_mismatch');});
test('bad face SHA denied',async()=>{const x=fixture();x.signedFaceMask[0]=255;await rejects(()=>run(x),'face:SHA_mismatch');});
test('no skin source denied',async()=>{const x=fixture();for(let i=0;i<900;i++)if(x.signedFaceMask[i])x.sourceRgba.set([25,26,27,255],i*4);x.sourceRgbaSha256=sha(x.sourceRgba);await rejects(()=>run(x),'insufficient_source_skin_evidence');});
test('transparent source face denied',async()=>{const x=fixture();x.sourceRgba[(11*30+11)*4+3]=0;x.sourceRgbaSha256=sha(x.sourceRgba);await rejects(()=>run(x),'nonopaque_face_source');});
test('nonbinary face denied',async()=>{const x=fixture();x.signedFaceMask[11*30+11]=1;x.signedFaceMaskSha256=sha(x.signedFaceMask);await rejects(()=>run(x),'nonbinary_face');});
test('oversized face denied',async()=>{const x=fixture();x.signedFaceMask.fill(255);x.signedFaceMaskSha256=sha(x.signedFaceMask);await rejects(()=>run(x),'insufficient_source_skin_evidence');});
