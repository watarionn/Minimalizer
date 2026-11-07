/** MinimalizerPublic P0 Stage204: pixel-exact source-mask contour frontier.
 * Original source and reviewer masks are PRIVATE input only; this module has
 * no network/filesystem, performs no semantic inference and never issues Golden.
 */
export const VERSION='p0-stage204-source-exact-contour-frontier-hold-v1';
const fail=s=>{throw new TypeError(s)};
const isBytes=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const index=(x,y,w)=>y*(w+1)+x;
function validate(width,height,mask){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000||!isBytes(mask)||mask.length!==width*height)fail('STAGE204_INVALID_SOURCE_MASK');
 for(const v of mask)if(v!==0&&v!==255)fail('STAGE204_NONBINARY_SOURCE_MASK');
}
function rasterize({rings,width,height}){
 const out=new Uint8Array(width*height);
 for(let y=0;y<height;y++){
  const cy=y+0.5,intersections=[];
  for(const ring of rings)for(let i=0;i<ring.length;i++){
   const a=ring[i],b=ring[(i+1)%ring.length];
   if((a[1]<=cy&&cy<b[1])||(b[1]<=cy&&cy<a[1]))intersections.push(a[0]+(cy-a[1])*(b[0]-a[0])/(b[1]-a[1]));
  }
  intersections.sort((a,b)=>a-b);
  if(intersections.length%2)fail('STAGE204_ODD_PARITY');
  for(let i=0;i<intersections.length;i+=2){
   const left=Math.max(0,Math.ceil(intersections[i]-.5));
   const right=Math.min(width,Math.ceil(intersections[i+1]-.5));
   for(let x=left;x<right;x++)out[y*width+x]=255;
  }
 }
 return out;
}
export function buildExactObservedBoundary({caseId,width,height,mask}={}){
 if(!['GC001','Raden'].includes(caseId))fail('STAGE204_UNKNOWN_CASE');
 validate(width,height,mask);
 const n=width*height,inside=(x,y)=>x>=0&&y>=0&&x<width&&y<height&&mask[y*width+x]===255;
 const edges=[],depart=new Map();
 function edge(x0,y0,x1,y1,dir){
  const a=index(x0,y0,width),b=index(x1,y1,width),id=edges.length;
  edges.push({a,b,dir,x:x0,y:y0});
  if(!depart.has(a))depart.set(a,new Int32Array(4).fill(-1));
  const d=depart.get(a);
  if(d[dir]!==-1)fail('STAGE204_DUPLICATE_BOUNDARY');d[dir]=id;
 }
 let pixels=0;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  if(!inside(x,y))continue;pixels++;
  if(!inside(x,y-1))edge(x,y,x+1,y,0);
  if(!inside(x+1,y))edge(x+1,y,x+1,y+1,1);
  if(!inside(x,y+1))edge(x+1,y+1,x,y+1,2);
  if(!inside(x-1,y))edge(x,y+1,x,y,3);
 }
 const visited=new Uint8Array(edges.length),rings=[];
 for(let start=0;start<edges.length;start++){
  if(visited[start])continue;
  const points=[];let curr=start;
  do{
   if(visited[curr])fail('STAGE204_PREMATURE_LOOP');visited[curr]=1;
   const e=edges[curr];points.push([e.x,e.y]);
   const d=depart.get(e.b);if(!d)fail('STAGE204_OPEN_BOUNDARY');
   // Right turn preserves connectivity at diagonally touching corners.
   let next=-1;
   for(const turn of [1,0,3,2]){
    const k=d[(e.dir+turn)%4];
    if(k!==-1&&(k===start||!visited[k])){next=k;break}
   }
   if(next===-1)fail('STAGE204_OPEN_OR_REVISITED_BOUNDARY');curr=next;
  }while(curr!==start);
  // Remove collinear vertices, introducing no non-source coordinates.
  let changed=true;
  while(changed&&points.length>4){
   changed=false;const keep=[];
   for(let k=0;k<points.length;k++){
    const a=points[(k+points.length-1)%points.length],b=points[k],c=points[(k+1)%points.length];
    const dx=b[0]-a[0],dy=b[1]-a[1],ex=c[0]-b[0],ey=c[1]-b[1];
    if(dx*ey-dy*ex===0&&dx*ex+dy*ey>0){changed=true;continue}keep.push(b);
   }
   if(keep.length<4)fail('STAGE204_DEGENERATE_LOOP');
   points.splice(0,points.length,...keep);
  }
  if(points.length<4)fail('STAGE204_INVALID_RING');rings.push(points);
 }
 if(visited.some(v=>v!==1))fail('STAGE204_UNVISITED_BOUNDARY');
 const replay=rasterize({rings,width,height});let spills=0,loss=0;
 for(let i=0;i<n;i++){
  if(replay[i]&&!mask[i])spills++;
  if(!replay[i]&&mask[i])loss++;
 }
 if(spills||loss)fail('STAGE204_RASTER_REPLAY_FAIL');
 const vertices=rings.reduce((sum,r)=>sum+r.length,0);
 const pathD=rings.map(r=>'M'+r.map(([x,y])=>x+' '+y).join('L')+'Z').join('');
 const hist=caseId==='GC001'?1887:1412;
 return {version:VERSION,caseId,width,height,sourcePixels:pixels,boundaryEdges:edges.length,
  loops:rings.length,explicitVertices:vertices,pathD,
  fillRule:'evenodd',exactRasterReplay:true,spilledPixels:0,lostPixels:0,
  historicalVertexBudget:hist,withinHistoricNumericBudget:vertices<=hist,
  originalSourceModified:false,unknownPixelsFilled:0,independentlyCertifiedSemanticPixels:0,
  semanticGolden:false,fullBodyVerified:false,releaseAuthorized:false,
  status:'SOURCE_ONLY_MASK_EXACT_CONTOUR_RESEARCH_HOLD'};
}
