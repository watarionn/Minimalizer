/** Stage69: independent immutable replay of source palette trial and exact chromatic footprint.
 * Zero owner/anatomy authority. Reject all forged preview fields and mismatched hashes.
 */
import {proposeSourceSpatialPalette} from './public-source-spatial-palette-p0.mjs';
import {encodeSourcePaletteSvg} from './public-source-palette-svg-p0.mjs';
export const VERSION='p0-stage69-source-rgb-preview-proof-v1';
const fail=x=>{throw new TypeError(x)};
const SHA=/^[0-9a-f]{64}$/;
const hash=async x=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',x))].map(x=>x.toString(16).padStart(2,'0')).join('');
export async function verifySourcePaletteTrial({width,height,sourceRgba,sourceSha256,ownerMask,ownerSha256,partition,proposal,previewSvg}){
 if(!SHA.test(sourceSha256||'')||!SHA.test(ownerSha256||'')||!crypto?.subtle||!proposal||!previewSvg||!partition)fail('INVALID_SOURCE_PALETTE_PROOF');
 if(await hash(sourceRgba)!==sourceSha256||await hash(ownerMask)!==ownerSha256)fail('SOURCE_PALETTE_PROVENANCE_MISMATCH');
 const rebuilt=proposeSourceSpatialPalette({width,height,sourceRgba,ownerMask,partition});
 for(const k of ['version','selection','acceptedTrial','changedPixels'])if(rebuilt[k]!==proposal[k])fail('SOURCE_PALETTE_TRIAL_TAMPERED');
 if(JSON.stringify(rebuilt.selectedAssignments)!==JSON.stringify(proposal.selectedAssignments)||JSON.stringify(rebuilt.before)!==JSON.stringify(proposal.before)||JSON.stringify(rebuilt.proposalMetrics)!==JSON.stringify(proposal.proposalMetrics))fail('SOURCE_PALETTE_TRIAL_TAMPERED');
 const regenerated=await encodeSourcePaletteSvg({width,height,ownerMask,ownerSha256,sourceRgba,sourceSha256,palette:partition.palette,assignments:rebuilt.selectedAssignments});
 if(regenerated.svg!==previewSvg.svg||regenerated.svgBytes!==previewSvg.svgBytes||regenerated.strokeCount!==previewSvg.strokeCount)fail('SOURCE_PALETTE_SVG_TAMPERED');
 return {version:VERSION,width,height,sourcePixels:regenerated.sourcePixels,colorL1Before:rebuilt.before.colorL1,colorL1Selected:rebuilt.acceptedTrial?rebuilt.proposalMetrics.colorL1:rebuilt.before.colorL1,sourceContrastEdges:rebuilt.before.highContrastEdges,sourceContrastRetained:rebuilt.acceptedTrial?rebuilt.proposalMetrics.retainedHighContrastEdges:rebuilt.before.retainedHighContrastEdges,unapprovedWeakEdgesBefore:rebuilt.before.unverifiedCreatedLowContrastEdges,unapprovedWeakEdgesSelected:rebuilt.acceptedTrial?rebuilt.proposalMetrics.unverifiedCreatedLowContrastEdges:rebuilt.before.unverifiedCreatedLowContrastEdges,acceptedSpatialTrial:rebuilt.acceptedTrial,svgPathsLayers:regenerated.layers.length,svgStrokeSegments:regenerated.strokeCount,svgBytes:regenerated.svgBytes,sourcePaletteOnly:true,sourceFootprintOnly:true,independentSemanticReviewPixels:0,wholeSceneGolden:false,wholeSceneSvgVertexBudgetPassed:false,productPaintAuthorized:false,releaseAuthorized:false,status:'SOURCE_COLOR_SVG_PREVIEW_ONLY_HOLD'};
}
