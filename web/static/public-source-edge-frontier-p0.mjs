/** P0 Stage170-173: finite source-color-edge/vertex frontier and honest review.
 * No global optimum claim, human identity, true human silhouette or release.
 */
import{buildAdaptiveSourceRgbPreview}from'./public-adaptive-source-rgb-p0.mjs';
import{auditOriginalSourceColorEdges}from'./public-source-edge-fidelity-p0.mjs';
import{buildSourceColorEdgeGuard}from'./public-source-edge-guard-p0.mjs';
export const VERSION='p0-stage170-173-source-edge-frontier-hold-v1';
const fail=s=>{throw new TypeError(s)};
const configs=Object.freeze([
 {tileSize:32,colorsPerTile:2,edgeThreshold:90},
 {tileSize:16,colorsPerTile:4,edgeThreshold:90},
 {tileSize:8,colorsPerTile:8,edgeThreshold:90},
 {tileSize:32,colorsPerTile:2,edgeThreshold:180}
]);
export async function buildSourceColorEdgeFrontier({source,draft,grid=configs}){
 if(!Array.isArray(grid)||grid.length<1||grid.length>8)fail('EDGE_FRONTIER_GRID_INVALID');
 const ids=new Set(),rows=[];
 let sourceHash=null,painted=null;
 for(const item of grid){
  if(!item||!Number.isInteger(item.tileSize)||!Number.isInteger(item.colorsPerTile)||
   !Number.isInteger(item.edgeThreshold))fail('EDGE_FRONTIER_PARAMETERS_INVALID');
  const id=item.tileSize+':'+item.colorsPerTile+':'+item.edgeThreshold;
  if(ids.has(id))fail('EDGE_FRONTIER_DUPLICATE_OPTION');ids.add(id);
  const adaptiveOptions={tileSize:item.tileSize,colorsPerTile:item.colorsPerTile};
  const [base,guard]=await Promise.all([
   buildAdaptiveSourceRgbPreview({source,draft,options:adaptiveOptions}),
   buildSourceColorEdgeGuard({source,draft,adaptiveOptions,
    edgeOptions:{edgeThreshold:item.edgeThreshold}})
  ]);
  if(!sourceHash){sourceHash=base.sourceRgbaSha256;painted=base.paintedSourceMaskSha256;}
  if(base.sourceRgbaSha256!==sourceHash||base.paintedSourceMaskSha256!==painted||
   base.paintedPixels!==guard.paintedSourcePixels||guard.guardedSourceRgbL1>base.totalRgbAbsoluteError)
   fail('EDGE_FRONTIER_ORIGINAL_MEMBERSHIP_MISMATCH');
  const baselineEdges=await auditOriginalSourceColorEdges({source,draft,
   renderedRgba:base.renderedRgba,options:{contrastThreshold:item.edgeThreshold}});
  rows.push({tileSize:item.tileSize,colorsPerTile:item.colorsPerTile,
   edgeThreshold:item.edgeThreshold,
   selectedOriginalSourcePixels:base.paintedPixels,
   originalSourceColorHighContrastLinks:guard.sourceHighContrastPairs,
   baseVertices:base.explicitVertices,guardVertices:guard.vertices,
   baseSvgBytes:base.svgBytes,guardSvgBytes:guard.svgBytes,
   baseSourceRgbChangedPixels:base.originalRgbChangedPixels,
   guardSourceRgbChangedPixels:guard.guardedRgbChangedPixels,
   baseSourceRgbL1:base.totalRgbAbsoluteError,
   guardSourceRgbL1:guard.guardedSourceRgbL1,
   baseHighContrastSourceLinksLost:baselineEdges.strongSourceColorEdgesLost,
   guardHighContrastSourceLinksLost:guard.sourceHighContrastEdgesLostAfterGuard,
   guardProtectedOriginalRgbEndpointPixels:guard.sourceObservedExactRgbEdgeEndpointPixels,
   roleSemanticHumanValidated:false,
   entireCharacterSilhouetteCovered:false,
   releaseAuthorized:false});
 }
 const frontier=rows.filter(a=>!rows.some(b=>b!==a&&
 b.guardVertices<=a.guardVertices&&b.guardSourceRgbL1<=a.guardSourceRgbL1&&
 (b.guardVertices<a.guardVertices||b.guardSourceRgbL1<a.guardSourceRgbL1)));
 return{version:VERSION,caseId:source.caseId,sourceRgbaSha256:sourceHash,
  originalSelectedMaskSha256:painted,candidates:rows,
  finiteEdgeColorPareto:frontier,
  originalSourceEdgesProtectedFromLoss:true,
  globalOptimalityUnknown:true,realHumanSourcePixelsVerified:0,
  authenticFullframeReviewApproved:false,
  originalWholeCharacterBudgetPassed:false,
  normalPublicEngineUnchanged:true,releaseAuthorized:false,
  status:'FINITE_ORIGINAL_EDGE_COLOR_VERTEX_FRONTIER_HOLD'};
}
export function chooseSourceColorEdgeCandidate(frontier,{maxVertices=Infinity,maxRgbL1=Infinity}={}){
 if(!frontier||frontier.version!==VERSION||!Array.isArray(frontier.candidates)||
 !(Number.isFinite(maxVertices)||maxVertices===Infinity)||maxVertices<0||
 !(Number.isFinite(maxRgbL1)||maxRgbL1===Infinity)||maxRgbL1<0)
 fail('EDGE_FRONTIER_SELECTION_BUDGET_INVALID');
 const candidates=frontier.candidates.filter(x=>x.guardVertices<=maxVertices&&x.guardSourceRgbL1<=maxRgbL1);
 const best=[...candidates].sort((a,b)=>a.guardVertices-b.guardVertices||a.guardSourceRgbL1-b.guardSourceRgbL1)[0]||null;
 return{version:VERSION,caseId:frontier.caseId,numericallyFeasibleAmongTestedSourceCandidates:!!best,
  selected:best,
  authenticatedWholeBodyHumanCoverage:false,
  globallyOptimal:false,
  productionAuthorized:false,status:best?'UNTRUSTED_PARTIAL_EDGE_CANDIDATE_HOLD':'NO_TESTED_CANDIDATE_WITHIN_GIVEN_NUMERIC_LIMITS_HOLD'};
}
