import{test}from'node:test';import assert from'node:assert/strict';import{createHash,webcrypto}from'node:crypto';
import{buildHumanReviewQueue}from'../../web/static/public-human-review-queue-p0.mjs';
import{encodeFullFrameDraftRle}from'../../web/static/public-fullframe-review-p0.mjs';
import{auditSingleFullFrameProposal,prepareIndependentReviewerSlots,auditTwoDraftHumanHandoff,reviewHandoffReleaseGate}from'../../web/static/public-human-review-evidence-106-p0.mjs';
import{buildUntrustedWholeFramePreview,verifyUntrustedWholeFramePreview,assessUntrustedWholeFrameBudget}from'../../web/static/public-untrusted-fullscene-preview-p0.mjs';
globalThis.crypto||=webcrypto;const sha=b=>createHash('sha256').update(b).digest('hex');
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
function source(caseId='GC001'){
 const w=8,h=8,n=w*h,rgba=new Uint8Array(n*4),face=new Uint8Array(n),back=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
 for(let i=0;i<n;i++)rgba.set([i%256,20,45,255],i*4);
 rgba[(n-1)*4+3]=0;back[0]=255;face[4*w+4]=255;left[1]=255;right[w+1]=255;
 return{caseId,width:w,height:h,sourceRgba:rgba,sourceRgbaSha256:sha(rgba),sourcePngSha256:'a'.repeat(64),
 faceMask:face,faceSha256:sha(face),backgroundMask:back,backgroundSha256:sha(back),
 owners:{left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}}};
}
async function fixture(){const s=source(),packet=await buildHumanReviewQueue(s),
 labels=new Uint8Array(64);labels[0]=1;labels[1]=9;labels[2]=5;labels[3]=5;labels[4*8+4]=3;
 const draft={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId:s.caseId,dimensions:[8,8],
 sourceRgbaSha256:s.sourceRgbaSha256,sourcePngSha256:s.sourcePngSha256,
 sourceEligibilitySha256:packet.eligibilitySha256,status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',
 approved:false,paintAuthorized:false,reviewerAuthenticated:false,roles,rle:encodeFullFrameDraftRle(labels)};
 return{s,packet,draft,labels};}
