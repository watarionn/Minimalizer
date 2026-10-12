/** Stage125–133: EXACT original RGB/alpha255 on UNTRUSTED class proposal pixels.
 * No generative fill, no medoid, no inventing pixels, no human semantics approved.
 * Opaque BACKGROUND is still possible if a label falsely describes a subject.
 * This research-only SVG is NEVER routed to product or counted as whole-body Golden.
 */
import {validateUntrustedFullFrameDraft} from './public-fullframe-review-p0.mjs';
export const VERSION='p0-stage125-133-exact-original-rgb-source-label-diagnostic-hold-v1';
const fail=s=>{throw new TypeError(s)};
const hex=(a,i)=>'#'+[a[i],a[i+1],a[i+2]].map(c=>c.toString(16).padStart(2,'0')).join('');
const utf8=s=>new TextEncoder().encode(s).length;
const allowed=new Set([2,4,5,6,7,8,9]);
const svgRect=([x0,y0,x1,y1])=>`M${x0} ${y0}h${x1-x0}v${y1-y0}h-${x1-x0}Z`;
function buildRuns({labels,rgba,width,height,maxRects}){
 const colorToRects=new Map(),colorToCounts=new Map();let prev=new Map(),total=0,rectangles=0;
 for(let y=0;y<height;y++){
  const current=new Map();let x=0;
  while(x<width){
   const i=y*width+x,role=labels[i];
   if(!allowed.has(role)){x++;continue;}
   if(rgba[4*i+3]!==255)fail('SOURCE_NONOPAQUE_RGB_PREVIEW');
   const color=hex(rgba,i*4),start=x;x++;
   while(x<width&&labels[y*width+x]===role&&rgba[(y*width+x)*4+3]===255&&
    hex(rgba,(y*width+x)*4)===color)x++;
   const key=role+'|'+color,runKey=key+'|'+start+'|'+x;
   let rect=prev.get(runKey);
   if(rect){rect[3]=y+1;}else{
    rect=[start,y,x,y+1];rectangles++;
    if(rectangles>maxRects)fail('ORIGINAL_RGB_RECT_BUDGET_EXCEEDED');
    if(!colorToRects.has(key))colorToRects.set(key,[]);
    colorToRects.get(key).push(rect);
   }
   colorToCounts.set(key,(colorToCounts.get(key)||0)+(x-start));
   current.set(runKey,rect);total+=x-start;
  }
  prev=current;
 }
 return {colorToRects,colorToCounts,rectangles,total};
}
function sourceRgbReplay({rgba,labels,width,height,colorToRects,total}){
 const n=width*height,seen=new Uint8Array(n);let observed=0,opaqueRgbMismatch=0,unexpected=0;
 for(const [key,rects]of colorToRects){
  const split=key.indexOf('|'),role=Number(key.slice(0,split)),color=key.slice(split+1);
  const rgb=[1,3,5].map(i=>parseInt(color.slice(i,i+2),16));
  for(const [x0,y0,x1,y1]of rects){
   if(x0<0||y0<0||x1>width||y1>height||x0>=x1||y0>=y1)fail('SOURCE_RGB_RECT_OUTSIDE_SOURCE');
   for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
    const i=y*width+x;if(seen[i])fail('SOURCE_RGB_OVERLAPPING_RECT');
    seen[i]=255;observed++;
    if(labels[i]!==role||rgba[4*i+3]!==255)unexpected++;
    if(rgb.some((v,j)=>v!==rgba[4*i+j]))opaqueRgbMismatch++;
   }
  }
 }
 if(unexpected||opaqueRgbMismatch||observed!==total)fail('ORIGINAL_RGB_REPLAY_DIFFERENCE');
 for(let i=0;i<n;i++)if((seen[i]===255)!==allowed.has(labels[i]))fail('ORIGINAL_RGB_MEMBERSHIP_CHANGED');
 return {opaqueRgbMismatch,unexpected,observed};
}
export async function buildSourceExactRgbPreview({source,draft,maxRectangles=160000}){
 if(!Number.isSafeInteger(maxRectangles)||maxRectangles<1||maxRectangles>160000)fail('SOURCE_RGB_BUDGET_INVALID');
 const review=await validateUntrustedFullFrameDraft({...source,draft});
 const {sourceRgba:rgba,width,height}=source,n=width*height;
 const runs=buildRuns({labels:review.labels,rgba,width,height,maxRects:maxRectangles});
 const replay=sourceRgbReplay({rgba,labels:review.labels,width,height,
  colorToRects:runs.colorToRects,total:runs.total});
 const colorLayers=[],fragments=[];
 for(const [key,rects]of runs.colorToRects){
  const [roleText,color]=key.split('|'),d=rects.map(svgRect).join('');
  fragments.push(`<path fill="${color}" d="${d}"/>`);
  colorLayers.push({role:Number(roleText),originalSourceColor:color,
   rectangles:rects.length,paintedPixels:runs.colorToCounts.get(key),
   exactSourceRgb:true,sourceExactPixelEdge:true});
 }
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">${fragments.join('')}</svg>`;
 const excluded=review.counts[0]+review.counts[1]+review.counts[3];
 if(replay.observed+excluded!==n)fail('ORIGINAL_RGB_PROPOSAL_AREA_MISMATCH');
 return {version:VERSION,caseId:source.caseId,sourceRgbaSha256:review.sourceRgbaSha256,
  labelsSha256:review.labelsSha256,width,height,
  paintedPixels:runs.total,excludedPixels:excluded,originalRgbMismatchPixels:0,
  fullSourceColorClasses:colorLayers.length,rectangles:runs.rectangles,vertices:runs.rectangles*4,
  svg,svgBytes:utf8(svg),colorLayers,
  fullCharacterSemanticTruth:false,originalSubjectVsBackgroundVerified:false,
  semanticPixelHumanApproved:0,realHumanReviewersAuthenticated:0,
  chromeDprProof:false,wholeCharacterBudgetApproved:false,paintAuthorized:false,
  releaseAuthorized:false,status:'SOURCE_EXACT_RGB_UNTRUSTED_PARTIAL_PREVIEW_HOLD'};
}
export async function verifySourceExactRgbPreview({source,draft,candidate}){
 if(!candidate||candidate.version!==VERSION)fail('SOURCE_EXACT_PREVIEW_REQUIRED');
 const baseline=await buildSourceExactRgbPreview({source,draft});
 const keys=['caseId','sourceRgbaSha256','labelsSha256','width','height','paintedPixels',
  'excludedPixels','originalRgbMismatchPixels','rectangles','vertices','svg',
  'svgBytes','fullSourceColorClasses'];
 if(keys.some(k=>candidate[k]!==baseline[k])||
 JSON.stringify(candidate.colorLayers)!==JSON.stringify(baseline.colorLayers)||
 candidate.semanticPixelHumanApproved!==0||candidate.realHumanReviewersAuthenticated!==0||
 candidate.originalSubjectVsBackgroundVerified!==false||
 candidate.fullCharacterSemanticTruth!==false||
 candidate.wholeCharacterBudgetApproved!==false||
 candidate.paintAuthorized!==false||candidate.releaseAuthorized!==false||
 candidate.status!=='SOURCE_EXACT_RGB_UNTRUSTED_PARTIAL_PREVIEW_HOLD')
 fail('SOURCE_EXACT_PREVIEW_TAMPERED');
 return {version:VERSION,caseId:baseline.caseId,originalSourceRgbExact:true,
  independentlyHumanReviewedPixels:0,fullSubjectVerified:false,
  releaseAuthorized:false,status:'LOSSLESS_SOURCE_RGB_REPLAY_PASS_GOLDEN_HOLD'};
}
export function evaluateExactRgbSceneCap(preview){
 if(!preview||preview.version!==VERSION||!['GC001','Raden'].includes(preview.caseId)||
 !Number.isSafeInteger(preview.vertices)||preview.vertices<4)fail('SOURCE_EXACT_SCENE_CANDIDATE_INVALID');
 const numericCap=preview.caseId==='GC001'?1887:1412;
 return {version:VERSION,caseId:preview.caseId,numericStage8Cap:numericCap,
  originalRgbExactPartialVertices:preview.vertices,overCapBy:Math.max(0,preview.vertices-numericCap),
  numericCapMetForPartialMask:preview.vertices<=numericCap,
  allBodyPixelsProven:false,trueWholeCharacterVerticesMeasured:false,
  sourceColorCorrectnessIndependentlyVerifiedByHuman:false,
  fullSceneApproved:false,releaseAuthorized:false,status:'SOURCE_EXACT_PARTIAL_MASK_SCENE_CAP_NOT_COMPARABLE'};
}
