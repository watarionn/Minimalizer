/** P0 Stage43: in-memory draft isolation on case switching. UNTRUSTED notes only.
 * Refuse cross-source or out-of-owner labels. Return copies, never paint.
 */
export const VERSION='p0-stage43-ephemeral-source-draft-isolation-v1';
const fail=x=>{throw new TypeError(x);};
const hex=/^[a-f0-9]{64}$/;
const typed=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
export function sealUntrustedSession({caseId,width,height,sourcePngSha256,sourceRgbaSha256,labels,eligible,brushHistory=[]}){
 const n=width*height;
 if(!['GC001','Raden'].includes(caseId)||!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||
 !hex.test(sourcePngSha256||'')||!hex.test(sourceRgbaSha256||'')||!typed(labels)||labels.length!==n||!typed(eligible)||eligible.length!==n||!Array.isArray(brushHistory)||brushHistory.length>12)fail('INVALID_SESSION');
 for(let i=0;i<n;i++){
  if(eligible[i]!==0&&eligible[i]!==1&&eligible[i]!==255)fail('INVALID_ELIGIBILITY');
  if(!Number.isInteger(labels[i])||labels[i]>4||(labels[i]&&!eligible[i]))fail('OUTSIDE_SOURCE_OWNER_LABEL');
 }
 for(const h of brushHistory){if(!typed(h)||h.length!==n)fail('INVALID_HISTORY');for(let i=0;i<n;i++)if(h[i]>4||(h[i]&&!eligible[i]))fail('INVALID_HISTORY_PIXEL');}
 return {version:VERSION,caseId,width,height,sourcePngSha256,sourceRgbaSha256,labels:new Uint8Array(labels),brushHistory:brushHistory.map(h=>new Uint8Array(h)),trust:'UNVERIFIED_LOCAL_DRAFT',independentReview:false,paintAuthorized:false,productPromotionAuthorized:false};
}
export function reopenUntrustedSession({session,caseId,width,height,sourcePngSha256,sourceRgbaSha256,eligible}){
 if(!session||session.version!==VERSION||session.caseId!==caseId||session.width!==width||session.height!==height||session.sourcePngSha256!==sourcePngSha256||session.sourceRgbaSha256!==sourceRgbaSha256||session.trust!=='UNVERIFIED_LOCAL_DRAFT'||session.independentReview!==false||session.paintAuthorized!==false||session.productPromotionAuthorized!==false)fail('SESSION_SOURCE_CONFLICT');
 return sealUntrustedSession({caseId,width,height,sourcePngSha256,sourceRgbaSha256,eligible,labels:session.labels,brushHistory:session.brushHistory});
}
