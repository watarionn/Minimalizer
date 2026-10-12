/** Stage93: exhaustive per-tile disagreement map, not truncated to first 512 pixels.
 * Source RGB high contrast prioritizes manual inspection only, not semantics.
 * Does NOT authenticate the people who made the two drafts.
 */
import {buildFullFrameReviewWorklist,validateUntrustedFullFrameDraft} from './public-fullframe-review-p0.mjs';
export const VERSION='p0-stage93-wholeframe-uncertainty-map-hold-v1';
const fail=s=>{throw new TypeError(s)};
export async function buildHumanReviewDisputeMap({source,drafts}){
 if(!Array.isArray(drafts)||drafts.length!==2)fail('TWO_MANUAL_DRAFTS_REQUIRED');
 const q=await buildFullFrameReviewWorklist({...source,tileSize:32});
 const [a,b]=await Promise.all(drafts.map(draft=>validateUntrustedFullFrameDraft({...source,draft})));
 if(a.labelsSha256===b.labelsSha256)fail('IDENTICAL_DRAFT_NOT_INDEPENDENT');
 let agree=0,disagree=0,abstain=0;
 const grid=q.tiles.map(t=>({tileId:t.tileId,bbox:t.bbox,
  sourceHighContrastEdges:t.sourceHighContrastEdges,historicalCandidatePixels:t.historicalOwnerCandidatePixels,
  matchingUntrustedPixels:0,disputedUntrustedPixels:0,abstainedPixels:0,
  reviewerIdentityEstablished:false,actualHumanGolden:false}));
 const cols=Math.ceil(q.width/32);
 for(let i=0;i<q.totalPixels;i++){
  const x=i%q.width,y=Math.floor(i/q.width),tile=grid[Math.floor(y/32)*cols+Math.floor(x/32)],v=a.labels[i],w=b.labels[i];
  if(!v||!w){tile.abstainedPixels++;abstain++;}
  else if(v===w){tile.matchingUntrustedPixels++;agree++;}
  else{tile.disputedUntrustedPixels++;disagree++;}
 }
 if(agree+disagree+abstain!==q.totalPixels||grid.reduce((n,t)=>n+t.matchingUntrustedPixels+t.disputedUntrustedPixels+t.abstainedPixels,0)!==q.totalPixels)fail('FULLFRAME_DISPUTE_AREA_MISMATCH');
 grid.sort((a,b)=>b.disputedUntrustedPixels-a.disputedUntrustedPixels||
 b.sourceHighContrastEdges-a.sourceHighContrastEdges||a.tileId-b.tileId);
 return {version:VERSION,caseId:q.caseId,sourceSha256:q.sourceRgbaSha256,
  originalPixels:q.totalPixels,originalTiles:grid.length,
  matchingUntrustedPixels:agree,disputedUntrustedPixels:disagree,abstainedPixels:abstain,
  prioritizedUntrustedTiles:grid,firstDraftSha256:a.labelsSha256,secondDraftSha256:b.labelsSha256,
  independentlyHumanReviewedPixels:0,personBackgroundHumanApproved:false,
  humanGoldenApproved:false,paintAuthorized:false,productReleaseAuthorized:false,
  status:'AWAITING_REAL_HUMAN_FULLFRAME_ADJUDICATION'};
}
