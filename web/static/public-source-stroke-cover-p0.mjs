/** Stage52: lossless vector encoding of SHA-pinned source-observed binary masks.
 * SVG stroke paths replace exact rectangular pixels, NOT original colors or anatomy.
 * Every stroke footprint must pass independent 340/680 browser pixel verification.
 * Endpoint count is a different metric from actual polygon vertices: NEVER
 * claim Stage8 SVG vertex cap passes on endpoints alone.
 */
import {exactSourceRectangleCover} from './public-source-exact-rect-cover-p0.mjs';
export const VERSION='p0-stage52-exact-source-stroke-cover-v1';
const fail=code=>{throw new TypeError(code);};
const SHA=/^[0-9a-f]{64}$/;
const typed=a=>a instanceof Uint8Array||a instanceof Uint8ClampedArray;
const scalar=n=>Number.isInteger(n)&&n>0&&n<=1600;
const str=n=>Number.isInteger(n)?String(n):String(n); // .5 centers never require rounding
async function digest(bytes){if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');const sha=await globalThis.crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(sha)].map(x=>x.toString(16).padStart(2,'0')).join('');}
function sourceRects(mask,width,height,orientation){
 if(orientation==='vertical')return exactSourceRectangleCover({width,height,sourceMask:mask}).rectangles;
 // Transpose source to discover broader vertical runs in the original image.
 const transposed=new Uint8Array(mask.length);
 for(let y=0;y<height;y++)for(let x=0;x<width;x++)transposed[x*height+y]=mask[y*width+x];
 return exactSourceRectangleCover({width:height,height:width,sourceMask:transposed}).rectangles.map(([a,b,c,d])=>[b,a,d,c]);
}
function toStrokes(rectangles,orientation){return rectangles.map(([x0,y0,x1,y1])=>{
 const width=x1-x0,height=y1-y0;
 return orientation==='vertical'
 ?{x0,y0,x1,y1,width,axis:'vertical',a:[x0+width/2,y0],b:[x0+width/2,y1]}
 :{x0,y0,x1,y1,width:height,axis:'horizontal',a:[x0,y0+height/2],b:[x1,y0+height/2]};
 });}
function svgGrouped(strokes){
 const groups=new Map();for(const s of strokes){const path=`M${str(s.a[0])} ${str(s.a[1])}${s.axis==='vertical'?'V':'H'}${str(s.axis==='vertical'?s.b[1]:s.b[0])}`;
  if(!groups.has(s.width))groups.set(s.width,[]);groups.get(s.width).push(path);}
 return [...groups.entries()].sort((a,b)=>a[0]-b[0]).map(([width,paths])=>`<path d="${paths.join('')}" fill="none" stroke="#000" stroke-width="${width}" stroke-linecap="butt"/>`).join('');
}
export async function buildSourceStrokeCover({width,height,sourceMask,sourceMaskSha256,orientation='best',maxStrokes=40000}){
 if(!scalar(width)||!scalar(height)||width*height>160000||!typed(sourceMask)||sourceMask.length!==width*height||!SHA.test(sourceMaskSha256||'')||!['best','vertical','horizontal'].includes(orientation)||!Number.isInteger(maxStrokes)||maxStrokes<1||maxStrokes>40000)fail('INVALID_SOURCE_STROKE_INPUT');
 if(await digest(sourceMask)!==sourceMaskSha256)fail('SOURCE_STROKE_MASK_SHA_MISMATCH');
 let positive=0;for(const a of sourceMask){if(a!==0&&a!==255)fail('NONBINARY_STROKE_SOURCE');if(a)positive++;}
 if(positive===0)fail('EMPTY_SOURCE_STROKE');
 const cands=(orientation==='best'?['vertical','horizontal']:[orientation]).map(axis=>({axis,strokes:toStrokes(sourceRects(sourceMask,width,height,axis),axis)}));
 cands.sort((a,b)=>a.strokes.length-b.strokes.length|| (a.axis==='vertical'?-1:1));
 const chosen=cands[0];if(chosen.strokes.length>maxStrokes)fail('STROKE_SOURCE_BUDGET_EXCEEDED');
 const sum=chosen.strokes.reduce((n,s)=>n+(s.x1-s.x0)*(s.y1-s.y0),0);
 if(sum!==positive)fail('STROKE_SOURCE_COVERAGE_MISMATCH');
 const svgPaths=svgGrouped(chosen.strokes);
 return {version:VERSION,width,height,maskSha256:sourceMaskSha256,orientation:chosen.axis,
  observedPixels:positive,strokes:chosen.strokes,strokeCount:chosen.strokes.length,
  endpointCount:2*chosen.strokes.length,rectangleEquivalentVertices:4*chosen.strokes.length,
  svgPaths,sourceMaskCoverageAlgebraic:true,
  browserDpr1Verified:false,browserDpr2Verified:false,
  endpointCostComparableToPolygonVertexBudget:false,
  sourceSemanticTruthVerified:false,paintAuthorized:false,releaseApproved:false,productPromotionAuthorized:false};
}
export function renderStrokeCoverSvg(cover){
 if(!cover||cover.version!==VERSION||!scalar(cover.width)||!scalar(cover.height)||typeof cover.svgPaths!=='string'||!/^<path\b/.test(cover.svgPaths))fail('INVALID_SOURCE_STROKE_COVER');
 if(!['vertical','horizontal'].includes(cover.orientation)||!Array.isArray(cover.strokes)||!cover.strokes.length||cover.strokes.length>40000||cover.endpointCount!==2*cover.strokes.length)fail('INVALID_SOURCE_STROKE_COVER');
 for(const s of cover.strokes){if(!s||s.axis!==cover.orientation||!Array.isArray(s.a)||!Array.isArray(s.b)||s.a.length!==2||s.b.length!==2||![s.x0,s.x1,s.y0,s.y1,s.width,...s.a,...s.b].every(Number.isFinite)||s.x0<0||s.y0<0||s.x1>cover.width||s.y1>cover.height||s.x0>=s.x1||s.y0>=s.y1||s.width<=0||s.width>1600)fail('INVALID_SOURCE_STROKE_COVER');
   const expected=s.axis==='vertical'?{a:[s.x0+(s.x1-s.x0)/2,s.y0],b:[s.x0+(s.x1-s.x0)/2,s.y1],width:s.x1-s.x0}:{a:[s.x0,s.y0+(s.y1-s.y0)/2],b:[s.x1,s.y0+(s.y1-s.y0)/2],width:s.y1-s.y0};
   if(s.width!==expected.width||JSON.stringify(s.a)!==JSON.stringify(expected.a)||JSON.stringify(s.b)!==JSON.stringify(expected.b))fail('INVALID_SOURCE_STROKE_COVER');
 }
 const actual=svgGrouped(cover.strokes);if(actual!==cover.svgPaths)fail('UNTRUSTED_SVG_SOURCE');
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${cover.width} ${cover.height}" width="${cover.width}" height="${cover.height}">${actual}</svg>`;
}
