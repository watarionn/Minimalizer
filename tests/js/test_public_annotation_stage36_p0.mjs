import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {buildCompleteSourceReviewQueue} from '../../web/static/public-annotation-complete-review-queue-p0.mjs';
import {encodeReviewRle} from '../../web/static/public-annotation-ingest-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=a=>createHash('sha256').update(a).digest('hex');
function fixture(caseId='GC001'){
  const width=16,height=16,n=width*height,sourceRgba=new Uint8Array(n*4),faceMask=new Uint8Array(n),backgroundMask=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){let i=y*width+x;sourceRgba.set([x<8?20:120,y<8?40:140,70,255],i*4);}
  for(let y=3;y<13;y++)for(let x=2;x<7;x++)left[y*width+x]=255;
  for(let y=3;y<13;y++)for(let x=10;x<15;x++)right[y*width+x]=255;
  faceMask[6*width+11]=255;backgroundMask[4*width+2]=255;sourceRgba[4*(8*width+4)+3]=0;
  const owners={left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}};
  return {caseId,width,height,sourceRgba,sourceRgbaSha256:sha(sourceRgba),sourcePngSha256:'a'.repeat(64),faceMask,faceSha256:sha(faceMask),backgroundMask,backgroundSha256:sha(backgroundMask),owners};
}
function draft(f,pixels){const labels=new Uint8Array(f.width*f.height);for(const [i,v] of pixels)labels[i]=v;
  return {format:'MinimalizerPublic-P0-source-manual-review-draft-v1',reviewStatus:'UNVERIFIED_UNTRUSTED_USER_ANNOTATION',approved:false,productPromotionAuthorized:false,
    caseId:f.caseId,dimensions:[f.width,f.height],sourcePngSha256:f.sourcePngSha256,sourceRgbaSha256:f.sourceRgbaSha256,faceSha256:f.faceSha256,
    backgroundObserverSha256:f.backgroundSha256,historicalOwnerSha256:{left_arm:f.owners.left_arm.sha256,right_arm:f.owners.right_arm.sha256},
    labels:{0:'unclassified',1:'sleeve_observation',2:'skin_forearm_observation',3:'hair_observation',4:'other_clothes_observation'},rle:encodeReviewRle(labels)};}
