/** Stage67: conservative source-observed spatial palette trial.
 * Historical owner mask is NOT verified anatomy. No drawing or automatic promotion.
 */
export const VERSION='p0-stage67-source-spatial-palette-v1';
const error=x=>{throw new TypeError(x)};
const typed=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const dist=(a,b)=>Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1])+Math.abs(a[2]-b[2]);
const rgbAt=(v,i)=>[v[i*4],v[i*4+1],v[i*4+2]];
function validate({width,height,sourceRgba,ownerMask,partition}){
 const n=width*height;if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||!typed(sourceRgba)||sourceRgba.length!==n*4||!typed(ownerMask)||ownerMask.length!==n||!partition||!typed(partition.assignments)||!Array.isArray(partition.palette)||partition.palette.length<1||partition.palette.length>16)error('INVALID_SPATIAL_SOURCE');
 const indices=new Int32Array(n).fill(-1);let k=0;
 for(let i=0;i<n;i++){if(ownerMask[i]!==0&&ownerMask[i]!==255)error('NONBINARY_SPATIAL_MASK');if(ownerMask[i]){if(sourceRgba[i*4+3]!==255)error('TRANSPARENT_SOURCE_OWNER');indices[i]=k++;}}
 if(k!==partition.assignments.length||k!==partition.pixels)error('SPATIAL_PARTITION_SIZE');
 for(const color of partition.palette)if(!Array.isArray(color)||color.length!==3||color.some(x=>!Number.isInteger(x)||x<0||x>255))error('INVALID_SPATIAL_PALETTE');
 for(const index of partition.assignments)if(index>=partition.palette.length)error('SPATIAL_LABEL_RANGE');
 return indices;
}
export function measureSourcePaletteTopology({width,height,sourceRgba,ownerMask,palette,assignments,indices=null,edgeThreshold=90,retainedThreshold=48}){
 const idx=indices??validate({width,height,sourceRgba,ownerMask,partition:{assignments,palette,pixels:assignments.length}});let colorL1=0,edgeCount=0,retainedEdges=0,createdEdges=0;
 const n=width*height,visited=new Uint8Array(n);let components=0;
 for(let i=0;i<n;i++)if(idx[i]>=0){const c=palette[assignments[idx[i]]];colorL1+=dist(rgbAt(sourceRgba,i),c);const x=i%width,y=Math.floor(i/width);
  for(const j of [x+1<width?i+1:-1,y+1<height?i+width:-1])if(j>=0&&idx[j]>=0){const contrast=dist(rgbAt(sourceRgba,i),rgbAt(sourceRgba,j)),pDiff=dist(c,palette[assignments[idx[j]]]);if(contrast>=edgeThreshold){edgeCount++;if(pDiff>=retainedThreshold)retainedEdges++;}else if(pDiff>=retainedThreshold)createdEdges++;}
  if(!visited[i]){components++;const stack=[i];visited[i]=1;while(stack.length){const at=stack.pop(),cx=at%width,cy=Math.floor(at/width),label=assignments[idx[at]];for(const j of [cx>0?at-1:-1,cx+1<width?at+1:-1,cy>0?at-width:-1,cy+1<height?at+width:-1])if(j>=0&&idx[j]>=0&&!visited[j]&&assignments[idx[j]]===label){visited[j]=1;stack.push(j);}}}
 }
 return {sourcePixels:assignments.length,colorL1,components,highContrastEdges:edgeCount,retainedHighContrastEdges:retainedEdges,unverifiedCreatedLowContrastEdges:createdEdges};
}
export function proposeSourceSpatialPalette({width,height,sourceRgba,ownerMask,partition,weakNeighborThreshold=65,extraErrorAllowance=18}){
 if(!Number.isInteger(weakNeighborThreshold)||weakNeighborThreshold<0||weakNeighborThreshold>765||!Number.isInteger(extraErrorAllowance)||extraErrorAllowance<0||extraErrorAllowance>200)error('INVALID_SPATIAL_OPTIONS');
 const idx=validate({width,height,sourceRgba,ownerMask,partition}),base=partition.assignments,proposal=base.slice(),palette=partition.palette;
 let changed=0,strongSourceContactsProtected=0;
 for(let i=0;i<idx.length;i++)if(idx[i]>=0){const y=Math.floor(i/width),x=i%width,source=rgbAt(sourceRgba,i);const contacts=[];
  for(const j of [x>0?i-1:-1,x+1<width?i+1:-1,y>0?i-width:-1,y+1<height?i+width:-1])if(j>=0&&idx[j]>=0){const contrast=dist(source,rgbAt(sourceRgba,j));if(contrast>weakNeighborThreshold){strongSourceContactsProtected++;continue;}contacts.push(base[idx[j]]);}
  const counts=new Map();for(const c of contacts)counts.set(c,(counts.get(c)||0)+1);
  const sorted=[...counts.entries()].sort((a,b)=>b[1]-a[1]||a[0]-b[0]);if(!sorted.length||sorted[0][1]<3||sorted[0][0]===base[idx[i]])continue;
  const chosen=sorted[0][0];if(dist(source,palette[chosen])>dist(source,palette[base[idx[i]]])+extraErrorAllowance)continue;
  proposal[idx[i]]=chosen;changed++;
 }
 const before=measureSourcePaletteTopology({width,height,sourceRgba,ownerMask,palette,assignments:base,indices:idx});
 const after=measureSourcePaletteTopology({width,height,sourceRgba,ownerMask,palette,assignments:proposal,indices:idx});
 // Full original-source criteria; do NOT sacrifice strong edges or invent weak-edge breaks.
 const good=changed>0&&after.components<before.components&&after.retainedHighContrastEdges>=before.retainedHighContrastEdges&&after.colorL1<=before.colorL1*1.01&&after.unverifiedCreatedLowContrastEdges<=before.unverifiedCreatedLowContrastEdges;
 return {version:VERSION,sourcePixels:base.length,changedPixels:changed,strongSourceContactsProtected,before,proposalMetrics:after,acceptedTrial:good,selectedAssignments:good?proposal:base.slice(),selection:good?'SPATIAL_TRIAL':'SOURCE_MEDOID_FALLBACK',anatomyVerified:false,sourceSilhouetteGoldenVerified:false,paintAuthorized:false,productionReleaseAuthorized:false};
}
