/** Stages111–114 opt-in, untrusted source-color SVG proof only.
 * Original RGB is sampled, never generated; the first source RGB per label is
 * deliberately quantized (NOT exact original RGB). Source mask is pixel exact.
 * No face/background proposals rendered. Unknown pixels remain transparent.
 */
import {validateUntrustedFullFrameDraft} from './public-fullframe-review-p0.mjs';
import {exactSourceRectangleCover} from './public-source-exact-rect-cover-p0.mjs';
export const VERSION='p0-stage111-114-untrusted-fullframe-proposal-v1';
const fail=s=>{throw new TypeError(s)};
const hash=async b=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('');
const bytes=s=>new TextEncoder().encode(s).length;
const paintableLabels=[2,4,5,6,7,8,9]; // no background/face; 9 is UNVERIFIED unknown subject
const svgPath=rects=>rects.map(([x0,y0,x1,y1])=>`M${x0} ${y0}h${x1-x0}v${y1-y0}h-${x1-x0}Z`).join('');
const hex=b=>'#'+[...b].map(v=>v.toString(16).padStart(2,'0')).join('');
export async function buildUntrustedWholeFramePreview({source,draft}){
 const q=await validateUntrustedFullFrameDraft({...source,draft});
 const {width,height,sourceRgba}=source,n=width*height;
 const painted=new Uint8Array(n),layers=[];let totalVertices=0,totalRects=0;
 let renderedSourcePixels=0,quantizedRgbMismatchPixels=0;
 const fragments=[];
 for(const role of paintableLabels){
  const mask=new Uint8Array(n);let count=0,first=-1;
  for(let i=0;i<n;i++)if(q.labels[i]===role){
   if(sourceRgba[4*i+3]!==255)fail('NONOPAQUE_SOURCE_IN_PROPOSAL');
   mask[i]=255;painted[i]=255;count++;if(first<0)first=i;
  }
  if(!count)continue;
  const rgb=sourceRgba.subarray(4*first,4*first+3),sourceRgb=hex(rgb);
  for(let i=0;i<n;i++)if(mask[i]&&(sourceRgba[4*i]!==rgb[0]||sourceRgba[4*i+1]!==rgb[1]||sourceRgba[4*i+2]!==rgb[2]))quantizedRgbMismatchPixels++;
  const rect=exactSourceRectangleCover({width,height,sourceMask:mask,maxRectangles:160000});
  if(rect.observedPixels!==count)fail('SOURCE_ROLE_COVERAGE_MISMATCH');
  const fragment=`<path d="${svgPath(rect.rectangles)}" fill="${sourceRgb}"/>`;
  fragments.push(fragment);renderedSourcePixels+=count;
  totalVertices+=rect.explicitVertexCost;totalRects+=rect.rectangleCount;
  layers.push({role,sourceRgb,sourcePixelCount:count,sourceFirstPixelIndex:first,
   exactSourceMemberMask:true,rectangleCount:rect.rectangleCount,
   explicitVertices:rect.explicitVertexCost,svgFragmentBytes:bytes(fragment)});
 }
 const foregroundLayers=layers.map(x=>x.role);
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">${fragments.join('')}</svg>`;
 return {version:VERSION,caseId:source.caseId,width,height,sourceRgbaSha256:q.sourceRgbaSha256,
  labelsSha256:q.labelsSha256,sourceEligibilitySha256:q.sourceEligibilitySha256,
  paintedMembershipSha256:await hash(painted),
  paintedSourcePixels:renderedSourcePixels,unreviewedOrExcludedPixels:n-renderedSourcePixels,
  rgbMismatchPixelsDueToSourcePaletteQuantization:quantizedRgbMismatchPixels,
  exactOriginalRgbEverywhere:quantizedRgbMismatchPixels===0,
  layers,foregroundLayers,svg,svgBytes:bytes(svg),totalRectangles:totalRects,
  totalExplicitVertices:totalVertices,sourcePixelMembershipVerified:true,
  untrustedFaceOrBackgroundExcluded:true,fullCharacterNotProven:true,
  signerHumanIdentityVerified:false,independentSemanticPixels:0,
  humanGoldenApproved:false,paintAuthorized:false,productionReleaseAuthorized:false,
  status:'PRIVATE_UNTRUSTED_SOURCE_COLOR_SVG_PREVIEW_ONLY'};
}
export async function verifyUntrustedWholeFramePreview({source,draft,candidate}){
 if(!candidate||candidate.version!==VERSION)fail('SOURCE_BOUND_PREVIEW_REQUIRED');
 const known=await buildUntrustedWholeFramePreview({source,draft});
 const keys=['svg','svgBytes','caseId','sourceRgbaSha256','labelsSha256',
  'sourceEligibilitySha256','paintedMembershipSha256','paintedSourcePixels',
  'unreviewedOrExcludedPixels','rgbMismatchPixelsDueToSourcePaletteQuantization',
  'totalRectangles','totalExplicitVertices','sourcePixelMembershipVerified'];
 if(keys.some(k=>candidate[k]!==known[k])||
  JSON.stringify(candidate.layers)!==JSON.stringify(known.layers)||
  candidate.humanGoldenApproved!==false||
  candidate.paintAuthorized!==false||
  candidate.productionReleaseAuthorized!==false||
  candidate.fullCharacterNotProven!==true||
  candidate.signerHumanIdentityVerified!==false||
  candidate.independentSemanticPixels!==0||
  candidate.untrustedFaceOrBackgroundExcluded!==true||
  candidate.status!=='PRIVATE_UNTRUSTED_SOURCE_COLOR_SVG_PREVIEW_ONLY')fail('SOURCE_BOUND_PREVIEW_TAMPERED');
 return {version:VERSION,caseId:known.caseId,pixelMembershipVerified:true,
  sourceRgbQuantizationMismatchPixels:known.rgbMismatchPixelsDueToSourcePaletteQuantization,
  independentHumanApproval:false,wholeCharacterApproved:false,paintAuthorized:false,
  status:'UNTRUSTED_PREVIEW_REPLAY_PASS_GOLDEN_HOLD'};
}
export function assessUntrustedWholeFrameBudget(preview){
 if(!preview||preview.version!==VERSION||!['GC001','Raden'].includes(preview.caseId)||
 !Number.isSafeInteger(preview.totalExplicitVertices)||preview.totalExplicitVertices<4)
 fail('BUDGET_REQUIRES_SOURCE_PREVIEW');
 const cap=preview.caseId==='GC001'?1887:1412;
 return {version:VERSION,caseId:preview.caseId,stage8HistoricSceneCap:cap,
  sourceOnlyUntrustedPreviewVertices:preview.totalExplicitVertices,
  previewOverCap:Math.max(0,preview.totalExplicitVertices-cap),
  withinNumericCapOnly:preview.totalExplicitVertices<=cap,
  actualWholeCharacterSubjectCoverageCertified:false,
  bodyPartSemanticsHumanCertified:false,wholeBodyVertexGateApproved:false,
  humanGoldenApproved:false,releaseAuthorized:false,
  status:'UNTRUSTED_PARTIAL_FULLFRAME_VERTEX_DIAGNOSTIC_HOLD'};
}
