import {test} from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto,createHash} from 'node:crypto';
import {encodeReviewRle,validateManualReviewDraft} from '../../web/static/public-annotation-ingest-p0.mjs';
import {deriveSourceAnnotationAuthority} from '../../web/static/public-annotation-authority-p0.mjs';
import {reviewReceiptPayload,auditExternallySignedReview,assessTwoCaseHumanReviewReadiness} from '../../web/static/public-review-attestation-boundary-p0.mjs';
import {buildExactSourceColorFill,verifyExactSourceColorFill} from '../../web/static/public-source-exact-color-fill-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=a=>createHash('sha256').update(a).digest('hex');
function reviewSample(caseId='GC001'){
 const width=8,height=8,n=width*height,sourceRgba=new Uint8Array(4*n),faceMask=new Uint8Array(n),
 backgroundMask=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n),labels=new Uint8Array(n);
 for(let i=0;i<n;i++)sourceRgba.set([100,110,120,255],i*4);
 for(let y=2;y<4;y++)for(let x=1;x<3;x++){left[y*width+x]=255;labels[y*width+x]=1;}
 for(let y=4;y<6;y++)for(let x=5;x<7;x++){right[y*width+x]=255;labels[y*width+x]=2;}
 const sourceRgbaSha256=sha(sourceRgba),faceSha256=sha(faceMask),backgroundSha256=sha(backgroundMask),sourcePngSha256='a'.repeat(64);
 const owners={left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}};
 const draft={format:'MinimalizerPublic-P0-source-manual-review-draft-v1',reviewStatus:'UNVERIFIED_UNTRUSTED_USER_ANNOTATION',approved:false,
 productPromotionAuthorized:false,caseId,dimensions:[width,height],sourcePngSha256,sourceRgbaSha256,
 historicalOwnerSha256:{left_arm:sha(left),right_arm:sha(right)},faceSha256,backgroundObserverSha256:backgroundSha256,
 labels:{0:'unclassified',1:'sleeve_observation',2:'skin_forearm_observation',3:'hair_observation',4:'other_clothes_observation'},rle:encodeReviewRle(labels)};
 return {draft,caseId,width,height,sourceRgba,sourceRgbaSha256,sourcePngSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,owners};
}
async function signedFixture(){
 const sourceValidation=reviewSample();
 const authority=await deriveSourceAnnotationAuthority({width:sourceValidation.width,height:sourceValidation.height,
  originalRgba:sourceValidation.sourceRgba,originalSha256:sourceValidation.sourceRgbaSha256,
  faceMask:sourceValidation.faceMask,faceSha256:sourceValidation.faceSha256,
  backgroundMask:sourceValidation.backgroundMask,backgroundSha256:sourceValidation.backgroundSha256,
  arms:sourceValidation.owners});
 const sourceEligibilitySha256=authority.sourceEligibilitySha256;
 const valid=await validateManualReviewDraft(sourceValidation);
 const pair=await crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},true,['sign','verify']);
 const publicKeySpki=new Uint8Array(await crypto.subtle.exportKey('spki',pair.publicKey));
 const pinnedPublicKeySha256=sha(publicKeySpki);
 const payload=reviewReceiptPayload({caseId:valid.caseId,sourceRgbaSha256:valid.sourceRgbaSha256,sourcePngSha256:valid.sourcePngSha256,
  labelsSha256:valid.labelsSha256,sourceEligibilitySha256,reviewerKeySha256:pinnedPublicKeySha256});
 const signature=new Uint8Array(await crypto.subtle.sign({name:'ECDSA',hash:'SHA-256'},pair.privateKey,new TextEncoder().encode(payload)));
 return {sourceValidation,sourceEligibilitySha256,receipt:{payload,signature},externalTrust:{publicKeySpki,pinnedPublicKeySha256}};
}
function sourceSample(width=14,height=11){
 const n=width*height,sourceRgba=new Uint8Array(n*4),ownerMask=new Uint8Array(n),palette=[[25,35,50],[190,145,105]],labels=[];
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const i=y*width+x,c=(x<7)?0:1;sourceRgba.set([...palette[c],255],4*i);
  if(x>=1&&x<=12&&y>=1&&y<=9){ownerMask[i]=255;labels.push(c);}
 }
 return {width,height,sourceRgba,ownerMask,sourceSha256:sha(sourceRgba),ownerSha256:sha(ownerMask),palette,
 assignments:Uint8Array.from(labels)};
}
test('S72 no authentic independent full-body review at baseline',()=>{
 const a=assessTwoCaseHumanReviewReadiness();
 assert.deepEqual(a.missingCases,['GC001','Raden']);assert.equal(a.sourceOwnerSemanticPixelsTrusted,0);
 assert.equal(a.productionReleaseAuthorized,false);
});
test('S72 duplicate self-claim review records denied',()=>assert.throws(()=>assessTwoCaseHumanReviewReadiness([{caseId:'GC001'},{caseId:'GC001'}]),/INVALID_HUMAN_REVIEW_RECORDS/));
test('S72 both nominal records still do not authorize anatomy',()=>{
 const a=assessTwoCaseHumanReviewReadiness([{caseId:'GC001',signed:true},{caseId:'Raden',approved:true}]);
 assert.equal(a.missingCases.length,0);assert.equal(a.fullBodySilhouetteReviewed,false);assert.equal(a.sourceOwnerSemanticPixelsTrusted,0);
});
test('S72 cryptographic transport verifies externally anchored test signature only',async()=>{
 const f=await signedFixture(),v=await auditExternallySignedReview(f);
 assert.equal(v.cryptographicSignatureValid,true);assert.equal(v.reviewedHistoricalOwnerCandidatePixels,8);
 assert.equal(v.externalReviewerIdentityIndependentlyEstablished,false);assert.equal(v.paintAuthorized,false);
});
test('S72 source label change rejects signed receipt',async()=>{
 const f=await signedFixture();f.sourceValidation.draft.rle=[[0,64]];
 await assert.rejects(()=>auditExternallySignedReview(f),/REVIEW_RECEIPT_DATA_CONFLICT/);
});
test('S72 unpinned forged reviewer key denied',async()=>{
 const f=await signedFixture();f.externalTrust.pinnedPublicKeySha256='0'.repeat(64);
 await assert.rejects(()=>auditExternallySignedReview(f),/EXTERNAL_REVIEW_KEY_PIN_MISMATCH/);
});
test('S72 forged signature denied',async()=>{
 const f=await signedFixture();f.receipt.signature[0]^=1;
 await assert.rejects(()=>auditExternallySignedReview(f),/INVALID_EXTERNAL_REVIEW_SIGNATURE/);
});
test('S72 untrusted review cannot serve as its own signer',async()=>{
 const f=await signedFixture();delete f.externalTrust;
 await assert.rejects(()=>auditExternallySignedReview(f),/EXTERNAL_REVIEW_ANCHOR_REQUIRED/);
});
test('S72 source changed while receipt same fails',async()=>{
 const f=await signedFixture();f.sourceValidation.sourceRgba[0]^=1;
 await assert.rejects(()=>auditExternallySignedReview(f),/SOURCE_ORIGINAL_SHA_MISMATCH/);
});
test('S73 candidate covers exact observed source and contains no image embedding',async()=>{
 const s=sourceSample(),v=await buildExactSourceColorFill(s);
 assert.equal(v.sourcePixels,108);assert.equal(v.sourceMembershipAlgebraicallyExact,true);
 assert(v.fillSvg.includes('<path'));assert(!v.fillSvg.includes('<image'));assert(!v.fillSvg.includes('<script'));assert(!v.fillSvg.includes('data:'));
});
test('S73 output color derives from actual source medoids',async()=>{
 const v=await buildExactSourceColorFill(sourceSample());assert(v.fillSvg.includes('fill="#192332"'));assert(v.fillSvg.includes('fill="#be9169"'));
});
test('S73 exact rectangle vertices counted, not stroke endpoints',async()=>{
 const v=await buildExactSourceColorFill(sourceSample());assert.equal(v.explicitRectangleVertices,4*v.rectangleCount);
 assert.equal(v.fullCharacterVertexBudgetMet,false);assert.equal(v.adoptedForProduct,false);
});
test('S73 source SHA modification denied',async()=>{
 const s=sourceSample();s.sourceRgba[0]^=1;
 await assert.rejects(()=>buildExactSourceColorFill(s),/COLOR_SVG_SHA_MISMATCH/);
});
test('S73 owner SHA modification denied',async()=>{
 const s=sourceSample();s.ownerMask[0]=255;
 await assert.rejects(()=>buildExactSourceColorFill(s),/COLOR_SVG_SHA_MISMATCH/);
});
test('S73 invented palette RGB rejected',async()=>{
 const s=sourceSample();s.palette[1]=[1,2,3];
 await assert.rejects(()=>buildExactSourceColorFill(s),/UNOBSERVED_SOURCE_COLOR/);
});
test('S73 forged source owner assignment rejected',async()=>{
 const s=sourceSample();s.assignments[0]=12;
 await assert.rejects(()=>buildExactSourceColorFill(s),/INVALID_COLOR_SVG_ASSIGNMENT/);
});
test('S73 deterministic exact SVG and orientation choice',async()=>{
 const s=sourceSample(),a=await buildExactSourceColorFill(s),b=await buildExactSourceColorFill(s);
 assert.equal(a.fillSvg,b.fillSvg);assert.deepEqual(a.layers,b.layers);
});
test('S74 independent source-mask replay passes',async()=>{
 const s=sourceSample(),candidate=await buildExactSourceColorFill(s),v=await verifyExactSourceColorFill({...s,candidate});
 assert.equal(v.sourcePixels,108);assert.equal(v.rasterSourceMembershipExact,true);assert.equal(v.releaseAuthorized,false);
});
test('S74 altered SVG markup denied',async()=>{
 const s=sourceSample(),candidate=await buildExactSourceColorFill(s);candidate.fillSvg+='<script/>';
 await assert.rejects(()=>verifyExactSourceColorFill({...s,candidate}),/SOURCE_FILL_REPLAY_MISMATCH/);
});
test('S74 altered geometry denied',async()=>{
 const s=sourceSample(),candidate=await buildExactSourceColorFill(s);candidate.layers[0].rectangles[0][0]--;
 await assert.rejects(()=>verifyExactSourceColorFill({...s,candidate}),/SOURCE_FILL_LAYER_TAMPERED/);
});
test('S74 source assignment tampering denied',async()=>{
 const s=sourceSample(),candidate=await buildExactSourceColorFill(s);s.assignments[0]^=1;
 await assert.rejects(()=>verifyExactSourceColorFill({...s,candidate}),/SOURCE_FILL_REPLAY_MISMATCH|SOURCE_FILL_LAYER_TAMPERED/);
});
test('S74 fake cost verdict denied',async()=>{
 const s=sourceSample(),candidate=await buildExactSourceColorFill(s);candidate.fillSmallerThanStroke=!candidate.fillSmallerThanStroke;
 await assert.rejects(()=>verifyExactSourceColorFill({...s,candidate}),/SOURCE_FILL_REPLAY_MISMATCH/);
});
test('S75 no browser parity is claimed by Node geometry proof',async()=>{
 const c=await buildExactSourceColorFill(sourceSample());
 assert.equal(c.realBrowserDprParityVerified,false);assert.equal(c.status,'PRIVATE_SOURCE_FILL_DIAGNOSTIC_HOLD');
});
test('S76 signed test fixture is not independent reviewer proof',async()=>{
 const f=await signedFixture(),v=await auditExternallySignedReview(f);
 assert.equal(v.semanticLabelAccuracyEstablished,false);assert.equal(v.fullCharacterGolden,false);
});

test('S72 signer cannot bypass independently recomputed source eligibility pin',async()=>{
 const f=await signedFixture();f.sourceEligibilitySha256='f'.repeat(64);
 await assert.rejects(()=>auditExternallySignedReview(f),/REVIEW_ELIGIBILITY_PIN_MISMATCH/);
});
test('S72 cross-case draft is rejected before review credit',async()=>{
 const f=await signedFixture();f.sourceValidation.caseId='Raden';
 await assert.rejects(()=>auditExternallySignedReview(f),/CASE_OR_FORMAT_CONFLICT/);
});
test('S72 label outside historically allowed owner fails despite signer',async()=>{
 const f=await signedFixture();const labels=new Uint8Array(64);labels[0]=1;
 f.sourceValidation.draft.rle=encodeReviewRle(labels);
 await assert.rejects(()=>auditExternallySignedReview(f),/OUTSIDE_SOURCE_OWNER_LABEL/);
});
