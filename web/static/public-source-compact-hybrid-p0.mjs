/** Stage80: lossless source-only color-layer SVG geometry competition.
 * Compare exact-fill rectangles against closed, evenodd source-pixel contours.
 * Never simplify pixels or treat byte savings as passed full-body shape budget.
 * Fail closed for tampered source; unsupported contour layers fall back to
 * independently raster-audited exact rectangles, never inventing geometry.
 */
import {buildExactSourceColorFill} from './public-source-exact-color-fill-p0.mjs';
import {traceSourceContours} from './public-source-contour-p0.mjs';
export const VERSION='p0-stage80-source-color-hybrid-contour-fill-hold-v1';
const fail=s=>{throw new TypeError(s)};
const digest=async x=>[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',x))].map(v=>v.toString(16).padStart(2,'0')).join('');
const size=s=>new TextEncoder().encode(s).length;
const toPath=rects=>rects.map(([x0,y0,x1,y1])=>`M${x0} ${y0}h${x1-x0}v${y1-y0}h-${x1-x0}Z`).join('');
/** Serialize literal orthogonal pixel-edge contours without point movement.
 * A Z always closes the final observed edge; holes use SVG evenodd.
 */
const orthogonalRingPath=rings=>rings.map(points=>{
 if(!Array.isArray(points)||points.length<4)fail('INVALID_ORTHOGONAL_RING');
 let d='M'+points[0][0]+' '+points[0][1];
 for(let i=1;i<points.length;i++){
  const [x,y]=points[i],[px,py]=points[i-1];
  if(x!==px&&y!==py||x===px&&y===py)fail('NONORTHOGONAL_SOURCE_EDGE');
  const absolute=x===px?'V'+y:'H'+x,relative=x===px?'v'+(y-py):'h'+(x-px);
  d+=size(absolute)<=size(relative)?absolute:relative;
 }
 const [x,y]=points.at(-1),[x0,y0]=points[0];
 if(x!==x0&&y!==y0)fail('NONORTHOGONAL_CLOSING_EDGE');
 return d+'Z';
}).join('');
function layersFromAssignments({width,height,ownerMask,palette,assignments}){
 const out=palette.map(()=>new Uint8Array(width*height));let k=0;
 for(let i=0;i<ownerMask.length;i++)if(ownerMask[i])out[assignments[k++]][i]=255;
 if(k!==assignments.length)fail('COMPACT_HYBRID_ASSIGNMENT_COUNT');
 return out;
}
export async function buildSourceCompactHybridSvg(input){
 // SHA, original RGB medoid and disjoint source-coverage authority comes from Stage73.
 const baseline=await buildExactSourceColorFill(input);
 const layers=layersFromAssignments(input);
 let paths='',explicitVertices=0,contourCount=0,rectCount=0,observed=0,contourFallbacks=0;
 const chosen=[];
 for(const r of baseline.layers){
  const mask=layers[r.layer],hex=r.rgb;
  const rectPath=toPath(r.rectangles),rectFragment=`<path d="${rectPath}" fill="${hex}"/>`;
  let best={method:'source_exact_rect_fill',fragment:rectFragment,vertices:r.explicitRectangleVertices,
   pathBytes:size(rectPath),rectangles:r.rectangles.length,contourRings:0};
  // The Stage12 tracer internally SHA-pins its supplied mask and scanline-rasterizes rings.
  // Tiny or too-complex observations simply retain Stage73's already-validated exact fill.
  if(r.sourcePixels>=20){
   try{
    const traced=await traceSourceContours({width:input.width,height:input.height,
     faceMask:new Uint8Array(input.width*input.height),features:[{id:'color_observation',mask,
     maskSha256:await digest(mask),evidenceLevel:'research_observation',evidenceRef:'source_color_layer_sha256'}],
     maxVertices:20000});
    const contour=traced.parts[0];
    const compactD=orthogonalRingPath(contour.rings);
    const fragment=`<path d="${compactD}" fill="${hex}" fill-rule="evenodd"/>`;
    if(contour.observedPixels!==r.sourcePixels||contour.coveredPixels!==r.sourcePixels)fail('HYBRID_CONTOUR_SOURCE_MISMATCH');
    if(size(fragment)<size(best.fragment))best={method:'exact_source_contour',fragment,vertices:contour.vertexCount,
     pathBytes:size(contour.pathD),rectangles:0,contourRings:contour.rings.length};
   }catch(e){
    if(!/^(TINY_UNSUPPORTED_OBSERVATION|EXPLICIT_SOURCE_RING_VERTEX_BUDGET|DEGENERATE_LOOP|DEGENERATE_COMPRESSED_RING|NONMANIFOLD_CONTOUR_REPEAT|OPEN_SOURCE_BOUNDARY|ODD_SCANLINE_INTERSECTIONS|INVALID_SCANLINE_BOUNDS|UNTRACED_BOUNDARY_EDGE)$/.test(e?.message||''))throw e;
    contourFallbacks++;
   }
  }
  observed+=r.sourcePixels;paths+=best.fragment;explicitVertices+=best.vertices;
  if(best.method==='exact_source_contour')contourCount++;else rectCount++;
  chosen.push({layer:r.layer,rgb:hex,pixels:r.sourcePixels,method:best.method,svgFragmentBytes:size(best.fragment),
   explicitVertices:best.vertices,rectangles:best.rectangles,contourRings:best.contourRings});
 }
 if(observed!==baseline.sourcePixels)fail('HYBRID_SOURCE_MEMBERSHIP_COUNT');
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${input.width} ${input.height}" width="${input.width}" height="${input.height}">${paths}</svg>`;
 if(size(svg)>baseline.fillSvgBytes)fail('HYBRID_BYTES_REGRESSION');
 return {version:VERSION,width:input.width,height:input.height,sourcePixels:observed,
  sourceRgbaSha256:baseline.originalRgbaSha256,ownerSha256:baseline.originalOwnerSha256,
  exactRectSvgBytes:baseline.fillSvgBytes,stage68StrokeSvgBytes:baseline.stage68StrokeSvgBytes,
  hybridSvg:svg,hybridSvgBytes:size(svg),byteSavingsOverRects:baseline.fillSvgBytes-size(svg),
  explicitVertices,chosenLayers:chosen,contourLayers:contourCount,rectangleLayers:rectCount,contourFallbacks,
  verifiedSourceOnlyMathematically:true,actualChromeDprVerified:false,
  independentSemanticPixels:0,fullSceneBudgetSatisfied:false,wholeImageGolden:false,
  productionReleaseAuthorized:false,status:'PRIVATE_HYBRID_PREVIEW_GOLDEN_HOLD'};
}
export async function verifySourceCompactHybridSvg({candidate,...input}){
 if(!candidate||candidate.version!==VERSION)fail('HYBRID_CANDIDATE_REQUIRED');
 const exact=await buildSourceCompactHybridSvg(input);
 const fields=['hybridSvg','hybridSvgBytes','exactRectSvgBytes','stage68StrokeSvgBytes','sourcePixels',
  'sourceRgbaSha256','ownerSha256','explicitVertices','contourLayers','rectangleLayers','contourFallbacks'];
 if(fields.some(k=>candidate[k]!==exact[k])||JSON.stringify(candidate.chosenLayers)!==JSON.stringify(exact.chosenLayers))fail('HYBRID_REPLAY_TAMPERED');
 return {version:VERSION,sourcePixels:exact.sourcePixels,
  svgBytes:exact.hybridSvgBytes,explicitVertices:exact.explicitVertices,
  sourceMembershipVerified:true,semanticAnatomyVerified:false,
  humanGoldenApproved:false,paintAuthorized:false,releaseAuthorized:false,
  status:'HYBRID_REPLAY_PASS_GOLDEN_HOLD'};
}
