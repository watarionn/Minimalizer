/** Stage11 hard gates. Neither pixel-MSE nor Chrome screenshot may sign Golden. */
export const VERSION='structural-p0-stage11-release-gate-v1';
const REQUIRE=[
 ['independentSemanticOwners','INDEPENDENT_SOURCE_PART_OWNER_ATTESTATION'],
 ['silhouetteAndArmsApproved','SILHOUETTE_ARMS_AND_COSTUME_GOLDEN'],
 ['faceExternalFeaturesSuppressed','FACE_FEATURES_OUTSIDE_SIGNED_MASK'],
 ['nativeBrowserWebCrypto','REAL_SECURE_ORIGIN_WEBCRYPTO'],
 ['svg340and680ClipParity','GENUINE_SVG_CHROME_340_680_CLIP_PARITY'],
 ['iphoneSafariReviewed','IPHONE_SAFARI_REVIEW'],
 ['humanGoldenApproved','INDEPENDENT_HUMAN_GOLDEN_SIGNOFF'],
 ['licenseAuditApproved','DEPENDENCY_LICENSE_GATE'],
 ['rollbackVerified','ROLLBACK_PROOF']
];
export function evaluateStructuralPromotion(evidence){
 if(!evidence||typeof evidence!=='object'||!Array.isArray(evidence.cases)||evidence.cases.length!==2)throw Error('REQUIRE_TWO_INDEPENDENT_CASES');
 const byName=new Map(evidence.cases.map(x=>[x.case,x]));
 if(byName.size!==2||!byName.has('GC001')||!byName.has('Raden'))throw Error('REQUIRE_GC001_AND_RADEN');
 const blockers=[];
 for(const [key,desc] of REQUIRE)if(evidence[key]!==true)blockers.push(desc);
 for(const [name,c] of byName){
  if(!Number.isInteger(c.originalVertices)||!Number.isInteger(c.allowedVertices)||c.allowedVertices<1)throw Error('INVALID_STAGE8_COUNT');
  if(c.originalVertices>c.allowedVertices)blockers.push(name+'_ORIGINAL_STAGE8_OVER_BUDGET_'+c.originalVertices+'_GT_'+c.allowedVertices);
  if(c.sourcePixelAuthorityPassed!==true)blockers.push(name+'_SOURCE_AUTHORITY_NOT_PASSED');
 }
 return {version:VERSION,blockers,blockerCount:blockers.length,
  productPromotionAuthorized:blockers.length===0,expectedStatus:blockers.length?'DRAFT_HOLD':'RELEASE_ELIGIBLE_AFTER_FINAL_REVIEW',
  mainChanged:false,localWorkerChanged:false};
}
