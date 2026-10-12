/** Stages106–110: source-bound fullframe annotation readiness.
 * Label proposals and key possession NEVER imply independent human identity.
 * No signature, JSON, synthetic annotation or pixel count can authorize paint.
 */
import {validateUntrustedFullFrameDraft,buildFullFrameReviewWorklist} from './public-fullframe-review-p0.mjs';
import {buildHumanReviewDisputeMap} from './public-human-review-dispute-map-p0.mjs';
import {verifyHumanReviewQueue} from './public-human-review-queue-p0.mjs';
export const VERSION='p0-stage106-110-private-review-readiness-v1';
const fail=s=>{throw new TypeError(s)};
const TASKS=Object.freeze(['source_background_subject','whole_subject_silhouette','head_face_blank',
 'left_and_right_hand_arm','sleeve_skin_boundary','hair_loose_strands',
 'collar_necktie','garment_internal_colors','small_source_features']);
export async function auditSingleFullFrameProposal({source,packet,draft}){
 const pinned=await verifyHumanReviewQueue(source,packet);
 const v=await validateUntrustedFullFrameDraft({...source,draft});
 const counts=v.counts;
 const total=source.width*source.height;
 let opaque=0;
 for(let i=3;i<source.sourceRgba.length;i+=4)if(source.sourceRgba[i]===255)opaque++;
 const opacityExclusion=total-opaque;
 const q=await buildFullFrameReviewWorklist({...source,tileSize:32});
 let tilesWithNoProposals=0;
 for(const t of q.tiles){
  let proposed=0;
  for(let y=t.bbox[1];y<t.bbox[3];y++)for(let x=t.bbox[0];x<t.bbox[2];x++)
   if(v.labels[y*source.width+x])proposed++;
  if(!proposed)tilesWithNoProposals++;
 }
 if(v.proposedPixels+v.opaqueUnreviewedPixels!==opaque)fail('SOURCE_OPAQUE_PROPOSAL_ACCOUNTING');
 return {version:VERSION,caseId:pinned.caseId,originalRgbaSha256:source.sourceRgbaSha256,
  originalSourcePixels:total,originalOpaquePixels:opaque,originalNonOpaquePixels:opacityExclusion,
  proposedPixels:v.proposedPixels,unreviewedOpaquePixels:v.opaqueUnreviewedPixels,
  backgroundProposalPixels:counts[1],faceProposalPixels:counts[3],uncertainSubjectPixels:counts[9],
  tiles:q.tiles.length,tilesWithNoProposals,sourceColorInference:false,
  reviewerPersonallyAuthenticated:false,reviewerKeyRegisteredByTrustedOperator:false,
  semanticLabelsCertified:0,wholeCharacterGolden:false,productionPaintAuthorized:false,
  status:'UNTRUSTED_PROPOSAL_FULLFRAME_AUDIT'};
}
export function prepareIndependentReviewerSlots({caseIds=['GC001','Raden']}={}){
 if(!Array.isArray(caseIds)||caseIds.length!==2||caseIds[0]!=='GC001'||caseIds[1]!=='Raden')
  fail('BOTH_PINNED_CASES_REQUIRED');
 return {version:VERSION,caseIds,requiredTasks:TASKS,
  reviewerA:{externallyEnrolled:false,verifiedPerson:false,signerKeyProvisioned:false},
  reviewerB:{externallyEnrolled:false,verifiedPerson:false,signerKeyProvisioned:false},
  independentPersonsCertified:0,sourceSemanticPixelsCertified:0,
  draftsAreHumanReviewed:false,approved:false,status:'REVIEWER_ENROLLMENT_NOT_YET_PERFORMED'};
}
export async function auditTwoDraftHumanHandoff({source,packet,drafts}){
 await verifyHumanReviewQueue(source,packet);
 const d=await buildHumanReviewDisputeMap({source,drafts});
 const grid=d.prioritizedUntrustedTiles.map(t=>({
  tileId:t.tileId,bbox:t.bbox,sourceEdges:t.sourceHighContrastEdges,
  bothLabelAgree:t.matchingUntrustedPixels,conflict:t.disputedUntrustedPixels,
  abstained:t.abstainedPixels,independentHumanAdjudicationRequired:true}));
 let disputed=0,abstained=0,matching=0;
 for(const t of grid){disputed+=t.conflict;abstained+=t.abstained;matching+=t.bothLabelAgree;}
 if(disputed+abstained+matching!==d.originalPixels)fail('FULLFRAME_TILE_ACCOUNTING_FAIL');
 return {version:VERSION,caseId:d.caseId,sourceRgbaSha256:d.sourceSha256,
  originalPixels:d.originalPixels,tiles:grid,disputed,abstained,untrustedMatching:matching,
  firstDraftLabelsSha256:d.firstDraftSha256,secondDraftLabelsSha256:d.secondDraftSha256,
  independentlyRegisteredHumanReviewers:0,adjudicatedHumanPixels:0,approvedPixels:0,
  humanGolden:false,productReleaseAuthorized:false,status:'WAIT_FOR_REAL_HUMAN_DUAL_REVIEW'};
}
export function reviewHandoffReleaseGate({cases=[]}={}){
 if(!Array.isArray(cases)||cases.length>2||cases.some(x=>!x||!['GC001','Raden'].includes(x.caseId))||
 new Set(cases.map(x=>x.caseId)).size!==cases.length)fail('INVALID_REVIEW_GATE_CASES');
 const missing=['GC001','Raden'].filter(x=>!cases.some(c=>c.caseId===x));
 return {version:VERSION,missingCases:missing,verifiedIndependentHumans:0,
  authenticallyAnnotatedPixels:0,personBackgroundGolden:false,
  handsAndSleevesGolden:false,necktieHairGolden:false,
  actualWholeCharacterBudgetPassed:false,realIphoneSafariHttpsPassed:false,
  rollbackPass:false,paintAuthorized:false,productReleaseAuthorized:false,
  status:'GOLDEN_HOLD_NO_AUTHENTICATED_REVIEW'};
}
