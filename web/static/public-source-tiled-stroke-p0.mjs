/** Stage57: locally choose horizontal/vertical source-exact strokes by disjoint tiles.
 * Research encoding, not a trusted anatomical mask nor permission to paint.
 */
import {buildSourceStrokeCover} from './public-source-stroke-cover-p0.mjs';
export const VERSION='p0-stage57-source-tiled-strokes-v1';
const fail=s=>{throw new TypeError(s);};
const typed=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const shaRx=/^[0-9a-f]{64}$/;
async function sha(x){if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');return [...new Uint8Array(await crypto.subtle.digest('SHA-256',x))].map(x=>x.toString(16).padStart(2,'0')).join('');}
function asSvg(strokes){
 const groups=new Map();
 for(const s of strokes){const d=s.axis==='vertical'?`M${s.a[0]} ${s.a[1]}V${s.b[1]}`:`M${s.a[0]} ${s.a[1]}H${s.b[0]}`;const k=`${s.axis}|${s.width}`;if(!groups.has(k))groups.set(k,[]);groups.get(k).push(d);}
 return [...groups.entries()].sort((a,b)=>a[0].localeCompare(b[0])).map(([key,paths])=>{const width=key.split('|')[1];return `<path d="${paths.join('')}" fill="none" stroke="#000" stroke-width="${width}" stroke-linecap="butt"/>`;}).join('');
}
export async function buildSourceTiledStrokeCandidate({width,height,sourceMask,sourceMaskSha256,tileSize=32,strictStrokeLimit=40000}){
 const n=width*height;
 if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||!typed(sourceMask)||sourceMask.length!==n||!shaRx.test(sourceMaskSha256||'')||![8,16,32,64,128].includes(tileSize)||!Number.isInteger(strictStrokeLimit)||strictStrokeLimit<1||strictStrokeLimit>40000)fail('INVALID_TILED_SOURCE');
 if(await sha(sourceMask)!==sourceMaskSha256)fail('TILED_SOURCE_SHA_MISMATCH');
 let count=0;for(const v of sourceMask){if(v!==0&&v!==255)fail('NONBINARY_TILED_SOURCE');if(v)count++;}
 if(!count)fail('EMPTY_TILED_SOURCE');
 const global=await buildSourceStrokeCover({width,height,sourceMask,sourceMaskSha256,maxStrokes:strictStrokeLimit});
 const strokes=[],tiles=[];let tileCovered=0;
 for(let y0=0;y0<height;y0+=tileSize)for(let x0=0;x0<width;x0+=tileSize){
  const tw=Math.min(tileSize,width-x0),th=Math.min(tileSize,height-y0);const mask=new Uint8Array(tw*th);let positive=0;
  for(let y=0;y<th;y++)for(let x=0;x<tw;x++){const v=sourceMask[(y+y0)*width+x+x0];mask[y*tw+x]=v;if(v)positive++;}
  if(!positive)continue;
  const local=await buildSourceStrokeCover({width:tw,height:th,sourceMask:mask,sourceMaskSha256:await sha(mask),maxStrokes:strictStrokeLimit});
  const shifted=local.strokes.map(s=>({...s,x0:s.x0+x0,x1:s.x1+x0,y0:s.y0+y0,y1:s.y1+y0,a:[s.a[0]+x0,s.a[1]+y0],b:[s.b[0]+x0,s.b[1]+y0]}));
  strokes.push(...shifted);if(strokes.length>strictStrokeLimit)fail('TILED_STROKE_LIMIT_EXCEEDED');
  tiles.push({x0,y0,tw,th,axis:local.orientation,sourcePixels:positive,strokeCount:shifted.length});tileCovered+=positive;
 }
 if(tileCovered!==count)fail('TILED_SOURCE_COVERAGE_MISMATCH');
 const chooseTiled=strokes.length<global.strokeCount;
 const selected=chooseTiled?strokes:global.strokes;
 return {version:VERSION,width,height,sourceMaskSha256,sourcePixels:count,tiles,globalStrokeCount:global.strokeCount,tiledStrokeCount:strokes.length,selectedStrokeCount:selected.length,selectedMode:chooseTiled?'tiled':'global',strokes:selected,svgPaths:chooseTiled?asSvg(strokes):global.svgPaths,
 endpointCount:selected.length*2,rectangleEquivalentVertexCount:selected.length*4,
 originalMaskUnmodified:true,sourcePixelExactAlgebraic:false,independentBrowserVerified:false,
 identityOrAnatomyVerified:false,paintAuthorized:false,productionReleaseAuthorized:false};
}
