import{test}from'node:test';import assert from'node:assert/strict';
import{createHash,webcrypto}from'node:crypto';
import{buildHumanReviewQueue}from'../../web/static/public-human-review-queue-p0.mjs';
import{encodeFullFrameDraftRle}from'../../web/static/public-fullframe-review-p0.mjs';
import{auditManualSourceDraft,buildFullImageConflictIntake,assessIntakeGate}from'../../web/static/public-manual-intake-audit-p0.mjs';
import{buildSourceExactRgbPreview,verifySourceExactRgbPreview,evaluateExactRgbSceneCap}from'../../web/static/public-source-rgb-lossless-preview-p0.mjs';
import{buildUntrustedWholeFramePreview}from'../../web/static/public-untrusted-fullscene-preview-p0.mjs';
globalThis.crypto||=webcrypto;const sha=x=>createHash('sha256').update(x).digest('hex');
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
function original(width=8,height=8,caseId='GC001'){
 const n=width*height,rgba=new Uint8Array(n*4),face=new Uint8Array(n),bg=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const i=y*width+x;rgba.set([11+(x%3),40+(y%2),90+(i%4),255],i*4);
 }
 rgba[(n-1)*4+3]=0;bg[0]=255;face[width*2+2]=255;left[1]=255;right[width+1]=255;
 return{caseId,width,height,sourceRgba:rgba,sourceRgbaSha256:sha(rgba),sourcePngSha256:'f'.repeat(64),
 faceMask:face,faceSha256:sha(face),backgroundMask:bg,backgroundSha256:sha(bg),
 owners:{left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}}};
}
async function fixture(width=8,height=8,caseId='GC001'){
 const s=original(width,height,caseId),packet=await buildHumanReviewQueue(s),labels=new Uint8Array(width*height);
 labels[0]=1;labels[1]=9;labels[2]=5;labels[3]=5;labels[4]=3;
 const draft={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId,
  dimensions:[width,height],sourcePngSha256:s.sourcePngSha256,sourceRgbaSha256:s.sourceRgbaSha256,
  sourceEligibilitySha256:packet.eligibilitySha256,status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',
  approved:false,paintAuthorized:false,reviewerAuthenticated:false,roles,rle:encodeFullFrameDraftRle(labels)};
 return{s,packet,draft,labels};
}
test('116 SHA-pinned manual intake counts entire original',async()=>{const{s,packet,draft}=await fixture(),z=await auditManualSourceDraft({source:s,packet,draft});assert.equal(z.allOriginalPixels,64);assert.equal(z.totalSourceTiles,1);assert.equal(z.actuallyAuthenticatedHumanSemanticPixels,0);});
test('117 original RGB tamper refused in manual intake',async()=>{const{s,packet,draft}=await fixture();s.sourceRgba[0]^=1;await assert.rejects(()=>auditManualSourceDraft({source:s,packet,draft}),/SOURCE_PIN_MISMATCH/);});
test('118 manual intake counts opaque unreviewed accurately',async()=>{const{s,packet,draft}=await fixture(),z=await auditManualSourceDraft({source:s,packet,draft});assert.equal(z.coverage.opaque,63);assert.equal(z.coverage.nonOpaque,1);assert.equal(z.coverage.proposed,5);assert.equal(z.coverage.unreviewed,58);});
test('119 every 32px tile accounted for at 340',async()=>{const{s,packet,draft}=await fixture(340,340),z=await auditManualSourceDraft({source:s,packet,draft});assert.equal(z.totalSourceTiles,121);assert.equal(z.tiles.reduce((a,t)=>a+t.opaqueSourcePixels+t.nonOpaqueSourcePixels,0),115600);});
test('120 reserved fake approval claim rejected outright',async()=>{const{s,packet,draft}=await fixture();draft.humanGolden=true;await assert.rejects(()=>auditManualSourceDraft({source:s,packet,draft}),/SELF_DECLARED_HUMAN_AUTHORITY_NOT_ALLOWED/);});
test('121 no spontaneous reviewer enrollment from file content',async()=>{const{s,packet,draft}=await fixture(),z=await auditManualSourceDraft({source:s,packet,draft});assert.equal(z.requiredIndependentPeople,2);assert.equal(z.independentlyEnrolledPeople,0);assert.equal(z.releaseAuthorized,false);});
test('122 two source drafts account for all disputes and abstentions',async()=>{const{s,packet,draft,labels}=await fixture();labels[2]=7;const z=await buildFullImageConflictIntake({source:s,packet,drafts:[draft,{...draft,rle:encodeFullFrameDraftRle(labels)}]});assert.equal(z.differingPixels,1);assert.equal(z.matchingUntrustedPixels,4);assert.equal(z.abstainedPixels,59);assert.equal(z.totalPixels,64);});
test('123 zero overlap draft is never independent consensus',async()=>{const{s,packet,draft,labels}=await fixture();labels.fill(0);const z=await buildFullImageConflictIntake({source:s,packet,drafts:[draft,{...draft,rle:encodeFullFrameDraftRle(labels)}]});assert.equal(z.matchingUntrustedPixels,0);assert.equal(z.adjudicatedSemanticPixels,0);});
test('124 same draft cannot impersonate two independent people',async()=>{const{s,packet,draft}=await fixture();await assert.rejects(()=>buildFullImageConflictIntake({source:s,packet,drafts:[draft,draft]}),/IDENTICAL_DRAFT_NOT_INDEPENDENT/);});
test('124 Golden flags ignored even when supplied for both cases',()=>{const g=assessIntakeGate({cases:[{caseId:'GC001',approved:true},{caseId:'Raden',approved:true}]});assert.equal(g.independentlyApprovedSourcePixels,0);assert.equal(g.productReleaseAuthorized,false);});
test('125 exact-original RGB SVG excludes face/background labels',async()=>{const{s,draft}=await fixture(),x=await buildSourceExactRgbPreview({source:s,draft});assert.equal(x.paintedPixels,3);assert.equal(x.excludedPixels,61);assert.equal(x.originalRgbMismatchPixels,0);assert.equal(x.releaseAuthorized,false);});
test('126 source RGB run segmentation merges only equal color',async()=>{const{s,draft}=await fixture(),x=await buildSourceExactRgbPreview({source:s,draft});assert.equal(x.vertices,x.rectangles*4);assert(x.rectangles<=x.paintedPixels);assert.equal(x.fullCharacterSemanticTruth,false);});
test('127 every SVG class color comes literally from source',async()=>{const{s,draft}=await fixture(),x=await buildSourceExactRgbPreview({source:s,draft});for(const l of x.colorLayers)assert(x.svg.includes(l.originalSourceColor));assert.equal(x.originalRgbMismatchPixels,0);});
test('128 source-transparent proposed label rejected before fill',async()=>{const{s,draft,labels}=await fixture();labels[63]=9;draft.rle=encodeFullFrameDraftRle(labels);await assert.rejects(()=>buildSourceExactRgbPreview({source:s,draft}),/FULLFRAME_NONOPAQUE_PROPOSAL/);});
test('129 deterministic exact RGBA output with repeat build',async()=>{const{s,draft}=await fixture(),a=await buildSourceExactRgbPreview({source:s,draft}),b=await buildSourceExactRgbPreview({source:s,draft});assert.equal(a.svg,b.svg);assert.equal(a.svgBytes,b.svgBytes);});
test('129 forged positive human Golden denied by verifier',async()=>{const{s,draft}=await fixture(),candidate=await buildSourceExactRgbPreview({source:s,draft});candidate.semanticPixelHumanApproved=3;await assert.rejects(()=>verifySourceExactRgbPreview({source:s,draft,candidate}),/SOURCE_EXACT_PREVIEW_TAMPERED/);});
test('129 altered SVG bytes rejected',async()=>{const{s,draft}=await fixture(),candidate=await buildSourceExactRgbPreview({source:s,draft});candidate.svg=candidate.svg.replace('fill=','stroke=');await assert.rejects(()=>verifySourceExactRgbPreview({source:s,draft,candidate}),/SOURCE_EXACT_PREVIEW_TAMPERED/);});
test('130 exact RGB fixes quantization of older one-color class preview',async()=>{const{s,draft}=await fixture(),a=await buildUntrustedWholeFramePreview({source:s,draft}),b=await buildSourceExactRgbPreview({source:s,draft});assert(a.rgbMismatchPixelsDueToSourcePaletteQuantization>0);assert.equal(b.originalRgbMismatchPixels,0);});
test('131 zero budget cannot be accepted as whole-character shape proof',async()=>{const{s,draft}=await fixture(),a=await buildSourceExactRgbPreview({source:s,draft}),b=evaluateExactRgbSceneCap(a);assert.equal(b.allBodyPixelsProven,false);assert.equal(b.fullSceneApproved,false);assert.equal(b.numericStage8Cap,1887);});
test('132 source SHA swapped blocks export',async()=>{const{s,draft}=await fixture();s.sourceRgba[2]^=1;await assert.rejects(()=>buildSourceExactRgbPreview({source:s,draft}),/SOURCE_PIN_MISMATCH/);});
test('130 quantized/exact source RGB frontier uses same pinned proposal',async()=>{const{s,draft}=await fixture(),{auditTwoPointSourceRgbFrontier}=await import('../../web/static/public-source-rgb-frontier-p0.mjs'),z=await auditTwoPointSourceRgbFrontier({source:s,draft});assert.equal(z.candidates.length,2);assert.equal(z.candidates[0].drawnPixels,z.candidates[1].drawnPixels);assert.equal(z.candidates[1].originalRgbMismatchPixels,0);});
test('131 frontier reports vertex growth for perfect RGB honestly',async()=>{const{s,draft}=await fixture(),{auditTwoPointSourceRgbFrontier}=await import('../../web/static/public-source-rgb-frontier-p0.mjs'),z=await auditTwoPointSourceRgbFrontier({source:s,draft});assert(z.rgbPixelsRecoveredFromQuantizedPreview>0);assert(z.explicitVertexIncreaseForFullRgb>=0);assert.equal(z.noGlobalOptimalityClaim,true);});
test('132 lack of human Golden never replaced by source-color agreement',async()=>{const{s,draft}=await fixture(),{auditTwoPointSourceRgbFrontier}=await import('../../web/static/public-source-rgb-frontier-p0.mjs'),z=await auditTwoPointSourceRgbFrontier({source:s,draft});assert.equal(z.fullCharacterCoverageVerified,false);assert.equal(z.productReleaseAuthorized,false);});
test('133 full RGB preview replay returns zero source RGB mismatches',async()=>{const{s,draft}=await fixture(),z=await buildSourceExactRgbPreview({source:s,draft}),v=await verifySourceExactRgbPreview({source:s,draft,candidate:z});assert.equal(v.originalSourceRgbExact,true);assert.equal(v.releaseAuthorized,false);});
test('134 no release even when selected subset fits historic numeric limit',async()=>{const{s,draft}=await fixture(),z=await buildSourceExactRgbPreview({source:s,draft}),v=evaluateExactRgbSceneCap(z);assert.equal(v.trueWholeCharacterVerticesMeasured,false);assert.equal(v.releaseAuthorized,false);});
test('135 original source input immutable after two-candidate study',async()=>{const{s,draft}=await fixture(),before=s.sourceRgba.slice(),{auditTwoPointSourceRgbFrontier}=await import('../../web/static/public-source-rgb-frontier-p0.mjs');await auditTwoPointSourceRgbFrontier({source:s,draft});assert.deepEqual(s.sourceRgba,before);});
