/** Stage28: compare two *untrusted* independent-looking annotations, never sign either. */
export const VERSION='structural-p0-stage28-blind-annotation-compare-v1';
export function compareReviewDrafts({first,second,eligibilityMask,unknownPolicy='abstain'}){
 if(!first||!second||first.caseId!==second.caseId||first.sourceRgbaSha256!==second.sourceRgbaSha256||first.width!==second.width||first.height!==second.height||
 !(first.labels instanceof Uint8Array)||!(second.labels instanceof Uint8Array)||!(eligibilityMask instanceof Uint8Array)||
 first.labels.length!==second.labels.length||first.labels.length!==eligibilityMask.length||unknownPolicy!=='abstain')throw Error('REVIEW_PAIR_LINEAGE_MISMATCH');
 let eligible=0,bothLabeled=0,agree=0,disagree=0,unreviewed=0;const classes=[0,0,0,0,0],disputes=[];
 for(let i=0;i<first.labels.length;i++){
  if(!eligibilityMask[i])continue;eligible++;
  const a=first.labels[i],b=second.labels[i];if(a>4||b>4)throw Error('INVALID_REVIEW_LABEL');
  if(!a||!b){unreviewed++;continue;}
  bothLabeled++;if(a===b){agree++;classes[a]++;}else{disagree++;if(disputes.length<200)disputes.push(i);}
 }
 return {version:VERSION,caseId:first.caseId,eligiblePixels:eligible,bothLabeledPixels:bothLabeled,
  equalLabeledPixels:agree,disputedPixels:disagree,unreviewedPixels:unreviewed,
  matchedFractionAmongDualLabels:bothLabeled?agree/bothLabeled:0,matchedFractionOfEligible:eligible?agree/eligible:0,
  classAgreement:classes,first200Disagreements:disputes,independentReviewerIdentityVerified:false,
  semanticGoldenApproved:false,sourceOwnerPaintingApproved:false,productPromotionAuthorized:false,
  status:'REQUIRES_TRUSTED_REVIEWER_ID_AND_PIXEL_GOLDEN'};
}
