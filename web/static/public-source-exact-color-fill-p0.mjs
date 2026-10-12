/** Stage73–74: exact source-observed medoid-color rectangle fill diagnostic.
 * Competes with Stage68 butt strokes on actual SVG bytes, NEVER counts stroke
 * endpoints as polygon vertices or promotes historic owner masks to anatomy.
 */
import {encodeSourcePaletteSvg} from './public-source-palette-svg-p0.mjs';
import {exactSourceRectangleCover} from './public-source-exact-rect-cover-p0.mjs';
export const VERSION='p0-stage73-source-color-compact-fill-preview-v1';
const fail=s=>{throw new TypeError(s)};
const rgbHex=c=>'#'+c.map(v=>v.toString(16).padStart(2,'0')).join('');
const utf8=s=>new TextEncoder().encode(s).length;
const typed=a=>a instanceof Uint8Array||a instanceof Uint8ClampedArray;
function rectangles(mask,w,h,axis){
 if(axis==='vertical')return exactSourceRectangleCover({width:w,height:h,sourceMask:mask}).rectangles;
 const tr=new Uint8Array(mask.length);
 for(let y=0;y<h;y++)for(let x=0;x<w;x++)tr[x*h+y]=mask[y*w+x];
 return exactSourceRectangleCover({width:h,height:w,sourceMask:tr}).rectangles.map(([y0,x0,y1,x1])=>[x0,y0,x1,y1]);
}
function geometryPath(rects){
 return rects.map(([x0,y0,x1,y1])=>`M${x0} ${y0}h${x1-x0}v${y1-y0}h-${x1-x0}Z`).join('');
}
function checkLayerSource({layerMask,rects,width,height}){
 const n=width*height,replay=new Uint8Array(n);let area=0;
 for(const q of rects){
  if(!Array.isArray(q)||q.length!==4||q.some(v=>!Number.isSafeInteger(v)))fail('NONINTEGER_SOURCE_FILL_RECT');
  const [x0,y0,x1,y1]=q;
  if(x0<0||y0<0||x1>width||y1>height||x0>=x1||y0>=y1)fail('OUTSIDE_SOURCE_FILL_RECT');
  for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){const i=y*width+x;if(replay[i])fail('OVERLAPPING_SOURCE_FILL_RECT');replay[i]=255;area++;}
 }
 for(let i=0;i<n;i++)if(replay[i]!==layerMask[i])fail('SOURCE_FILL_PIXELS_DIFFER');
 return area;
}
function partitionLayers({width,height,ownerMask,assignments,palette}){
 const n=width*height,layers=palette.map(()=>new Uint8Array(n));let k=0;
 for(let i=0;i<n;i++)if(ownerMask[i]){
  const v=assignments[k++];if(v>=palette.length)fail('SOURCE_FILL_BAD_ASSIGNMENT');layers[v][i]=255;
 }
 if(k!==assignments.length)fail('SOURCE_FILL_PARTITION_COUNT');
 return layers;
}
export async function buildExactSourceColorFill(input){
 // Stage68 guards the independently provided owner/source SHA and every RGB medoid.
 const baseline=await encodeSourcePaletteSvg(input);
 const {width,height,ownerMask,assignments,palette}=input;
 const layers=partitionLayers({width,height,ownerMask,assignments,palette});
 const rows=[];let paths='',rectCount=0,observed=0;
 for(let j=0;j<layers.length;j++){
  const mask=layers[j],pixels=mask.reduce((a,v)=>a+(v===255),0);
  if(!pixels)continue;
  const variants=['vertical','horizontal'].map(axis=>{
   const rects=rectangles(mask,width,height,axis);return {axis,rects,path:geometryPath(rects)};
  });
  variants.sort((a,b)=>utf8(a.path)-utf8(b.path)||a.rects.length-b.rects.length|| (a.axis==='vertical'?-1:1));
  const best=variants[0];if(checkLayerSource({layerMask:mask,rects:best.rects,width,height})!==pixels)fail('SOURCE_FILL_AREA_MISMATCH');
  rectCount+=best.rects.length;observed+=pixels;
  paths+=`<path d="${best.path}" fill="${rgbHex(palette[j])}"/>`;
  rows.push({layer:j,rgb:rgbHex(palette[j]),sourcePixels:pixels,rectangles:best.rects,axis:best.axis,
   explicitRectangleVertices:best.rects.length*4,pathBytes:utf8(best.path)});
 }
 if(observed!==baseline.sourcePixels)fail('SOURCE_FILL_TOTAL_MISMATCH');
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">${paths}</svg>`;
 const svgBytes=utf8(svg);
 return {version:VERSION,width,height,sourcePixels:observed,
  originalOwnerSha256:baseline.sourceOwnerSha256,originalRgbaSha256:baseline.sourceRgbaSha256,
  layers:rows,rectangleCount:rectCount,explicitRectangleVertices:rectCount*4,
  fillSvg:svg,fillSvgBytes:svgBytes,stage68StrokeSvgBytes:baseline.svgBytes,
  stage68StrokeSegments:baseline.strokeCount,
  byteReductionVsStroke:baseline.svgBytes-svgBytes,
  fillSmallerThanStroke:svgBytes<baseline.svgBytes,
  adoptedForProduct:false,semanticTruthEstablished:false,fullCharacterVertexBudgetMet:false,
  realBrowserDprParityVerified:false,sourceMembershipAlgebraicallyExact:true,
  status:'PRIVATE_SOURCE_FILL_DIAGNOSTIC_HOLD'};
}
/** Stage74: derive anew from independently supplied source, require byte and footprint identity. */
export async function verifyExactSourceColorFill({candidate,...input}){
 if(!candidate||candidate.version!==VERSION||typeof candidate.fillSvg!=='string')fail('INVALID_SOURCE_FILL_CANDIDATE');
 const fresh=await buildExactSourceColorFill(input);
 if(candidate.fillSvg!==fresh.fillSvg||candidate.fillSvgBytes!==fresh.fillSvgBytes||
 candidate.originalOwnerSha256!==fresh.originalOwnerSha256||
 candidate.originalRgbaSha256!==fresh.originalRgbaSha256||
 candidate.rectangleCount!==fresh.rectangleCount||
 candidate.explicitRectangleVertices!==fresh.explicitRectangleVertices||
 candidate.sourcePixels!==fresh.sourcePixels||
 candidate.fillSmallerThanStroke!==fresh.fillSmallerThanStroke)fail('SOURCE_FILL_REPLAY_MISMATCH');
 const layers=partitionLayers(input);let whole=new Uint8Array(input.width*input.height),painted=0;
 if(!Array.isArray(candidate.layers)||candidate.layers.length!==fresh.layers.length)fail('SOURCE_FILL_LAYER_TAMPERED');
 for(let j=0;j<candidate.layers.length;j++){
  const t=candidate.layers[j],expected=fresh.layers[j];
  if(JSON.stringify(t)!==JSON.stringify(expected))fail('SOURCE_FILL_LAYER_TAMPERED');
  const layerMask=layers[t.layer];painted+=checkLayerSource({layerMask,rects:t.rectangles,width:input.width,height:input.height});
  for(let i=0;i<whole.length;i++)if(layerMask[i]){if(whole[i])fail('COLOR_LAYERS_OVERLAP');whole[i]=255;}
 }
 for(let i=0;i<whole.length;i++)if(whole[i]!==input.ownerMask[i])fail('OWNER_FILL_FOOTPRINT_CHANGED');
 if(painted!==fresh.sourcePixels)fail('SOURCE_FILL_TOTAL_MISMATCH');
 return {version:VERSION,originalOwnerSha256:fresh.originalOwnerSha256,
  originalRgbaSha256:fresh.originalRgbaSha256,sourcePixels:painted,
  fillSvgBytes:fresh.fillSvgBytes,stage68StrokeSvgBytes:fresh.stage68StrokeSvgBytes,
  explicitRectangleVertices:fresh.explicitRectangleVertices,
  rasterSourceMembershipExact:true,independentReviewPixels:0,releaseAuthorized:false,
  status:'SOURCE_FILL_REPLAY_PASS_GOLDEN_HOLD'};
}
