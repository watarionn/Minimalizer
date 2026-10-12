/** Stage50: objective source/frozen-Public difference inventory, NOT semantic judgement.
 * Background is a separate UNSIGNED observation, not an independent foreground truth.
 */
export const VERSION='p0-stage50-original-vs-frozen-public-rgb-ledger-v1';
const fail=s=>{throw new TypeError(s);};
const rx=/^[a-f0-9]{64}$/;
async function pin(bytes,hash,label){if(!(bytes instanceof Uint8Array||bytes instanceof Uint8ClampedArray)||!rx.test(hash||'')||!globalThis.crypto?.subtle)fail('INVALID_'+label);const s=[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');if(s!==hash)fail(label+'_SHA_MISMATCH');}
export async function inventorySourceFidelity({width,height,sourceRgba,sourceSha256,baselineRgba,baselineSha256,leftArmMask,leftSha256,rightArmMask,rightSha256,faceMask,faceSha256,observedBackground,backgroundSha256}){
 const n=width*height;
 if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||sourceRgba?.length!==4*n||baselineRgba?.length!==4*n)fail('INVALID_IMAGE_DIMENSIONS');
 const input=[['SOURCE',sourceRgba,sourceSha256],['BASELINE',baselineRgba,baselineSha256],['LEFT',leftArmMask,leftSha256],['RIGHT',rightArmMask,rightSha256],['FACE',faceMask,faceSha256],['BACKGROUND',observedBackground,backgroundSha256]];
 for(const [k,v,h] of input){if(k!=='SOURCE'&&k!=='BASELINE'&&v?.length!==n)fail('INVALID_MASK_DIMENSIONS');await pin(v,h,k);}
 const zones={visibleHistoricalArms:{pixels:0,rgbDifferent:0,l1:0},protectedFace:{pixels:0,rgbDifferent:0,l1:0},observedBackground:{pixels:0,rgbDifferent:0,l1:0},other:{pixels:0,rgbDifferent:0,l1:0}};
 for(let i=0;i<n;i++){
  for(const mask of [leftArmMask,rightArmMask,faceMask,observedBackground])if(mask[i]!==0&&mask[i]!==255)fail('NONBINARY_OBSERVATION');
  if(leftArmMask[i]&&rightArmMask[i])fail('HISTORIC_OWNER_OVERLAP');
  const group=faceMask[i]?'protectedFace':observedBackground[i]?'observedBackground':(leftArmMask[i]||rightArmMask[i])?'visibleHistoricalArms':'other';
  const a=zones[group];a.pixels++;let d=0;for(let c=0;c<3;c++)d+=Math.abs(sourceRgba[4*i+c]-baselineRgba[4*i+c]);a.l1+=d;if(d)a.rgbDifferent++;
 }
 return {version:VERSION,width,height,zones,accountedPixels:Object.values(zones).reduce((s,x)=>s+x.pixels,0),
  originalSourceRgbaSha256:sourceSha256,frozenBaselineSha256:baselineSha256,
  backgroundIndependentTruth:false,measuresVisualQuality:false,independentSemanticLabels:0,
  candidatePaintAuthorized:false,productionReleaseAuthorized:false};
}
