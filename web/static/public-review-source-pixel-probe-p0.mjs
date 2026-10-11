/** P0 Stage44: source-locked read-only pixel inspection, never generative inference.
 * Historical owner tags are geometry only, NEVER verified anatomy.
 */
import {deriveSourceAnnotationAuthority} from './public-annotation-authority-p0.mjs';
export const VERSION='p0-stage44-source-rgb-immutable-pixel-probe-v1';
const fail=s=>{throw new TypeError(s);};
export async function probePinnedOriginalSourcePixel({width,height,sourceRgba,sourceRgbaSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,owners,x,y,minContrast=96}){
 if(!Number.isInteger(x)||!Number.isInteger(y)||x<0||y<0||x>=width||y>=height||!Number.isInteger(minContrast)||minContrast<0||minContrast>765)fail('PIXEL_OUT_OF_RANGE');
 const valid=await deriveSourceAnnotationAuthority({width,height,originalRgba:sourceRgba,originalSha256:sourceRgbaSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,arms:owners});
 const i=y*width+x,at=i*4;
 const rgb=[sourceRgba[at],sourceRgba[at+1],sourceRgba[at+2]];
 let neighboringHighContrast=0,neighboringFace=0,neighboringBackground=0,neighboringAlpha=0;
 for(const [dx,dy] of [[-1,0],[1,0],[0,-1],[0,1]]){
  const xx=x+dx,yy=y+dy;if(xx<0||yy<0||xx>=width||yy>=height)continue;
  const j=yy*width+xx,o=4*j;
  if(Math.abs(sourceRgba[at]-sourceRgba[o])+Math.abs(sourceRgba[at+1]-sourceRgba[o+1])+Math.abs(sourceRgba[at+2]-sourceRgba[o+2])>=minContrast)neighboringHighContrast++;
  if(faceMask[j])neighboringFace++;
  if(backgroundMask[j])neighboringBackground++;
  if(sourceRgba[o+3]!==255)neighboringAlpha++;
 }
 return {version:VERSION,x,y,sourceRgb:rgb,sourceAlpha:sourceRgba[at+3],historicalEligible:Boolean(valid.eligible[i]),
  historicalCandidate:valid.left[i]?'left_arm':valid.right[i]?'right_arm':'none',
  protectedFace:Boolean(faceMask[i]),protectedObservedBackground:Boolean(backgroundMask[i]),
  sourceContrastNeighbors:neighboringHighContrast,faceNeighbors:neighboringFace,backgroundNeighbors:neighboringBackground,alphaNeighbors:neighboringAlpha,
  sourceSha256:sourceRgbaSha256,sourcePixelExact:true,sourceSemanticTruthVerified:false,semanticLabel:'unknown',
  noPixelMutation:true,paintAuthorized:false,productPromotionAuthorized:false};
}
