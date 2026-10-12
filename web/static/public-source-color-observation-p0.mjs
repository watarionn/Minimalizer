/** Stage62: SHA-pinned original RGB evidence, not anatomical/paint authority. */
import {deriveSourceAnnotationAuthority} from './public-annotation-authority-p0.mjs';
export const VERSION='p0-stage62-source-color-observation-v1';
const bad=s=>{throw new TypeError(s)};
const typed=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const hash=async b=>[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('');
export async function observeSourceColorOwners({width,height,originalRgba,originalSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,arms,baselineRgba,baselineSha256}){
 const n=width*height;
 if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||!typed(baselineRgba)||baselineRgba.length!==4*n||typeof baselineSha256!=='string'||!/^[a-f0-9]{64}$/.test(baselineSha256)||!globalThis.crypto?.subtle)bad('INVALID_COLOR_EVIDENCE');
 if(await hash(baselineRgba)!==baselineSha256)bad('BASELINE_SHA_MISMATCH');
 const auth=await deriveSourceAnnotationAuthority({width,height,originalRgba,originalSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,arms});
 const zones=[];
 for(const [owner,mask] of [['left_arm',auth.left],['right_arm',auth.right]]){
  let pixels=0,sourceVsBaselineL1=0,sourceContrastEdges=0,protectedContacts=0;
  const rgb=new Uint8Array(auth.byOwner[owner]*3);let at=0;
  for(let i=0;i<n;i++)if(mask[i]){
   const x=i%width,y=Math.floor(i/width),p=i*4;pixels++;
   for(let c=0;c<3;c++){rgb[at++]=originalRgba[p+c];sourceVsBaselineL1+=Math.abs(originalRgba[p+c]-baselineRgba[p+c]);}
   for(const j of [x+1<width?i+1:-1,y+1<height?i+width:-1])if(j>=0){if(mask[j]){
    let delta=0;for(let c=0;c<3;c++)delta+=Math.abs(originalRgba[p+c]-originalRgba[j*4+c]);if(delta>=90)sourceContrastEdges++;
   }else if(faceMask[j]||backgroundMask[j]||originalRgba[j*4+3]!==255)protectedContacts++;}
  }
  zones.push({owner,pixels,sourceVsBaselineL1,sourceContrastEdges,protectedContacts,rgb,
   sourceMaskSha256:await hash(mask),sourceMask:mask});
 }
 return {version:VERSION,width,height,originalRgba,originalSha256,baselineSha256,eligiblePixels:auth.eligiblePixels,excluded:{face:auth.excludedFace,background:auth.excludedBackground,alpha:auth.excludedAlpha},zones,
  independentAnatomicalPixels:0,anatomyApproved:false,originalOnly:true,productPaintAuthorized:false,productionReleaseAuthorized:false};
}
