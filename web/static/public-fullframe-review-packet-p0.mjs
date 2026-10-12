/** Stage82–84 isolated full-original-frame review packaging.
 * No identity provider here. Human-supplied brush labels are never semantic truth.
 * Reviewer flags, duplicate submissions, opaque background, original mask names
 * and digest strings MUST NOT auto-authorize paint or a release.
 */
import {buildFullFrameReviewWorklist,validateUntrustedFullFrameDraft,
 compareUntrustedFullFrameDrafts} from './public-fullframe-review-p0.mjs';
export const VERSION='p0-stage82-fullframe-offline-packet-hold-v1';
const fail=x=>{throw new TypeError(x)};
const PIN=/^[a-f0-9]{64}$/;
const sha=async s=>{
 if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');
 return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)))].map(x=>x.toString(16).padStart(2,'0')).join('');
};
const TASKS=['whole_character_silhouette','background_vs_subject','head_face_suppression',
 'arms_and_hands','sleeves_and_skin','hair_and_fine_strands','neckwear_and_collar',
 'garments_and_folds','small_source_features','golden_review'];
const core=p=>({version:p.version,caseId:p.caseId,sourceIdentity:p.sourceIdentity,tiles:p.tiles,
 topics:p.topics,totals:p.totals});
export async function buildPrivateFullFrameReviewPacket(source){
 const q=await buildFullFrameReviewWorklist({...source,tileSize:32});
 const sourceIdentity={caseId:q.caseId,width:q.width,height:q.height,
  originalRgbaSha256:q.sourceRgbaSha256,originalPngSha256:q.sourcePngSha256,
  eligibilitySha256:q.sourceEligibilitySha256};
 const tiles=q.tiles.map(t=>({id:t.tileId,bbox:t.bbox,pixels:t.pixels,
  sourceHighContrastEdges:t.sourceHighContrastEdges,reviewPriority:t.reviewPriority}));
 const packet={version:VERSION,caseId:q.caseId,sourceIdentity,tiles,topics:TASKS,
  totals:{tiles:tiles.length,allOriginalPixels:q.totalPixels,opaquePixels:q.opaquePixels,
   nonOpaquePixels:q.nonOpaquePixels,sourceEdges:q.sourceHighContrastEdges,
   historicCandidatePixels:q.historicalOwnerCandidatePixels}};
 const packetSha256=await sha(JSON.stringify(core(packet)));
 return {...packet,packetSha256,wholeFrameHumanReviewed:false,authenticatedReviewers:0,
  sourceSemanticVerifiedPixels:0,backgroundConfirmed:false,originalPixelPaintAuthorized:false,
  productionReleaseAuthorized:false,status:'PRIVATE_REVIEW_PACKET_UNVERIFIED'};
}
/** Never accept a package claiming identity without independently re-derived bytes. */
export async function validatePrivateReviewPacket({source,packet}){
 if(!packet||!PIN.test(packet.packetSha256||''))fail('INVALID_REVIEW_PACKET');
 const fresh=await buildPrivateFullFrameReviewPacket(source);
 if(packet.packetSha256!==fresh.packetSha256||JSON.stringify(core(packet))!==JSON.stringify(core(fresh))||
 packet.wholeFrameHumanReviewed!==false||packet.authenticatedReviewers!==0||
 packet.sourceSemanticVerifiedPixels!==0||packet.productionReleaseAuthorized!==false)
  fail('REVIEW_PACKET_SOURCE_OR_TRUST_TAMPERED');
 return {version:VERSION,caseId:fresh.caseId,packetSha256:fresh.packetSha256,
  eligibleForPrivateManualReview:true,independentHumanVerificationEstablished:false,
  allOriginalSourcePixelsQueued:true,sourcePaintAuthorized:false};
}
/** A tile mark is a navigation/bookmark hint, NOT evidence that review was done. */
export async function inspectUntrustedFullFrameSubmission({source,packet,submission}){
 const valid=await validatePrivateReviewPacket({source,packet});
 if(!submission||submission.format!=='MinimalizerPublic-P0-fullframe-review-submission-v1'||
 submission.packetSha256!==valid.packetSha256||submission.caseId!==valid.caseId||
 !Array.isArray(submission.tileMarks)||submission.tileMarks.length>packet.tiles.length||
 submission.approved!==false||submission.reviewerAuthenticated!==false||
 submission.paintAuthorized!==false)fail('UNTRUSTED_SUBMISSION_IDENTITY');
 const legal=new Set(packet.tiles.map(x=>x.id)),seen=new Set(),marks={unvisited:0,visited:0,needs_revisit:0};
 for(const m of submission.tileMarks){
  if(!m||!Number.isSafeInteger(m.tileId)||!legal.has(m.tileId)||seen.has(m.tileId)||
  !['visited','unvisited','needs_revisit'].includes(m.navigationState)||
  Object.keys(m).sort().join(',')!=='navigationState,tileId')fail('INVALID_UNTRUSTED_TILE_MARK');
  seen.add(m.tileId);marks[m.navigationState]++;
 }
 marks.unvisited+=packet.tiles.length-seen.size;
 const validated=await validateUntrustedFullFrameDraft({...source,draft:submission.draft});
 return {version:VERSION,caseId:valid.caseId,packetSha256:valid.packetSha256,
  labelsSha256:validated.labelsSha256,proposedSourcePixels:validated.proposedPixels,
  unreviewedOpaqueSourcePixels:validated.opaqueUnreviewedPixels,tileNavigation:marks,
  reviewerIdentityTrusted:false,anatomicalLabelsCertified:0,
  sourceRGBUnmodified:true,paintAuthorized:false,productionReleaseAuthorized:false,
  status:'UNTRUSTED_OFFLINE_SUBMISSION_HOLD'};
}
export async function adjudicationWorklistFromSubmissions({source,packet,submissions}){
 await validatePrivateReviewPacket({source,packet});
 if(!Array.isArray(submissions)||submissions.length!==2)fail('TWO_SUBMISSIONS_REQUIRED');
 const a=await inspectUntrustedFullFrameSubmission({source,packet,submission:submissions[0]});
 const b=await inspectUntrustedFullFrameSubmission({source,packet,submission:submissions[1]});
 const compared=await compareUntrustedFullFrameDrafts({...source,drafts:submissions.map(x=>x.draft)});
 const tiles=[];
 for(const t of packet.tiles){
  let conflicts=0;
  for(const i of compared.first512DisagreementIndices){
   const x=i%source.width,y=Math.floor(i/source.width);
   if(x>=t.bbox[0]&&x<t.bbox[2]&&y>=t.bbox[1]&&y<t.bbox[3])conflicts++;
  }
  tiles.push({tileId:t.id,bbox:t.bbox,sourceEdgeCount:t.sourceHighContrastEdges,
   first512ConflictSamples:conflicts,needsActualHumanAdjudication:conflicts>0,
   approved:false});
 }
 tiles.sort((x,y)=>y.first512ConflictSamples-x.first512ConflictSamples||
 y.sourceEdgeCount-x.sourceEdgeCount||x.tileId-y.tileId);
 return {version:VERSION,caseId:packet.caseId,packetSha256:packet.packetSha256,
  submittedLabelDigests:[a.labelsSha256,b.labelsSha256],
  matchingUntrustedPixels:compared.untrustedMatchingPixels,
  disputedUntrustedPixels:compared.untrustedDisagreedPixels,
  abstainedUntrustedPixels:compared.abstainedPixels,
  tiles,reviewersIndependentlyAuthenticated:0,certifiedSemanticPixels:0,
  actualGoldenHumanApproval:false,paintAuthorized:false,releaseAuthorized:false,
  status:'FULLFRAME_ADJUDICATION_HUMAN_ACTION_REQUIRED'};
}
export function releaseGateAfterPrivateFullFrameReview({cases=[]}={}){
 if(!Array.isArray(cases)||cases.length>2||new Set(cases.map(x=>x?.caseId)).size!==cases.length||
 cases.some(x=>!['GC001','Raden'].includes(x.caseId)))fail('INVALID_RELEASE_GATE_CASES');
 return {version:VERSION,missingOriginals:['GC001','Raden'].filter(c=>!cases.some(x=>x.caseId===c)),
  independentHumanSemanticPixelCount:0,realIphoneSafariVerified:false,
  fullCharacterSvgBudgetPassed:false,wholeCharacterHumanGolden:false,
  rollbackVerified:false,paintAuthorized:false,productionReleaseAuthorized:false,
  status:'DRAFT_HOLD'};
}
