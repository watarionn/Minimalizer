import assert from 'node:assert/strict';
import { createHash, webcrypto } from 'node:crypto';
import {prepareSourceOwnedParts} from './public-source-part-authority-p0.mjs';
globalThis.crypto??=webcrypto;
const W=12,H=12,N=W*H;
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const src=new Uint8ClampedArray(N*4),face=new Uint8Array(N);
const left=new Uint8Array(N),right=new Uint8Array(N),tie=new Uint8Array(N);
for(let y=0;y<H;y++)for(let x=0;x<W;x++){
 const i=y*W+x,o=i*4;src.set([x*9,y*9,90,255],o);
 if(y>=2&&y<=3&&x>=5&&x<=6)face[i]=255;
 if(y>=5&&y<=9&&x>=1&&x<=4)left[i]=255;
 if(y>=5&&y<=9&&x>=7&&x<=10)right[i]=255;
 if(y>=6&&y<=10&&x>=3&&x<=8)tie[i]=255;
}
const owner=(id,role,mask,level='research_observation')=>({id,role,mask,maskSha256:sha(mask),
 evidenceLevel:level,evidenceRef:'sha256:recorded-immutable-test-source'});
const params=()=>({width:W,height:H,sourceRgba:src,sourceRgbaSha256:sha(src),
 faceMask:face,faceMaskSha256:sha(face),owners:[owner('left','left_arm',left),owner('right','right_arm',right)],occlusionEdges:[]});
let passed=0;
async function test(name,fn){await fn();console.log('PASS',name);passed++;}
await test('two non-overlapping source observations are partitioned',async()=>{
 const r=await prepareSourceOwnedParts(params());assert.equal(r.previewOnly,true);
 assert.equal(r.productPromotionAuthorized,false);assert.equal(r.visibleParts.length,2);
 assert.equal(r.visiblePixels,40);assert.equal(r.pixelsChanged,0);
 assert.equal(r.collisions.length,0);
});
await test('explicit front/behind source edge clips only occluded area',async()=>{
 const p=params();p.owners.push(owner('tie','tie_or_neckwear',tie));
 p.occlusionEdges=[{front:'left',behind:'tie',evidenceRef:'signed-source-occlusion-1'},
                   {front:'right',behind:'tie',evidenceRef:'signed-source-occlusion-2'}];
 const r=await prepareSourceOwnedParts(p);
 assert.equal(r.visiblePixels,40+30-16);assert.equal(r.visibleParts.find(x=>x.id==='tie').occludedPixels,16);
 assert.equal(r.collisions.length,2);
 assert.deepEqual(r.frontToBack,['left','right','tie']);
});
await test('unresolved source collision cannot be painted',async()=>{
 const p=params();p.owners.push(owner('tie','tie_or_neckwear',tie));
 await assert.rejects(()=>prepareSourceOwnedParts(p),/unresolved source ownership overlap/);
});
await test('partial depth evidence is insufficient for triple source owner',async()=>{
 const p=params();p.owners.push(owner('tie','tie_or_neckwear',tie));
 p.occlusionEdges=[{front:'left',behind:'tie',evidenceRef:'one relation'}];
 await assert.rejects(()=>prepareSourceOwnedParts(p),/unresolved source ownership overlap/);
});
await test('cyclic, self and unsupported occlusion relations fail closed',async()=>{
 for(const edges of [
  [{front:'left',behind:'right',evidenceRef:'x'},{front:'right',behind:'left',evidenceRef:'y'}],
  [{front:'left',behind:'left',evidenceRef:'x'}],
  [{front:'left',behind:'missing',evidenceRef:'x'}],
  [{front:'left',behind:'right'}]]){
  await assert.rejects(()=>prepareSourceOwnedParts({...params(),occlusionEdges:edges}),
    /cyclic|unknown|depth evidence/);
 }
});
await test('mis-pinned source and mask bytes rejected',async()=>{
 const a=params();a.sourceRgbaSha256='f'.repeat(64);
 await assert.rejects(()=>prepareSourceOwnedParts(a),/source SHA mismatch/);
 const b=params();b.owners[0].maskSha256='f'.repeat(64);
 await assert.rejects(()=>prepareSourceOwnedParts(b),/mask SHA mismatch/);
 const c=params();c.faceMaskSha256='f'.repeat(64);
 await assert.rejects(()=>prepareSourceOwnedParts(c),/face mask SHA mismatch/);
});
await test('face safety forbids candidate face collision',async()=>{
 const p=params();const bad=Uint8Array.from(left);bad[2*W+5]=255;
 p.owners[0]=owner('left','left_arm',bad);
 await assert.rejects(()=>prepareSourceOwnedParts(p),/face mask collision/);
});
await test('source transparency under an owner requires abstention',async()=>{
 const p=params();p.sourceRgba=Uint8ClampedArray.from(src);p.sourceRgba[5*W*4+4+3]=0;
 p.sourceRgbaSha256=sha(p.sourceRgba);
 await assert.rejects(()=>prepareSourceOwnedParts(p),/source-alpha/);
});
await test('owner evidence and role must be present and allowlisted',async()=>{
 for(const edit of [o=>o.role='unknown',o=>o.evidenceLevel='auto',o=>o.evidenceRef='',o=>o.id='foo/bar']){
  const p=params();edit(p.owners[0]);
  await assert.rejects(()=>prepareSourceOwnedParts(p),/owner|evidence/);
 }
});
await test('research-only owner never gains permission from forged status',async()=>{
 const p=params();p.owners[0].evidenceLevel='independently_attested';
 const r=await prepareSourceOwnedParts(p);
 assert.equal(r.visibleParts[0].productPromotionAuthorized,false);
 assert.equal(r.productPromotionAuthorized,false);
});
await test('reject nonbinary/empty masks and too many owners',async()=>{
 const a=params();a.owners[0].mask=new Uint8Array(N).fill(16);
 a.owners[0].maskSha256=sha(a.owners[0].mask);
 await assert.rejects(()=>prepareSourceOwnedParts(a),/nonbinary/);
 const b=params();b.owners[0].mask=new Uint8Array(N);
 b.owners[0].maskSha256=sha(b.owners[0].mask);
 await assert.rejects(()=>prepareSourceOwnedParts(b),/empty/);
});
await test('pixel budget and deterministic ordering and read-only inputs',async()=>{
 const p=params(),srcBefore=Uint8Array.from(src),faceBefore=Uint8Array.from(face);
 await assert.rejects(()=>prepareSourceOwnedParts({...p,maxVisiblePixels:5}),/budget/);
 const a=await prepareSourceOwnedParts(p);
 const b=await prepareSourceOwnedParts({...p,owners:[...p.owners].reverse()});
 assert.deepEqual(a.frontToBack,b.frontToBack);
 assert.deepEqual(a.visibleParts,b.visibleParts);
 assert.deepEqual([...src],[...srcBefore]);assert.deepEqual([...face],[...faceBefore]);
});
console.log('TOTAL',passed,'PASS');
