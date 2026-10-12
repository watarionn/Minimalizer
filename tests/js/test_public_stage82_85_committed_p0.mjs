import {test} from 'node:test';import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {buildHumanReviewQueue,verifyHumanReviewQueue} from '../../web/static/public-human-review-queue-p0.mjs';
import {inspectManualDraft} from '../../web/static/public-manual-draft-inspection-p0.mjs';
import {compareManualDrafts} from '../../web/static/public-manual-review-compare-p0.mjs';
import {auditOriginalFramePixels} from '../../web/static/public-original-frame-proof-p0.mjs';
import {encodeFullFrameDraftRle} from '../../web/static/public-fullframe-review-p0.mjs';
globalThis.crypto||=webcrypto;const sha=b=>createHash('sha256').update(b).digest('hex');
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
function source(){const w=8,n=64,rgba=new Uint8Array(4*n),face=new Uint8Array(n),bg=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
for(let i=0;i<n;i++)rgba.set([20,30,40,255],4*i);rgba[255]=0;left[1]=255;right[10]=255;
return {caseId:'GC001',width:w,height:w,sourceRgba:rgba,sourceRgbaSha256:sha(rgba),sourcePngSha256:'a'.repeat(64),faceMask:face,faceSha256:sha(face),backgroundMask:bg,backgroundSha256:sha(bg),owners:{left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}}};}
async function setup(){const s=source(),p=await buildHumanReviewQueue(s),labels=new Uint8Array(64);labels[1]=2;labels[2]=7;
const draft={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId:s.caseId,dimensions:[8,8],sourcePngSha256:s.sourcePngSha256,sourceRgbaSha256:s.sourceRgbaSha256,sourceEligibilitySha256:p.eligibilitySha256,status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',approved:false,paintAuthorized:false,reviewerAuthenticated:false,roles,rle:encodeFullFrameDraftRle(labels)};
return {s,p,draft,labels};}
test('S82 SHA pinned whole frame and false authority blocked',async()=>{
 const {s,p}=await setup();assert.equal(p.totalOriginalPixels,64);
 assert.equal((await verifyHumanReviewQueue(s,p)).verifiedSemanticPixels,0);
 p.rgbaSha256='0'.repeat(64);await assert.rejects(()=>verifyHumanReviewQueue(s,p),/UNTRUSTED_REVIEW_PACKET/);
});
test('S83 original source draft has no paint authority',async()=>{
 const {s,p,draft}=await setup(),x=await inspectManualDraft({source:s,packet:p,draft});
 assert.equal(x.proposedPixels,2);assert.equal(x.productPaintAuthorized,false);
});
test('S83 fake approval cannot pass',async()=>{
 const {s,p,draft}=await setup();draft.approved=true;
 await assert.rejects(()=>inspectManualDraft({source:s,packet:p,draft}),/UNTRUSTED_FULLFRAME_DRAFT_IDENTITY/);
});
test('S84 two changed proposals have unapproved disputes',async()=>{
 const {s,p,draft,labels}=await setup();labels[1]=5;
 const second={...draft,rle:encodeFullFrameDraftRle(labels)};
 const out=await compareManualDrafts({source:s,packet:p,drafts:[draft,second]});
 assert.equal(out.disputedPixels,1);assert.equal(out.semanticPixelsApproved,0);
});
test('S84 identical content cannot masquerade as independent reviewer',async()=>{
 const {s,p,draft}=await setup();await assert.rejects(()=>compareManualDrafts({source:s,packet:p,drafts:[draft,draft]}),/FULLFRAME_DUPLICATE_DRAFTS_NOT_INDEPENDENT/);
});
test('S85 DPR1 exact source RGBA, single-channel alteration rejected',async()=>{
 const {s}=await setup(),rgba=s.sourceRgba.slice();
 const input={width:8,height:8,sourceRgba:s.sourceRgba,sourceSha256:s.sourceRgbaSha256,renderedRgba:rgba,scale:1};
 assert.equal((await auditOriginalFramePixels(input)).pixelExact,true);
 rgba[3]^=1;assert.equal((await auditOriginalFramePixels(input)).pixelExact,false);
});
test('S85 DPR2 source RGBA exactness is not iPhone Safari',async()=>{
 const {s}=await setup(),rgba=new Uint8Array(16*16*4);
 for(let y=0;y<16;y++)for(let x=0;x<16;x++)rgba.set(s.sourceRgba.slice(4*(Math.floor(y/2)*8+Math.floor(x/2)),4*(Math.floor(y/2)*8+Math.floor(x/2))+4),4*(y*16+x));
 const input={width:8,height:8,sourceRgba:s.sourceRgba,sourceSha256:s.sourceRgbaSha256,renderedRgba:rgba,scale:2};
 const r=await auditOriginalFramePixels(input);assert.equal(r.pixelExact,true);assert.equal(r.iphoneSafariVerified,false);
});
test('S85 unpinned original source rejected',async()=>{
 const {s}=await setup();
 await assert.rejects(()=>auditOriginalFramePixels({width:8,height:8,sourceRgba:s.sourceRgba,sourceSha256:'0'.repeat(64),renderedRgba:s.sourceRgba.slice(),scale:1}),/ORIGINAL_SOURCE_SHA_MISMATCH/);
});
