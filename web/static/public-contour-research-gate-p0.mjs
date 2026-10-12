/** Stage15: explicit source-vector research decision. Full character remains HOLD.
 * Do not silently replace Stage8 ring budget with a feature-only budget.
 */
export const VERSION='structural-p0-stage15-contour-release-decision-v1';
export function evaluateContourResearchGate({cases,visualGoldenApproved=false,
 secureOriginNativeWebCrypto=false,fullCharacterSvgChromeParity=false,
 independentSemanticOwners=false,iphoneSafariVerified=false,rollbackVerified=false}){
 if(!Array.isArray(cases)||cases.length!==2||new Set(cases.map(x=>x.case)).size!==2||
 !cases.some(x=>x.case==='GC001')||!cases.some(x=>x.case==='Raden'))throw Error('REQUIRE_TWO_DISTINCT_SIGNED_CASES');
 const blockers=[],reports=[];
 for(const c of cases){
  if(!Number.isInteger(c.originalStage8Vertices)||!Number.isInteger(c.maxStage8Vertices)||
  !Number.isInteger(c.exactFeatureVertices)||c.exactFeatureVertices<1||c.maxStage8Vertices<1)throw Error('INVALID_RING_BUDGET');
  if(c.exactDprMaskParity!==true||c.sourceMaskProof!==true||c.sourceColorProvenance!==true)blockers.push(c.case+'_SOURCE_VECTOR_PARITY_NOT_PASS');
  if(c.originalStage8Vertices>c.maxStage8Vertices)blockers.push(c.case+'_ORIGINAL_STAGE8_OVER_BUDGET');
  const combined=c.originalStage8Vertices+c.exactFeatureVertices;
  if(combined>c.maxStage8Vertices)blockers.push(c.case+'_STAGE8_PLUS_ADDITIONAL_CONTOURS_OVER_BUDGET');
  if(c.simplifiedDprMaskParity!==true)blockers.push(c.case+'_SIMPLIFIED_DPR2_BLEED');
  reports.push({case:c.case,existingVertices:c.originalStage8Vertices,
   additionalSourceContourVertices:c.exactFeatureVertices,conservativeTotal:combined,
   productionVertexCap:c.maxStage8Vertices,passesProductionVertexCap:combined<=c.maxStage8Vertices});
 }
 const remaining={visualGoldenApproved,secureOriginNativeWebCrypto,fullCharacterSvgChromeParity,
 independentSemanticOwners,iphoneSafariVerified,rollbackVerified};
 for(const [key,done] of Object.entries(remaining))if(done!==true)blockers.push('NOT_VERIFIED_'+key);
 return {version:VERSION,cases:reports,blockers,blockerCount:blockers.length,
 releaseEligible: false,productPromotionAuthorized:false,
 expectedStatus:'DRAFT_HOLD',mainChanged:false,localWorkerChanged:false,
 next:'Improve independent owner semantics and full-character budget without creating source-absent content'};
}
