/** Structural P0 Stage27: connected label inventory and source adjacency, not semantic classification. */
export const VERSION='structural-p0-stage27-annotation-topology-v1';
const err=x=>{throw new TypeError(x);};
export function inspectAnnotationTopology({width,height,labels,sourceRgba,minimumIslandPixels=18}){
 const n=width*height;if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||!(labels instanceof Uint8Array)||labels.length!==n||
 !(sourceRgba instanceof Uint8Array||sourceRgba instanceof Uint8ClampedArray)||sourceRgba.length!==4*n||!Number.isInteger(minimumIslandPixels)||minimumIslandPixels<1)err('INVALID_TOPOLOGY_INPUT');
 const seen=new Uint8Array(n),groups=[],edges=Array.from({length:5},()=>new Int32Array(5)),totals=new Int32Array(5);
 for(let i=0;i<n;i++){
  const v=labels[i];if(v>4)err('INVALID_SOURCE_LABEL');totals[v]++;
  const x=i%width,y=Math.floor(i/width);
  for(const [dx,dy] of [[1,0],[0,1]]){const xx=x+dx,yy=y+dy;if(xx>=width||yy>=height)continue;const w=labels[yy*width+xx];if(w!==v){edges[v][w]++;edges[w][v]++;}}
  if(!v||seen[i])continue;
  let count=0,contrast=0,originPixel=i,bbox=[width,height,0,0];const stack=[i];seen[i]=1;
  while(stack.length){const k=stack.pop(),px=k%width,py=Math.floor(k/width);count++;bbox[0]=Math.min(bbox[0],px);bbox[1]=Math.min(bbox[1],py);bbox[2]=Math.max(bbox[2],px+1);bbox[3]=Math.max(bbox[3],py+1);
   for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
    const xx=px+dx,yy=py+dy;if(xx<0||yy<0||xx>=width||yy>=height)continue;const q=yy*width+xx;
    if(labels[q]===v){if(!seen[q]){seen[q]=1;stack.push(q);}}
    else{const a=4*k,b=4*q;if(Math.abs(sourceRgba[a]-sourceRgba[b])+Math.abs(sourceRgba[a+1]-sourceRgba[b+1])+Math.abs(sourceRgba[a+2]-sourceRgba[b+2])>=96)contrast++;}
   }
  }
  groups.push({label:v,pixels:count,bbox,sourceContrastBoundaryEdges:contrast,smallIsland:count<minimumIslandPixels,originPixel});
 }
 groups.sort((a,b)=>a.label-b.label||b.pixels-a.pixels||a.originPixel-b.originPixel);
 return {version:VERSION,labelsCount:Array.from(totals),components:groups,componentCount:groups.length,smallIslands:groups.filter(x=>x.smallIsland).length,
  classAdjacency:edges.map(x=>Array.from(x)),sourceTopologicalObservationOnly:true,independentSemanticApproval:false,productPromotionAuthorized:false};
}
