import{test}from'node:test';import assert from'node:assert/strict';import{createHash,webcrypto}from'node:crypto';
import{buildTwoCasePrivateReviewManifest,summarizeReviewProgress,createHumanAdjudicationAgenda,assessSourceOnlyReleaseEvidence}from'../../web/static/public-human-review-protocol-p0.mjs';
import{buildHumanReviewQueue}from'../../web/static/public-human-review-queue-p0.mjs';
import{encodeFullFrameDraftRle}from'../../web/static/public-fullframe-review-p0.mjs';
import{buildOriginalOpaqueGeometry,stage100Hold}from'../../web/static/public-wholeframe-opacity-p0.mjs';
globalThis.crypto||=webcrypto;const sha=b=>createHash('sha256').update(b).digest('hex');
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
function source(caseId='GC001',width=8,height=8){
 const n=width*height,originalRgba=new Uint8Array(n*4),faceMask=new Uint8Array(n),backgroundMask=new Uint8Array(n),l=new Uint8Array(n),r=new Uint8Array(n);
 for(let i=0;i<n;i++)originalRgba.set([30,50,80,255],i*4);
 originalRgba[4*(n-1)+3]=0;l[1]=255;r[width+1]=255;
 const sourceRgba=originalRgba;
 return {caseId,width,height,sourceRgba,sourceRgbaSha256:sha(originalRgba),sourcePngSha256:'f'.repeat(64),
 originalRgba,originalRgbaSha256:sha(originalRgba),faceMask,faceSha256:sha(faceMask),
 backgroundMask,backgroundSha256:sha(backgroundMask),
 owners:{left_arm:{mask:l,sha256:sha(l)},right_arm:{mask:r,sha256:sha(r)}}};
}
async function setup(){const s=source(),packet=await buildHumanReviewQueue(s),labels=new Uint8Array(64);
 labels[1]=5;labels[2]=7;
 const draft={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId:s.caseId,
 dimensions:[8,8],sourceRgbaSha256:s.sourceRgbaSha256,sourcePngSha256:s.sourcePngSha256,
 sourceEligibilitySha256:packet.eligibilitySha256,status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',
 approved:false,paintAuthorized:false,reviewerAuthenticated:false,roles,rle:encodeFullFrameDraftRle(labels)};
 return {s,packet,draft,labels};}
test('S96 two originals independently pinned, no humans certified',async()=>{
 const r=await buildTwoCasePrivateReviewManifest([source('GC001'),source('Raden')]);
 assert.equal(r.cases.length,2);assert.equal(r.cases[0].originalPixels,64);
 assert.equal(r.reviewersExternallyAuthenticated,0);assert.equal(r.productionReleaseAuthorized,false);
});
test('S96 reversed or repeated source not accepted',async()=>{
 await assert.rejects(()=>buildTwoCasePrivateReviewManifest([source('Raden'),source('GC001')]),/TWO_ORDERED_ORIGINAL_CASES_REQUIRED/);
});
test('S97 untrusted proposed pixels not actual human semantic evidence',async()=>{
 const {s,packet,draft}=await setup();
 const r=await summarizeReviewProgress({source:s,packet,draft});
 assert.equal(r.proposedSourcePixels,2);assert.equal(r.actualIndependentHumanPixelsVerified,0);
 assert.equal(r.opaqueSourcePixelsWithoutProposals,61);
});
test('S97 corrupted original rejected',async()=>{
 const {s,packet,draft}=await setup();s.sourceRgba[0]^=1;
 await assert.rejects(()=>summarizeReviewProgress({source:s,packet,draft}),/SOURCE_PIN_MISMATCH/);
});
test('S98 every original tile gets human agenda and all disputed pixels accounted',async()=>{
 const {s,draft,labels}=await setup();labels[1]=6;
 const q=await createHumanAdjudicationAgenda({source:s,drafts:[draft,{...draft,rle:encodeFullFrameDraftRle(labels)}]});
 assert.equal(q.allOriginalTilesQueued,1);assert.equal(q.untrustedDisagreements,1);
 assert.equal(q.actualHumanAdjudications,0);assert.equal(q.releaseAuthorized,false);
});
test('S98 duplicate untrusted drafts cannot count as two humans',async()=>{
 const {s,draft}=await setup();
 await assert.rejects(()=>createHumanAdjudicationAgenda({source:s,drafts:[draft,draft]}),/IDENTICAL_DRAFT_NOT_INDEPENDENT/);
});
test('S99 forged good release records never bypass missing Golden or Safari',()=>{
 const x=assessSourceOnlyReleaseEvidence([{caseId:'GC001',humanApproved:true},{caseId:'Raden',humanApproved:true}]);
 assert.equal(x.missingCases.length,0);assert.equal(x.independentlyVerifiedHumanSemanticPixels,0);
 assert.equal(x.releaseAuthorized,false);assert.equal(x.physicalIphoneSafariHttpsVerified,false);
});
test('S100 opaque original pixel mask includes background and excludes alpha fringe',async()=>{
 const s=source(),z=await buildOriginalOpaqueGeometry(s);
 assert.equal(z.alpha255PixelCount,63);assert.equal(z.nonOpaquePixels,1);
 assert.equal(z.originalAlpha255MembershipExact,true);assert.equal(z.bodySilhouetteNotCertified,true);
 assert.equal(z.productionSvgAuthorized,false);
});
test('S101 original-only opacity SVG deterministic',async()=>{
 const s=source(),a=await buildOriginalOpaqueGeometry(s),b=await buildOriginalOpaqueGeometry(s);
 assert.equal(a.svg,b.svg);assert.equal(a.svgBytes,b.svgBytes);
 assert.equal(a.explicitVertices,a.rectangles.length*4);
});
test('S101 original RGB SHA swap rejected',async()=>{
 const s=source();s.originalRgbaSha256='0'.repeat(64);
 await assert.rejects(()=>buildOriginalOpaqueGeometry(s),/ORIGINAL_RGBA_SHA_MISMATCH/);
});
test('S102 opaque source is not a human silhouette, no production adoption',async()=>{
 const z=await buildOriginalOpaqueGeometry(source('Raden'));
 assert.equal(z.opaqueBackgroundMayBeIncluded,true);
 assert.equal(z.semanticHumanPixelsCertified,0);assert.equal(stage100Hold().releaseAuthorized,false);
});
test('S103 every release evidence gate remains closed',()=>{
 const z=assessSourceOnlyReleaseEvidence();
 assert.deepEqual(z.missingCases,['GC001','Raden']);
 assert.equal(z.wholeSceneSvgVertexBudgetMet,false);
 assert.equal(z.rollbackVerified,false);
});
