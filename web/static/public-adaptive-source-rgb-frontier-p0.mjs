/** Stages146–150: inspect a FINITE sampling grid, not proof of optimum.
 * A path's RGB may be source observed but still WRONG vs selected original pixel.
 * This never claims a complete person silhouette or human approval.
 */
import{buildAdaptiveSourceRgbPreview,VERSION as ADAPTIVE_VERSION}from'./public-adaptive-source-rgb-p0.mjs';
export const VERSION='p0-stage146-150-finite-adaptive-frontier-hold-v1';
const fail=s=>{throw new TypeError(s)};
const AXES=Object.freeze([{tileSize:8,colorsPerTile:1},{tileSize:8,colorsPerTile:2},
 {tileSize:8,colorsPerTile:4},{tileSize:8,colorsPerTile:8},
 {tileSize:16,colorsPerTile:1},{tileSize:16,colorsPerTile:2},
 {tileSize:16,colorsPerTile:4},{tileSize:16,colorsPerTile:8},
 {tileSize:32,colorsPerTile:1},{tileSize:32,colorsPerTile:2},
 {tileSize:32,colorsPerTile:4},{tileSize:32,colorsPerTile:8}]);
export async function buildFiniteAdaptiveSourceRgbFrontier({source,draft,grid=AXES,maxPixelL1=765}){
 if(!Array.isArray(grid)||grid.length<1||grid.length>16||
  grid.some(x=>!x||!Number.isInteger(x.tileSize)||!Number.isInteger(x.colorsPerTile)))
  fail('FINITE_FRONTIER_GRID_INVALID');
 const identity=new Set(grid.map(x=>x.tileSize+'/'+x.colorsPerTile));
 if(identity.size!==grid.length)fail('FINITE_FRONTIER_DUPLICATE_OPTIONS');
 const rows=[];let pinned=null,pinnedMask=null,painted=null;
 for(const o of grid){
  const x=await buildAdaptiveSourceRgbPreview({source,draft,options:{...o,maxPixelL1}});
  if(x.version!==ADAPTIVE_VERSION||x.releaseAuthorized!==false)fail('UNTRUSTED_ADAPTIVE_AUTHORITY_CHANGED');
  if(pinned===null){pinned=x.sourceRgbaSha256;pinnedMask=x.paintedSourceMaskSha256;painted=x.paintedPixels;}
  if(pinned!==x.sourceRgbaSha256||pinnedMask!==x.paintedSourceMaskSha256||painted!==x.paintedPixels)
   fail('FRONTIER_CANDIDATE_SOURCE_IDENTITY_DRIFT');
  rows.push({tileSize:o.tileSize,colorsPerTile:o.colorsPerTile,
   originalRgbChangedPixels:x.originalRgbChangedPixels,
   totalRgbAbsoluteError:x.totalRgbAbsoluteError,
   meanRgbL1PerPaintedPixel:x.meanRgbL1PerPaintedPixel,
   worstPixelRgbL1:x.worstPixelRgbL1,
   sourceRgbSse:x.sourceRgbSse,paintedPixels:x.paintedPixels,
   rectangles:x.rectangleCount,vertices:x.explicitVertices,svgBytes:x.svgBytes,
   originalRgbaSha256:x.sourceRgbaSha256,sourceMembershipSha256:x.paintedSourceMaskSha256,
   authenticatedSemanticPixels:0,wholeCharacterGolden:false});
 }
 const nondominated=rows.filter(a=>!rows.some(b=>b!==a&&
  b.vertices<=a.vertices&&b.totalRgbAbsoluteError<=a.totalRgbAbsoluteError&&
  (b.vertices<a.vertices||b.totalRgbAbsoluteError<a.totalRgbAbsoluteError)));
 const cheapest=[...rows].sort((a,b)=>a.vertices-b.vertices||a.totalRgbAbsoluteError-b.totalRgbAbsoluteError)[0];
 const leastError=[...rows].sort((a,b)=>a.totalRgbAbsoluteError-b.totalRgbAbsoluteError||a.vertices-b.vertices)[0];
 return{version:VERSION,caseId:source.caseId,originalRgbaSha256:pinned,
  selectedSourceMaskSha256:pinnedMask,untrustedSelectedSourcePixels:painted,
  candidates:rows,finitePareto:nondominated,lowestVertices:cheapest,
  lowestRgbError:leastError,globalParetoOrOptimalityEstablished:false,
  wholeCharacterSceneStudied:false,independentlyHumanApprovedPixels:0,
  realIphoneSafariVerified:false,releaseAuthorized:false,
  status:'FINITE_PARTIAL_SOURCE_RGB_GEOMETRY_FRONTIER_GOLDEN_HOLD'};
}
export function chooseBoundedPartialCandidate(frontier,{maxMeanL1=Infinity,maxVertices=Infinity}={}){
 if(!frontier||frontier.version!==VERSION||!Array.isArray(frontier.candidates)||
 !(Number.isFinite(maxMeanL1)||maxMeanL1===Infinity)||maxMeanL1<0||
 !(Number.isFinite(maxVertices)||maxVertices===Infinity)||maxVertices<0)
  fail('FINITE_FRONTIER_SELECTION_POLICY_INVALID');
 const feasible=frontier.candidates.filter(x=>x.meanRgbL1PerPaintedPixel<=maxMeanL1&&x.vertices<=maxVertices);
 const chosen=[...feasible].sort((a,b)=>a.vertices-b.vertices||a.totalRgbAbsoluteError-b.totalRgbAbsoluteError)[0]||null;
 return{version:VERSION,caseId:frontier.caseId,anyFiniteCandidateUnderRequestedNumericBudgets:!!chosen,
  selected:chosen,originalSourceRgbObservedOnly:true,
  fullCharacterShapeGolden:false,trueWholeSceneBudgetPassed:false,
  humanSemanticAuthorityGranted:false,releaseAuthorized:false,
  status:chosen?'UNTRUSTED_PARTIAL_DIAGNOSTIC_SELECTED_HOLD':'FINITE_GRID_NO_FEASIBLE_CANDIDATE_HOLD'};
}
