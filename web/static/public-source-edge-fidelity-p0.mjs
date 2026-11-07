/** P0 Stage156-162. Pixelwise ORIGINAL-RGB and source-color-edge fidelity.
 * These source color edges are NOT human-confirmed anatomy or foreground.
 * Historical owner labels, even when matching, are untrusted semantic proposals.
 */
import{validateUntrustedFullFrameDraft}from'./public-fullframe-review-p0.mjs';
export const VERSION='p0-stage156-162-source-rgb-edge-audit-hold-v1';
const fail=s=>{throw new TypeError(s)};
const labelsEligible=new Set([2,4,5,6,7,8,9]);
const colorL1=(a,ai,b,bi)=>Math.abs(a[ai]-b[bi])+Math.abs(a[ai+1]-b[bi+1])+Math.abs(a[ai+2]-b[bi+2]);
const sumRgbDelta=(a,i,b,j)=>Math.abs(a[i]-b[j])+Math.abs(a[i+1]-b[j+1])+Math.abs(a[i+2]-b[j+2]);
function getAuditSettings({contrastThreshold=90,tileSize=32}={}){
 if(!Number.isInteger(contrastThreshold)||contrastThreshold<1||contrastThreshold>765)fail('EDGE_CONTRAST_THRESHOLD_INVALID');
 if(![8,16,32,64].includes(tileSize))fail('EDGE_TILE_SIZE_INVALID');
 return{contrastThreshold,tileSize};
}
export async function auditOriginalSourceColorEdges({source,draft,renderedRgba,options={}}){
 const opt=getAuditSettings(options);
 const v=await validateUntrustedFullFrameDraft({...source,draft});
 const{width,height,sourceRgba:original}=source,n=width*height;
 if(!(renderedRgba instanceof Uint8Array||renderedRgba instanceof Uint8ClampedArray)||
 renderedRgba.length!==4*n)fail('SOURCE_EDGE_RENDERED_RGBA_REQUIRED');
 const selected=new Uint8Array(n),errors=[],cols=Math.ceil(width/opt.tileSize);
 const tiles=[];
 for(let y=0;y<height;y+=opt.tileSize)for(let x=0;x<width;x+=opt.tileSize){
  tiles.push({bbox:[x,y,Math.min(x+opt.tileSize,width),Math.min(y+opt.tileSize,height)],
   selectedOriginalPixels:0,changedRgbPixels:0,sumOriginalRgbL1:0,
   selectedMaskBoundaryLinks:0,highContrastInteriorLinks:0,highContrastLinksLost:0,
   artificialHighContrastLinks:0,sourceContrastDistortionL1:0,
   humanSemanticPixelsCertified:0});
 }
 let selectedCount=0,wrongRgb=0,rgbL1=0,worstL1=0,sourceRgbSse=0;
 let maskBoundary=0,interiorLinks=0,originalHigh=0,outputHigh=0,retained=0,lost=0,invented=0,contrastError=0;
 const roleAt=i=>labelsEligible.has(v.labels[i]);
 const tileAt=i=>tiles[Math.floor(Math.floor(i/width)/opt.tileSize)*cols+Math.floor((i%width)/opt.tileSize)];
 for(let i=0;i<n;i++){
  const painted=roleAt(i),j=4*i,alpha=renderedRgba[j+3],tile=tileAt(i);
  selected[i]=painted?255:0;
  if(painted){
   if(original[j+3]!==255||alpha!==255)fail('SOURCE_EDGE_SELECTED_ALPHA_CHANGED');
   const e=colorL1(original,j,renderedRgba,j);
   errors.push(e);selectedCount++;rgbL1+=e;tile.selectedOriginalPixels++;tile.sumOriginalRgbL1+=e;
   if(e){wrongRgb++;tile.changedRgbPixels++;}worstL1=Math.max(worstL1,e);
   for(let k=0;k<3;k++){const d=original[j+k]-renderedRgba[j+k];sourceRgbSse+=d*d;}
  }else if(alpha!==0||renderedRgba[j]||renderedRgba[j+1]||renderedRgba[j+2]){
   fail('SOURCE_EDGE_PAINT_OUTSIDE_UNTRUSTED_MEMBERSHIP');
  }
  for(const neighbor of [(i%width+1<width)?i+1:-1,(i+width<n)?i+width:-1]){
   if(neighbor<0)continue;
   const a=painted,b=roleAt(neighbor);
   if(a!==b){maskBoundary++;tile.selectedMaskBoundaryLinks++;continue;}
   if(!a||v.labels[i]!==v.labels[neighbor])continue; // do NOT grant semantic neighbor ownership across labels
   interiorLinks++;
   const orig= sumRgbDelta(original,j,original,4*neighbor);
   const out= sumRgbDelta(renderedRgba,j,renderedRgba,4*neighbor);
   const origHigh=orig>=opt.contrastThreshold,outHigh=out>=opt.contrastThreshold;
   if(origHigh){originalHigh++;tile.highContrastInteriorLinks++;}
   if(outHigh)outputHigh++;
   if(origHigh&&outHigh)retained++;
   if(origHigh&&!outHigh){lost++;tile.highContrastLinksLost++;}
   if(!origHigh&&outHigh){invented++;tile.artificialHighContrastLinks++;}
   const err=Math.abs(orig-out);
   contrastError+=err;tile.sourceContrastDistortionL1+=err;
  }
 }
 errors.sort((a,b)=>a-b);
 const p95=errors.length?errors[Math.ceil(errors.length*.95)-1]:0;
 if(retained+lost!==originalHigh||retained+invented!==outputHigh)fail('EDGE_LINK_CONSERVATION');
 if(tiles.reduce((a,t)=>a+t.selectedOriginalPixels,0)!==selectedCount)fail('EDGE_SELECTED_TILE_CONSERVATION');
 return{version:VERSION,caseId:source.caseId,sourceRgbaSha256:source.sourceRgbaSha256,
  untrustedLabelsSha256:v.labelsSha256,options:opt,width,height,
  originalFullFramePixels:n,untrustedSelectedSourcePixels:selectedCount,
  rgbChangedSourcePixels:wrongRgb,totalRgbL1:rgbL1,meanRgbL1:selectedCount?rgbL1/selectedCount:0,
  maxPixelRgbL1:worstL1,p95PixelRgbL1:p95,sourceRgbSse,
  untrustedMaskBoundaryLinks:maskBoundary,
  withinUntrustedRoleNeighborPairs:interiorLinks,
  sourceHighContrastNeighborPairs:originalHigh,renderedHighContrastNeighborPairs:outputHigh,
  strongSourceColorEdgesRetained:retained,strongSourceColorEdgesLost:lost,
  renderedArtificialStrongColorEdges:invented,sourceColorContrastDistortionL1:contrastError,
  originalTiles:tiles,
  originalRgbEdgeMetricNotAnatomy:true,verifiedHumanSemanticPixels:0,
  bodySilhouetteGolden:false,sourceRoleSemanticsVerified:false,
  releaseAuthorized:false,status:'SOURCE_ONLY_RGB_EDGE_DIAGNOSTIC_GOLDEN_HOLD'};
}
/** Review PRIORITIES from computed source RGB only; not semantic human votes. */
export function buildSourceColorManualReviewAgenda(audit,{maxTiles=256}={}){
 if(!audit||audit.version!==VERSION||!Array.isArray(audit.originalTiles)||
 !Number.isInteger(maxTiles)||maxTiles<1||maxTiles>256)
  fail('SOURCE_RGB_REVIEW_AGENDA_INVALID');
 const rows=audit.originalTiles.map((tile,i)=>({
  tileIndex:i,sourceBounds:tile.bbox,
  priorityScore:tile.highContrastLinksLost*8+tile.artificialHighContrastLinks*6+
   tile.sourceContrastDistortionL1+tile.selectedMaskBoundaryLinks*2,
  selectedOriginalRgbPixels:tile.selectedOriginalPixels,
  originalMaskBoundaryLinks:tile.selectedMaskBoundaryLinks,
  sourceRgbHighContrastLost:tile.highContrastLinksLost,
  artificialSourceColorEdges:tile.artificialHighContrastLinks,
  sourceColorContrastError:tile.sourceContrastDistortionL1,
  requiredManualReviewTopics:['is_this_subject_or_background','left_right_arm_and_hand',
   'sleeve_skin_transition','neckwear_collars','fine_hair','face_features_must_be_omitted'],
  humanReviewerAssigned:false,manuallyCertifiedPixels:0
 }));
 rows.sort((a,b)=>b.priorityScore-a.priorityScore||a.tileIndex-b.tileIndex);
 return{version:VERSION,caseId:audit.caseId,
  sourceRgbaSha256:audit.sourceRgbaSha256,
  untrustedLabelsSha256:audit.untrustedLabelsSha256,
  totalOriginalTiles:rows.length,returnedHighestPriorityTiles:rows.slice(0,maxTiles),
  remainingSourceTilesNotDroppedFromFullFrame:audit.originalTiles.length,
  independentReviewersVerified:0,semanticHumanGolden:false,
  productReleaseAuthorized:false,status:'SOURCE_COLOR_PRIORITY_ONLY_MANUAL_REVIEW_STILL_REQUIRED'};
}
