/** Structural P0 Stage26. Validate private Stage25 RLE; NEVER authorize paint. */
export const VERSION='structural-p0-stage26-untrusted-review-ingest-v1';
const fail=m=>{throw new TypeError(m);};
const typed=a=>a instanceof Uint8Array||a instanceof Uint8ClampedArray;
const hex=/^[a-f0-9]{64}$/;
const FORMAT='MinimalizerPublic-P0-source-manual-review-draft-v1';
const EXPECTED={0:'unclassified',1:'sleeve_observation',2:'skin_forearm_observation',3:'hair_observation',4:'other_clothes_observation'};
const sha=async a=>{
 if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');
 return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');
};
export function decodeReviewRle({rle,expectedPixels,maxRuns=25000}){
 if(!Number.isInteger(expectedPixels)||expectedPixels<1||expectedPixels>160000||!Array.isArray(rle)||!rle.length||rle.length>maxRuns)fail('RLE_BOUNDS');
 const out=new Uint8Array(expectedPixels);let offset=0;
 for(const run of rle){
  if(!Array.isArray(run)||run.length!==2||!Number.isInteger(run[0])||run[0]<0||run[0]>4||!Number.isSafeInteger(run[1])||run[1]<1||offset+run[1]>expectedPixels)fail('RLE_CORRUPT');
  out.fill(run[0],offset,offset+run[1]);offset+=run[1];
 }
 if(offset!==expectedPixels)fail('RLE_LENGTH_MISMATCH');
 return out;
}
export function encodeReviewRle(labels){
 if(!typed(labels)||!labels.length||labels.length>160000)fail('INVALID_LABEL_BYTES');
 const out=[];let value=labels[0],size=0;
 for(const v of labels){if(!Number.isInteger(v)||v<0||v>4)fail('INVALID_LABEL_BYTES');if(v!==value){out.push([value,size]);value=v;size=0;}size++;}
 out.push([value,size]);return out;
}
/** All source authority is a caller-provided independent byte input, not supplied by draft. */
export async function validateManualReviewDraft({draft,caseId,width,height,sourceRgba,sourceRgbaSha256,sourcePngSha256,
 faceMask,faceSha256,backgroundMask,backgroundSha256,owners}){
 if(!draft||!['GC001','Raden'].includes(caseId)||!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000)fail('REVIEW_INPUT');
 const n=width*height;
 if(!typed(sourceRgba)||sourceRgba.length!==4*n||!typed(faceMask)||faceMask.length!==n||!typed(backgroundMask)||backgroundMask.length!==n||
 !owners||Array.isArray(owners)||!['left_arm','right_arm'].every(x=>typed(owners[x]?.mask)&&owners[x].mask.length===n&&hex.test(owners[x].sha256||'')))fail('INVALID_TRUSTED_SOURCE');
 const inputs=[[sourceRgba,sourceRgbaSha256,'SOURCE'],[faceMask,faceSha256,'FACE'],[backgroundMask,backgroundSha256,'BACKGROUND'],
 ...['left_arm','right_arm'].map(id=>[owners[id].mask,owners[id].sha256,id])];
 for(const [bytes,pin,tag] of inputs){if(!hex.test(pin||'')||await sha(bytes)!==pin)fail(tag+'_ORIGINAL_SHA_MISMATCH');}
 if(!hex.test(sourcePngSha256||'')||draft.format!==FORMAT||draft.caseId!==caseId||!Array.isArray(draft.dimensions)||draft.dimensions.length!==2||draft.dimensions[0]!==width||draft.dimensions[1]!==height)fail('CASE_OR_FORMAT_CONFLICT');
 for(const [name,a,b] of [['PNG',draft.sourcePngSha256,sourcePngSha256],['RGBA',draft.sourceRgbaSha256,sourceRgbaSha256],['FACE',draft.faceSha256,faceSha256],['BACKGROUND',draft.backgroundObserverSha256,backgroundSha256],
 ...['left_arm','right_arm'].map(id=>[id,draft.historicalOwnerSha256?.[id],owners[id].sha256])]){
 if(a!==b)fail(name+'_DRAFT_SOURCE_MISMATCH');}
 if(!draft.labels||Object.keys(draft.labels).length!==5||Object.entries(EXPECTED).some(([k,v])=>draft.labels[k]!==v))fail('LABEL_MAP_CONFLICT');
 if(draft.approved!==false||draft.productPromotionAuthorized!==false||draft.reviewStatus!=='UNVERIFIED_UNTRUSTED_USER_ANNOTATION')fail('UNTRUSTED_CLAIM');
 const labels=decodeReviewRle({rle:draft.rle,expectedPixels:n});
 const counts=new Int32Array(5),armCounts={left_arm:new Int32Array(5),right_arm:new Int32Array(5)};
 let excluded=0,eligible=0;
 for(let i=0;i<n;i++){
  const v=labels[i];if(v&&sourceRgba[4*i+3]!==255)fail('ALPHA_EXCLUDED_LABEL');
  if(faceMask[i]&&v)fail('FACE_EXCLUDED_LABEL');if(backgroundMask[i]&&v)fail('BACKGROUND_EXCLUDED_LABEL');
  const left=owners.left_arm.mask[i],right=owners.right_arm.mask[i];
  if((left!==0&&left!==255)||(right!==0&&right!==255)||(faceMask[i]!==0&&faceMask[i]!==255)||(backgroundMask[i]!==0&&backgroundMask[i]!==255))fail('NONBINARY_ORIGINAL_MASK');
  if(left&&right&&v)fail('OVERLAPPING_ARM_LABEL');
  const allowed=!!(left||right)&&!faceMask[i]&&!backgroundMask[i]&&sourceRgba[4*i+3]===255;
  if(v&&!allowed)fail('OUTSIDE_SOURCE_OWNER_LABEL');
  counts[v]++;if(allowed){eligible++;armCounts[left?'left_arm':'right_arm'][v]++;}else excluded++;
 }
 return {version:VERSION,caseId,width,height,sourceRgbaSha256,sourcePngSha256,labels,labelsSha256:await sha(labels),
 counts:Array.from(counts),perArmCounts:Object.fromEntries(Object.entries(armCounts).map(([k,v])=>[k,Array.from(v)])),eligiblePixels:eligible,
 unclassifiedEligiblePixels:armCounts.left_arm[0]+armCounts.right_arm[0],excludedPixels:excluded,
 annotationTrust:'UNVERIFIED',independentBoundaryVerified:false,productPromotionAuthorized:false,stage18PaintAllowed:false};
}
