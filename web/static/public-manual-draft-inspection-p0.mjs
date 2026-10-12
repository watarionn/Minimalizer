/** Stage83: manual whole-frame annotation remains an untrusted source-bound draft. */
import {validateUntrustedFullFrameDraft} from './public-fullframe-review-p0.mjs';
import {verifyHumanReviewQueue} from './public-human-review-queue-p0.mjs';
export async function inspectManualDraft({source,packet,draft}){
 await verifyHumanReviewQueue(source,packet);
 const v=await validateUntrustedFullFrameDraft({...source,draft});
 return {caseId:v.caseId,labelsSha256:v.labelsSha256,proposedPixels:v.proposedPixels,
  independentlyReviewedPixels:0,productPaintAuthorized:false,status:'UNTRUSTED_DRAFT_HOLD'};
}
