// MinimalizerPublic-only opt-in independent WASM SVG raster audit.
// Read-only copies of existing owner rings. NEVER replace production render.
import { Resvg, initWasm } from "./vendor/resvg-wasm/index.mjs";

export const VERSION = "public-resvg-wasm-independent-raster-v1";
const LIMIT = Object.freeze({shapes:8, rings:48, vertices:1600, pixels:160000, chars:60000});
let initialized = null;
function invalid(status) {
  return Object.freeze({version:VERSION,status,shapesAudited:0,ringsAudited:0,
    differentPixels:null,totalPixels:0,maxChannelDelta:null,exactNativeParity:false,
    pngBytes:0,applied:false});
}
function makePath(points) {
  if (!Array.isArray(points) || points.length < 3) return null;
  const result=[];
  for (let i=0;i<points.length;i++) {
    const p=points[i];
    if (!Array.isArray(p) || p.length !== 2 ||
      !Number.isFinite(p[0]) || !Number.isFinite(p[1]) ||
      Math.abs(p[0]) > 1e6 || Math.abs(p[1]) > 1e6) return null;
    result.push((i ? "L" : "M") + p[0] + " " + p[1]);
  }
  return result.join(" ") + " Z";
}
export function makeSourceSvg(shapes, width, height) {
  if (!Array.isArray(shapes) || !Number.isInteger(width) ||
    !Number.isInteger(height) || width<1 || height<1 ||
    width*height>LIMIT.pixels) return {status:"invalid-input"};
  let seen=0,rings=0,vertices=0,chars=0,truncated=false;
  const paths=[];
  for (const shape of shapes) {
    if (seen >= LIMIT.shapes) {truncated=true;break;}
    if (!shape || !Array.isArray(shape.rgb) || shape.rgb.length !== 3 ||
      !shape.rgb.every(c=>Number.isInteger(c)&&c>=0&&c<=255))
      return {status:"invalid-shape"};
    const loops=Array.isArray(shape.rings)&&shape.rings.length
      ? shape.rings : [shape.polygon];
    if (!loops.length || loops.some(x=>!Array.isArray(x)))
      return {status:"invalid-shape"};
    const vertexCount=loops.reduce((n,loop)=>n+loop.length,0);
    if (rings+loops.length>LIMIT.rings || vertices+vertexCount>LIMIT.vertices) {
      truncated=true;break;
    }
    const chunks=loops.map(makePath);
    if (chunks.some(x=>x===null)) return {status:"invalid-ring"};
    const d=chunks.join(" ");
    if (chars+d.length>LIMIT.chars) {truncated=true;break;}
    paths.push('<path fill="rgb('+shape.rgb.join(",")+
      ')" fill-rule="evenodd" d="'+d+'"/>');
    seen++;rings+=loops.length;vertices+=vertexCount;chars+=d.length;
  }
  if (!seen) return {status:truncated?"bounded":"empty"};
  const svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+width+
    '" height="'+height+'" viewBox="0 0 '+width+' '+height+'">'+
    paths.join("")+'</svg>';
  return {status:truncated?"truncated":"ok",svg,seen,rings,vertices};
}
export function compareRgba(left,right) {
  if (!left || !right || left.length!==right.length || left.length%4!==0)
    return null;
  let differentPixels=0,maxChannelDelta=0,absoluteChannelDelta=0;
  for(let i=0;i<left.length;i+=4) {
    let diff=false;
    for(let j=0;j<4;j++) {
      const delta=Math.abs(left[i+j]-right[i+j]);
      if(delta) diff=true;
      maxChannelDelta=Math.max(maxChannelDelta,delta);
      absoluteChannelDelta+=delta;
    }
    if(diff) differentPixels++;
  }
  return {differentPixels,totalPixels:left.length/4,maxChannelDelta,
    absoluteChannelDelta,exactNativeParity:differentPixels===0};
}
async function ensureWasm() {
  if (!initialized) {
    initialized=(async()=>{
      const url=new URL("./vendor/resvg-wasm/index_bg.wasm",import.meta.url);
      const response=await fetch(url);
      if(!response.ok) throw new Error("resvg-wasm asset unavailable");
      // Initialize explicitly with self-hosted bytes, no CDN or remote fetch.
      await initWasm(new Uint8Array(await response.arrayBuffer()));
    })();
  }
  return initialized;
}
async function rgbaFromImage(bytes,mime,width,height) {
  const url=URL.createObjectURL(new Blob([bytes],{type:mime}));
  try {
    const image=new Image();
    image.src=url;
    await image.decode();
    const canvas=document.createElement("canvas");
    canvas.width=width;canvas.height=height;
    const context=canvas.getContext("2d",{willReadFrequently:true});
    if(!context) throw new Error("canvas unavailable");
    context.clearRect(0,0,width,height);
    context.drawImage(image,0,0,width,height);
    return context.getImageData(0,0,width,height).data;
  } finally { URL.revokeObjectURL(url); }
}
export async function auditShapes(shapes,width,height) {
  const source=makeSourceSvg(shapes,width,height);
  if(!source.svg) return invalid(source.status);
  const base={version:VERSION,shapesAudited:source.seen,
    ringsAudited:source.rings,vertices:source.vertices,
    totalPixels:width*height,sourceSvgBytes:new TextEncoder().encode(source.svg).length,
    applied:false};
  let renderer=null,rendered=null;
  try {
    await ensureWasm();
    renderer=new Resvg(source.svg,{fitTo:{mode:"original"},
      font:{loadSystemFonts:false}});
    if(renderer.width!==width || renderer.height!==height)
      throw new Error("renderer dimension mismatch");
    rendered=renderer.render();
    const png=rendered.asPng();
    const wasm=await rgbaFromImage(png,"image/png",width,height);
    const native=await rgbaFromImage(source.svg,"image/svg+xml",width,height);
    const diff=compareRgba(native,wasm);
    if(!diff) throw new Error("uncomparable pixels");
    return Object.freeze({...base,
      status:source.status==="truncated"?"truncated":"ok",
      ...diff,pngBytes:png.byteLength,renderer:"resvg-wasm@2.6.2"});
  } catch(_err) {
    return Object.freeze({...base,status:"error",differentPixels:null,
      maxChannelDelta:null,absoluteChannelDelta:null,exactNativeParity:false,
      pngBytes:0});
  } finally {
    if(rendered && typeof rendered.free==="function") rendered.free();
    if(renderer && typeof renderer.free==="function") renderer.free();
  }
}