const five=f=>[3*16+3,3*16+4,4*16+3,4*16+4,5*16+4];
const pair=f=>[draft(f,five(f).map(i=>[i,1])),draft(f,five(f).map((i,j)=>[i,j===2?2:1]))];
const run=(f=fixture(),drafts=[])=>buildCompleteSourceReviewQueue({...f,drafts,tileSize:8});
test('S36 enumerates ALL eligible source pixels including risk-free tiles',async()=>{const r=await run();assert.equal(r.eligiblePixels,97);assert.equal(r.tilePixelCoverage,97);assert(r.allEligiblePixelsQueued);assert.equal(r.reviewTasks.reduce((s,t)=>s+t.eligiblePixels,0),97);});
test('S36 counts eligible arms with no person classes inferred',async()=>{const r=await run();assert.deepEqual(r.eligibleByOwner,{left_arm:48,right_arm:49});assert.equal(r.reviewerVerifiedPixels,0);assert.equal(r.stage18PaintAllowed,false);});
test('S36 no drafts means every eligible pixel needs review',async()=>{const r=await run();assert.equal(r.unclassifiedPixels,97);assert.equal(r.unverifiedMatchingPixels,0);assert.equal(r.disagreedPixels,0);});
test('S36 source risk and queue determinism',async()=>{const f=fixture();assert.deepEqual(await run(f),await run(f));});
test('S36 exactly one synthetic conflict plus 4 untrusted agreements',async()=>{const f=fixture(),r=await run(f,pair(f));assert.equal(r.unverifiedMatchingPixels,4);assert.equal(r.disagreedPixels,1);assert.equal(r.unclassifiedPixels,92);assert.equal(r.reviewerVerifiedPixels,0);});
test('S36 task coverage accounts for all observed status categories',async()=>{const f=fixture(),r=await run(f,pair(f));assert.equal(r.reviewTasks.reduce((s,t)=>s+t.unclassified+t.disagreement+t.unverifiedAgreement,0),97);});
test('S36 first task prioritizes disagreement over identical score tiles',async()=>{const f=fixture(),r=await run(f,pair(f));const task=r.reviewTasks.find(t=>t.disagreement===1);assert(task);assert.equal(r.reviewTasks[0].tileId,task.tileId);});
test('S36 output contains coordinates/counts but neither RGBA nor owner masks',async()=>{const r=await run();const t=JSON.stringify(r);assert(!t.includes('sourceRgba:'));assert(!('eligible' in r));assert(!('labels' in r));assert(!('originalRgba' in r));});
test('S36 rejects protected-face annotation while preserving no-paint',async()=>{const f=fixture(),d=pair(f);const rogue=draft(f,[[6*16+11,1]]);await assert.rejects(()=>run(f,[d[0],rogue]),/FACE_EXCLUDED_LABEL/);});
test('S36 rejects forged review approval',async()=>{const f=fixture(),d=pair(f);d[0].approved=true;await assert.rejects(()=>run(f,d),/UNTRUSTED_CLAIM/);});
test('S36 rejects duplicated review bytes pretending two reviewers',async()=>{const f=fixture(),d=pair(f);await assert.rejects(()=>run(f,[d[0],d[0]]),/DUPLICATE_REVIEW_DATA/);});
test('S36 refuses stale source PNG lineage',async()=>{const f=fixture(),d=pair(f);d[1].sourcePngSha256='0'.repeat(64);await assert.rejects(()=>run(f,d),/PNG_DRAFT_SOURCE_MISMATCH/);});
test('S36 refuses source rgba modified without pinned digest',async()=>{const f=fixture();f.sourceRgba[0]++;await assert.rejects(()=>run(f),/SOURCE_PIN_MISMATCH/);});
test('S36 refuses legacy arm overlap even without draft labels',async()=>{const f=fixture();f.owners.right_arm.mask[3*16+3]=255;f.owners.right_arm.sha256=sha(f.owners.right_arm.mask);await assert.rejects(()=>run(f),/HISTORICAL_OWNER_COLLISION/);});
test('S36 refuses to truncate a full review queue under task budget',async()=>{const f=fixture();await assert.rejects(()=>buildCompleteSourceReviewQueue({...f,tileSize:4,maxTasks:1}),/COMPLETE_REVIEW_QUEUE_BUDGET_EXCEEDED/);});
test('S36 refuses single draft to avoid unpaired conformance pretence',async()=>{const f=fixture();await assert.rejects(()=>run(f,[pair(f)[0]]),/INVALID_STAGE36_QUEUE_INPUT/);});
test('S36 no source-absent labels or masks generated under zero contrast',async()=>{const f=fixture(),r=await buildCompleteSourceReviewQueue({...f,tileSize:8,minContrast:765});assert.equal(r.sourceContrastEdges,0);assert.equal(r.eligiblePixels,97);assert.equal(r.productPromotionAuthorized,false);});
test('S36 two case IDs separated even with same fixture coordinates',async()=>{const a=await run(fixture('GC001')),b=await run(fixture('Raden'));assert.notEqual(a.caseId,b.caseId);assert.equal(a.eligiblePixels,b.eligiblePixels);});

// Stage41 CI adapter: include the source-pinned Stage37-40 research suite.
import './test_public_review_stage37_40_p0.mjs';

// Stage46 CI adapter: source-only mobile viewport, case isolation and original RGB probe.
import './test_public_review_stage42_43_p0.mjs';
import './test_public_review_stage44_p0.mjs';

// Stage51 research CI adapter, source evidence only.
import './test_public_source_fidelity_stage47_50_p0.mjs';

// Stage56 source-exact research-only SVG stroke parity guard (no product activation).
import './test_public_source_stroke_stage52_55_p0.mjs';

// Stage61: verify original-source research only, never enable product painting.
import './test_public_source_stroke_stage57_60_p0.mjs';

// Stage66: source-attested color observation/medoid diagnostic, no normal product paint.
import './test_public_source_color_stage62_65_p0.mjs';
