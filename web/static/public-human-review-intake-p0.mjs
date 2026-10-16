/** Stages181-185: intake of external human-created, privately stored full-original reviews.
 * This module NEVER provisions people, verifies physical identity, or authorizes release.
 * Its inputs MUST NOT include private source bytes in GitHub, logs or public webpages.
 */
import {validateUntrustedFullFrameDraft,buildFullFrameReviewWorklist} from './public-fullframe-review-p0.mjs';
export const VERSION='p0-stage181-185-private-human-intake-v1';
const fail=s=>{throw new TypeError(s)};
const ROLES=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal',
 'sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
const SLOTS=['A','B'];
function originalOnly(source){
 if(!source||!['GC001','Raden'].includes(source.caseId)||source.width!==340||source.height!==340)
  fail('STAGE181_REQUIRES_340_ORIGINAL_CASE');
}
export function createOperatorReviewChecklist(){
 return {version:VERSION,originalCases:['GC001','Raden'],reviewSlots:[...SLOTS],
  requiredFiles:SLOTS.flatMap(slot=>['GC001','Raden'].map(caseId=>slot+'_'+caseId+'_review.json')),
  externalIdentityValidation:'OUT_OF_BAND_REQUIRED',
  fileSubmissionTrust:'UNTRUSTED_UNTIL_ORIGINAL_SHA_REVALIDATED',
  independentReviewersVerified:0,independentlyReviewedPixels:0,
  goldenApproved:false,productReleaseAuthorized:false,
  status:'REVIEWER_AVAILABILITY_REPORTED_NO_IDENTITY_ATTESTATION_YET'};
}
export async function auditPrivateReviewerSubmission({source,draft,slot}){
 originalOnly(source);
 if(!SLOTS.includes(slot))fail('INVALID_OPERATOR_ASSIGNED_SLOT');
 const q=await buildFullFrameReviewWorklist({...source,tileSize:32});
 const v=await validateUntrustedFullFrameDraft({...source,draft});
 let opaque=0,unknown=0;
 const tileMissing=q.tiles.map(t=>({tileId:t.tileId,bbox:t.bbox,unreviewedOpaque:0,uncertainOpaque:0}));
 for(let i=0;i<v.labels.length;i++){
  if(source.sourceRgba[4*i+3]!==255)continue;
  opaque++;
  const k=v.labels[i],x=i%340,y=Math.floor(i/340);
  const t=tileMissing[Math.floor(y/32)*11+Math.floor(x/32)];
  if(k===0)t.unreviewedOpaque++;
  if(k===9){t.uncertainOpaque++;unknown++;}
 }
 if(opaque!==q.opaquePixels||v.proposedPixels+v.opaqueUnreviewedPixels!==opaque ||
  tileMissing.reduce((n,t)=>n+t.unreviewedOpaque,0)!==v.opaqueUnreviewedPixels ||
  tileMissing.reduce((n,t)=>n+t.uncertainOpaque,0)!==unknown)fail('SUBMISSION_FULL_ORIGINAL_ACCOUNTING_FAIL');
 const outstanding=tileMissing.filter(x=>x.unreviewedOpaque||x.uncertainOpaque)
   .sort((a,b)=>(b.unreviewedOpaque+b.uncertainOpaque)-(a.unreviewedOpaque+a.uncertainOpaque)||a.tileId-b.tileId);
 return {version:VERSION,slot,caseId:q.caseId,sourceRgbaSha256:q.sourceRgbaSha256,
  sourcePngSha256:q.sourcePngSha256,sourceEligibilitySha256:q.sourceEligibilitySha256,
  labelsSha256:v.labelsSha256,originalPixels:q.totalPixels,originalOpaquePixels:opaque,
  originalTransparentOrNonopaquePixels:q.totalPixels-opaque,originalTiles:121,
  untrustedProposedPixels:v.proposedPixels,unreviewedOpaquePixels:v.opaqueUnreviewedPixels,
  uncertainOpaquePixels:unknown,classProposalCounts:Object.fromEntries(ROLES.map((r,i)=>[r,v.counts[i]])),
  outstandingReviewTiles:outstanding,
  reviewCoverageReady:v.opaqueUnreviewedPixels===0&&unknown===0,
  signerIdentityExternallyVerified:false,independentHumanPixelGoldApproved:0,
  paintedOriginalPixels:0,paintAuthorized:false,productReleaseAuthorized:false,
  status:'UNTRUSTED_SUBMISSION_AWAITING_HUMAN_PROVENANCE'};
}
export async function comparePrivateReviewerPair({source,draftA,draftB}){
 originalOnly(source);
 const [a,b]=await Promise.all([
  validateUntrustedFullFrameDraft({...source,draft:draftA}),
  validateUntrustedFullFrameDraft({...source,draft:draftB})
 ]);
 let identical=0,disagree=0,abstain=0,opaque=0,uncertain=0;
 const grid=Array.from({length:121},(_,tileId)=>({tileId,agree:0,disputed:0,abstained:0,uncertain:0}));
 for(let i=0;i<a.labels.length;i++){
  const sourceOpaque=source.sourceRgba[4*i+3]===255;
  if(!sourceOpaque)continue;
  opaque++;
  const x=i%340,y=Math.floor(i/340),t=grid[Math.floor(y/32)*11+Math.floor(x/32)];
  const u=a.labels[i],v=b.labels[i];
  if(u===0||v===0){abstain++;t.abstained++;}
  else if(u===9||v===9){uncertain++;t.uncertain++;}
  else if(u===v){identical++;t.agree++;}
  else{disagree++;t.disputed++;}
 }
 if(identical+disagree+abstain+uncertain!==opaque ||
 grid.reduce((n,t)=>n+t.agree+t.disputed+t.abstained+t.uncertain,0)!==opaque)
 fail('HUMAN_INTAKE_PIXEL_ACCOUNTING_FAIL');
 return {version:VERSION,caseId:source.caseId,sourceRgbaSha256:source.sourceRgbaSha256,
  firstLabelsSha256:a.labelsSha256,secondLabelsSha256:b.labelsSha256,
  identicalContentsWithoutIndependenceProof:a.labelsSha256===b.labelsSha256,
  originalOpaquePixels:opaque,untrustedAgreementPixels:identical,
  untrustedDisputePixels:disagree,unreviewedOpaquePixels:abstain,uncertainOpaquePixels:uncertain,
  allOriginalOpaquePixelsAccounted:true,tiles:grid,
  needsManualAdjudicationPixels:disagree+abstain+uncertain,
  externalIdentityProofRecorded:false,independentPersonsVerified:0,
  humanSemanticPixelsCertified:0,goldenApproved:false,productReleaseAuthorized:false,
  status:'UNTRUSTED_PAIR_REQUIRES_EXTERNAL_IDENTITY_AND_MANUAL_ADJUDICATION'};
}
export async function evaluateTwoCaseManualIntake({cases}){
 if(!cases||Object.keys(cases).sort().join(',')!=='GC001,Raden')fail('TWO_SOURCE_CASES_REQUIRED');
 const out={};
 for(const key of ['GC001','Raden']){
  const o=cases[key];
  if(!o||o.source?.caseId!==key)fail('CROSS_CASE_MANUAL_INTAKE_REJECTED');
  const [a,b,pair]=await Promise.all([
   auditPrivateReviewerSubmission({source:o.source,draft:o.draftA,slot:'A'}),
   auditPrivateReviewerSubmission({source:o.source,draft:o.draftB,slot:'B'}),
   comparePrivateReviewerPair({source:o.source,draftA:o.draftA,draftB:o.draftB})
  ]);
  out[key]={A:a,B:b,pair};
 }
 return {version:VERSION,cases:out,sourceCasesValidated:2,untrustedSubmissionsValidated:4,
  externalHumanIdentitiesVerified:0,independentlyCertifiedPixels:0,
  fullCharacterGoldenPassed:false,fullbodyVertexGatePassed:false,
  physicalIphoneSafariPassed:false,rollbackRehearsed:false,
  releaseAuthorized:false,status:'WAIT_FOR_TRUE_HUMAN_IDENTITY_AND_ADJUDICATED_GOLDEN'};
}