test('S106 independent human slots are empty, not self-attested',()=>{const z=prepareIndependentReviewerSlots();assert.equal(z.independentPersonsCertified,0);assert.equal(z.reviewerA.externallyEnrolled,false);});
test('S106 reviewer case swap fails',()=>assert.throws(()=>prepareIndependentReviewerSlots({caseIds:['Raden','GC001']}),/BOTH_PINNED_CASES_REQUIRED/));
test('S107 source-pinned complete original accounting includes opaque background',async()=>{const{s,packet,draft}=await fixture(),z=await auditSingleFullFrameProposal({source:s,packet,draft});assert.equal(z.originalSourcePixels,64);assert.equal(z.originalOpaquePixels,63);assert.equal(z.proposedPixels,5);assert.equal(z.unreviewedOpaquePixels,58);assert.equal(z.backgroundProposalPixels,1);assert.equal(z.semanticLabelsCertified,0);});
test('S107 modified source is refused',async()=>{const{s,packet,draft}=await fixture();s.sourceRgba[0]^=1;await assert.rejects(()=>auditSingleFullFrameProposal({source:s,packet,draft}),/SOURCE_PIN_MISMATCH/);});
test('S108 zero labels cannot masquerade as complete manual review',async()=>{const{s,packet,draft}=await fixture();draft.rle=encodeFullFrameDraftRle(new Uint8Array(64));const z=await auditSingleFullFrameProposal({source:s,packet,draft});assert.equal(z.unreviewedOpaquePixels,63);assert.equal(z.reviewerPersonallyAuthenticated,false);});
test('S109 untrusted dual conflict atlas counts every original pixel',async()=>{const{s,packet,draft,labels}=await fixture();labels[2]=9;const b={...draft,rle:encodeFullFrameDraftRle(labels)},z=await auditTwoDraftHumanHandoff({source:s,packet,drafts:[draft,b]});assert.equal(z.tiles.length,1);assert.equal(z.disputed,1);assert.equal(z.untrustedMatching,4);assert.equal(z.abstained,59);assert.equal(z.productReleaseAuthorized,false);});
test('S109 duplicated submissions cannot claim independent human review',async()=>{const{s,packet,draft}=await fixture();await assert.rejects(()=>auditTwoDraftHumanHandoff({source:s,packet,drafts:[draft,draft]}),/IDENTICAL_DRAFT_NOT_INDEPENDENT/);});
test('S110 explicit product gate ignores forged approved flags',()=>{const z=reviewHandoffReleaseGate({cases:[{caseId:'GC001',approved:true},{caseId:'Raden',approved:true}]});assert.equal(z.authenticallyAnnotatedPixels,0);assert.equal(z.productReleaseAuthorized,false);assert.equal(z.personBackgroundGolden,false);});
test('S111 source-only proposal preview ignores face and background',async()=>{const{s,draft}=await fixture(),z=await buildUntrustedWholeFramePreview({source:s,draft});assert.equal(z.paintedSourcePixels,3);assert.deepEqual(z.foregroundLayers,[5,9]);assert.equal(z.untrustedFaceOrBackgroundExcluded,true);assert.equal(z.productionReleaseAuthorized,false);});
test('S111 all displayed colors are literal RGB values from source',async()=>{const{s,draft}=await fixture(),z=await buildUntrustedWholeFramePreview({source:s,draft});for(const layer of z.layers){const i=layer.sourceFirstPixelIndex;assert.equal(layer.sourceRgb,'#'+[...s.sourceRgba.subarray(i*4,i*4+3)].map(v=>v.toString(16).padStart(2,'0')).join(''));}});
test('S112 correct source pixels but honest quantized RGB mismatch',async()=>{const{s,draft}=await fixture(),z=await buildUntrustedWholeFramePreview({source:s,draft});assert.equal(z.rgbMismatchPixelsDueToSourcePaletteQuantization,1);assert.equal(z.exactOriginalRgbEverywhere,false);assert.equal(z.sourcePixelMembershipVerified,true);});
test('S112 original input remains byte-for-byte unchanged',async()=>{const{s,draft}=await fixture(),before=s.sourceRgba.slice();await buildUntrustedWholeFramePreview({source:s,draft});assert.deepEqual(s.sourceRgba,before);});
test('S112 source-transparent pixel label must fail rather than fill hole',async()=>{const{s,draft,labels}=await fixture();labels[63]=9;draft.rle=encodeFullFrameDraftRle(labels);await assert.rejects(()=>buildUntrustedWholeFramePreview({source:s,draft}),/FULLFRAME_NONOPAQUE_PROPOSAL/);});
test('S113 source-bound SVG render deterministic and sealed by replay',async()=>{const{s,draft}=await fixture(),z=await buildUntrustedWholeFramePreview({source:s,draft}),q=await verifyUntrustedWholeFramePreview({source:s,draft,candidate:z});assert.equal(q.pixelMembershipVerified,true);assert.equal(q.paintAuthorized,false);assert.equal((await buildUntrustedWholeFramePreview({source:s,draft})).svg,z.svg);});
test('S113 forged Golden candidate rejected',async()=>{const{s,draft}=await fixture(),z=await buildUntrustedWholeFramePreview({source:s,draft});z.humanGoldenApproved=true;await assert.rejects(()=>verifyUntrustedWholeFramePreview({source:s,draft,candidate:z}),/SOURCE_BOUND_PREVIEW_TAMPERED/);});
test('S113 SVG byte or membership tampering rejected',async()=>{const{s,draft}=await fixture(),z=await buildUntrustedWholeFramePreview({source:s,draft});z.svg=z.svg.replace('fill=', 'stroke=');await assert.rejects(()=>verifyUntrustedWholeFramePreview({source:s,draft,candidate:z}),/SOURCE_BOUND_PREVIEW_TAMPERED/);});
test('S114 budget always HOLD even if numeric rectangle vertices fit',async()=>{const{s,draft}=await fixture(),z=await buildUntrustedWholeFramePreview({source:s,draft}),v=assessUntrustedWholeFrameBudget(z);assert.equal(v.wholeBodyVertexGateApproved,false);assert.equal(v.actualWholeCharacterSubjectCoverageCertified,false);assert.equal(v.releaseAuthorized,false);});
test('S115 changed original file fails before preview can be built',async()=>{const{s,draft}=await fixture();s.sourceRgba[4]^=1;await assert.rejects(()=>buildUntrustedWholeFramePreview({source:s,draft}),/SOURCE_PIN_MISMATCH/);});
test('S113 falsified identity and semantic status cannot pass replay',async()=>{const{s,draft}=await fixture(),z=await buildUntrustedWholeFramePreview({source:s,draft});z.signerHumanIdentityVerified=true;await assert.rejects(()=>verifyUntrustedWholeFramePreview({source:s,draft,candidate:z}),/SOURCE_BOUND_PREVIEW_TAMPERED/);});
test('S114 even zero numeric cap excess can never mean full-body Golden',async()=>{const{s,draft}=await fixture(),z=await buildUntrustedWholeFramePreview({source:s,draft}),a=assessUntrustedWholeFrameBudget(z);assert.equal(a.previewOverCap,0);assert.equal(a.fullCharacterBudgetMet,undefined);assert.equal(a.bodyPartSemanticsHumanCertified,false);});
