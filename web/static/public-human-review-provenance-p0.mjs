/** Stage92: independent verifier-key transport for whole-image untrusted drafts.
 * ECDSA verifies possession of externally pinned signing key only.
 * It cannot prove human identity, independence, label truth or Golden.
 */
import {verifyHumanReviewQueue} from './public-human-review-queue-p0.mjs';
import {validateUntrustedFullFrameDraft} from './public-fullframe-review-p0.mjs';
export const VERSION='p0-stage92-wholeframe-review-receipt-crypto-not-human-v1';
const SHA=/^[a-f0-9]{64}$/;
const bytes=b=>b instanceof Uint8Array||b instanceof Uint8ClampedArray;
const fail=s=>{throw new TypeError(s)};
const digest=async a=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');
export function fullFrameReceiptPayload({caseId,sourceRgbaSha256,sourcePngSha256,packetSha256,labelsSha256,publicKeySha256}){
 if(!['GC001','Raden'].includes(caseId)||[sourceRgbaSha256,sourcePngSha256,packetSha256,labelsSha256,publicKeySha256].some(x=>!SHA.test(x||'')))fail('INVALID_FULLFRAME_RECEIPT_FIELDS');
 return JSON.stringify({format:'MinimalizerPublic-P0-fullframe-review-crypto-receipt-v1',caseId,
  sourceRgbaSha256,sourcePngSha256,packetSha256,labelsSha256,publicKeySha256});
}
export async function inspectExternallyPinnedFullFrameReceipt({source,packet,draft,receipt,externalTrust}){
 if(!crypto?.subtle||!receipt||!externalTrust||!bytes(receipt.signature)||receipt.signature.length!==64||
 !bytes(externalTrust.publicKeySpki)||externalTrust.publicKeySpki.length<40||
 !SHA.test(externalTrust.pinnedPublicKeySha256||''))fail('EXTERNAL_FULLFRAME_KEY_REQUIRED');
 const q=await verifyHumanReviewQueue(source,packet);
 const reviewed=await validateUntrustedFullFrameDraft({...source,draft});
 const keySha=await digest(externalTrust.publicKeySpki);
 if(keySha!==externalTrust.pinnedPublicKeySha256)fail('EXTERNAL_FULLFRAME_KEY_PIN_MISMATCH');
 const expected=fullFrameReceiptPayload({caseId:source.caseId,sourceRgbaSha256:source.sourceRgbaSha256,
  sourcePngSha256:source.sourcePngSha256,packetSha256:packet.packetSha256,
  labelsSha256:reviewed.labelsSha256,publicKeySha256:keySha});
 if(receipt.payload!==expected)fail('FULLFRAME_RECEIPT_SOURCE_OR_DRAFT_SWAPPED');
 let valid=false;
 try{
  const key=await crypto.subtle.importKey('spki',externalTrust.publicKeySpki,{name:'ECDSA',namedCurve:'P-256'},false,['verify']);
  valid=await crypto.subtle.verify({name:'ECDSA',hash:'SHA-256'},key,receipt.signature,new TextEncoder().encode(expected));
 }catch{fail('FULLFRAME_SIGNATURE_MALFORMED')}
 if(!valid)fail('FULLFRAME_SIGNATURE_INVALID');
 return {version:VERSION,caseId:q.caseId,keySha256:keySha,labelsSha256:reviewed.labelsSha256,
  sourcePacketSha256:packet.packetSha256,proposedSourcePixels:reviewed.proposedPixels,
  signatureCryptographicallyVerified:true,signerHumanIdentityVerified:false,independentHumanReviewers:0,
  semanticPixelsGoldApproved:0,paintAuthorized:false,productReleaseAuthorized:false,
  status:'SIGNATURE_TRANSPORT_ONLY_HUMAN_AUTHORITY_HOLD'};
}
export function compareDistinctSigningAnchors(a,b){
 if(!a||!b||!SHA.test(a.keySha256||'')||!SHA.test(b.keySha256||'')||
 a.keySha256===b.keySha256)fail('DISTINCT_EXTERNAL_SIGNER_KEY_PINS_REQUIRED');
 return {distinctPublicKeysObserved:true,distinctHumanReviewersVerified:false,
  semanticAccuracyEstablished:false,humanGoldenApproved:false,paintAuthorized:false,
  status:'DISTINCT_KEYS_DO_NOT_PROVE_INDEPENDENT_HUMANS'};
}
