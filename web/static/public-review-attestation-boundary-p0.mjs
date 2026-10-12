/** Stage72: cryptographic review receipt transport, not anatomical endorsement.
 * A verified key signature only proves possession of its private key. The trust
 * anchor MUST arrive independently; this module never registers reviewers.
 * All research outputs remain DRAFT/HOLD and cannot authorize paint.
 */
import {validateManualReviewDraft} from './public-annotation-ingest-p0.mjs';
import {deriveSourceAnnotationAuthority} from './public-annotation-authority-p0.mjs';
export const VERSION='p0-stage72-cryptographic-review-transport-hold-v1';
const SHA=/^[a-f0-9]{64}$/;
const bytes=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const fail=x=>{throw new TypeError(x)};
const digest=async a=>[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');
export function reviewReceiptPayload({caseId,sourceRgbaSha256,sourcePngSha256,labelsSha256,sourceEligibilitySha256,reviewerKeySha256}){
 if(!['GC001','Raden'].includes(caseId)||[sourceRgbaSha256,sourcePngSha256,labelsSha256,sourceEligibilitySha256,reviewerKeySha256].some(x=>!SHA.test(x||'')))fail('INVALID_REVIEW_RECEIPT_PAYLOAD');
 return JSON.stringify({format:'MinimalizerPublic-P0-review-receipt-v1',caseId,sourceRgbaSha256,sourcePngSha256,labelsSha256,sourceEligibilitySha256,reviewerKeySha256});
}
export async function auditExternallySignedReview({sourceValidation,sourceEligibilitySha256,receipt,externalTrust}){
 if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');
 if(!sourceValidation||!SHA.test(sourceEligibilitySha256||'')||!receipt||!externalTrust||
 !bytes(externalTrust.publicKeySpki)||externalTrust.publicKeySpki.length<40||
 !SHA.test(externalTrust.pinnedPublicKeySha256||'')||!bytes(receipt.signature)||receipt.signature.length!==64)fail('EXTERNAL_REVIEW_ANCHOR_REQUIRED');
 const keySha=await digest(externalTrust.publicKeySpki);
 if(keySha!==externalTrust.pinnedPublicKeySha256)fail('EXTERNAL_REVIEW_KEY_PIN_MISMATCH');
 const validated=await validateManualReviewDraft(sourceValidation);
 const authority=await deriveSourceAnnotationAuthority({width:sourceValidation.width,height:sourceValidation.height,
  originalRgba:sourceValidation.sourceRgba,originalSha256:sourceValidation.sourceRgbaSha256,
  faceMask:sourceValidation.faceMask,faceSha256:sourceValidation.faceSha256,
  backgroundMask:sourceValidation.backgroundMask,backgroundSha256:sourceValidation.backgroundSha256,
  arms:sourceValidation.owners});
 if(authority.sourceEligibilitySha256!==sourceEligibilitySha256)fail('REVIEW_ELIGIBILITY_PIN_MISMATCH');
 if(validated.sourceRgbaSha256!==sourceValidation.sourceRgbaSha256||
 validated.sourcePngSha256!==sourceValidation.sourcePngSha256)fail('REVIEW_SOURCE_VALIDATION_CHANGED');
 const payload=reviewReceiptPayload({caseId:validated.caseId,sourceRgbaSha256:validated.sourceRgbaSha256,
  sourcePngSha256:validated.sourcePngSha256,labelsSha256:validated.labelsSha256,
  sourceEligibilitySha256,reviewerKeySha256:keySha});
 if(receipt.payload!==payload)fail('REVIEW_RECEIPT_DATA_CONFLICT');
 let verified=false;
 try {
  const key=await globalThis.crypto.subtle.importKey('spki',externalTrust.publicKeySpki,{name:'ECDSA',namedCurve:'P-256'},false,['verify']);
  verified=await globalThis.crypto.subtle.verify({name:'ECDSA',hash:'SHA-256'},key,receipt.signature,new TextEncoder().encode(payload));
 } catch { fail('INVALID_EXTERNAL_REVIEW_SIGNATURE'); }
 if(!verified)fail('INVALID_EXTERNAL_REVIEW_SIGNATURE');
 const labeled=validated.eligiblePixels-validated.unclassifiedEligiblePixels;
 return {version:VERSION,caseId:validated.caseId,sourceRgbaSha256:validated.sourceRgbaSha256,
  reviewedHistoricalOwnerCandidatePixels:labeled,eligibleHistoricalOwnerCandidatePixels:validated.eligiblePixels,
  cryptographicSignatureValid:true,publicKeyPinnedByCaller:true,
  externalReviewerIdentityIndependentlyEstablished:false,semanticLabelAccuracyEstablished:false,
  fullCharacterSegmentationEstablished:false,fullCharacterGolden:false,
  productPromotionAuthorized:false,paintAuthorized:false,status:'DRAFT_HOLD_NEEDS_INDEPENDENT_REVIEW_AUTHORITY'};
}
export function assessTwoCaseHumanReviewReadiness(records=[]){
 if(!Array.isArray(records)||records.length>2||new Set(records.map(x=>x?.caseId)).size!==records.length||
 records.some(x=>!['GC001','Raden'].includes(x.caseId)))fail('INVALID_HUMAN_REVIEW_RECORDS');
 const missing=['GC001','Raden'].filter(c=>!records.some(x=>x.caseId===c));
 return {version:VERSION,caseIdsPresent:records.map(x=>x.caseId),missingCases:missing,
  sourceOwnerSemanticPixelsTrusted:0,fullBodySilhouetteReviewed:false,neckwearReviewed:false,
  hairAndSleeveBoundaryReviewed:false,independentlyAuthenticatedReviewerCount:0,
  status:'DRAFT_HOLD_HUMAN_REVIEW_REQUIRED',paintAuthorized:false,productionReleaseAuthorized:false};
}
