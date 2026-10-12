/** Stage55: collect source-pinned stroke encodings for source-observed parts.
 * Input role is a hypothesis, never anatomy, and no original colors are inferred.
 * Strictly research-only. Geometry/endpoint counts cannot authorize a release.
 */
import {buildSourceStrokeCover} from './public-source-stroke-cover-p0.mjs';
export const VERSION='p0-stage55-source-stroke-multifeature-experiment-v1';
const fail=s=>{throw new TypeError(s);};
const typed=a=>a instanceof Uint8Array||a instanceof Uint8ClampedArray;
const sha=/^[0-9a-f]{64}$/;
async function digest(bytes){if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');}
export async function buildSourceStrokeResearchBundle({caseId,width,height,faceMask,faceMaskSha256,features,strokeLimit=30000}){
 if(!['GC001','Raden'].includes(caseId)||!Number.isInteger(width)||!Number.isInteger(height)||width*height<1||width*height>160000||!typed(faceMask)||faceMask.length!==width*height||!sha.test(faceMaskSha256||'')||!Array.isArray(features)||features.length<1||features.length>8||!Number.isInteger(strokeLimit)||strokeLimit<1||strokeLimit>30000)fail('INVALID_STROKE_BUNDLE');
 if(await digest(faceMask)!==faceMaskSha256)fail('FACE_MASK_PIN_MISMATCH');
 for(const bit of faceMask)if(bit!==0&&bit!==255)fail('NONBINARY_FACE_MASK');
 const occupied=new Uint8Array(width*height),names=new Set(),parts=[];
 let origVertices=0,sourcePixels=0,strokes=0,endpoints=0;
 for(const f of features){
  if(!f||typeof f.id!=='string'||!/^([a-z][a-z0-9_-]{0,40})$/.test(f.id)||names.has(f.id)||f.evidenceLevel!=='research_observation'||!typed(f.sourceMask)||f.sourceMask.length!==width*height||!sha.test(f.sourceMaskSha256||'')||!Number.isInteger(f.contourVertices)||f.contourVertices<4)fail('INVALID_STROKE_FEATURE');
  names.add(f.id);
  for(let i=0;i<occupied.length;i++){const v=f.sourceMask[i];if(v!==0&&v!==255)fail('NONBINARY_STROKE_FEATURE');if(v){if(faceMask[i])fail('FACE_CONFLICT');if(occupied[i])fail('CROSS_FEATURE_OVERLAP');occupied[i]=255;}}
  const c=await buildSourceStrokeCover({width,height,sourceMask:f.sourceMask,sourceMaskSha256:f.sourceMaskSha256});
  strokes+=c.strokeCount;endpoints+=c.endpointCount;origVertices+=f.contourVertices;sourcePixels+=c.observedPixels;
  if(strokes>strokeLimit)fail('STROKE_BUNDLE_LIMIT_EXCEEDED');
  parts.push({id:f.id,sourceMaskSha256:f.sourceMaskSha256,observedPixels:c.observedPixels,strokes:c.strokeCount,endpointCount:c.endpointCount,contourVertices:f.contourVertices,axis:c.orientation,endpointSavings:f.contourVertices-c.endpointCount,
   // A generated SVG path is an encoding of source-geometry. Consumer colors remain unapproved.
   svgPath:c.svgPaths,independentReview:false});
 }
 return {version:VERSION,caseId,width,height,parts,observedSourcePixels:sourcePixels,sourceContourVertices:origVertices,strokeSegments:strokes,strokeEndpoints:endpoints,endpointSavings:origVertices-endpoints,
  zeroSourceAbsentPixelsAlgebraic:true,scale340ChromeVerified:false,scale680ChromeVerified:false,
  sourceColorsCertified:false,semanticAnatomyVerified:false,wholeCharacterGoldenVerified:false,
  vertexBudgetCertified:false,realIphoneSafariVerified:false,paintAuthorized:false,productionReleaseAuthorized:false,status:'RESEARCH_ONLY_DRAFT_HOLD'};
}
