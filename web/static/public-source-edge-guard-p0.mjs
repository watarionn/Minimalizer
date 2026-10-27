/** Stage163-169: deterministic SOURCE RGB edge-endpoint locks.
 * A lock is a color-edge measurement, NOT a person or anatomy segmentation.
 * Endpoint RGB is copied from observed original source, never invented.
 */
import{validateUntrustedFullFrameDraft}from'./public-fullframe-review-p0.mjs';
import{buildAdaptiveSourceRgbPreview}from'./public-adaptive-source-rgb-p0.mjs';
import{auditOriginalSourceColorEdges}from'./public-source-edge-fidelity-p0.mjs';
export const VERSION='p0-stage163-169-source-color-edge-guard-hold-v1';
const fail=s=>{throw new TypeError(s)};
const ELIGIBLE=new Set([2,4,5,6,7,8,9]);
const pack=(a,j)=>(a[j]<<16)|(a[j+1]<<8)|a[j+2];
const rgb=x=>[(x>>16)&255,(x>>8)&255,x&255];
const hex=x=>'#'+x.toString(16).padStart(6,'0');
const absRgb=(a,ai,b,bi)=>Math.abs(a[ai]-b[bi])+Math.abs(a[ai+1]-b[bi+1])+Math.abs(a[ai+2]-b[bi+2]);
const sha=async a=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');
const enc=s=>new TextEncoder().encode(s).length;
const dRect=([x0,y0,x1,y1])=>`M${x0} ${y0}h${x1-x0}v${y1-y0}h-${x1-x0}Z`;
function readEdgeSettings({edgeThreshold=90,maxRectangles=160000}={}){
 if(![45,90,135,180,270,360].includes(edgeThreshold))fail('EDGE_GUARD_THRESHOLD_UNSUPPORTED');
 if(!Number.isInteger(maxRectangles)||maxRectangles<1||maxRectangles>160000)
  fail('EDGE_GUARD_RECTANGLE_BUDGET_INVALID');
 return{edgeThreshold,maxRectangles};
}
function rgbGroups({width,height,labels,rgba,cap}){
 const groups=new Map();let previous=new Map(),count=0;
 for(let y=0;y<height;y++){
  let x=0;const next=new Map();
  while(x<width){
   const role=labels[y*width+x];
   if(!ELIGIBLE.has(role)){x++;continue;}
   const value=pack(rgba,4*(y*width+x)),first=x;x++;
   while(x<width&&labels[y*width+x]===role&&pack(rgba,4*(y*width+x))===value)x++;
   const layer=role+'|'+value,key=layer+'|'+first+'|'+x;
   let rect=previous.get(key);
   if(rect){rect[3]=y+1;}else{
    rect=[first,y,x,y+1];count++;
    if(count>cap)fail('EDGE_GUARD_RECTANGLE_CAP_EXCEEDED');
    if(!groups.has(layer))groups.set(layer,[]);
    groups.get(layer).push(rect);
   }
   next.set(key,rect);
  }
  previous=next;
 }
 return{groups,rectangleCount:count};
}
export async function buildSourceColorEdgeGuard({source,draft,adaptiveOptions={},edgeOptions={}}){
 const o=readEdgeSettings(edgeOptions);
 const validated=await validateUntrustedFullFrameDraft({...source,draft});
 const baseline=await buildAdaptiveSourceRgbPreview({source,draft,options:adaptiveOptions});
 const {width,height,sourceRgba:original}=source,n=width*height,labels=validated.labels;
 const locked=new Uint8Array(n),guarded=new Uint8Array(baseline.renderedRgba);
 let highSourcePairs=0;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const i=y*width+x;if(!ELIGIBLE.has(labels[i]))continue;
  for(const j of [x+1<width?i+1:-1,y+1<height?i+width:-1]){
   if(j<0||labels[j]!==labels[i])continue;
   if(absRgb(original,4*i,original,4*j)>=o.edgeThreshold){
    highSourcePairs++;locked[i]=255;locked[j]=255;
   }
  }
 }
 let lockedPixels=0;
 for(let i=0;i<n;i++)if(locked[i]){
  if(!ELIGIBLE.has(labels[i])||original[4*i+3]!==255)fail('EDGE_LOCKED_PIXEL_NOT_IN_SOURCE');
  guarded.set(original.subarray(4*i,4*i+4),4*i);lockedPixels++;
 }
 const cover=rgbGroups({width,height,labels,rgba:guarded,cap:o.maxRectangles});
 let covered=0;
 for(const [key,rects]of cover.groups){
  const ix=key.indexOf('|'),role=Number(key.slice(0,ix)),color=Number(key.slice(ix+1));
  for(const [x0,y0,x1,y1]of rects)for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
   const i=y*width+x;
   if(labels[i]!==role||pack(guarded,4*i)!==color||
   guarded[4*i+3]!==255)fail('GUARDED_COLOR_RECT_NOT_SOURCE');
   covered++;
  }
 }
 if(covered!==baseline.paintedPixels)fail('GUARDED_PIXEL_MEMBERSHIP_CHANGED');
 const paths=[...cover.groups].map(([key,rects])=>{
  const color=Number(key.slice(key.indexOf('|')+1));
  return `<path fill="${hex(color)}" d="${rects.map(dRect).join('')}"/>`;
 });
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">${paths.join('')}</svg>`;
 const [before,after]=await Promise.all([
  auditOriginalSourceColorEdges({source,draft,renderedRgba:baseline.renderedRgba,
   options:{contrastThreshold:o.edgeThreshold}}),
  auditOriginalSourceColorEdges({source,draft,renderedRgba:guarded,
   options:{contrastThreshold:o.edgeThreshold}})
 ]);
 if(after.totalRgbL1>before.totalRgbL1||after.rgbChangedSourcePixels>before.rgbChangedSourcePixels||
 after.strongSourceColorEdgesLost!==0||after.sourceHighContrastNeighborPairs!==highSourcePairs)
  fail('SOURCE_EDGE_GUARD_DID_NOT_PROTECT_ORIGINAL');
 return{version:VERSION,caseId:source.caseId,sourceRgbaSha256:source.sourceRgbaSha256,
  labelsSha256:validated.labelsSha256,options:{adaptiveOptions:baseline.options,edgeOptions:o},
  paintedSourcePixels:baseline.paintedPixels,sourceHighContrastPairs:highSourcePairs,
  sourceObservedExactRgbEdgeEndpointPixels:lockedPixels,
  sourceEdgeEndpointMaskSha256:await sha(locked),
  baselineRgbChangedPixels:before.rgbChangedSourcePixels,
  guardedRgbChangedPixels:after.rgbChangedSourcePixels,
  baselineSourceRgbL1:before.totalRgbL1,guardedSourceRgbL1:after.totalRgbL1,
  sourceHighContrastEdgesLostAfterGuard:after.strongSourceColorEdgesLost,
  sourceArtificialStrongEdgesAfterGuard:after.renderedArtificialStrongColorEdges,
  originalContrastDistortionL1AfterGuard:after.sourceColorContrastDistortionL1,
  rectangles:cover.rectangleCount,vertices:cover.rectangleCount*4,svg,svgBytes:enc(svg),
  guardedRenderedRgbaSha256:await sha(guarded),guardedRenderedRgba:guarded,
  allColorsObservedInOriginalSource:true,originalSelectedPixelMembershipExact:true,
  sourceEdgesDoNotCertifyPersonGeometry:true,independentHumanSemanticPixels:0,
  trueWholebodySvgBudgetApproved:false,defaultPublicConverterChanged:false,
  releaseAuthorized:false,status:'SOURCE_EDGE_ENDPOINT_RGB_LOCK_GOLDEN_HOLD'};
}
export async function verifySourceColorEdgeGuard({source,draft,candidate}){
 if(!candidate||candidate.version!==VERSION)fail('SOURCE_GUARD_CANDIDATE_REQUIRED');
 const baseline=await buildSourceColorEdgeGuard({source,draft,
  adaptiveOptions:candidate.options?.adaptiveOptions,edgeOptions:candidate.options?.edgeOptions});
 const keys=['caseId','sourceRgbaSha256','labelsSha256','paintedSourcePixels',
 'sourceHighContrastPairs','sourceObservedExactRgbEdgeEndpointPixels',
 'sourceEdgeEndpointMaskSha256','baselineRgbChangedPixels','guardedRgbChangedPixels',
 'baselineSourceRgbL1','guardedSourceRgbL1','sourceHighContrastEdgesLostAfterGuard',
 'sourceArtificialStrongEdgesAfterGuard','originalContrastDistortionL1AfterGuard',
 'rectangles','vertices','svg','svgBytes','guardedRenderedRgbaSha256',
 'allColorsObservedInOriginalSource','originalSelectedPixelMembershipExact',
 'sourceEdgesDoNotCertifyPersonGeometry','independentHumanSemanticPixels',
 'trueWholebodySvgBudgetApproved','defaultPublicConverterChanged',
 'releaseAuthorized','status'];
 if(keys.some(k=>baseline[k]!==candidate[k])||
 JSON.stringify(candidate.options)!==JSON.stringify(baseline.options)||
 !(candidate.guardedRenderedRgba instanceof Uint8Array)||
 candidate.guardedRenderedRgba.length!==baseline.guardedRenderedRgba.length||
 candidate.guardedRenderedRgba.some((x,i)=>x!==baseline.guardedRenderedRgba[i]))
 fail('SOURCE_EDGE_GUARD_REPLAY_TAMPERED');
 return{version:VERSION,sourceRgbEdgeEndpointsProtected:true,
  realIndependentHumanLabels:0,wholeCharacterGeometryCertified:false,
  releaseAuthorized:false,status:'SOURCE_RGB_EDGE_GUARD_VERIFIED_HOLD'};
}
export function guardSourceColorEdgeRelease({cases=[]}={}){
 if(!Array.isArray(cases)||cases.length>2||
 cases.some(x=>!x||!['GC001','Raden'].includes(x.caseId))||
 new Set(cases.map(x=>x.caseId)).size!==cases.length)
 fail('SOURCE_EDGE_RELEASE_CASE_INVALID');
 return{version:VERSION,unresolvedOriginalCases:['GC001','Raden'].filter(x=>!cases.some(c=>c.caseId===x)),
  independentHumanReviewerCount:0,
  authenticatedFullframeSemanticPixels:0,
  wholebodyShapeAndPartsGolden:false,
  trueFullbodyVerticesUnderHistoricalCap:false,
  realIphoneSafariHttpsChecked:false,rollbackTested:false,
  productionConverterAuthorized:false,status:'SOURCE_COLOR_EDGE_RESEARCH_GOLDEN_HOLD'};
}
