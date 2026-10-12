/** Stage96–99: original-image human review packet audit and full-scene gate.
 * This is a paper trail, not a human. Never accept session flags as evidence
 * of verified human identity or anatomical ground truth.
 */
import {buildHumanReviewQueue,verifyHumanReviewQueue} from './public-human-review-queue-p0.mjs';
import {validateUntrustedFullFrameDraft} from './public-fullframe-review-p0.mjs';
import {buildHumanReviewDisputeMap} from './public-human-review-dispute-map-p0.mjs';
export const VERSION='p0-stage96-99-fullscene-review-preflight-v1';
const fail=s=>{throw new TypeError(s)};
const TOPICS=Object.freeze(['person_background_silhouette','arm_and_hands','skin_and_sleeve',
 'hair_and_fine_strands','collar_and_neckwear','garment_and_tiny_features','face_suppression']);
export async function buildTwoCasePrivateReviewManifest(cases){
 if(!Array.isArray(cases)||cases.length!==2||cases[0]?.caseId!=='GC001'||cases[1]?.caseId!=='Raden')
  fail('TWO_ORDERED_ORIGINAL_CASES_REQUIRED');
 const rows=[];
 for(const source of cases){
  const q=await buildHumanReviewQueue(source);
  const v=await verifyHumanReviewQueue(source,q);
  if(v.originalPixelsQueued!==source.width*source.height)fail('ORIGINAL_FRAME_COVERAGE_MISMATCH');
  rows.push({caseId:source.caseId,sourceRgbaSha256:q.rgbaSha256,sourcePngSha256:q.pngSha256,
   packetSha256:q.packetSha256,sourceEligibilitySha256:q.eligibilitySha256,
   originalPixels:q.totalOriginalPixels,reviewTiles:q.tiles.length,topics:TOPICS,
   blankHumanSemantics:true,proposedHumanPixels:0,verifiedHumanPixels:0,
   realHumanReviewerEnrolled:false,status:'AWAITING_OFFLINE_HUMAN_REVIEW'});
 }
 return {version:VERSION,cases:rows,mandatoryTopics:TOPICS,reviewersExternallyAuthenticated:0,
  humanGoldenApproved:false,paintAuthorized:false,productionReleaseAuthorized:false,
  status:'REVIEW_WORKSPACE_READY_NO_HUMAN_EVIDENCE'};
}
/** Untrusted draft may be syntactically complete; content alone NEVER proves human review. */
export async function summarizeReviewProgress({source,packet,draft}){
 await verifyHumanReviewQueue(source,packet);
 const v=await validateUntrustedFullFrameDraft({...source,draft});
 const opaque=source.sourceRgba.reduce((n,a,i)=>n+(i%4===3&&a===255?1:0),0);
 const proposed=v.proposedPixels;
 if(proposed>opaque)fail('LABEL_PIXELS_EXCEED_SOURCE');
 return {version:VERSION,caseId:source.caseId,sourceSha256:source.sourceRgbaSha256,
  originalPixels:source.width*source.height,opaqueSourcePixels:opaque,
  proposedSourcePixels:proposed,opaqueSourcePixelsWithoutProposals:opaque-proposed,
  nonopaquePixels:source.width*source.height-opaque,
  syntacticProposalFraction:opaque?proposed/opaque:0,
  actualIndependentHumanPixelsVerified:0,proposalIsHumanGolden:false,
  humanIdentityVerified:false,paintAuthorized:false,status:'UNTRUSTED_MANUAL_DRAFT_STATISTICS'};
}
/** Every original source tile, not merely two historical owner masks. */
export async function createHumanAdjudicationAgenda({source,drafts}){
 const disputes=await buildHumanReviewDisputeMap({source,drafts});
 const todo=disputes.prioritizedUntrustedTiles.map(t=>({
  tileId:t.tileId,bbox:t.bbox,untrustedDisputes:t.disputedUntrustedPixels,
  untrustedAbstentions:t.abstainedPixels,sourceHighContrastEdges:t.sourceHighContrastEdges,
  reviewTasks:TOPICS,requiresActualHumanJudgment:true,authenticated:false
 }));
 return {version:VERSION,caseId:source.caseId,sourceSha256:source.sourceRgbaSha256,
  allOriginalTilesQueued:todo.length,untrustedAgreements:disputes.matchingUntrustedPixels,
  untrustedDisagreements:disputes.disputedUntrustedPixels,
  untrustedAbstentions:disputes.abstainedPixels,agenda:todo,
  actualHumanAdjudications:0,paintAuthorized:false,releaseAuthorized:false,
  status:'INDEPENDENT_HUMAN_REVIEW_AND_ADJUDICATION_NOT_STARTED'};
}
export function assessSourceOnlyReleaseEvidence(records=[]){
 if(!Array.isArray(records)||records.length>2||records.some(x=>!x||!['GC001','Raden'].includes(x.caseId))||
 new Set(records.map(x=>x.caseId)).size!==records.length)fail('INVALID_RELEASE_RECORDS');
 return {version:VERSION,missingCases:['GC001','Raden'].filter(c=>!records.some(x=>x.caseId===c)),
  independentlyVerifiedHumanSemanticPixels:0,faceSuppressionApproved:false,
  wholeSceneSvgVertexBudgetMet:false,fullBodyGoldenApproved:false,
  physicalIphoneSafariHttpsVerified:false,rollbackVerified:false,
  productPaintAuthorized:false,releaseAuthorized:false,status:'FAIL_CLOSED_GOLDEN_HOLD'};
}
