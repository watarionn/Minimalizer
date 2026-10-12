/** Stage63: source-sampled diagnostic color planes, WITHOUT anatomical labeling or product painting. */
export const VERSION='p0-stage63-source-medoid-diagnostic-v1';
const fail=x=>{throw new TypeError(x)};
const medoid=(rgb,indices)=>{
 const xs=[0,1,2].map(c=>indices.map(i=>rgb[i*3+c]).sort((a,b)=>a-b)[indices.length>>1]);
 let best=indices[0],distance=Infinity;
 for(const i of indices){const d=Math.abs(rgb[3*i]-xs[0])+Math.abs(rgb[3*i+1]-xs[1])+Math.abs(rgb[3*i+2]-xs[2]);if(d<distance||(d===distance&&i<best)){best=i;distance=d;}}
 return [rgb[3*best],rgb[3*best+1],rgb[3*best+2]];
};
export function partitionObservedSourceColors({rgb,pixels,maxColors=6,minClusterPixels=24}){
 if(!(rgb instanceof Uint8Array||rgb instanceof Uint8ClampedArray)||!Number.isInteger(pixels)||pixels<1||pixels>160000||rgb.length!==pixels*3||!Number.isInteger(maxColors)||maxColors<1||maxColors>16||!Number.isInteger(minClusterPixels)||minClusterPixels<1||minClusterPixels>10000)fail('INVALID_SOURCE_COLOR_PARTITION');
 const groups=[Array.from({length:pixels},(_,i)=>i)];
 const details=g=>{const lo=[255,255,255],hi=[0,0,0];for(const i of g)for(let c=0;c<3;c++){const v=rgb[3*i+c];if(v<lo[c])lo[c]=v;if(v>hi[c])hi[c]=v;}const spreads=hi.map((h,c)=>h-lo[c]),axis=spreads.indexOf(Math.max(...spreads));return {axis,range:spreads[axis],score:spreads[axis]*g.length};};
 while(groups.length<maxColors){let chosen=-1,score=0;
  for(let j=0;j<groups.length;j++){const g=groups[j];if(g.length<2*minClusterPixels)continue;const d=details(g);if(d.range&&d.score>score){score=d.score;chosen=j;}}
  if(chosen<0)break;
  const g=groups[chosen],a=details(g).axis;
  const ordered=g.slice().sort((x,y)=>rgb[x*3+a]-rgb[y*3+a]||x-y),mid=Math.floor(ordered.length/2);
  if(rgb[ordered[0]*3+a]===rgb[ordered[ordered.length-1]*3+a])break;
  groups.splice(chosen,1,ordered.slice(0,mid),ordered.slice(mid));
 }
 const palette=groups.map(g=>medoid(rgb,g));const assignments=new Uint8Array(pixels);
 let colorL1=0;for(let j=0;j<groups.length;j++)for(const i of groups[j]){assignments[i]=j;for(let c=0;c<3;c++)colorL1+=Math.abs(rgb[i*3+c]-palette[j][c]);}
 const single=medoid(rgb,Array.from({length:pixels},(_,i)=>i));let singleColorL1=0;
 for(let i=0;i<pixels;i++)for(let c=0;c<3;c++)singleColorL1+=Math.abs(rgb[3*i+c]-single[c]);
 if(colorL1>singleColorL1)fail('PALETTE_WORSE_THAN_SINGLE_MEDOID');
 return {version:VERSION,pixels,clusterCounts:groups.map(g=>g.length),palette,assignments,colorL1,singleColorL1,measuredL1Reduction:singleColorL1-colorL1,
  medoidsAreOriginalSourceSamples:true,sourceAnatomyCertified:false,visualQualityCertified:false,productPaintAuthorized:false};
}
