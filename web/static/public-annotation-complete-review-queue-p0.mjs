/** MinimalizerPublic P0 Stage36: lossless COVERAGE work queue, not semantic owner inference.
 * Tile enumeration must include EVERY eligible pixel, even if risk score is zero.
 * User-supplied draft hashes/labels are untrusted even when two drafts agree.
 * This module performs NO paint, no approval and no promotion.
 */
import {deriveSourceAnnotationAuthority} from './public-annotation-authority-p0.mjs';
import {validateManualReviewDraft} from './public-annotation-ingest-p0.mjs';
import {compareSourceReviewDraftPair} from './public-annotation-dual-review-p0.mjs';
export const VERSION='p0-stage36-complete-source-review-coverage-v1';
const fail=s=>{throw new TypeError(s);};
export async function buildCompleteSourceReviewQueue({caseId,width,height,sourceRgba,sourceRgbaSha256,sourcePngSha256,
  faceMask,faceSha256,backgroundMask,backgroundSha256,owners,drafts=[],tileSize=20,maxTasks=1500,minContrast=90}){
  if(!['GC001','Raden'].includes(caseId)||!Number.isInteger(tileSize)||tileSize<4||tileSize>80||
    !Number.isInteger(maxTasks)||maxTasks<1||maxTasks>10000||!Number.isInteger(minContrast)||minContrast<0||minContrast>765||
    !Array.isArray(drafts)||![0,2].includes(drafts.length))fail('INVALID_STAGE36_QUEUE_INPUT');
  const authority=await deriveSourceAnnotationAuthority({width,height,originalRgba:sourceRgba,originalSha256:sourceRgbaSha256,
    faceMask,faceSha256,backgroundMask,backgroundSha256,arms:owners});
  const n=width*height,tx=Math.ceil(width/tileSize),ty=Math.ceil(height/tileSize);
  const cells=new Map();const get=(x,y)=>{
    const gx=Math.floor(x/tileSize),gy=Math.floor(y/tileSize),id=gy*tx+gx;
    let t=cells.get(id);if(!t){t={tileId:id,bbox:[gx*tileSize,gy*tileSize,Math.min(width,(gx+1)*tileSize),Math.min(height,(gy+1)*tileSize)],
      leftEligible:0,rightEligible:0,unclassified:0,unverifiedAgreement:0,disagreement:0,sourceBoundaryEdges:0,
      sourceContrastEdges:0,faceContacts:0,backgroundContacts:0,alphaContacts:0,reviewerVerifiedPixels:0};cells.set(id,t);}return t;
  };
  let pair=null,aLabels=null,bLabels=null;
  if(drafts.length===2){
    const common={caseId,width,height,sourceRgba,sourceRgbaSha256,sourcePngSha256,faceMask,faceSha256,
      backgroundMask,backgroundSha256,owners};
    // Never trust per-draft status fields; independently re-pin BOTH drafts and source.
    pair=await compareSourceReviewDraftPair({...common,drafts});
    const [a,b]=await Promise.all(drafts.map(draft=>validateManualReviewDraft({...common,draft})));
    if(a.labelsSha256!==pair.draftHashes[0]||b.labelsSha256!==pair.draftHashes[1])fail('REVIEW_PAIR_PIN_MISMATCH');
    aLabels=a.labels;bLabels=b.labels;
  }
  let eligibleTotal=0,disagreements=0,unknown=0,agreement=0,edges=0,contrastEdges=0;
  const offsets=[[1,0],[-1,0],[0,1],[0,-1]];
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const i=y*width+x;if(!authority.eligible[i])continue;
    const tile=get(x,y);eligibleTotal++;
    if(authority.left[i])tile.leftEligible++;else if(authority.right[i])tile.rightEligible++;else fail('UNOWNED_ELIGIBLE_PIXEL');
    const a=aLabels?.[i]||0,b=bLabels?.[i]||0;
    if(a&&b){if(a===b){tile.unverifiedAgreement++;agreement++;}else{tile.disagreement++;disagreements++;}}
    else{tile.unclassified++;unknown++;}
    for(const [dx,dy] of offsets){
      const nx=x+dx,ny=y+dy;
      if(nx<0||ny<0||nx>=width||ny>=height){tile.sourceBoundaryEdges++;edges++;continue;}
      const j=ny*width+nx;
      if(!authority.eligible[j]){tile.sourceBoundaryEdges++;edges++;
        if(faceMask[j])tile.faceContacts++;
        if(backgroundMask[j])tile.backgroundContacts++;
        if(sourceRgba[4*j+3]!==255)tile.alphaContacts++;
      }
      const sourceL1=Math.abs(sourceRgba[4*i]-sourceRgba[4*j])+Math.abs(sourceRgba[4*i+1]-sourceRgba[4*j+1])+Math.abs(sourceRgba[4*i+2]-sourceRgba[4*j+2]);
      if(sourceL1>=minContrast){tile.sourceContrastEdges++;contrastEdges++;}
    }
  }
  if(eligibleTotal!==authority.eligiblePixels||authority.byOwner.left_arm+authority.byOwner.right_arm!==eligibleTotal)fail('AUTHORITY_COVERAGE_MISMATCH');
  if(pair&&(pair.disagreedPixels!==disagreements||pair.unverifiedMatchingPixels!==agreement||pair.abstainedPixels!==unknown))fail('CROSS_REVIEW_ACCOUNTING_MISMATCH');
  if(cells.size>maxTasks)fail('COMPLETE_REVIEW_QUEUE_BUDGET_EXCEEDED'); // no silent truncation of low-risk/unknown regions
  const tasks=[...cells.values()].map(t=>({...t,
    eligiblePixels:t.leftEligible+t.rightEligible,
    priorityScore:1000*t.disagreement+3*t.unclassified+4*t.faceContacts+3*t.backgroundContacts+3*t.alphaContacts+t.sourceContrastEdges+t.sourceBoundaryEdges,
    semanticStatus:'UNVERIFIED_REQUIRES_INDEPENDENT_SOURCE_REVIEW'}));
  tasks.sort((a,b)=>b.priorityScore-a.priorityScore||a.tileId-b.tileId);
  const totalTasks=tasks.length,visited=tasks.reduce((s,t)=>s+t.eligiblePixels,0);
  if(visited!==eligibleTotal||tasks.some(t=>t.eligiblePixels<1||t.eligiblePixels!==t.unclassified+t.unverifiedAgreement+t.disagreement))fail('REVIEW_TILE_COVERAGE_MISMATCH');
  return {version:VERSION,caseId,width,height,tileSize,sourceRgbaSha256,sourceEligibilitySha256:authority.sourceEligibilitySha256,
    eligiblePixels:eligibleTotal,eligibleByOwner:authority.byOwner,allEligiblePixelsQueued:true,
    totalReviewTiles:totalTasks,tilePixelCoverage:visited,sourceBoundaryEdges:edges,sourceContrastEdges:contrastEdges,
    unverifiedMatchingPixels:agreement,disagreedPixels:disagreements,unclassifiedPixels:unknown,
    reviewerVerifiedPixels:0,reviewerProvenanceVerified:false,reviewTasks:tasks,sourceRgbaExported:false,
    semanticOwnerApproved:false,stage18PaintAllowed:false,productPromotionAuthorized:false,reviewStatus:'COMPLETE_QUEUE_UNVERIFIED'};
}
