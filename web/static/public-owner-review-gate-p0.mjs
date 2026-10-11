/** P0 Stage19: never equate source RGB gain with anatomical segmentation.
 * Pixels may be source-owned and still belong to hair, backdrop, or skin.
 * Semantic approval requires independent review; measured MSE never grants it.
 */
export const VERSION='structural-p0-stage19-visual-semantic-hold-v1';
const VALID=['GC001','Raden'];
export function evaluateOwnerVisualGate({cases,fullCharacterGolden=false,iphoneSafariPassed=false,realPublicRoutePassed=false,
 independentSemanticReviews=false,fullSvgBudgetPassed=false}){
 if(!Array.isArray(cases)||cases.length!==2||new Set(cases.map(c=>c.case)).size!==2||
   !VALID.every(label=>cases.some(c=>c.case===label)))throw Error('REQUIRE_TWO_DISTINCT_CASES');
 const blockers=[],rows=[];
 for(const label of VALID){
  const c=cases.find(v=>v.case===label);
  for(const key of ['signedOwnerPixels','candidateChangedPixels','backgroundProtectedChangedPixels',
   'faceProtectedChangedPixels','alphaChangedPixels','outsideSignedOwnerPixels','colorErrorGainPercent']){
   if(!Number.isFinite(c[key])||c[key]<0)throw Error(label+'_INVALID_AUDIT_'+key);
  }
  if(c.candidateChangedPixels>c.signedOwnerPixels)blockers.push(label+'_PIXEL_BUDGET_EXCEEDED');
  if(c.backgroundProtectedChangedPixels!==0)blockers.push(label+'_BACKGROUND_MUTATION');
  if(c.faceProtectedChangedPixels!==0)blockers.push(label+'_FACE_MUTATION');
  if(c.alphaChangedPixels!==0)blockers.push(label+'_ALPHA_MUTATION');
  if(c.outsideSignedOwnerPixels!==0)blockers.push(label+'_UNAUTHORIZED_OWNER_PIXEL');
  if(c.backgroundObserverIndependentlySigned!==true)blockers.push(label+'_BACKGROUND_OBSERVER_UNATTESTED');
  if(c.sleeveForearmHairSeparatedAndReviewed!==true)blockers.push(label+'_ARM_SLEEVE_HAIR_SEMANTICS_UNREVIEWED');
  if(c.fullArmSilhouetteRecovered!==true)blockers.push(label+'_ARM_SILHOUETTE_NOT_GOLDEN');
  if(c.visualReviewRejected===true)blockers.push(label+'_VISIBLE_ARTIFACT_REJECTED');
  rows.push({case:label,changed:c.candidateChangedPixels,
   sourceRGBGainPercent:c.colorErrorGainPercent,backgroundChanges:c.backgroundProtectedChangedPixels,
   meaningOfColorGain:'pixel_fitness_only',semanticApproval:false});
 }
 for(const [ok,tag] of [[independentSemanticReviews,'INDEPENDENT_SOURCE_SEMANTIC_SIGNOFF'],
   [fullCharacterGolden,'FULL_CHARACTER_HUMAN_GOLDEN'],[iphoneSafariPassed,'IPHONE_SAFARI'],
   [realPublicRoutePassed,'REAL_PUBLIC_E2E'],[fullSvgBudgetPassed,'FULL_SVG_COMPLEXITY_BUDGET']]){
  if(ok!==true)blockers.push(tag+'_NOT_PASSED');
 }
 return {version:VERSION,realCases:rows,blockerCount:blockers.length,blockers,
  stage17AuthorityOnly:true,stage18SourceColorOnly:true,
  status:'DRAFT_HOLD',researchPreviewAuthorized:false,productPromotionAuthorized:false,
  next:'Obtain independent signed semantic sleeve/skin/hair boundaries and a human Golden without changing source image content'};
}
