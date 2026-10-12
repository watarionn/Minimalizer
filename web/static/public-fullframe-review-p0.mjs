/** Stages77–79: full-original-frame review worklist and two untrusted semantic drafts.
 * This intentionally covers ALL original pixels rather than historical arm masks.
 * A source RGB edge, a historical mask, or two matching annotations does NOT
 * imply anatomy, background ownership, human identity, or painting authority.
 */
import {deriveSourceAnnotationAuthority} from './public-annotation-authority-p0.mjs';
export const VERSION='p0-stage77-79-fullframe-human-worklist-hold-v1';
const FAIL=s=>{throw new TypeError(s);};
const isBytes=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const PIN=/^[a-f0-9]{64}$/;
const ROLES=Object.freeze(['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject']);
const sha=async x=>{if(!globalThis.crypto?.subtle)FAIL('WEBCRYPTO_REQUIRED');return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',x))].map(x=>x.toString(16).padStart(2,'0')).join('');};
const sourceCheck=async o=>{
 if(!o||!['GC001','Raden'].includes(o.caseId)||!Number.isInteger(o.width)||!Number.isInteger(o.height)||o.width<1||o.height<1||o.width*o.height>160000||
 !isBytes(o.sourceRgba)||o.sourceRgba.length!==4*o.width*o.height||!PIN.test(o.sourceRgbaSha256||'')||!PIN.test(o.sourcePngSha256||''))FAIL('FULLFRAME_SOURCE_REQUIRED');
 const authority=await deriveSourceAnnotationAuthority({width:o.width,height:o.height,originalRgba:o.sourceRgba,originalSha256:o.sourceRgbaSha256,
  faceMask:o.faceMask,faceSha256:o.faceSha256,backgroundMask:o.backgroundMask,backgroundSha256:o.backgroundSha256,arms:o.owners});
 return authority;
};
export async function buildFullFrameReviewWorklist(input){
 const authority=await sourceCheck(input);
 const {caseId,width,height,sourceRgba,sourceRgbaSha256,sourcePngSha256,faceMask,backgroundMask}=input;
 const tileSize=input.tileSize??32;
 if(!Number.isInteger(tileSize)||tileSize<8||tileSize>128)FAIL('INVALID_FULLFRAME_TILE');
 const tiles=[];let total=0,opaque=0,transparent=0,originalHighContrastEdges=0,ownerCandidatePixels=0;
 for(let y0=0;y0<height;y0+=tileSize)for(let x0=0;x0<width;x0+=tileSize){
  const x1=Math.min(x0+tileSize,width),y1=Math.min(y0+tileSize,height),id=tiles.length;
  let alphaOpaque=0,notOpaque=0,faceObserved=0,backdropObserved=0,eligibleHistoric=0,otherOpaqueUnknown=0,strongEdges=0;
  for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
   const i=y*width+x,a=sourceRgba[4*i+3],f=Boolean(faceMask[i]),b=Boolean(backgroundMask[i]),h=Boolean(authority.eligible[i]);
   if(a===255)alphaOpaque++;else notOpaque++;
   if(f)faceObserved++;if(b)backdropObserved++;if(h)eligibleHistoric++;
   if(a===255&&!f&&!b&&!h)otherOpaqueUnknown++;
   // Full-original-image RGB edge evidence. Neither endpoint has semantic truth.
   if(a===255)for(const j of [x+1<width?i+1:-1,y+1<height?i+width:-1]){
    if(j<0||sourceRgba[4*j+3]!==255)continue;
    const d=Math.abs(sourceRgba[4*i]-sourceRgba[4*j])+Math.abs(sourceRgba[4*i+1]-sourceRgba[4*j+1])+Math.abs(sourceRgba[4*i+2]-sourceRgba[4*j+2]);
    if(d>=90)strongEdges++;
   }
  }
  const pixels=(x1-x0)*(y1-y0);
  if(alphaOpaque+notOpaque!==pixels)FAIL('FULLFRAME_TILE_ACCOUNTING');
  total+=pixels;opaque+=alphaOpaque;transparent+=notOpaque;originalHighContrastEdges+=strongEdges;ownerCandidatePixels+=eligibleHistoric;
  tiles.push({tileId:id,bbox:[x0,y0,x1,y1],pixels,alphaOpaque,notOpaque,faceObserved,
   unapprovedBackdropObserved:backdropObserved,historicalOwnerCandidatePixels:eligibleHistoric,
   otherOpaqueUnknown,sourceHighContrastEdges:strongEdges,reviewPriority:strongEdges+2*eligibleHistoric,
   state:'UNREVIEWED',semanticLabelsVerified:0});
 }
 if(total!==width*height||ownerCandidatePixels!==authority.eligiblePixels)FAIL('FULLFRAME_COVERAGE_MISMATCH');
 return {version:VERSION,caseId,width,height,sourceRgbaSha256,sourcePngSha256,sourceEligibilitySha256:authority.sourceEligibilitySha256,
  totalPixels:total,opaquePixels:opaque,nonOpaquePixels:transparent,sourceHighContrastEdges:originalHighContrastEdges,
  historicalOwnerCandidatePixels:ownerCandidatePixels,tiles,allOriginalPixelsQueued:true,
  backgroundSemanticsCertified:false,bodySilhouetteCertified:false,independentlyHumanVerifiedPixels:0,
  reviewStatus:'AWAITING_AUTHENTIC_HUMAN_FULLFRAME_REVIEW',paintAuthorized:false,productionReleaseAuthorized:false};
}
export function encodeFullFrameDraftRle(labels){
 if(!isBytes(labels)||labels.length<1||labels.length>160000)FAIL('INVALID_FULLFRAME_LABELS');
 const out=[];let last=-1;
 for(const v of labels){if(!Number.isInteger(v)||v>=ROLES.length)FAIL('INVALID_FULLFRAME_LABEL');if(v===last)out.at(-1)[1]++;else{out.push([v,1]);last=v;}}
 return out;
}
function decode(rle,n){
 if(!Array.isArray(rle)||rle.length<1||rle.length>n)FAIL('INVALID_FULLFRAME_RLE');
 const out=new Uint8Array(n);let at=0;
 for(const z of rle){
  if(!Array.isArray(z)||z.length!==2||!Number.isInteger(z[0])||z[0]<0||z[0]>=ROLES.length||!Number.isSafeInteger(z[1])||z[1]<1||at+z[1]>n)FAIL('INVALID_FULLFRAME_RLE');
  out.fill(z[0],at,at+z[1]);at+=z[1];
 }
 if(at!==n)FAIL('FULLFRAME_RLE_LENGTH');
 return out;
}
export async function validateUntrustedFullFrameDraft({...o}){
 const auth=await sourceCheck(o),n=o.width*o.height,d=o.draft;
 if(!d||d.format!=='MinimalizerPublic-P0-fullframe-review-draft-v1'||d.caseId!==o.caseId||
 !Array.isArray(d.dimensions)||d.dimensions.length!==2||d.dimensions[0]!==o.width||d.dimensions[1]!==o.height||
 d.sourcePngSha256!==o.sourcePngSha256||d.sourceRgbaSha256!==o.sourceRgbaSha256||d.sourceEligibilitySha256!==auth.sourceEligibilitySha256||
 d.status!=='UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL'||d.approved!==false||d.paintAuthorized!==false||
 d.reviewerAuthenticated!==false||!Array.isArray(d.roles)||JSON.stringify(d.roles)!==JSON.stringify(ROLES))FAIL('UNTRUSTED_FULLFRAME_DRAFT_IDENTITY');
 const labels=decode(d.rle,n),counts=new Array(ROLES.length).fill(0);let originalOpaqueUnreviewed=0,proposed=0;
 for(let i=0;i<n;i++){
  const v=labels[i],a=o.sourceRgba[i*4+3];
  if(v&&a!==255)FAIL('FULLFRAME_NONOPAQUE_PROPOSAL');
  counts[v]++;if(v)proposed++;else if(a===255)originalOpaqueUnreviewed++;
 }
 return {version:VERSION,caseId:o.caseId,width:o.width,height:o.height,sourceRgbaSha256:o.sourceRgbaSha256,
  sourcePngSha256:o.sourcePngSha256,sourceEligibilitySha256:auth.sourceEligibilitySha256,
  labelsSha256:await sha(labels),labels,counts,proposedPixels:proposed,opaqueUnreviewedPixels:originalOpaqueUnreviewed,
  humanIdentityVerified:false,authenticReviewApproved:false,productPaintAuthorized:false,status:'UNTRUSTED_FULLFRAME_DRAFT_HOLD'};
}
export async function compareUntrustedFullFrameDrafts({...o}){
 if(!Array.isArray(o.drafts)||o.drafts.length!==2)FAIL('TWO_FULLFRAME_DRAFTS_REQUIRED');
 const common={...o};delete common.drafts;
 const [a,b]=await Promise.all(o.drafts.map(draft=>validateUntrustedFullFrameDraft({...common,draft})));
 if(a.labelsSha256===b.labelsSha256)FAIL('FULLFRAME_DUPLICATE_DRAFTS_NOT_INDEPENDENT');
 const n=o.width*o.height,conflicts=[],counts=new Array(ROLES.length).fill(0);
 let agree=0,disagree=0,abstain=0;
 for(let i=0;i<n;i++){
  const x=a.labels[i],y=b.labels[i];
  if(!x||!y)abstain++;
  else if(x===y){counts[x]++;agree++;}
  else{disagree++;if(conflicts.length<512)conflicts.push(i);}
 }
 return {version:VERSION,caseId:o.caseId,sourceRgbaSha256:a.sourceRgbaSha256,
  sourceEligibilitySha256:a.sourceEligibilitySha256,totalPixels:n,
  untrustedMatchingPixels:agree,untrustedDisagreedPixels:disagree,abstainedPixels:abstain,
  matchingClassCounts:counts,first512DisagreementIndices:conflicts,
  independentHumanIdentityEstablished:false,wholeCharacterHumanGolden:false,semanticPixelsAuthenticated:0,
  paintAuthorized:false,releaseAuthorized:false,status:'REQUIRES_INDEPENDENT_HUMAN_ADJUDICATION'};
}
export function fullFrameGoldenGate({cases=[]}={}){
 if(!Array.isArray(cases)||cases.length>2||new Set(cases.map(x=>x.caseId)).size!==cases.length||
 cases.some(x=>!['GC001','Raden'].includes(x.caseId)))FAIL('INVALID_FULLFRAME_GATE_CASES');
 return {version:VERSION,missingCases:['GC001','Raden'].filter(id=>!cases.some(x=>x.caseId===id)),
  independentlyAuthenticatedSemanticPixels:0,fullBodySilhouetteGolden:false,
  armSleeveNeckwearHairGolden:false,fullSceneSvgBudgetPassed:false,realIphoneSafariPassed:false,
  rollbackPassed:false,stage18PaintAuthorized:false,releaseAuthorized:false,status:'DRAFT_HOLD'};
}
