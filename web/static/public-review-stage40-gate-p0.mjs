/** Stage40: finite read-only two-case release gate. Never admit untrusted review labels. */
export const VERSION='p0-stage40-source-review-bundle-hold-v1';
export function evaluateSourceReviewBundleGate({cases,fullCharacterGolden=false,iphoneSafariVerified=false,realPublicVerified=false,vertexBudgetPassed=false,rollbackVerified=false}){
 if(!Array.isArray(cases)||cases.length!==2||new Set(cases.map(x=>x.caseId)).size!==2||!['GC001','Raden'].every(k=>cases.some(c=>c.caseId===k)))throw Error('REQUIRE_TWO_CASES');
 const blockers=[],summaries=[];
 for(const name of ['GC001','Raden']){const x=cases.find(c=>c.caseId===name);
   if(!Number.isInteger(x?.eligiblePixels)||x.eligiblePixels<1||!Number.isInteger(x?.queuedPixels)||x.queuedPixels<0||
   !Number.isInteger(x?.verifiedSemanticPixels)||x.verifiedSemanticPixels<0||x.verifiedSemanticPixels>x.eligiblePixels||
   !Number.isInteger(x?.missingTiles)||x.missingTiles<0)throw Error(name+'_INVALID_COUNTS');
   if(x.queuedPixels!==x.eligiblePixels)blockers.push(name+'_QUEUE_INCOMPLETE');
   if(x.missingTiles!==0)blockers.push(name+'_TILES_NOT_COVERED');
   if(x.verifiedSemanticPixels<x.eligiblePixels)blockers.push(name+'_UNSIGNED_SEMANTIC_PIXELS');
   if(x.trustedIndependentReviewer!==true)blockers.push(name+'_INDEPENDENT_REVIEWER_NOT_ATTESTED');
   if(x.anatomyGoldenApproved!==true)blockers.push(name+'_ARM_AND_SLEEVE_GOLDEN_MISSING');
   summaries.push({caseId:name,queuedPixels:x.queuedPixels,sourcePixels:x.eligiblePixels,
     semanticPixelsTrustedByThisModule:0});}
 for(const [flag,name] of [[fullCharacterGolden,'FULL_BODY_GOLDEN'],[iphoneSafariVerified,'IPHONE_SAFARI'],[realPublicVerified,'REAL_PUBLIC'],[vertexBudgetPassed,'FULL_SVG_VERTEX_BUDGET'],[rollbackVerified,'ROLLBACK']])if(flag!==true)blockers.push(name+'_UNVERIFIED');
 return {version:VERSION,cases:summaries,blockers,blockerCount:blockers.length,status:'DRAFT_HOLD',
   reviewerVerifierPresent:false,paintAuthorized:false,productionReleaseAuthorized:false,productPromotionAuthorized:false};
}
