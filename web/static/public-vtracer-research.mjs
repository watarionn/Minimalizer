// MinimalizerPublic opt-in VTracer WASM observer, strictly read-only.
// Traces ONLY the existing completed Public PNG canvas at bounded resolution.
// Candidate SVG is never returned, stored or applied to production rendering.
import initVTracer, {to_svg as traceRgba} from "./vendor/vtracer-wasm/vtracer.mjs";

export const VERSION = "public-vtracer-raster-observer-v1";
const MAX_SIDE=96;
const MAX_PIXELS=MAX_SIDE*MAX_SIDE;
const MAX_SVG_CHARS=140000;
const OPTIONS=Object.freeze({
  binary:false,mode:"polygon",hierarchical:"stacked",
  cornerThreshold:60,lengthThreshold:4,maxIterations:10,
  spliceThreshold:45,filterSpeckle:4,colorPrecision:6,
  layerDifference:16,pathPrecision:4,
});
let initPromise;
function unavailable(status) {
  return Object.freeze({version:VERSION,status,applied:false,
    tracedSvgBytes:0,changedPixels:null,pixelExact:false});
}
export function sampleSize(width,height){
  if(!Number.isInteger(width)||!Number.isInteger(height)||
    width<1||height<1||width>32768||height>32768)return null;
  const k=Math.min(1,MAX_SIDE/Math.max(width,height));
  const w=Math.max(1,Math.round(width*k)),h=Math.max(1,Math.round(height*k));
  if(w*h>MAX_PIXELS)return null;
  return {width:w,height:h,downsampled:k<1};
}
export function compareRgba(source,target){
  if(!source||!target||source.length!==target.length||
    source.length%4!==0)return null;
  let changedPixels=0,maxChannelDelta=0,absoluteChannelDelta=0;
  for(let i=0;i<source.length;i+=4){
    let different=false;
    for(let j=0;j<4;j++){
      const delta=Math.abs(source[i+j]-target[i+j]);
      maxChannelDelta=Math.max(maxChannelDelta,delta);
      absoluteChannelDelta+=delta;
      if(delta!==0)different=true;
    }
    if(different)changedPixels++;
  }
  return {changedPixels,maxChannelDelta,absoluteChannelDelta,
    meanAbsChannelDelta:Math.round(
      absoluteChannelDelta*1000/source.length)/1000,
    comparedPixels:source.length/4,pixelExact:changedPixels===0};
}
async function ensureWasm(){
  if(!initPromise){
    initPromise=(async()=>{
      const url=new URL("./vendor/vtracer-wasm/vtracer.wasm",import.meta.url);
      const response=await fetch(url);
      if(!response.ok)throw new Error("VTracer WASM unavailable");
      await initVTracer({module_or_path:new Uint8Array(await response.arrayBuffer())});
    })();
  }
  return initPromise;
}
export function traceCandidate(rgba,width,height){
  if(!(rgba instanceof Uint8Array)||rgba.length!==width*height*4||
    !Number.isInteger(width)||!Number.isInteger(height)||
    width<1||height<1||width*height>MAX_PIXELS){
    throw new Error("invalid bounded VTracer input");
  }
  // A standalone, disposable SVG. Its geometry may be lossy and cannot
  // become the MinimalizerPublic output without a separate release gate.
  const svg=traceRgba(rgba,width,height,{...OPTIONS});
  if(typeof svg!=="string"||svg.length>MAX_SVG_CHARS||
     !svg.includes("<svg")||!svg.includes("</svg>")||
     /<script|foreignObject|<image|\shref\s*=|xlink:href/i.test(svg))
    throw new Error("invalid or unsafe traced SVG");
  return svg;
}
async function svgToPixels(svg,width,height){
  const url=URL.createObjectURL(new Blob([svg],{type:"image/svg+xml"}));
  try{
    const img=new Image();
    img.src=url;
    await img.decode();
    const canvas=document.createElement("canvas");
    canvas.width=width;canvas.height=height;
    const ctx=canvas.getContext("2d",{willReadFrequently:true});
    if(!ctx)throw new Error("no canvas context");
    ctx.clearRect(0,0,width,height);
    ctx.drawImage(img,0,0,width,height);
    return ctx.getImageData(0,0,width,height).data;
  }finally{URL.revokeObjectURL(url);}
}
export async function auditCanvas(sourceCanvas){
  if(!sourceCanvas||!Number.isInteger(sourceCanvas.width)||
     !Number.isInteger(sourceCanvas.height))return unavailable("invalid-input");
  const size=sampleSize(sourceCanvas.width,sourceCanvas.height);
  if(!size)return unavailable("invalid-input");
  let svg;
  try {
    const canvas=document.createElement("canvas");
    canvas.width=size.width;canvas.height=size.height;
    const ctx=canvas.getContext("2d",{willReadFrequently:true});
    if(!ctx)throw new Error("no canvas context");
    ctx.drawImage(sourceCanvas,0,0,size.width,size.height);
    const rgba=ctx.getImageData(0,0,size.width,size.height).data;
    await ensureWasm();
    svg=traceCandidate(new Uint8Array(rgba),size.width,size.height);
    const raster=await svgToPixels(svg,size.width,size.height);
    const diff=compareRgba(rgba,raster);
    if(!diff)throw new Error("incomparable image data");
    return Object.freeze({version:VERSION,
      status:diff.pixelExact?"exact":"pixel-mismatch",...diff,
      sampleWidth:size.width,sampleHeight:size.height,
      downsampled:size.downsampled,
      tracedSvgBytes:new TextEncoder().encode(svg).length,
      sourceCanvasUntouched:true,applied:false});
  }catch(_){
    return unavailable("error");
  }
}
