/** Stage47: native browser capability probe; not a signed Safari or public-origin proof. */
export const VERSION='p0-stage47-secure-browser-capability-v1';
export function probeNativeReviewOrigin(){
  const loc=globalThis.location;
  const href=typeof loc?.href==='string'?loc.href:'';
  let protocol='unavailable',hostname='';
  try {const u=new URL(href);protocol=u.protocol;hostname=u.hostname.toLowerCase();}catch{}
  const secure=globalThis.isSecureContext===true;
  const subtle=!!globalThis.crypto?.subtle && typeof globalThis.crypto.subtle.digest==='function';
  const validHttps=protocol==='https:' && hostname!=='';
  return {version:VERSION,protocol,secureContext:secure,nativeSubtleAvailable:subtle,
    nativeSecureReviewUsable:validHttps&&secure&&subtle,
    realProductionOriginTested:false,iphoneSafariVerified:false,
    reviewerIdentityVerified:false,productPromotionAuthorized:false,
    status:validHttps&&secure&&subtle?'SECURE_CAPABILITY_ONLY_NOT_PRODUCTION_CERTIFIED':'REAL_HTTPS_ORIGIN_PROOF_REQUIRED'};
}
