/** P0 Stage18: replay externally SOURCE-OBSERVED macro-color partitions inside
 * historically signed visible owners. Each color is a medoid of ORIGINAL pixels.
 * No anatomy/skin/sleeve guessing; MSE-only results are never semantic approval.
 */
export const VERSION='structural-p0-stage18-source-owned-color-masses-v1';
const typed=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const fail=x=>{throw new TypeError(x);};
const shaPattern=/^[0-9a-f]{64}$/;
async function sha(bytes){if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');}
const loss=(a,b,at)=>{let s=0;for(let k=0;k<3;k++)s+=(a[at+k]-b[at+k])**2;return s;};
function colorMedoid(original,indices){const cs=[[],[],[]];for(const i of indices)for(let k=0;k<3;k++)cs[k].push(original[i*4+k]);const mid=cs.map(v=>{v.sort((a,b)=>a-b);return (v[(v.length-1)>>1]+v[v.length>>1])/2;});let b=Infinity,result=null;for(const i of indices){const c=[original[i*4],original[i*4+1],original[i*4+2]],d=c.reduce((sum,v,k)=>sum+(v-mid[k])**2,0);if(d<b){b=d;result=c;}}return result;}
export async function replaySourceOwnedColorMasses({width,height,originalRgba,originalSha256,
  frozenRgba,frozenSha256,visibleOwners,partitions,minPartitionPixels=60,maxChangedPixels=18000}){
 const n=width*height;if(!Number.isInteger(n)||n<1||n>160000||!typed(originalRgba)||!typed(frozenRgba)||originalRgba.length!==4*n||frozenRgba.length!==4*n)fail('INVALID_INPUT');
 if(!shaPattern.test(originalSha256||'')||!shaPattern.test(frozenSha256||'')||await sha(originalRgba)!==originalSha256||await sha(frozenRgba)!==frozenSha256)fail('SOURCE_BASELINE_SHA_MISMATCH');
 if(!Array.isArray(visibleOwners)||!visibleOwners.length||!Array.isArray(partitions)||!partitions.length||partitions.length>32)fail('INVALID_EVIDENCE');
 if(!Number.isInteger(minPartitionPixels)||minPartitionPixels<20||!Number.isInteger(maxChangedPixels)||maxChangedPixels<0||maxChangedPixels>n)fail('INVALID_BUDGET');
 const owners=new Map();const available=new Uint8Array(n);
 for(const o of visibleOwners){if(!o||typeof o.role!=='string'||owners.has(o.role)||!typed(o.visibleMask)||o.visibleMask.length!==n)fail('INVALID_OWNER');owners.set(o.role,o.visibleMask);for(let i=0;i<n;i++){if(o.visibleMask[i]!==0&&o.visibleMask[i]!==255)fail('NONBINARY_OWNER');if(o.visibleMask[i]){if(available[i])fail('OVERLAPPING_VISIBLE_OWNERS');available[i]=255;}}}
 const output=new Uint8ClampedArray(frozenRgba),already=new Uint8Array(n),ids=new Set(),results=[];let changed=0;
 for(const p of partitions){
  if(!p||typeof p.id!=='string'||!/^[a-z][a-z0-9_-]{0,47}$/.test(p.id)||ids.has(p.id)||!owners.has(p.parentRole)||p.evidenceLevel!=='source_color_observation'||!p.evidenceRef||!typed(p.mask)||p.mask.length!==n||!shaPattern.test(p.maskSha256||''))fail('INVALID_PARTITION_AUTHORITY');
  ids.add(p.id);if(await sha(p.mask)!==p.maskSha256)fail('PARTITION_SHA_MISMATCH');
  const indices=[];for(let i=0;i<n;i++){
    if(p.mask[i]!==0&&p.mask[i]!==255)fail('NONBINARY_PARTITION');if(!p.mask[i])continue;
    if(!owners.get(p.parentRole)[i]||!available[i]||already[i])fail('PARTITION_OUTSIDE_SIGNED_OWNER_OR_OVERLAP');
    if(originalRgba[i*4+3]!==255||frozenRgba[i*4+3]!==255)fail('SOURCE_ALPHA_NOT_OPAQUE');
    indices.push(i);
  }
  if(indices.length<minPartitionPixels||indices.length>n/3)fail('PARTITION_BUDGET');
  const col=colorMedoid(originalRgba,indices);
  let before=0,after=0;
  for(const i of indices){const k=i*4;before+=loss(originalRgba,frozenRgba,k);
    for(let j=0;j<3;j++)after+=(originalRgba[k+j]-col[j])**2;}
  const accepted=after<before*.99;
  if(accepted){for(const i of indices){const o=i*4;
     if(output[o]!==col[0]||output[o+1]!==col[1]||output[o+2]!==col[2])changed++;
     output[o]=col[0];output[o+1]=col[1];output[o+2]=col[2];}}
  for(const i of indices)already[i]=255;
  results.push({id:p.id,parentRole:p.parentRole,pixels:indices.length,sourcePixelMedoid:col,
   sourceRgbErrorBefore:before,sourceRgbErrorAfter:after,acceptedAsPreview:accepted,
   candidateSemanticApproved:false});
 }
 if(changed>maxChangedPixels)fail('CHANGED_PIXEL_BUDGET');
 for(let i=0;i<n;i++){const k=i*4;if(output[k+3]!==frozenRgba[k+3])throw Error('ALPHA_MUTATION');
  if((!already[i]||!available[i])&&(output[k]!==frozenRgba[k]||output[k+1]!==frozenRgba[k+1]||output[k+2]!==frozenRgba[k+2]))throw Error('OUTSIDE_SOURCE_OWNER');}
 return {rgba:output,audit:{version:VERSION,changedPixels:changed,partitions:results,
  sourcePaletteOnly:true,semanticClassApproval:false,sourceAbsentChangedPixels:0,
  productPromotionAuthorized:false,previewOnly:true}};
}
