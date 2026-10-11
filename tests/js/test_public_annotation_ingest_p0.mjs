import {test} from 'node:test';import assert from 'node:assert/strict';import {webcrypto,createHash} from 'node:crypto';
import {validateManualReviewDraft,decodeReviewRle,encodeReviewRle} from '../../web/static/public-annotation-ingest-p0.mjs';
import {inspectAnnotationTopology} from '../../web/static/public-annotation-topology-p0.mjs';
import {compareReviewDrafts} from '../../web/static/public-independent-review-compare-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=x=>createHash('sha256').update(x).digest('hex');
function sample(caseId='GC001'){
 const width=12,height=12,n=width*height,sourceRgba=new Uint8Array(n*4),faceMask=new Uint8Array(n),backgroundMask=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n),labels=new Uint8Array(n);
 for(let i=0;i<n;i++)sourceRgba.set([100,111,125,255],i*4);
 for(let y=2;y<8;y++)for(let x=1;x<5;x++){left[y*width+x]=255;labels[y*width+x]=1;}
 for(let y=2;y<8;y++)for(let x=7;x<11;x++){right[y*width+x]=255;labels[y*width+x]=2;}
 faceMask[2*width+3]=255;labels[2*width+3]=0; backgroundMask[3*width+3]=255;labels[3*width+3]=0;
 sourceRgba[4*(4*width+3)+3]=0;labels[4*width+3]=0;
 const sourceRgbaSha256=sha(sourceRgba),faceSha256=sha(faceMask),backgroundSha256=sha(backgroundMask),sourcePngSha256='a'.repeat(64);
 const owners={left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}};
 const draft={format:'MinimalizerPublic-P0-source-manual-review-draft-v1',reviewStatus:'UNVERIFIED_UNTRUSTED_USER_ANNOTATION',approved:false,productPromotionAuthorized:false,caseId,dimensions:[width,height],sourcePngSha256,sourceRgbaSha256,
 historicalOwnerSha256:{left_arm:sha(left),right_arm:sha(right)},faceSha256,backgroundObserverSha256:backgroundSha256,
 labels:{0:'unclassified',1:'sleeve_observation',2:'skin_forearm_observation',3:'hair_observation',4:'other_clothes_observation'},rle:encodeReviewRle(labels)};
 const inputs={caseId,width,height,sourceRgba,sourceRgbaSha256,sourcePngSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,owners};return {inputs,draft,labels};
}
test('S26 verifies case/sha/owner with read-only original bytes',async()=>{const s=sample(),r=await validateManualReviewDraft({...s.inputs,draft:s.draft});assert.deepEqual(r.labels,s.labels);assert.equal(r.productPromotionAuthorized,false);assert.equal(r.counts[1],21);assert.equal(r.counts[2],24);assert.equal(r.eligiblePixels,45);});
test('S26 deterministic SHA',async()=>{const s=sample();const a=await validateManualReviewDraft({...s.inputs,draft:s.draft}),b=await validateManualReviewDraft({...s.inputs,draft:s.draft});assert.equal(a.labelsSha256,b.labelsSha256);});
test('S26 all unknown allowed, not promoted',async()=>{const s=sample();s.draft.rle=[[0,144]];const r=await validateManualReviewDraft({...s.inputs,draft:s.draft});assert.equal(r.unclassifiedEligiblePixels,45);assert.equal(r.productPromotionAuthorized,false);});
test('S26 rejects changed case',async()=>{const s=sample();s.draft.caseId='Raden';await assert.rejects(()=>validateManualReviewDraft({...s.inputs,draft:s.draft}),/CASE_OR_FORMAT/);});
test('S26 rejects false source SHA',async()=>{const s=sample();s.draft.sourceRgbaSha256='f'.repeat(64);await assert.rejects(()=>validateManualReviewDraft({...s.inputs,draft:s.draft}),/RGBA_DRAFT_SOURCE/);});
test('S26 rejects changed owner source',async()=>{const s=sample();s.inputs.owners.left_arm.mask[0]=255;await assert.rejects(()=>validateManualReviewDraft({...s.inputs,draft:s.draft}),/left_arm_ORIGINAL_SHA/);});
test('S26 rejects label inside face',async()=>{const s=sample();s.labels[2*12+3]=1;s.draft.rle=encodeReviewRle(s.labels);await assert.rejects(()=>validateManualReviewDraft({...s.inputs,draft:s.draft}),/FACE_EXCLUDED/);});
test('S26 rejects label inside background',async()=>{const s=sample();s.labels[3*12+3]=1;s.draft.rle=encodeReviewRle(s.labels);await assert.rejects(()=>validateManualReviewDraft({...s.inputs,draft:s.draft}),/BACKGROUND_EXCLUDED/);});
test('S26 rejects source-alpha alteration',async()=>{const s=sample();s.labels[4*12+3]=1;s.draft.rle=encodeReviewRle(s.labels);await assert.rejects(()=>validateManualReviewDraft({...s.inputs,draft:s.draft}),/ALPHA_EXCLUDED/);});
test('S26 rejects label outside signed arms',async()=>{const s=sample();s.labels[0]=1;s.draft.rle=encodeReviewRle(s.labels);await assert.rejects(()=>validateManualReviewDraft({...s.inputs,draft:s.draft}),/OUTSIDE_SOURCE_OWNER/);});
test('S26 rejects untrusted approval claim',async()=>{const s=sample();s.draft.approved=true;await assert.rejects(()=>validateManualReviewDraft({...s.inputs,draft:s.draft}),/UNTRUSTED_CLAIM/);});
test('S26 rejects label map substitution',async()=>{const s=sample();s.draft.labels[1]='real_signed_skin';await assert.rejects(()=>validateManualReviewDraft({...s.inputs,draft:s.draft}),/LABEL_MAP_CONFLICT/);});
test('S26 rejects RLE zero run',()=>assert.throws(()=>decodeReviewRle({rle:[[1,0],[0,144]],expectedPixels:144}),/RLE_CORRUPT/));
test('S26 rejects RLE overlong run',()=>assert.throws(()=>decodeReviewRle({rle:[[1,145]],expectedPixels:144}),/RLE_CORRUPT/));
test('S26 rejects RLE short stream',()=>assert.throws(()=>decodeReviewRle({rle:[[1,143]],expectedPixels:144}),/RLE_LENGTH_MISMATCH/));
test('S26 rejects RLE decimal and invalid code',()=>{assert.throws(()=>decodeReviewRle({rle:[[1.5,144]],expectedPixels:144}),/RLE_CORRUPT/);assert.throws(()=>decodeReviewRle({rle:[[7,144]],expectedPixels:144}),/RLE_CORRUPT/);});
test('S26 source RLE roundtrip',()=>{const s=sample();assert.deepEqual(decodeReviewRle({rle:encodeReviewRle(s.labels),expectedPixels:144}),s.labels);});
test('S27 source-connected topology counts',()=>{const s=sample();const q=inspectAnnotationTopology({width:12,height:12,labels:s.labels,sourceRgba:s.inputs.sourceRgba});assert.equal(q.labelsCount[1],21);assert.equal(q.labelsCount[2],24);assert.equal(q.productPromotionAuthorized,false);});
test('S27 rejects invalid input and tampered code',()=>{const s=sample();const lab=s.labels.slice();lab[0]=9;assert.throws(()=>inspectAnnotationTopology({width:12,height:12,labels:lab,sourceRgba:s.inputs.sourceRgba}),/INVALID_SOURCE_LABEL/);});
test('S27 disconnected tiny fragments flagged',()=>{const s=sample();s.labels.fill(0);s.labels[0]=1;s.labels[143]=1;const r=inspectAnnotationTopology({width:12,height:12,labels:s.labels,sourceRgba:s.inputs.sourceRgba});assert.equal(r.componentCount,2);assert.equal(r.smallIslands,2);});
test('S28 two annotations can agree but never claim independent identities',async()=>{const s=sample(),a=await validateManualReviewDraft({...s.inputs,draft:s.draft}),e=new Uint8Array(144).fill(255);const r=compareReviewDrafts({first:a,second:a,eligibilityMask:e});assert.equal(r.disputedPixels,0);assert.equal(r.independentReviewerIdentityVerified,false);assert.equal(r.sourceOwnerPaintingApproved,false);});
test('S28 disagreement tracked and abstained',async()=>{const s=sample(),a=await validateManualReviewDraft({...s.inputs,draft:s.draft}),b={...a,labels:a.labels.slice()};b.labels[2*12+1]=3;const r=compareReviewDrafts({first:a,second:b,eligibilityMask:new Uint8Array(144).fill(255)});assert.equal(r.disputedPixels,1);assert(r.unreviewedPixels>0);});
test('S28 wrong case fails closed',async()=>{const s=sample(),a=await validateManualReviewDraft({...s.inputs,draft:s.draft});assert.throws(()=>compareReviewDrafts({first:a,second:{...a,caseId:'Raden'},eligibilityMask:new Uint8Array(144).fill(255)}),/REVIEW_PAIR_LINEAGE_MISMATCH/);});
test('S28 source disagreement fails closed',async()=>{const s=sample(),a=await validateManualReviewDraft({...s.inputs,draft:s.draft});assert.throws(()=>compareReviewDrafts({first:a,second:{...a,sourceRgbaSha256:'f'.repeat(64)},eligibilityMask:new Uint8Array(144).fill(255)}),/REVIEW_PAIR_LINEAGE_MISMATCH/);});
