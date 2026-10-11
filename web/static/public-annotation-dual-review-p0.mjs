/** P0 Stage33. Compare individually SHA-verified drafts; agreement is NOT reviewer identity. */
import {validateManualReviewDraft} from './public-annotation-ingest-p0.mjs';
import {deriveSourceAnnotationAuthority} from './public-annotation-authority-p0.mjs';
export const VERSION='p0-stage33-two-draft-cross-check-v1';
const err=s=>{throw new TypeError(s);};
const sha=async bytes=>[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
export async function compareSourceReviewDraftPair({caseId,width,height,sourceRgba,sourceRgbaSha256,sourcePngSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,owners,drafts}){
 if(!Array.isArray(drafts)||drafts.length!==2||!drafts[0]||!drafts[1])err('REQUIRE_TWO_DRAFTS');
 if(!globalThis.crypto?.subtle)err('WEBCRYPTO_REQUIRED');
 const common={caseId,width,height,sourceRgba,sourceRgbaSha256,sourcePngSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,owners};
 const authority=await deriveSourceAnnotationAuthority({width,height,originalRgba:sourceRgba,originalSha256:sourceRgbaSha256,
 faceMask,faceSha256,backgroundMask,backgroundSha256,arms:owners});
 const [a,b]=await Promise.all(drafts.map(draft=>validateManualReviewDraft({...common,draft})));
 if(a.labelsSha256===b.labelsSha256)err('DUPLICATE_REVIEW_DATA_NOT_INDEPENDENT');
 const consensus=new Uint8Array(width*height);let agreements=0,disagreements=0,abstentions=0,dual=0;
 const counters={sleeve_observation:0,skin_forearm_observation:0,hair_observation:0,other_clothes_observation:0};
 const disputedIndices=[];
 for(let i=0;i<consensus.length;i++){
  const va=a.labels[i],vb=b.labels[i];
  if(!authority.eligible[i]){if(va||vb)err('EXCLUDED_PIXEL_REVIEWED');continue;}
  if(!va||!vb){abstentions++;continue;}
  dual++;
  if(va===vb){consensus[i]=va;agreements++;counters[['','sleeve_observation','skin_forearm_observation','hair_observation','other_clothes_observation'][va]]++;}
  else{disagreements++;if(disputedIndices.length<256)disputedIndices.push(i);}
 }
 return {version:VERSION,caseId,sourceRgbaSha256,eligibilitySha256:authority.sourceEligibilitySha256,
  draftHashes:[a.labelsSha256,b.labelsSha256],eligiblePixels:authority.eligiblePixels,duallyLabeledPixels:dual,
  unverifiedMatchingPixels:agreements,disagreedPixels:disagreements,abstainedPixels:abstentions,
  coverageFraction:authority.eligiblePixels?agreements/authority.eligiblePixels:0,consensusByClass:counters,
  consensusLabelsSha256:await sha(consensus),first256Disagreements:disputedIndices,
  independentReviewersVerified:false,reviewerReceiptTrusted:false,semanticTruthApproved:false,
  paintAuthorized:false,productPromotionAuthorized:false,status:'REVIEWER_PROVENANCE_AND_GOLDEN_HOLD'};
}
