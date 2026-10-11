/** P0 Stage17: source pinned owner, face and background veto. Research only.
 * A historical Stage04 owner signature is NOT independent semantic approval.
 * The independently observed exclusion must be pinned; no generated masks.
 */
export const VERSION='structural-p0-stage17-owner-evidence-guard-v1';
const typed=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const hex=/^[a-f0-9]{64}$/;
const err=x=>{throw new TypeError(x);};
const ROLES=new Set(['left_arm','right_arm','torso','major_clothing','lower_body']);
async function checkHash(bytes,sha,tag){if(!hex.test(sha||''))err(tag+'_SHA_REQUIRED');if(!globalThis.crypto?.subtle)err('WEBCRYPTO_MISSING');const got=[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');if(got!==sha)err(tag+'_SHA_MISMATCH');}
function binary(b,n,tag){if(!typed(b)||b.length!==n)err(tag+'_SIZE');let c=0;for(const v of b){if(v!==0&&v!==255)err(tag+'_NONBINARY');if(v)c++;}return c;}
/** Background mask is a conservative external *observation*, NOT a semantic classifier.
 * Pixel authority = Stage04 signed owner & opaque decoded source & !face & !background.
 * If arm spans both garment and hair, this API DOES NOT certify sleeve semantics.
 */
export async function prepareVisibleSourceOwners({width,height,sourceRgba,sourceSha256,faceMask,faceSha256,
  backgroundMask,backgroundSha256,owners,maxOwnerPixels=85000}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000)err('DIMENSIONS');
 const n=width*height;if(!typed(sourceRgba)||sourceRgba.length!==4*n)err('SOURCE_RGBA');
 binary(faceMask,n,'FACE');binary(backgroundMask,n,'BACKGROUND');
 if(!Array.isArray(owners)||owners.length<1||owners.length>6)err('OWNERS_REQUIRED');
 await Promise.all([[sourceRgba,sourceSha256,'SOURCE'],[faceMask,faceSha256,'FACE'],[backgroundMask,backgroundSha256,'BACKGROUND']].map(x=>checkHash(...x)));
 const occupied=new Uint8Array(n),names=new Set(),records=[];let totalVisible=0;
 for(const o of owners){
  if(!o||!ROLES.has(o.role)||names.has(o.role)||o.evidenceLevel!=='historical_stage04_signed'||typeof o.evidenceRef!=='string'||!o.evidenceRef.trim())err('OWNER_PROVENANCE');names.add(o.role);
  const originalPixels=binary(o.mask,n,o.role);if(originalPixels<20||originalPixels>maxOwnerPixels)err('OWNER_BUDGET');await checkHash(o.mask,o.maskSha256,o.role);
  let faceExcluded=0,backExcluded=0,alphaExcluded=0,otherOwnerCollision=0,valid=0;
  const visible=new Uint8Array(n);
  for(let i=0;i<n;i++)if(o.mask[i]){
   if(faceMask[i]){faceExcluded++;continue;}
   if(backgroundMask[i]){backExcluded++;continue;}
   if(sourceRgba[i*4+3]!==255){alphaExcluded++;continue;}
   if(occupied[i]){otherOwnerCollision++;continue;}
   visible[i]=255;valid++;
  }
  if(otherOwnerCollision)err('UNRESOLVED_VISIBLE_OWNER_OVERLAP');
  if(valid<20)err('OWNER_WITHOUT_VISIBLE_SOURCE');
  for(let i=0;i<n;i++)if(visible[i])occupied[i]=255;
  totalVisible+=valid;
  records.push({role:o.role,visibleMask:visible,originalPixels,visiblePixels:valid,
   excludedFace:faceExcluded,excludedBackground:backExcluded,excludedAlpha:alphaExcluded,
   historicalOwnerSemanticApproval:false,sourceBackgroundObserverSigned:false,
   contaminationFraction:(faceExcluded+backExcluded+alphaExcluded)/originalPixels});
 }
 return {version:VERSION,owners:records,totalVisiblePixels:totalVisible,
  noSourceAbsentPixels:true,independentSemanticOwnerApproval:false,
  productPromotionAuthorized:false,previewOnly:true};
}
