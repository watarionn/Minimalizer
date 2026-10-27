import {test} from 'node:test';import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {buildHumanReviewQueue} from '../../web/static/public-human-review-queue-p0.mjs';
import {encodeFullFrameDraftRle} from '../../web/static/public-fullframe-review-p0.mjs';
import {createOperatorReviewChecklist,auditPrivateReviewerSubmission,comparePrivateReviewerPair,evaluateTwoCaseManualIntake} from '../../web/static/public-human-review-intake-p0.mjs';
globalThis.crypto||=webcrypto;const sha=b=>createHash('sha256').update(b).digest('hex');
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
async function fixture(caseId='GC001'){
 const n=340*340,rgba=new Uint8Array(n*4),faceMask=new Uint8Array(n),
 backgroundMask=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
 for(let i=0;i<n;i++)rgba.set([i%250,(i>>1)%250,60,255],4*i);
 rgba[4*(n-1)+3]=0;faceMask[0]=255;backgroundMask[1]=255;left[2]=255;right[3]=255;
 const source={caseId,width:340,height:340,sourceRgba:rgba,sourceRgbaSha256:sha(rgba),
 sourcePngSha256:'c'.repeat(64),faceMask,faceSha256:sha(faceMask),
 backgroundMask,backgroundSha256:sha(backgroundMask),
 owners:{left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}}};
 const q=await buildHumanReviewQueue(source),base={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId,
 dimensions:[340,340],sourcePngSha256:source.sourcePngSha256,sourceRgbaSha256:source.sourceRgbaSha256,
 sourceEligibilitySha256:q.eligibilitySha256,status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',
 approved:false,paintAuthorized:false,reviewerAuthenticated:false,roles};
 const A=new Uint8Array(n),B=new Uint8Array(n);A[0]=3;B[0]=3;A[1]=1;B[1]=1;A[2]=5;B[2]=4;A[3]=4;B[3]=4;A[4]=9;B[4]=9;
 const d=bytes=>({...base,rle:encodeFullFrameDraftRle(bytes)});
 return {source,draftA:d(A),draftB:d(B),allOpaque:()=>{const x=new Uint8Array(n);x.fill(1);x[n-1]=0;return d(x);}};
}
test('181 operator slots prepared but availability is NOT identity enrollment',()=>{
 const q=createOperatorReviewChecklist();assert.equal(q.requiredFiles.length,4);
 assert.equal(q.independentReviewersVerified,0);assert.equal(q.goldenApproved,false);
});
test('181 reviewer slot cannot be invented in submitted JSON',async()=>{
 const q=await fixture();await assert.rejects(()=>auditPrivateReviewerSubmission({source:q.source,draft:q.draftA,slot:'C'}),/INVALID_OPERATOR_ASSIGNED_SLOT/);
});
test('181 only 340x340 original-shaped case IDs are admitted',async()=>{
 const q=await fixture();await assert.rejects(()=>auditPrivateReviewerSubmission({source:{...q.source,width:16},draft:q.draftA,slot:'A'}),/STAGE181_REQUIRES_340_ORIGINAL_CASE/);
});
test('182 source pin, class proposal counts and 121 original tiles are preserved',async()=>{
 const q=await fixture(),v=await auditPrivateReviewerSubmission({source:q.source,draft:q.draftA,slot:'A'});
 assert.equal(v.sourceRgbaSha256,q.source.sourceRgbaSha256);assert.equal(v.originalPixels,115600);
 assert.equal(v.originalTiles,121);assert.equal(v.originalOpaquePixels,115599);
 assert.equal(v.untrustedProposedPixels,5);assert.equal(v.unreviewedOpaquePixels,115594);
 assert.equal(v.uncertainOpaquePixels,1);assert.equal(v.classProposalCounts.skin_proposal,1);
 assert.equal(v.signerIdentityExternallyVerified,false);
});
test('182 fully proposed opaque original is ready only for external human review',async()=>{
 const q=await fixture(),v=await auditPrivateReviewerSubmission({source:q.source,draft:q.allOpaque(),slot:'B'});
 assert.equal(v.unreviewedOpaquePixels,0);assert.equal(v.reviewCoverageReady,true);
 assert.equal(v.independentHumanPixelGoldApproved,0);assert.equal(v.productReleaseAuthorized,false);
});
test('182 uncertain pixels prevent review-coverage readiness',async()=>{
 const q=await fixture(),v=await auditPrivateReviewerSubmission({source:q.source,draft:q.draftA,slot:'A'});
 assert.equal(v.reviewCoverageReady,false);assert(v.outstandingReviewTiles.length>0);
});
test('182 source mutation is detected before treating any labels as valid',async()=>{
 const q=await fixture();q.source.sourceRgba[3]^=1;
 await assert.rejects(()=>auditPrivateReviewerSubmission({source:q.source,draft:q.draftA,slot:'A'}),/SOURCE_PIN_MISMATCH/);
});
test('182 alpha excluded source cannot be annotated as opaque',async()=>{
 const q=await fixture();const x=new Uint8Array(115600);x[115599]=4;
 q.draftA={...q.draftA,rle:encodeFullFrameDraftRle(x)};
 await assert.rejects(()=>auditPrivateReviewerSubmission({source:q.source,draft:q.draftA,slot:'A'}),/FULLFRAME_NONOPAQUE_PROPOSAL/);
});
test('183 dual draft comparison counts uncertainty separate from disputes',async()=>{
 const q=await fixture(),v=await comparePrivateReviewerPair({source:q.source,draftA:q.draftA,draftB:q.draftB});
 assert.equal(v.untrustedAgreementPixels,3);assert.equal(v.untrustedDisputePixels,1);
 assert.equal(v.uncertainOpaquePixels,1);assert.equal(v.unreviewedOpaquePixels,115594);
 assert.equal(v.originalOpaquePixels,115599);assert.equal(v.humanSemanticPixelsCertified,0);
});
test('183 identical drafts do not prove humans and do not get wrongly rejected',async()=>{
 const q=await fixture(),v=await comparePrivateReviewerPair({source:q.source,draftA:q.draftA,draftB:q.draftA});
 assert.equal(v.identicalContentsWithoutIndependenceProof,true);
 assert.equal(v.independentPersonsVerified,0);assert.equal(v.productReleaseAuthorized,false);
});
test('183 full original tile accounting remains exact',async()=>{
 const q=await fixture(),v=await comparePrivateReviewerPair({source:q.source,draftA:q.draftA,draftB:q.draftB});
 assert.equal(v.tiles.length,121);
 assert.equal(v.tiles.reduce((n,t)=>n+t.agree+t.disputed+t.abstained+t.uncertain,0),v.originalOpaquePixels);
});
test('184 both original cases and four untrusted submissions validate without Golden',async()=>{
 const a=await fixture('GC001'),b=await fixture('Raden');
 const v=await evaluateTwoCaseManualIntake({cases:{GC001:a,Raden:b}});
 assert.equal(v.sourceCasesValidated,2);assert.equal(v.untrustedSubmissionsValidated,4);
 assert.equal(v.externalHumanIdentitiesVerified,0);assert.equal(v.releaseAuthorized,false);
});
test('184 cross-case substitution fails closed',async()=>{
 const a=await fixture('GC001'),b=await fixture('Raden');
 await assert.rejects(()=>evaluateTwoCaseManualIntake({cases:{GC001:b,Raden:a}}),/CROSS_CASE_MANUAL_INTAKE_REJECTED/);
});
test('185 forged human approval JSON rejected',async()=>{
 const q=await fixture();q.draftB.approved=true;
 await assert.rejects(()=>comparePrivateReviewerPair({source:q.source,draftA:q.draftA,draftB:q.draftB}),/UNTRUSTED_FULLFRAME_DRAFT_IDENTITY/);
});
test('185 missing original case is a hard stop not release',async()=>{
 const q=await fixture();
 await assert.rejects(()=>evaluateTwoCaseManualIntake({cases:{GC001:q}}),/TWO_SOURCE_CASES_REQUIRED/);
});
