import {test} from 'node:test';import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {buildPrivateOriginalReviewerHtml} from '../../web/static/public-offline-human-review-p0.mjs';
import {buildHumanReviewQueue} from '../../web/static/public-human-review-queue-p0.mjs';
import {fullFrameReceiptPayload,inspectExternallyPinnedFullFrameReceipt,compareDistinctSigningAnchors} from '../../web/static/public-human-review-provenance-p0.mjs';
import {buildHumanReviewDisputeMap} from '../../web/static/public-human-review-dispute-map-p0.mjs';
import {encodeFullFrameDraftRle} from '../../web/static/public-fullframe-review-p0.mjs';
globalThis.crypto||=webcrypto;const sha=b=>createHash('sha256').update(b).digest('hex');
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
function sample(width=8,height=8,caseId='GC001'){
 const n=width*height,sourceRgba=new Uint8Array(4*n),faceMask=new Uint8Array(n),backgroundMask=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
 for(let i=0;i<n;i++)sourceRgba.set([11,35,50,255],4*i);
 sourceRgba[4*(n-1)+3]=0;left[1]=255;right[width+1]=255;
 return {caseId,width,height,sourceRgba,sourceRgbaSha256:sha(sourceRgba),sourcePngSha256:'1'.repeat(64),faceMask,faceSha256:sha(faceMask),backgroundMask,backgroundSha256:sha(backgroundMask),owners:{left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}}};
}
async function prepared(){
 const source=sample(),packet=await buildHumanReviewQueue(source),labels=new Uint8Array(64);labels[1]=5;labels[2]=7;
 const draft={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId:source.caseId,dimensions:[8,8],
 sourceRgbaSha256:source.sourceRgbaSha256,sourcePngSha256:source.sourcePngSha256,
 sourceEligibilitySha256:packet.eligibilitySha256,
 status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',approved:false,paintAuthorized:false,reviewerAuthenticated:false,
 roles,rle:encodeFullFrameDraftRle(labels)};
 return {source,packet,draft,labels};
}
test('Stage91 actual original 340 square locked inside private HTML with no public release',async()=>{
 const source=sample(340,340),q=await buildPrivateOriginalReviewerHtml(source);
 assert.equal(q.tiles,121);assert.equal(q.sourcePixels,115600);assert.equal(q.humanPixelsReviewed,0);
 assert.match(q.html,/__privateReview/);assert.match(q.html,/UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL/);
 assert(!q.html.includes('__PINNED_SOURCE_RGBA_BASE64__'));assert.equal(q.publicDeploymentAllowed,false);
});
test('Stage91 source mutation rejected by SHA check',async()=>{
 const source=sample(340,340);source.sourceRgba[0]^=1;
 await assert.rejects(()=>buildPrivateOriginalReviewerHtml(source),/SOURCE_PIN_MISMATCH/);
});
test('Stage91 synthetic small frame cannot masquerade as private original',async()=>{
 await assert.rejects(()=>buildPrivateOriginalReviewerHtml(sample()),/PRIVATE_REVIEW_FIXED_ORIGINAL_340_ONLY/);
});
test('Stage91 reviewer HTML deterministic for original byte identity',async()=>{
 const source=sample(340,340),a=await buildPrivateOriginalReviewerHtml(source),b=await buildPrivateOriginalReviewerHtml(source);
 assert.equal(a.htmlSha256,b.htmlSha256);
});
test('Stage92 receipt payload rejects changed source digest',()=>{
 const z={caseId:'GC001',sourceRgbaSha256:'a'.repeat(64),sourcePngSha256:'b'.repeat(64),
  packetSha256:'c'.repeat(64),labelsSha256:'d'.repeat(64),publicKeySha256:'e'.repeat(64)};
 assert.match(fullFrameReceiptPayload(z),/fullframe-review-crypto-receipt-v1/);
 assert.throws(()=>fullFrameReceiptPayload({...z,sourceRgbaSha256:'bad'}),/INVALID_FULLFRAME_RECEIPT_FIELDS/);
});
test('Stage92 self-submitted anchor without public key refused',async()=>{
 const {source,packet,draft}=await prepared();
 await assert.rejects(()=>inspectExternallyPinnedFullFrameReceipt({source,packet,draft,
  receipt:{signature:new Uint8Array(64)},externalTrust:{pinnedPublicKeySha256:'a'.repeat(64)}}),/EXTERNAL_FULLFRAME_KEY_REQUIRED/);
});
test('Stage92 genuinely signed P256 receipt is key transport, NEVER a human identity',async()=>{
 const {source,packet,draft}=await prepared();
 const key=await crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},true,['sign','verify']);
 const publicKeySpki=new Uint8Array(await crypto.subtle.exportKey('spki',key.publicKey));
 const pin=sha(publicKeySpki),tmp=await crypto.subtle.digest('SHA-256',new Uint8Array(64));
 const labels=new Uint8Array(64);labels[1]=5;labels[2]=7;
 const text=fullFrameReceiptPayload({caseId:source.caseId,sourceRgbaSha256:source.sourceRgbaSha256,
  sourcePngSha256:source.sourcePngSha256,packetSha256:packet.packetSha256,labelsSha256:sha(labels),publicKeySha256:pin});
 const signature=new Uint8Array(await crypto.subtle.sign({name:'ECDSA',hash:'SHA-256'},key.privateKey,new TextEncoder().encode(text)));
 assert.equal(signature.length,64);
 const input={source,packet,draft,receipt:{payload:text,signature},externalTrust:{publicKeySpki,pinnedPublicKeySha256:pin}};
 const ok=await inspectExternallyPinnedFullFrameReceipt(input);
 assert.equal(ok.signatureCryptographicallyVerified,true);assert.equal(ok.signerHumanIdentityVerified,false);
 assert.equal(ok.productReleaseAuthorized,false);assert.equal(ok.semanticPixelsGoldApproved,0);
 input.receipt={payload:text,signature:signature.slice()};input.receipt.signature[0]^=1;
 await assert.rejects(()=>inspectExternallyPinnedFullFrameReceipt(input),/FULLFRAME_SIGNATURE_INVALID/);
});
test('Stage92 distinct signing keys cannot be advertised as independent humans',()=>{
 const a={keySha256:'a'.repeat(64)},b={keySha256:'b'.repeat(64)};
 assert.equal(compareDistinctSigningAnchors(a,b).distinctHumanReviewersVerified,false);
 assert.throws(()=>compareDistinctSigningAnchors(a,a),/DISTINCT_EXTERNAL_SIGNER_KEY_PINS_REQUIRED/);
});
test('Stage93 exact per-pixel disagreement mapped without the first512 truncation',async()=>{
 const {source,draft,labels}=await prepared();
 labels[1]=6;const second={...draft,rle:encodeFullFrameDraftRle(labels)};
 const result=await buildHumanReviewDisputeMap({source,drafts:[draft,second]});
 assert.equal(result.originalPixels,64);assert.equal(result.disputedUntrustedPixels,1);
 assert.equal(result.matchingUntrustedPixels,1);assert.equal(result.abstainedPixels,62);
 assert.equal(result.prioritizedUntrustedTiles[0].disputedUntrustedPixels,1);
 assert.equal(result.independentlyHumanReviewedPixels,0);
});
test('Stage93 identical drafts cannot create simulated two-reviewer consensus',async()=>{
 const {source,draft}=await prepared();
 await assert.rejects(()=>buildHumanReviewDisputeMap({source,drafts:[draft,draft]}),/IDENTICAL_DRAFT_NOT_INDEPENDENT/);
});
test('Stage93 all pixels accounted and no source modifications',async()=>{
 const {source,draft,labels}=await prepared(),before=source.sourceRgba.slice();
 labels[2]=0;const res=await buildHumanReviewDisputeMap({source,drafts:[draft,{...draft,rle:encodeFullFrameDraftRle(labels)}]});
 assert.equal(res.matchingUntrustedPixels+res.disputedUntrustedPixels+res.abstainedPixels,64);
 assert.deepEqual(source.sourceRgba,before);assert.equal(res.paintAuthorized,false);
});
test('Stage93 detects >512 real-grid disagreements without truncating tile totals',async()=>{
 const source=sample(340,340),q=await buildHumanReviewQueue(source);
 const a=new Uint8Array(115600),b=new Uint8Array(115600);
 for(let i=0;i<1024;i++){a[i]=5;b[i]=6;}
 const base={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId:'GC001',dimensions:[340,340],
  sourceRgbaSha256:source.sourceRgbaSha256,sourcePngSha256:source.sourcePngSha256,
  sourceEligibilitySha256:q.eligibilitySha256,status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',
  approved:false,paintAuthorized:false,reviewerAuthenticated:false,roles};
 const result=await buildHumanReviewDisputeMap({source,drafts:[{...base,rle:encodeFullFrameDraftRle(a)},{...base,rle:encodeFullFrameDraftRle(b)}]});
 assert.equal(result.disputedUntrustedPixels,1024);assert.equal(result.originalTiles,121);
 assert.equal(result.prioritizedUntrustedTiles.reduce((sum,t)=>sum+t.disputedUntrustedPixels,0),1024);
 assert.equal(result.humanGoldenApproved,false);
});
test('Stage92 tampering a cryptographic signed receipt payload cannot create authority',async()=>{
 const {source,packet,draft}=await prepared();
 const k=await crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},true,['sign','verify']);
 const keyBytes=new Uint8Array(await crypto.subtle.exportKey('spki',k.publicKey));
 const fake={receipt:{payload:'not-an-original-payload',signature:new Uint8Array(64)},
  externalTrust:{publicKeySpki:keyBytes,pinnedPublicKeySha256:sha(keyBytes)}};
 await assert.rejects(()=>inspectExternallyPinnedFullFrameReceipt({source,packet,draft,...fake}),/FULLFRAME_RECEIPT_SOURCE_OR_DRAFT_SWAPPED/);
});
test('Stage93 changed source original hashes cannot pass an old manual draft',async()=>{
 const {source,draft,labels}=await prepared();source.sourceRgba[0]^=1;labels[1]=6;
 await assert.rejects(()=>buildHumanReviewDisputeMap({source,drafts:[draft,{...draft,rle:encodeFullFrameDraftRle(labels)}]}),/SOURCE_PIN_MISMATCH/);
});
