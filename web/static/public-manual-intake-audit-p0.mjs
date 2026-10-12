/** Stages116–124: independent-human ORIGINAL REVIEW intake preflight.
 * Manual drafts and labels have ZERO authority until independently enrolled
 * people examine source. Untrusted JSON's own attestations are not evidence.
 */
import {buildFullFrameReviewWorklist,validateUntrustedFullFrameDraft} from './public-fullframe-review-p0.mjs';
import {buildHumanReviewDisputeMap} from './public-human-review-dispute-map-p0.mjs';
import {verifyHumanReviewQueue} from './public-human-review-queue-p0.mjs';
export const VERSION='p0-stage116-124-human-intake-preflight-no-human-claims-v1';
const fail=s=>{throw new TypeError(s)};
const ROLES=['unreviewed','background_proposal','hair_proposal','face_proposal',
 'skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal',
 'accessory_proposal','uncertain_subject'];
const REVIEW_TOPICS=['person_background_boundary','both_arm_silhouettes','hands_and_fingers',
 'skin_and_sleeve_boundary','hair_loose_strands','neckwear_collar','garment_internal_regions','face_feature_omission'];
const FORBIDDEN=/^(?:humanGolden|independentlyVerifiedHuman|humanApproved|certifiedSemanticPixels|productReleaseAuthorized|verifiedReviewerIdentity|reviewerIsHuman|trustedPerson|paintingAllowed)$/;
function restrictClaims(d){
 if(!d||typeof d!=='object'||Array.isArray(d))fail('REVIEW_DRAFT_OBJECT_REQUIRED');
 for(const key of Object.keys(d))if(FORBIDDEN.test(key)&&d[key]!==false&&d[key]!==0&&d[key]!==null)
  fail('SELF_DECLARED_HUMAN_AUTHORITY_NOT_ALLOWED');
}
function tileAnalysis(q,labels,rgba){
 const cols=Math.ceil(q.width/32),out=q.tiles.map(t=>({...t,
  opaqueSourcePixels:0,nonOpaqueSourcePixels:0,
  proposedPixels:0,unreviewedOpaquePixels:0,uncertainPixels:0,
  roleCounts:new Array(ROLES.length).fill(0),independentlyHumanReviewed:false}));
 for(let i=0;i<labels.length;i++){
  const t=out[Math.floor(i/q.width/32)*cols+Math.floor((i%q.width)/32)];
  const opaque=rgba[4*i+3]===255;
  if(opaque)t.opaqueSourcePixels++;else t.nonOpaqueSourcePixels++;
  if(labels[i])t.proposedPixels++;else if(opaque)t.unreviewedOpaquePixels++;
  if(labels[i]===9)t.uncertainPixels++;
  t.roleCounts[labels[i]]++;
 }
 return out;
}
export async function auditManualSourceDraft({source,packet,draft}){
 restrictClaims(draft);
 await verifyHumanReviewQueue(source,packet);
 const w=await buildFullFrameReviewWorklist({...source,tileSize:32});
 const r=await validateUntrustedFullFrameDraft({...source,draft});
 const grid=tileAnalysis(w,r.labels,source.sourceRgba);
 const coverage=grid.reduce((a,t)=>{
  a.opaque+=t.opaqueSourcePixels;a.nonOpaque+=t.nonOpaqueSourcePixels;
  a.proposed+=t.proposedPixels;a.unreviewed+=t.unreviewedOpaquePixels;
  a.uncertain+=t.uncertainPixels;return a;
 },{opaque:0,nonOpaque:0,proposed:0,unreviewed:0,uncertain:0});
 if(coverage.proposed!==r.proposedPixels||coverage.opaque!==r.proposedPixels+r.opaqueUnreviewedPixels||
 coverage.opaque+coverage.nonOpaque!==source.width*source.height)fail('REVIEW_ALL_TILES_ACCOUNTING_ERROR');
 return {version:VERSION,caseId:source.caseId,originalRgbaSha256:source.sourceRgbaSha256,
  originalPngSha256:source.sourcePngSha256,untrustedLabelsSha256:r.labelsSha256,
  width:source.width,height:source.height,allOriginalPixels:w.totalPixels,
  totalSourceTiles:grid.length,coverage,requiredReviewTopics:REVIEW_TOPICS,
  tiles:grid,requiredIndependentPeople:2,independentlyEnrolledPeople:0,
  actuallyAuthenticatedHumanSemanticPixels:0,
  claimsHumanIdentityEstablished:false,semanticsApproved:false,
  faceSuppressionCertified:false,releaseAuthorized:false,
  status:'ORIGINAL_DRAFT_INTAKE_AUDIT_NEEDS_REAL_HUMANS'};
}
export async function buildFullImageConflictIntake({source,packet,drafts}){
 if(!Array.isArray(drafts)||drafts.length!==2)fail('TWO_ACTUAL_DRAFT_FILES_REQUIRED');
 for(const d of drafts)restrictClaims(d);
 const [a,b,conflicts]=await Promise.all([
  auditManualSourceDraft({source,packet,draft:drafts[0]}),
  auditManualSourceDraft({source,packet,draft:drafts[1]}),
  buildHumanReviewDisputeMap({source,drafts})]);
 const rows=conflicts.prioritizedUntrustedTiles.map(t=>({
  tileId:t.tileId,sourceBounds:t.bbox,
  untrustedMatching:t.matchingUntrustedPixels,
  untrustedConflicts:t.disputedUntrustedPixels,
  stillUnclassified:t.abstainedPixels,
  sourceRgbBoundaryPriority:t.sourceHighContrastEdges,
  allTasks:REVIEW_TOPICS,verifiedHumanConsensusPixels:0,
  mustBeIndependentlyAdjudicated:true
 }));
 const count=rows.reduce((a,t)=>a+t.untrustedMatching+t.untrustedConflicts+t.stillUnclassified,0);
 if(count!==source.width*source.height)fail('DUAL_REVIEW_SUM_NOT_WHOLE_ORIGINAL');
 return {version:VERSION,caseId:source.caseId,
  originalRgbaSha256:source.sourceRgbaSha256,firstDraftSha256:a.untrustedLabelsSha256,
  secondDraftSha256:b.untrustedLabelsSha256,totalPixels:count,
  proposedPixelsA:a.coverage.proposed,proposedPixelsB:b.coverage.proposed,
  differingPixels:conflicts.disputedUntrustedPixels,
  abstainedPixels:conflicts.abstainedPixels,
  matchingUntrustedPixels:conflicts.matchingUntrustedPixels,
  tileReviews:rows,actualIndependentHumans:0,
  adjudicatedSemanticPixels:0,faceSuppressionGolden:false,
  subjectBackgroundGolden:false,releaseAuthorized:false,
  status:'DUAL_UNTRUSTED_FILES_AWAIT_INDEPENDENT_HUMAN_ADJUDICATION'};
}
export function assessIntakeGate({cases=[]}={}){
 if(!Array.isArray(cases)||cases.length>2||cases.some(c=>!c||!['GC001','Raden'].includes(c.caseId))||
 new Set(cases.map(c=>c.caseId)).size!==cases.length)fail('INVALID_INTAKE_CASES');
 return {version:VERSION,
  missingOriginalCases:['GC001','Raden'].filter(c=>!cases.some(x=>x.caseId===c)),
  independentlyVerifiedReviewers:0,independentlyApprovedSourcePixels:0,
  sourceHumanLabelsGolden:false,wholeCharacterColorGolden:false,
  historicalStage8VertexBudgetResolved:false,
  physicalIphoneSafariVerified:false,rollbackVerified:false,
  productReleaseAuthorized:false,status:'ORIGINAL_REVIEW_GOLDEN_HOLD'};
}
