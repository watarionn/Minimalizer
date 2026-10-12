/** Stage14: independent source-only SVG browser parity proof at DPR1 + DPR2.
 * A candidate path passing 340px may bleed at 680px from antialiasing.
 * Reject ANY coverage loss or painted pixels not represented by source mask.
 */
export const VERSION='structural-p0-stage14-svg-dpr-source-mask-guard-v1';
const typed=a=>a instanceof Uint8Array||a instanceof Uint8ClampedArray;
const bad=s=>{throw new TypeError(s);};
export function evaluateSvgSourceParity({width,height,sourceMask,renderedAlpha340,renderedAlpha680}){
 const n=width*height;if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||
 !typed(sourceMask)||sourceMask.length!==n||!typed(renderedAlpha340)||renderedAlpha340.length!==n||
 !typed(renderedAlpha680)||renderedAlpha680.length!==n*4)bad('INVALID_SVG_DPR_INPUT');
 let mismatch340=0,mismatch680=0,spill340=0,spill680=0,under340=0,under680=0,observed=0,aa340=0,aa680=0;
 for(let i=0;i<n;i++){
  const s=sourceMask[i];if(s!==0&&s!==255)bad('SOURCE_MASK_NONBINARY');
  if(s)observed++;
  const p=renderedAlpha340[i],match=(p===255)===(s===255);if(!match)mismatch340++;
  if(p&&s===0)spill340++;if(!p&&s)under340++;if(p&&p!==255)aa340++;
  const x=i%width,y=Math.floor(i/width);
  for(let dy=0;dy<2;dy++)for(let dx=0;dx<2;dx++){
   const j=(y*2+dy)*(width*2)+x*2+dx,a=renderedAlpha680[j];
   if((a===255)!==(s===255))mismatch680++;
   if(a&&s===0)spill680++;if(!a&&s)under680++;if(a&&a!==255)aa680++;
  }
 }
 const allExact=mismatch340===0&&mismatch680===0&&spill340===0&&spill680===0&&
 under340===0&&under680===0&&aa340===0&&aa680===0;
 return {version:VERSION,sourcePixels:observed,mismatch340,mismatch680,spill340,spill680,
 under340,under680,antialias340:aa340,antialias680:aa680,
 exact340and680:allExact,productPromotionAuthorized:false,
 humanGoldenApproved:false,fullCharacterSvgVerified:false};
}
