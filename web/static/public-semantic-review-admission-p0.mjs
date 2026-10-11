/** Stage22â23: fail-closed review ledger / Stage18 paint boundary.
 * A user-supplied `approved`, sha or `signed` string cannot upgrade trust.
 * Only separately verified, trusted review infrastructure may issue a promotion token.
 * This research module neither signs nor issues such a token.
 */
export const VERSION='structural-p0-stage22-23-trust-separated-admission-v1';
const ROLES=new Set(['sleeve','forearm_skin','hair','garment','accessory','unknown']);
export function auditProposedSemanticReview({packet,annotations=[]}){
 if(!packet||!['GC001','Raden'].includes(packet.caseId)||!Array.isArray(packet.observations)||!Array.isArray(annotations))throw Error('INVALID_REVIEW_PACKET');
 const entries=new Map(packet.observations.map(x=>[x.id,x]));if(entries.size!==packet.observations.length)throw Error('DUPLICATE_OBSERVATION_IDS');
 const annotated=new Set(),risks=[];
 for(const a of annotations){
  if(!a||!entries.has(a.observationId)||annotated.has(a.observationId)||!ROLES.has(a.proposedClass))throw Error('INVALID_REVIEW_ANNOTATION');
  annotated.add(a.observationId);
  const p=entries.get(a.observationId);
  if(a.observationSha256!==p.sourceObservationSha256)throw Error('REVIEW_SOURCE_SHA_CONFLICT');
  risks.push({observationId:a.observationId,proposedClass:a.proposedClass,
   note:'UNTRUSTED_ANNOTATION_REQUIRES_INDEPENDENT_PIXEL_MASK_REVIEW'});
 }
 const missing=packet.observations.filter(p=>!annotated.has(p.id)).map(p=>p.id);
 return {version:VERSION,caseId:packet.caseId,reviewedCount:annotated.size,pendingCount:missing.length,
  proposedClassCounts:Object.fromEntries([...ROLES].map(role=>[role,risks.filter(x=>x.proposedClass===role).length])),
  pendingObservationIds:missing,unverifiedAnnotations:risks,reviewerIdentityVerified:false,
  originalSourceSemanticBoundaryAttested:false,artifactIdentityVerified:false,
  usableForProduction:false,productPromotionAuthorized:false,
  status:'AWAITING_INDEPENDENT_MASK_AND_REVIEWER_ATTESTATION'};
}
export function gateSourceOwnerPaint({packets,reviewReceipts=[]}){
 if(!Array.isArray(packets)||packets.length!==2||new Set(packets.map(p=>p.caseId)).size!==2||
  !packets.some(p=>p.caseId==='GC001')||!packets.some(p=>p.caseId==='Raden'))throw Error('REQUIRE_TWO_CASES');
 if(!Array.isArray(reviewReceipts))throw Error('INVALID_RECEIPTS');
 const blockers=[];for(const packet of packets){
  if(!Array.isArray(packet.observations)||!Array.isArray(packet.owners)||!packet.sourceOnlyTopologyObservation)throw Error('INVALID_SOURCE_PROVENANCE');
  const receipt=reviewReceipts.find(x=>x.caseId===packet.caseId);
  // Explicitly disregard untrusted user-input review toggles. No trusted verifier in this research module.
  blockers.push(packet.caseId+'_INDEPENDENT_REVIEWER_PROOF_UNAVAILABLE');
  blockers.push(packet.caseId+'_SLEEVE_SKIN_HAIR_SEMANTICS_UNATTESTED');
  if(packet.owners.some(x=>x.unclassifiedPixels>0))blockers.push(packet.caseId+'_UNCLASSIFIED_OWNER_PIXELS');
  if(packet.observations.some(x=>x.componentCount>1))blockers.push(packet.caseId+'_DISCONNECTED_COLOR_REGIONS_NEED_REVIEW');
  if(receipt&&receipt.originalSourceSemanticBoundaryAttested===true)blockers.push(packet.caseId+'_SELF_DECLARED_ATTESTATION_REJECTED');
 }
 blockers.push('HUMAN_GOLDEN_UNVERIFIED','STAGE8_FULL_SVG_BUDGET_UNVERIFIED','REAL_PUBLIC_AND_SAFARI_UNVERIFIED');
 return {version:VERSION,blockers,blockerCount:blockers.length,stage18PaintAllowed:false,
  previewCandidateAdopted:false,productPromotionAuthorized:false,status:'DRAFT_HOLD',
  next:'Independent source-level sleeve/skin/hair annotation and trusted review, then recheck real-case SVG/Golden'};
}
