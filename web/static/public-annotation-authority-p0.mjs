/** P0 Stage31. Build a SHA-pinned SOURCE eligibility mask. Never signs semantic truth. */
export const VERSION='p0-stage31-source-eligibility-v1';
const type=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const rx=/^[a-f0-9]{64}$/;
function fail(s){throw new TypeError(s);}
const sha=async bytes=>{
 if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_UNAVAILABLE');
 return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
};
const pin=async(bytes,digest,name)=>{if(!rx.test(digest||'')||await sha(bytes)!==digest)fail(name+'_PIN_MISMATCH');};
const binary=(a,n,name)=>{
 if(!type(a)||a.length!==n)fail(name+'_SIZE');
 for(const v of a)if(v!==0&&v!==255)fail(name+'_NONBINARY');
};
/** All input masks are passed separately from the untrusted annotation JSON. */
export async function deriveSourceAnnotationAuthority({width,height,originalRgba,originalSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,arms}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000)fail('INVALID_CANVAS');
 const n=width*height;
 if(!type(originalRgba)||originalRgba.length!==4*n)fail('SOURCE_SIZE');
 binary(faceMask,n,'FACE');binary(backgroundMask,n,'BACKGROUND');
 if(!arms||Array.isArray(arms)||Object.keys(arms).sort().join(',')!=='left_arm,right_arm')fail('ARMS_REQUIRED');
 for(const r of ['left_arm','right_arm'])binary(arms[r]?.mask,n,r);
 await Promise.all([[originalRgba,originalSha256,'SOURCE'],[faceMask,faceSha256,'FACE'],[backgroundMask,backgroundSha256,'BACKGROUND'],...['left_arm','right_arm'].map(x=>[arms[x].mask,arms[x].sha256,x])].map(x=>pin(...x)));
 const eligible=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);let excludedAlpha=0,excludedBackground=0,excludedFace=0,eligibleCount=0;
 const totals={left_arm:0,right_arm:0};
 for(let i=0;i<n;i++){
  const a=arms.left_arm.mask[i],b=arms.right_arm.mask[i];
  if(a&&b)fail('HISTORICAL_OWNER_COLLISION'); // even in yet-unlabelled locations
  if(!a&&!b)continue;
  if(faceMask[i]){excludedFace++;continue;}
  if(backgroundMask[i]){excludedBackground++;continue;}
  if(originalRgba[i*4+3]!==255){excludedAlpha++;continue;}
  eligible[i]=255;(a?left:right)[i]=255;eligibleCount++;totals[a?'left_arm':'right_arm']++;
 }
 return {version:VERSION,width,height,originalSha256,sourceEligibilitySha256:await sha(eligible),eligible,left,right,eligiblePixels:eligibleCount,
  byOwner:totals,excludedFace,excludedBackground,excludedAlpha,
  semanticTruthEstablished:false,reviewerIdentityVerified:false,stage18PaintAllowed:false,productPromotionAuthorized:false};
}
