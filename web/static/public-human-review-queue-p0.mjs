/** Stage82 full-frame source-only review packet; labels remain untrusted. */
import {buildFullFrameReviewWorklist} from './public-fullframe-review-p0.mjs';
export const VERSION='p0-stage82-human-review-queue-hold-v1';
const fail=x=>{throw new TypeError(x)};
const sha=async s=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)))].map(x=>x.toString(16).padStart(2,'0')).join('');
export async function buildHumanReviewQueue(source){
 const q=await buildFullFrameReviewWorklist({...source,tileSize:32});
 const core={version:VERSION,caseId:q.caseId,rgbaSha256:q.sourceRgbaSha256,pngSha256:q.sourcePngSha256,
  eligibilitySha256:q.sourceEligibilitySha256,tiles:q.tiles.map(x=>({id:x.tileId,bbox:x.bbox,sourceEdges:x.sourceHighContrastEdges})),
  totalOriginalPixels:q.totalPixels};
 return {...core,packetSha256:await sha(JSON.stringify(core)),humanReviewAccepted:false,authenticatedHumanPixels:0,
  backgroundSemanticsVerified:false,paintAuthorized:false,status:'HUMAN_REVIEW_REQUIRED'};
}
export async function verifyHumanReviewQueue(source,packet){
 const fresh=await buildHumanReviewQueue(source);
 if(!packet||packet.packetSha256!==fresh.packetSha256||JSON.stringify(packet.tiles)!==JSON.stringify(fresh.tiles)||
 packet.rgbaSha256!==fresh.rgbaSha256||packet.pngSha256!==fresh.pngSha256||
 packet.eligibilitySha256!==fresh.eligibilitySha256||packet.caseId!==fresh.caseId||
 packet.totalOriginalPixels!==fresh.totalOriginalPixels||packet.backgroundSemanticsVerified!==false||
 packet.status!=='HUMAN_REVIEW_REQUIRED'||packet.humanReviewAccepted!==false||
 packet.authenticatedHumanPixels!==0||packet.paintAuthorized!==false)
  fail('UNTRUSTED_REVIEW_PACKET');
 return {caseId:fresh.caseId,originalPixelsQueued:fresh.totalOriginalPixels,verifiedSemanticPixels:0,
  status:'HUMAN_REVIEW_REQUIRED'};
}
