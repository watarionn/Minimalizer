/** Stage64/65: high-contrast-edge retention + owner and source membership audit. No repaint. */
import {partitionObservedSourceColors} from './public-source-medoid-partition-p0.mjs';
export const VERSION='p0-stage65-source-color-boundary-diagnostic-hold-v1';
const bad=x=>{throw new TypeError(x)};
export function evaluateObservedColorBoundaries({width,height,originalRgba,ownerMask,partition,edgeThreshold=90,retainedThreshold=48}){
 const n=width*height;
 if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||originalRgba?.length!==4*n||ownerMask?.length!==n||!partition||partition.assignments?.length!==partition.pixels||!Array.isArray(partition.palette)||!Number.isInteger(edgeThreshold)||edgeThreshold<1||edgeThreshold>765||!Number.isInteger(retainedThreshold)||retainedThreshold<1||retainedThreshold>765)bad('INVALID_EDGE_DIAGNOSTIC');
 let total=0,detected=0,at=0,spill=0,sourcePixels=0;const index=new Int32Array(n).fill(-1);
 for(let i=0;i<n;i++){if(ownerMask[i]!==0&&ownerMask[i]!==255)bad('NONBINARY_OWNER');if(ownerMask[i]){index[i]=at++;sourcePixels++;}}
 if(at!==partition.pixels)bad('OWNER_PARTITION_SIZE_MISMATCH');
 const palette=partition.palette,assignment=partition.assignments;
 for(let i=0;i<n;i++)if(ownerMask[i]){
  const x=i%width,y=Math.floor(i/width),k=index[i],cluster=assignment[k];if(cluster>=palette.length)bad('PALETTE_INDEX_OUTSIDE_SOURCE');
  for(const j of [x+1<width?i+1:-1,y+1<height?i+width:-1])if(j>=0&&ownerMask[j]){
   const p=4*i,q=4*j;let contrast=0;for(let c=0;c<3;c++)contrast+=Math.abs(originalRgba[p+c]-originalRgba[q+c]);
   if(contrast>=edgeThreshold){total++;const a=palette[cluster],b=palette[assignment[index[j]]];let retained=0;for(let c=0;c<3;c++)retained+=Math.abs(a[c]-b[c]);if(retained>=retainedThreshold)detected++;}
  }
 }
 return {version:VERSION,sourcePixels,highContrastEdges:total,retainedHighContrastEdges:detected,retention:total?detected/total:null,spill,unassigned:0,
  reviewerApprovedPixels:0,semanticAuthority:false,automaticSourceColorPaint:false,productionReleaseAuthorized:false};
}
export async function runSourceColorDiagnostic({observation,maxColors=6,minClusterPixels=24}){
 if(!observation||!Array.isArray(observation.zones)||observation.zones.length!==2||observation.productionReleaseAuthorized!==false)bad('INVALID_OBSERVATION');
 const rows=[];
 for(const z of observation.zones){if(z.pixels===0)continue;const partition=partitionObservedSourceColors({rgb:z.rgb,pixels:z.pixels,maxColors,minClusterPixels});
  const edge=evaluateObservedColorBoundaries({width:observation.width,height:observation.height,originalRgba:observation.originalRgba,ownerMask:z.sourceMask,partition});
  rows.push({historicOwner:z.owner,sourcePixels:z.pixels,palette:partition.palette,clusterCounts:partition.clusterCounts,sourceColorL1:partition.colorL1,oneSourceMedoidL1:partition.singleColorL1,edge,
    hasSemanticReview:false,sourcePaletteNotReleaseArt:true});
 }
 return {version:VERSION,rows,sourcePixels:rows.reduce((a,x)=>a+x.sourcePixels,0),releaseVerdict:'HOLD_NO_INDEPENDENT_ANATOMY',paintAuthorized:false};
}
