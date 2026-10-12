/** Stage68: data-only, source-pinned colored stroke SVG for historic owner candidate pixels.
 * PRIVATE visual research, never approval to use these historical owner labels for anatomy.
 */
import {buildSourceStrokeCover} from './public-source-stroke-cover-p0.mjs';
export const VERSION='p0-stage68-source-color-stroke-preview-v1';
const fail=x=>{throw new TypeError(x)};
const typed=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const SHA=/^[a-f0-9]{64}$/;
const toHex=rgb=>'#'+rgb.map(x=>x.toString(16).padStart(2,'0')).join('');
const hex=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
export async function encodeSourcePaletteSvg({width,height,ownerMask,ownerSha256,sourceRgba,sourceSha256,palette,assignments}){
 const n=width*height;if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||!typed(ownerMask)||ownerMask.length!==n||!typed(sourceRgba)||sourceRgba.length!==n*4||!SHA.test(ownerSha256||'')||!SHA.test(sourceSha256||'')||!Array.isArray(palette)||!palette.length||palette.length>16||!typed(assignments)||!crypto?.subtle)fail('INVALID_COLOR_SVG_INPUT');
 if(await hex(ownerMask)!==ownerSha256||await hex(sourceRgba)!==sourceSha256)fail('COLOR_SVG_SHA_MISMATCH');
 const layers=palette.map(()=>new Uint8Array(n));let k=0;
 for(let i=0;i<n;i++){if(ownerMask[i]!==0&&ownerMask[i]!==255)fail('NONBINARY_SVG_OWNER');if(ownerMask[i]){if(sourceRgba[i*4+3]!==255)fail('COLOR_SVG_ALPHA_OWNER');const j=assignments[k++];if(j>=palette.length)fail('INVALID_COLOR_SVG_ASSIGNMENT');layers[j][i]=255;}}
 if(k!==assignments.length)fail('COLOR_SVG_PARTITION_SIZE');
 // Verify every provided palette color occurs in the selected original pixels.
 const observedColors=new Set();for(let i=0;i<n;i++)if(ownerMask[i])observedColors.add(`${sourceRgba[i*4]},${sourceRgba[i*4+1]},${sourceRgba[i*4+2]}`);
 for(const c of palette)if(!Array.isArray(c)||c.length!==3||c.some(x=>!Number.isInteger(x)||x<0||x>255)||!observedColors.has(c.join(',')))fail('UNOBSERVED_SOURCE_COLOR');
 const rows=[];let strokeCount=0,paths='',observed=0;
 for(let j=0;j<layers.length;j++){
  const color=palette[j];if(!Array.isArray(color)||color.length!==3||color.some(x=>!Number.isInteger(x)||x<0||x>255))fail('INVALID_COLOR_SVG_PALETTE');
  let pixels=0;for(const v of layers[j])if(v)pixels++;
  if(!pixels)continue;
  const cover=await buildSourceStrokeCover({width,height,sourceMask:layers[j],sourceMaskSha256:await hex(layers[j])});
  const sourceText=cover.svgPaths;if(sourceText.includes('<image')||sourceText.includes('<script'))fail('UNTRUSTED_COLOR_STROKES');
  const colorHex=toHex(color);
  paths+=sourceText.replaceAll('stroke="#000"',`stroke="${colorHex}"`);
  if(!paths.includes(colorHex))fail('COLOR_STROKE_ENCODING_FAIL');
  observed+=pixels;strokeCount+=cover.strokeCount;
  rows.push({layer:j,rgb:colorHex,sourcePixels:pixels,strokeCount:cover.strokeCount,orientation:cover.orientation});
 }
 if(observed!==k)fail('COLOR_SVG_COVERAGE_MISMATCH');
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">${paths}</svg>`;
 return {version:VERSION,width,height,sourcePixels:k,layers:rows,strokeCount,svg,svgBytes:new TextEncoder().encode(svg).length,sourceOwnerSha256:ownerSha256,sourceRgbaSha256:sourceSha256,backgroundTransparent:true,productionReleaseAuthorized:false,independentSemanticApproval:false,wholeSceneVertexBudgetMet:false};
}
