/** P0 Stage32. Source RGB contact and review-priority tiles, not sleeves/skin classification. */
export const VERSION='p0-stage32-source-boundary-risk-v1';
const type=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const fail=s=>{throw new TypeError(s);};
export function buildSourceBoundaryReviewQueue({width,height,originalRgba,authority,faceMask,backgroundMask,tileSize=20,minContrast=90,maxTiles=20}){
 const n=width*height;
 if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||!type(originalRgba)||originalRgba.length!==n*4||
 !type(authority)||authority.length!==n||!type(faceMask)||faceMask.length!==n||!type(backgroundMask)||backgroundMask.length!==n||
 !Number.isInteger(tileSize)||tileSize<4||tileSize>80||!Number.isInteger(minContrast)||minContrast<0||minContrast>765||
 !Number.isInteger(maxTiles)||maxTiles<1||maxTiles>100)fail('INVALID_REVIEW_QUEUE_INPUT');
 const cellsX=Math.ceil(width/tileSize),cellsY=Math.ceil(height/tileSize), tiles=new Map();
 const put=(x,y,type,weight)=>{const ix=Math.floor(x/tileSize),iy=Math.floor(y/tileSize),id=iy*cellsX+ix;
  let t=tiles.get(id);if(!t){t={id,gridX:ix,gridY:iy,bbox:[ix*tileSize,iy*tileSize,Math.min(width,(ix+1)*tileSize),Math.min(height,(iy+1)*tileSize)],
  sourceContrastEdges:0,faceContacts:0,backgroundContacts:0,alphaContacts:0,unknownOwnerBoundaryEdges:0};tiles.set(id,t);}t[type]+=weight;};
 let count=0,edges=0,contactFace=0,contactBackground=0,contactAlpha=0,highContrast=0;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const i=y*width+x;if(authority[i]!==0&&authority[i]!==255)fail('NONBINARY_AUTHORITY');
  if(faceMask[i]!==0&&faceMask[i]!==255||backgroundMask[i]!==0&&backgroundMask[i]!==255)fail('NONBINARY_EXCLUSION');
  if(!authority[i])continue;
  if(faceMask[i]||backgroundMask[i]||originalRgba[4*i+3]!==255)fail('SOURCE_AUTHORITY_COLLISION');
  count++;
  for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
   const nx=x+dx,ny=y+dy;if(nx<0||ny<0||nx>=width||ny>=height){edges++;put(x,y,'unknownOwnerBoundaryEdges',1);continue;}
   const j=ny*width+nx;
   if(!authority[j]){
    edges++;put(x,y,'unknownOwnerBoundaryEdges',1);
    if(faceMask[j]){contactFace++;put(x,y,'faceContacts',1);}
    if(backgroundMask[j]){contactBackground++;put(x,y,'backgroundContacts',1);}
    if(originalRgba[4*j+3]!==255){contactAlpha++;put(x,y,'alphaContacts',1);}
   }
   let contrast=0;for(let c=0;c<3;c++)contrast+=Math.abs(originalRgba[4*i+c]-originalRgba[4*j+c]);
   if(contrast>=minContrast){highContrast++;put(x,y,'sourceContrastEdges',1);}
  }
 }
 // A danger score queues manual review. It cannot create a mask, label or paint authority.
 const ranked=[...tiles.values()].map(t=>({...t,score:t.sourceContrastEdges+4*t.faceContacts+3*t.backgroundContacts+3*t.alphaContacts+t.unknownOwnerBoundaryEdges}));
 ranked.sort((a,b)=>b.score-a.score||a.id-b.id);
 return {version:VERSION,eligiblePixels:count,ownerBoundaryEdges:edges,faceContacts:contactFace,backgroundContacts:contactBackground,
  alphaContacts:contactAlpha,sourceContrastEdges:highContrast,totalRiskTiles:ranked.length,
  suggestedReviewTiles:ranked.slice(0,maxTiles),reviewerWorklistOnly:true,sourcePixelsClassified:0,
  semanticLabelsDerived:false,sourceAbsentPaintingAllowed:false,productPromotionAuthorized:false};
}
