/** Stage37: derive immutable, source-pinned private REVIEW tile identity.
 * The manifest contains geometry and SHA lineage, NOT semantic truth or source RGBA.
 * Recompute from independently supplied source/masks; never trust a JSON claim.
 */
import {buildCompleteSourceReviewQueue} from './public-annotation-complete-review-queue-p0.mjs';
export const VERSION='p0-stage37-source-pinned-complete-tile-identity-v1';
const fail=s=>{throw new TypeError(s);};
const digest=async v=>{
 if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');
 return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',v))].map(x=>x.toString(16).padStart(2,'0')).join('');
};
export async function buildPinnedReviewTileManifest(inputs){
 const q=await buildCompleteSourceReviewQueue(inputs);
 if(q.eligiblePixels!==q.tilePixelCoverage||q.reviewerVerifiedPixels!==0||!q.allEligiblePixelsQueued)fail('INCOMPLETE_REVIEW_QUEUE');
 const tiles=q.reviewTasks.map(t=>({tileId:t.tileId,bbox:t.bbox,eligiblePixels:t.eligiblePixels,
   leftEligible:t.leftEligible,rightEligible:t.rightEligible,unknown:t.unclassified,
   disputed:t.disagreement,unverifiedAgreement:t.unverifiedAgreement,priorityScore:t.priorityScore}));
 const totals=tiles.reduce((a,t)=>{a.total+=t.eligiblePixels;a.unknown+=t.unknown;a.disputed+=t.disputed;a.matching+=t.unverifiedAgreement;return a;},{total:0,unknown:0,disputed:0,matching:0});
 if(totals.total!==q.eligiblePixels||totals.unknown!==q.unclassifiedPixels||totals.disputed!==q.disagreedPixels||totals.matching!==q.unverifiedMatchingPixels)fail('TILE_MANIFEST_ACCOUNTING_ERROR');
 if(new Set(tiles.map(t=>t.tileId)).size!==tiles.length)fail('DUPLICATE_TILES');
 const sourceIdentity={caseId:q.caseId,width:q.width,height:q.height,tileSize:q.tileSize,
   sourceRgbaSha256:q.sourceRgbaSha256,sourceEligibilitySha256:q.sourceEligibilitySha256};
 const core={version:VERSION,sourceIdentity,tiles,totals};
 const manifestSha256=await digest(new TextEncoder().encode(JSON.stringify(core)));
 return {...core,manifestSha256,semanticClassesCertified:false,independentReviewerVerified:false,
   paintAuthorized:false,productPromotionAuthorized:false,reviewStatus:'UNVERIFIED_QUEUE'};
}
