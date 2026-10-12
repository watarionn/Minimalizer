/** MinimalizerPublic P0 Stage12: source-exact pixel-edge contour graph.
 * Research only; no geometry inferred between disconnected source pixels.
 * The vector path is a literal boundary encoding of SHA pinned observations;
 * each source pixel is represented only when independently present in the mask.
 * This can exceed production complexity budgets and must not be promoted.
 */
export const VERSION='structural-p0-stage12-contour-graph-v1';
const typed=a=>a instanceof Uint8Array||a instanceof Uint8ClampedArray;
const shaPattern=/^[0-9a-f]{64}$/;
const fail=s=>{throw new TypeError(s);};
const E=(x,y,d)=>`${x},${y},${d}`;
const key=(x,y)=>`${x},${y}`;
async function hash(x){if(!globalThis.crypto?.subtle)fail('SHA256_UNAVAILABLE');return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',x))].map(x=>x.toString(16).padStart(2,'0')).join('');}
const dx=[1,0,-1,0],dy=[0,1,0,-1];
function trace(mask,w,h){
 const edges=[],out=new Map();
 const add=(x,y,d)=>{const id=edges.length;edges.push({x,y,d});const a=key(x,y);if(!out.has(a))out.set(a,[]);out.get(a).push(id);};
 // Clockwise perimeter of an occupied pixel. Neighbors block shared edges.
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  const i=y*w+x;if(!mask[i])continue;
  if(y===0||!mask[i-w])add(x,y,0);
  if(x===w-1||!mask[i+1])add(x+1,y,1);
  if(y===h-1||!mask[i+w])add(x+1,y+1,2);
  if(x===0||!mask[i-1])add(x,y+1,3);
 }
 const seen=new Uint8Array(edges.length),loops=[];
 for(let start=0;start<edges.length;start++){
  if(seen[start])continue;
  let at=start,raw=[],steps=0;
  while(true){
   if(seen[at])fail('NONMANIFOLD_CONTOUR_REPEAT');
   const e=edges[at];seen[at]=1;raw.push([e.x,e.y]);steps++;
   if(steps>edges.length)fail('LOOP_WALK_EXCEEDED');
   const nx=e.x+dx[e.d],ny=e.y+dy[e.d],nexts=out.get(key(nx,ny))||[];
   const candidates=nexts.filter(i=>!seen[i]);
   if(!candidates.length){
    if(nx!==edges[start].x||ny!==edges[start].y)fail('OPEN_SOURCE_BOUNDARY');
    break;
   }
   // Right turn resolves diagonal corner contact as separate 4-connected rings.
   const preferred=[(e.d+1)%4,e.d,(e.d+3)%4,(e.d+2)%4];
   candidates.sort((a,b)=>preferred.indexOf(edges[a].d)-preferred.indexOf(edges[b].d)||a-b);
   at=candidates[0];
  }
  if(raw.length<4)fail('DEGENERATE_LOOP');
  const compressed=[];
  for(let j=0;j<raw.length;j++){
   const a=raw[(j+raw.length-1)%raw.length],b=raw[j],c=raw[(j+1)%raw.length];
   const straight=(a[0]===b[0]&&b[0]===c[0])||(a[1]===b[1]&&b[1]===c[1]);
   if(!straight)compressed.push(b);
  }
  if(compressed.length<4)fail('DEGENERATE_COMPRESSED_RING');
  loops.push(compressed);
 }
 if(seen.some(v=>!v))fail('UNTRACED_BOUNDARY_EDGE');
 return {rings:loops,rawBoundaryEdges:edges.length};
}
function rasterize(rings,w,h){
 const output=new Uint8Array(w*h);
 // Even-odd scanline parity works for holes, detached components and corner contact.
 for(let y=0;y<h;y++){
  const xs=[];
  for(const pts of rings)for(let i=0;i<pts.length;i++){
   const a=pts[i],b=pts[(i+1)%pts.length];
   if(a[0]!==b[0])continue;
   if(y>=Math.min(a[1],b[1])&&y<Math.max(a[1],b[1]))xs.push(a[0]);
  }
  xs.sort((a,b)=>a-b);
  if(xs.length%2!==0)fail('ODD_SCANLINE_INTERSECTIONS');
  for(let j=0;j<xs.length;j+=2){
   if(xs[j]<0||xs[j+1]>w||xs[j]>=xs[j+1])fail('INVALID_SCANLINE_BOUNDS');
   for(let x=xs[j];x<xs[j+1];x++)output[y*w+x]=255;
  }
 }
 return output;
}
export function rasterizeSourceRings({rings,width,height}){
 if(!Array.isArray(rings)||!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000)fail('INVALID_RASTER');
 return rasterize(rings,width,height);
}
function svgPath(rings){return rings.map(pts=>'M'+pts.map(([x,y])=>`${x} ${y}`).join('L')+'Z').join('');}
/** Return source-exact vector rings. This does NOT certify a semantic feature. */
export async function traceSourceContours({width,height,faceMask,features,maxVertices=5000}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000)fail('INVALID_DIMENSIONS');
 const n=width*height;
 if(!typed(faceMask)||faceMask.length!==n||Array.from(faceMask).some(v=>v!==0&&v!==255))fail('INVALID_FACE_MASK');
 if(!Array.isArray(features)||features.length<1||features.length>8)fail('INVALID_FEATURES');
 if(!Number.isInteger(maxVertices)||maxVertices<4||maxVertices>20000)fail('INVALID_VERTEX_BUDGET');
 const seen=new Uint8Array(n),parts=[],ids=new Set();let vertices=0,rawEdges=0;
 for(const f of features){
  if(!f||typeof f.id!=='string'||!/^([a-z][a-z0-9_-]{0,47})$/.test(f.id)||ids.has(f.id)||
     f.evidenceLevel!=='research_observation'||typeof f.evidenceRef!=='string'||!f.evidenceRef.trim()||
     !typed(f.mask)||f.mask.length!==n||!shaPattern.test(f.maskSha256||''))fail('UNSIGNED_OBSERVATION');
  ids.add(f.id);
  if(await hash(f.mask)!==f.maskSha256)fail('MASK_SHA_MISMATCH');
  let pixels=0;
  for(let i=0;i<n;i++){
   const v=f.mask[i];if(v!==0&&v!==255)fail('NONBINARY_FEATURE_MASK');
   if(v){if(faceMask[i])fail('FACE_CONFLICT');if(seen[i])fail('CROSS_FEATURE_OVERLAP');seen[i]=1;pixels++;}
  }
  if(pixels<20)fail('TINY_UNSUPPORTED_OBSERVATION');
  const {rings,rawBoundaryEdges}=trace(f.mask,width,height);
  const proof=rasterize(rings,width,height);
  for(let i=0;i<n;i++)if(proof[i]!==f.mask[i])fail('SOURCE_CONTOUR_RASTER_MISMATCH');
  const count=rings.reduce((n,r)=>n+r.length,0);
  vertices+=count;rawEdges+=rawBoundaryEdges;
  if(vertices>maxVertices)fail('EXPLICIT_SOURCE_RING_VERTEX_BUDGET');
  parts.push({id:f.id,role:f.role,sourceMaskSha256:f.maskSha256,observedPixels:pixels,
   coveredPixels:pixels,coverage:1,discardedPixels:0,rings,vertexCount:count,rawBoundaryEdges,
   pathD:svgPath(rings),fillRule:'evenodd',semanticAuthority:'research_observation_only'});
 }
 return {version:VERSION,parts,totalVertices:vertices,rawBoundaryEdges:rawEdges,
  sourcePixelCoverage:1,allGeometrySourceContained:true,faceUnchanged:true,
  originalMaskMutation:false,originalSourceOnly:true,humanGoldenApproved:false,productPromotionAuthorized:false};
}
