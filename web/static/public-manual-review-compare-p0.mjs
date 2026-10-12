/** Stage84: untrusted dual review disagreement without reviewer identity claims. */
import {inspectManualDraft} from './public-manual-draft-inspection-p0.mjs';
import {compareUntrustedFullFrameDrafts} from './public-fullframe-review-p0.mjs';
export async function compareManualDrafts({source,packet,drafts}){
 if(!Array.isArray(drafts)||drafts.length!==2)throw new TypeError('TWO_DRAFTS_REQUIRED');
 await Promise.all(drafts.map(draft=>inspectManualDraft({source,packet,draft})));
 const r=await compareUntrustedFullFrameDrafts({...source,drafts});
 return {caseId:source.caseId,untrustedMatchingPixels:r.untrustedMatchingPixels,
  disputedPixels:r.untrustedDisagreedPixels,abstainedPixels:r.abstainedPixels,
  first512Disagreements:r.first512DisagreementIndices,authenticatedReviewers:0,
  semanticPixelsApproved:0,paintAuthorized:false,status:'INDEPENDENT_HUMAN_ADJUDICATION_REQUIRED'};
}
