/** Stages130–134: two-point SOURCE fidelity versus vertex budget study.
 * No proof that a Pareto optimum for complete characters was found.
 * Both candidates are untrusted and may contain false historic 'owner' pixels.
 */
import{buildSourceExactRgbPreview}from'./public-source-rgb-lossless-preview-p0.mjs';
import{buildUntrustedWholeFramePreview}from'./public-untrusted-fullscene-preview-p0.mjs';
export const VERSION='p0-stage130-134-source-rgb-cost-frontier-hold-v1';
const fail=s=>{throw new TypeError(s)};
export async function auditTwoPointSourceRgbFrontier({source,draft}){
 const [exact,compact]=await Promise.all([
  buildSourceExactRgbPreview({source,draft}),buildUntrustedWholeFramePreview({source,draft})]);
 if(exact.sourceRgbaSha256!==compact.sourceRgbaSha256||
  exact.labelsSha256!==compact.labelsSha256||
  exact.paintedPixels!==compact.paintedSourcePixels||
  exact.originalRgbMismatchPixels!==0)fail('FRONTIER_SOURCE_OR_MASK_IDENTITY_CHANGED');
 const cap=source.caseId==='GC001'?1887:1412;
 const rows=[
  {name:'quantized_source_sample_preview',svgBytes:compact.svgBytes,
   explicitVertices:compact.totalExplicitVertices,originalRgbMismatchPixels:compact.rgbMismatchPixelsDueToSourcePaletteQuantization,
   drawnPixels:compact.paintedSourcePixels,withinHistoricNumericCap:compact.totalExplicitVertices<=cap,
   originalSourceRgbFidelity:compact.rgbMismatchPixelsDueToSourcePaletteQuantization===0},
  {name:'original_rgb_exact_rectangle_preview',svgBytes:exact.svgBytes,
   explicitVertices:exact.vertices,originalRgbMismatchPixels:0,
   drawnPixels:exact.paintedPixels,withinHistoricNumericCap:exact.vertices<=cap,
   originalSourceRgbFidelity:true}
 ];
 const noExampleSatisfiesBoth=rows.every(x=>!x.withinHistoricNumericCap||!x.originalSourceRgbFidelity);
 return {version:VERSION,caseId:source.caseId,sourceRgbaSha256:exact.sourceRgbaSha256,
  labelsSha256:exact.labelsSha256,untrustedSourceCandidatePixels:exact.paintedPixels,
  historicFullSceneNumericCap:cap,
  candidates:rows,
  rgbPixelsRecoveredFromQuantizedPreview:compact.rgbMismatchPixelsDueToSourcePaletteQuantization,
  explicitVertexIncreaseForFullRgb:exact.vertices-compact.totalExplicitVertices,
  svgByteIncreaseForFullRgb:exact.svgBytes-compact.svgBytes,
  noCandidateAmongTheseTwoMeetsBothNumericCriteria:noExampleSatisfiesBoth,
  noGlobalOptimalityClaim:true,
  fullCharacterCoverageVerified:false,realHumanSemanticsVerified:false,
  actualFullBodyBudgetVerified:false,realIphoneSafariVerified:false,
  productReleaseAuthorized:false,status:'TWO_PARTIAL_SOURCE_RGB_BUDGET_POINTS_GOLDEN_HOLD'};
}
