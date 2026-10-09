// MinimalizerPublic opt-in Clipper2-WASM geometry observer.
// Performs source-owner viewport intersections on COPIES only; never renders candidates.
import Clipper2Z from "./vendor/clipper2-wasm/clipper2z.mjs";

export const VERSION = "public-clipper2-source-exact-viewport-v1";
const SCALE=256;
const LIMIT=Object.freeze({shapes:8,rings:48,vertices:1600,pixels:160000,
  resultRings:128,resultVertices:3600});
let wasmPromise;
const base=(status)=>Object.freeze({version:VERSION,status,
  auditedShapes:0,exactShapes:0,rejectedShapes:0,skippedShapes:0,
  rasterDifferentPixels:0,candidateRings:0,applied:false});
export async function initialize() {
  if (!wasmPromise) {
    const url=new URL("./vendor/clipper2-wasm/clipper2z.wasm",import.meta.url).href;
    wasmPromise=Clipper2Z({locateFile:(name)=>{
      if(name!=="clipper2z.wasm")throw new Error("Unexpected WASM asset");
      return url;
    }});
  }
  return wasmPromise;
}
function ringsOf(shape) {
  return Array.isArray(shape?.rings)&&shape.rings.length
    ? shape.rings : [shape?.polygon];
}
function copyExactRing(points) {
  if (!Array.isArray(points) || points.length<3)return null;
  const flat=[];
  const cleaned=points.length>3 && Array.isArray(points[0]) &&
    Array.isArray(points.at(-1)) &&
    points[0][0]===points.at(-1)[0] &&
    points[0][1]===points.at(-1)[1] ? points.slice(0,-1) : points;
  if(cleaned.length<3)return null;
  for(const p of cleaned){
    if(!Array.isArray(p)||p.length!==2||
       !Number.isFinite(p[0])||!Number.isFinite(p[1]))return null;
    const x=p[0]*SCALE,y=p[1]*SCALE;
    // No silent rounding of original owners.
    if(!Number.isSafeInteger(x) || !Number.isSafeInteger(y) ||
       Math.abs(x)>10000000 || Math.abs(y)>10000000)return null;
    flat.push(x,y);
  }
  return {flat,cleaned:cleaned.map(p=>p.slice())};
}
function binaryDifference(a,b) {
  if(!a||!b||a.length!==b.length)return null;
  let n=0;
  for(let i=0;i<a.length;i++)if(a[i]!==b[i])n++;
  return n;
}
export function sourceOwnerInput(shape) {
  const loops=ringsOf(shape);
  if (!loops.length)return null;
  const converted=loops.map(copyExactRing);
  if(converted.some(x=>!x))return null;
  return {flat:converted.map(x=>x.flat),
    loops:converted.map(x=>x.cleaned),
    vertices:converted.reduce((n,x)=>n+x.cleaned.length,0)};
}
export function viewportClip(module, flatLoops, width,height) {
  const sources=new module.Paths64();
  const windows=new module.Paths64();
  let solution;
  try {
    for(const flat of flatLoops){
      const one=module.MakePath64(flat);
      try{sources.push_back(one);}finally{one.delete();}
    }
    const viewport=module.MakePath64([0,0,width*SCALE,0,
      width*SCALE,height*SCALE,0,height*SCALE]);
    try{windows.push_back(viewport);}finally{viewport.delete();}
    solution=module.Intersect64(sources,windows,module.FillRule.EvenOdd);
    const count=solution.size();
    if(count>LIMIT.resultRings)throw new Error("Result ring budget");
    const rings=[];let vertices=0;
    for(let i=0;i<count;i++){
      const ring=solution.get(i);
      try{
        const coordinates=ring.view();
        if(coordinates.length%3!==0)throw new Error("Malformed result");
        const points=[];
        for(let j=0;j<coordinates.length;j+=3){
          const x=Number(coordinates[j])/SCALE;
          const y=Number(coordinates[j+1])/SCALE;
          if(!Number.isFinite(x)||!Number.isFinite(y))
            throw new Error("Unsafe WASM result");
          points.push([x,y]);
        }
        if(points.length<3)throw new Error("Degenerate result");
        vertices+=points.length;
        if(vertices>LIMIT.resultVertices)throw new Error("Result point budget");
        rings.push(points);
      }finally{ring.delete();}
    }
    return rings;
  }finally{
    if(solution)solution.delete();
    sources.delete();
    windows.delete();
  }
}
export async function auditShapes(shapes,width,height,raster) {
  if(!Array.isArray(shapes)||!Number.isInteger(width)||
     !Number.isInteger(height)||width<1||height<1||
     width*height>LIMIT.pixels)return base("invalid-input");
  if(!raster||typeof raster.rasterizeLoops!=="function")return base("unavailable");
  let mod;
  try{mod=await initialize();}catch{return base("unavailable");}
  let auditedShapes=0,exactShapes=0,rejectedShapes=0,skippedShapes=0;
  let rasterDifferentPixels=0,candidateRings=0,processedRings=0,processedVertices=0;
  let truncated=false;
  try{
    for(const shape of shapes){
      if(auditedShapes>=LIMIT.shapes){truncated=true;break;}
      const source=sourceOwnerInput(shape);
      if(!source){skippedShapes++;continue;}
      if(processedRings+source.loops.length>LIMIT.rings||
         processedVertices+source.vertices>LIMIT.vertices){
        truncated=true;break;
      }
      processedRings+=source.loops.length;
      processedVertices+=source.vertices;
      const clipped=viewportClip(mod,source.flat,width,height);
      const original=raster.rasterizeLoops(source.loops,width,height,2);
      const candidate=raster.rasterizeLoops(clipped,width,height,2);
      const diff=binaryDifference(original,candidate);
      if(diff===null)throw new Error("Incomparable owner masks");
      rasterDifferentPixels+=diff;
      candidateRings+=clipped.length;
      auditedShapes++;
      if(diff===0)exactShapes++;else rejectedShapes++;
    }
    return Object.freeze({version:VERSION,
      status:truncated?"truncated":"ok",
      auditedShapes,exactShapes,rejectedShapes,skippedShapes,
      inputRings:processedRings,sourceVertices:processedVertices,
      candidateRings,rasterDifferentPixels,applied:false});
  }catch{
    return Object.freeze({version:VERSION,status:"error",
      auditedShapes,exactShapes,rejectedShapes,skippedShapes,
      inputRings:processedRings,sourceVertices:processedVertices,
      candidateRings,rasterDifferentPixels,applied:false});
  }
}
