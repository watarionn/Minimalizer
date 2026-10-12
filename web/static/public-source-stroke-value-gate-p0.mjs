/** Stage60: independently rebuild source candidate and audit it before reporting cost.
 * Never equate stroke endpoints with Stage8 polygon vertex caps; never paint.
 */
import {buildSourceTiledStrokeCandidate} from './public-source-tiled-stroke-p0.mjs';
import {auditTiledStrokeRaster} from './public-source-stroke-raster-audit-p0.mjs';
export const VERSION='p0-stage60-rebuilt-source-stroke-value-gate-v1';
const bad=x=>{throw new TypeError(x);};
export async function evaluateSourceStrokeEncoding({width,height,sourceMask,sourceMaskSha256,candidate,tileSize=32,referenceContourVertices=null,originalSvgByteCount=null}){
 if(!candidate||candidate.sourceMaskSha256!==sourceMaskSha256||candidate.width!==width||candidate.height!==height||![null,undefined].includes(referenceContourVertices)&&(!Number.isInteger(referenceContourVertices)||referenceContourVertices<4)||![null,undefined].includes(originalSvgByteCount)&&(!Number.isInteger(originalSvgByteCount)||originalSvgByteCount<1))bad('INVALID_STROKE_ENCODING_PROOF');
 const independent=await buildSourceTiledStrokeCandidate({width,height,sourceMask,sourceMaskSha256,tileSize});
 for(const key of ['svgPaths','selectedStrokeCount','selectedMode','globalStrokeCount','tiledStrokeCount','endpointCount','rectangleEquivalentVertexCount'])if(candidate[key]!==independent[key])bad('CANDIDATE_PROVENANCE_MISMATCH');
 if(JSON.stringify(candidate.strokes)!==JSON.stringify(independent.strokes)||JSON.stringify(candidate.tiles)!==JSON.stringify(independent.tiles))bad('CANDIDATE_STROKES_TAMPERED');
 const proof=auditTiledStrokeRaster({width,height,sourceMask,candidate:independent});if(!proof.mathematicallyExact)bad('CANDIDATE_RASTER_NOT_EXACT');
 const markupBytes=new TextEncoder().encode(independent.svgPaths).length;
 const sourcePixelSafe=true,segmentSavingsOverGlobal=independent.globalStrokeCount-independent.selectedStrokeCount;
 const originalBytes=originalSvgByteCount??null;
 return {version:VERSION,width,height,sourcePixelCount:proof.sourcePixels,selectedStrokeCount:independent.selectedStrokeCount,svgMarkupBytes:markupBytes,strokeEndpointCount:independent.endpointCount,rectangleEquivalentVertexCount:independent.rectangleEquivalentVertexCount,segmentSavingsOverGlobal,byteSavingVersusProvidedContour:originalBytes===null?null:originalBytes-markupBytes,
  sourcePixelSafe,zeroOutsideSourceAtBothScales:proof.mismatch340===0&&proof.mismatch680===0,
  referenceContourVertices:referenceContourVertices??null,strokeEndpointsComparableToContours:false,
  wholeSceneBudgetValidated:false,realIphoneSafariVerified:false,anatomicalSemanticsVerified:false,sourceColorRewriteAuthorized:false,paintAuthorized:false,productionReleaseAuthorized:false};
}
