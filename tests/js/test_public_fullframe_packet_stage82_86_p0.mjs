import {test} from 'node:test';import assert from 'node:assert/strict';
import {webcrypto,createHash} from 'node:crypto';
import {buildPrivateFullFrameReviewPacket,validatePrivateReviewPacket,inspectUntrustedFullFrameSubmission,adjudicationWorklistFromSubmissions,releaseGateAfterPrivateFullFrameReview} from '../../web/static/public-fullframe-review-packet-p0.mjs';
import {encodeFullFrameDraftRle} from '../../web/static/public-fullframe-review-p0.mjs';
globalThis.crypto ||= webcrypto;const h=b=>createHash('sha256').update(b).digest('hex');
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
function source(caseId='GC001'){
 const width=12,height=12,n=width*height,sourceRgba=new Uint8Array(n*4),faceMask=new Uint8Array(n),backgroundMask=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
 for(let i=0;i<n;i++)sourceRgba.set([30,60,80,255],i*4);
 for(let y=1;y<5;y++)for(let x=1;x<4;x++)left[y*width+x]=255;
 for(let y=6;y<10;y++)for(let x=8;x<11;x++)right[y*width+x]=255;
 backgroundMask[0]=255;faceMask[5*width+5]=255;sourceRgba[4*(n-1)+3]=0;
 return {caseId,width,height,sourceRgba,sourceRgbaSha256:h(sourceRgba),sourcePngSha256:'e'.repeat(64),faceMask,faceSha256:h(faceMask),backgroundMask,backgroundSha256:h(backgroundMask),owners:{left_arm:{mask:left,sha256:h(left)},right_arm:{mask:right,sha256:h(right)}}};
}
async function sample(){
 const s=source(),packet=await buildPrivateFullFrameReviewPacket(s),labels=new Uint8Array(144);
 labels[1]=2;labels[2]=7;labels[3]=5;
 const draft={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId:s.caseId,dimensions:[12,12],sourcePngSha256:s.sourcePngSha256,sourceRgbaSha256:s.sourceRgbaSha256,sourceEligibilitySha256:packet.sourceIdentity.eligibilitySha256,status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',approved:false,paintAuthorized:false,reviewerAuthenticated:false,roles,rle:encodeFullFrameDraftRle(labels)};
 const submission={format:'MinimalizerPublic-P0-fullframe-review-submission-v1',caseId:s.caseId,packetSha256:packet.packetSha256,tileMarks:[{tileId:0,navigationState:'visited'}],approved:false,reviewerAuthenticated:false,paintAuthorized:false,draft};
 return {s,packet,draft,submission,labels};
}
test('S86 original review packet is source-pinned and not authoritative',async()=>{
 const {s,packet}=await sample(),v=await validatePrivateReviewPacket({source:s,packet});
 assert.equal(packet.totals.allOriginalPixels,144);assert.equal(v.sourcePaintAuthorized,false);
 assert.equal(packet.authenticatedReviewers,0);
});
test('S86 source alteration fails closed',async()=>{
 const {s,packet}=await sample();s.sourceRgba[0]^=1;
 await assert.rejects(()=>validatePrivateReviewPacket({source:s,packet}),/SOURCE_PIN_MISMATCH/);
});
test('S86 forged packet identity and reviewer approval rejected',async()=>{
 const {s,packet}=await sample();
 packet.authenticatedReviewers=2;
 await assert.rejects(()=>validatePrivateReviewPacket({source:s,packet}),/REVIEW_PACKET_SOURCE_OR_TRUST_TAMPERED/);
 packet.authenticatedReviewers=0;packet.tiles[0].bbox=[0,0,1,1];
 await assert.rejects(()=>validatePrivateReviewPacket({source:s,packet}),/REVIEW_PACKET_SOURCE_OR_TRUST_TAMPERED/);
});
test('S86 untrusted user draft does not mutate original',async()=>{
 const {s,packet,submission}=await sample(),before=s.sourceRgba.slice();
 const v=await inspectUntrustedFullFrameSubmission({source:s,packet,submission});
 assert.equal(v.proposedSourcePixels,3);assert.equal(v.anatomicalLabelsCertified,0);
 assert.deepEqual(s.sourceRgba,before);
});
test('S86 tile navigation cannot authorize anatomy',async()=>{
 const {s,packet,submission}=await sample();
 const v=await inspectUntrustedFullFrameSubmission({source:s,packet,submission});
 assert.equal(v.tileNavigation.visited,1);assert.equal(v.reviewerIdentityTrusted,false);
});
test('S86 false submission approval and forged key rejected',async()=>{
 const {s,packet,submission}=await sample();
 submission.approved=true;
 await assert.rejects(()=>inspectUntrustedFullFrameSubmission({source:s,packet,submission}),/UNTRUSTED_SUBMISSION_IDENTITY/);
 submission.approved=false;submission.packetSha256='0'.repeat(64);
 await assert.rejects(()=>inspectUntrustedFullFrameSubmission({source:s,packet,submission}),/UNTRUSTED_SUBMISSION_IDENTITY/);
});
test('S86 transparent pixels are never labelable',async()=>{
 const {s,packet,submission,labels}=await sample();
 labels[143]=2;submission.draft.rle=encodeFullFrameDraftRle(labels);
 await assert.rejects(()=>inspectUntrustedFullFrameSubmission({source:s,packet,submission}),/FULLFRAME_NONOPAQUE_PROPOSAL/);
});
test('S86 duplicate navigation marks fail closed',async()=>{
 const {s,packet,submission}=await sample();
 submission.tileMarks.push({tileId:0,navigationState:'visited'});
 await assert.rejects(()=>inspectUntrustedFullFrameSubmission({source:s,packet,submission}),/UNTRUSTED_SUBMISSION_IDENTITY|INVALID_UNTRUSTED_TILE_MARK/);
});
test('S86 disputed manual labels stay untrusted',async()=>{
 const {s,packet,submission,labels}=await sample();
 const b={...submission,draft:{...submission.draft}};
 labels[2]=3;b.draft.rle=encodeFullFrameDraftRle(labels);
 const r=await adjudicationWorklistFromSubmissions({source:s,packet,submissions:[submission,b]});
 assert.equal(r.disputedUntrustedPixels,1);assert.equal(r.matchingUntrustedPixels,2);
 assert.equal(r.reviewersIndependentlyAuthenticated,0);assert.equal(r.paintAuthorized,false);
});
test('S86 duplicate annotations are not two independent humans',async()=>{
 const {s,packet,submission}=await sample();
 await assert.rejects(()=>adjudicationWorklistFromSubmissions({source:s,packet,submissions:[submission,submission]}),/FULLFRAME_DUPLICATE_DRAFTS_NOT_INDEPENDENT/);
});
test('S86 no synthetic manual review can pass product gate',()=>{
 const r=releaseGateAfterPrivateFullFrameReview({cases:[{caseId:'GC001',approved:true},{caseId:'Raden',approved:true}]});
 assert.equal(r.productionReleaseAuthorized,false);assert.equal(r.realIphoneSafariVerified,false);
 assert.equal(r.wholeCharacterHumanGolden,false);assert.equal(r.independentHumanSemanticPixelCount,0);
});
