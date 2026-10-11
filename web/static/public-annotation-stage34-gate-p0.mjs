/** P0 Stage34. A factual checklist only; never upgrades an untrusted review draft. */
export const VERSION='p0-stage34-evidence-and-scope-gate-v1';
const CA=['GC001','Raden'];
export function evaluateTwoCaseOwnerRecovery({cases,fullCharacterGolden=false,realPublicOriginTested=false,iphoneSafariTested=false,vertexBudgetPassed=false,rollbackTested=false}){
 if(!Array.isArray(cases)||cases.length!==2||new Set(cases.map(c=>c.caseId)).size!==2||!CA.every(id=>cases.some(c=>c.caseId===id)))throw Error('REQUIRE_TWO_REAL_CASES');
 const blockers=[];
 for(const id of CA){const x=cases.find(v=>v.caseId===id);
  for(const key of ['eligiblePixels','proposedPixels','independentlyAttestedPixels','unknownPixels','sourceOutsideChangedPixels'])if(!Number.isInteger(x[key])||x[key]<0)throw Error('INVALID_COUNT_'+id+'_'+key);
  if(x.proposedPixels>x.eligiblePixels||x.independentlyAttestedPixels>x.proposedPixels||x.unknownPixels>x.eligiblePixels)throw Error('IMPOSSIBLE_COVERAGE_'+id);
  if(x.sourceOutsideChangedPixels!==0)blockers.push(id+'_SOURCE_OUTSIDE_MUTATION');
  if(x.independentReviewerVerified!==true)blockers.push(id+'_REVIEWER_PROVENANCE_MISSING');
  if(x.independentlyAttestedPixels<x.eligiblePixels)blockers.push(id+'_UNATTESTED_BOUNDARY_PIXELS');
  if(x.unknownPixels>0)blockers.push(id+'_UNKNOWN_SOURCE_PIXELS');
  if(x.visualAnatomyGolden!==true)blockers.push(id+'_ANATOMY_GOLDEN_NOT_SIGNED');
 }
 for(const [v,k] of [[fullCharacterGolden,'FULL_CHARACTER_GOLDEN'],[realPublicOriginTested,'REAL_PUBLIC_ORIGIN'],[iphoneSafariTested,'IPHONE_SAFARI'],[vertexBudgetPassed,'FULL_SVG_VERTEX_BUDGET'],[rollbackTested,'ROLLBACK']])if(v!==true)blockers.push(k+'_UNVERIFIED');
 return {version:VERSION,blockers,blockerCount:blockers.length,status:'DRAFT_HOLD',stage18PaintAllowed:false,
  independentReviewerTrustInfrastructurePresent:false,productionReleaseAuthorized:false,
  productPromotionAuthorized:false,semanticGoldenApproved:false};
}
