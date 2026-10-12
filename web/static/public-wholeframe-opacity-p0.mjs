/** Stages100-103 original opacity only. Opaque background included; NOT anatomy. */
import{exactSourceRectangleCover}from'./public-source-exact-rect-cover-p0.mjs';
export const VERSION='p0-stage100-103-original-opacity-diagnostic-hold-v1';
const fail=s=>{throw new TypeError(s)};
const hash=async b=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(v=>v.toString(16).padStart(2,'0')).join('');
const utf8=s=>new TextEncoder().encode(s).length;
function checkOriginal({caseId,width,height,originalRgba,originalRgbaSha256}){
 if(!['GC001','Raden'].includes(caseId)||!Number.isInteger(width)||!Number.isInteger(height)||
 width<1||height<1||width*height>160000||
 !(originalRgba instanceof Uint8Array||originalRgba instanceof Uint8ClampedArray)||
 originalRgba.length!==width*height*4||!/^[a-f0-9]{64}$/.test(originalRgbaSha256||''))fail('ORIGINAL_PIN_REQUIRED');
}
function coverage(mask,w,h,axis){
 if(axis==='vertical')return exactSourceRectangleCover({width:w,height:h,sourceMask:mask}).rectangles;
 const trans=new Uint8Array(mask.length);
 for(let y=0;y<h;y++)for(let x=0;x<w;x++)trans[x*h+y]=mask[y*w+x];
 return exactSourceRectangleCover({width:h,height:w,sourceMask:trans}).rectangles.map(([y0,x0,y1,x1])=>[x0,y0,x1,y1]);
}
const path=rects=>rects.map(([x0,y0,x1,y1])=>`M${x0} ${y0}h${x1-x0}v${y1-y0}h-${x1-x0}Z`).join('');
function verifyCover(rects,mask,w,h){
 const seen=new Uint8Array(mask.length);let pixels=0;
 for(const rect of rects){if(!Array.isArray(rect)||rect.length!==4||rect.some(x=>!Number.isSafeInteger(x)))fail('OPACITY_NONINTEGER_RECT');
  const [x0,y0,x1,y1]=rect;if(x0<0||y0<0||x1>w||y1>h||x1<=x0||y1<=y0)fail('OPACITY_BOUNDS');
  for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){const i=y*w+x;if(seen[i])fail('OPACITY_RECT_OVERLAP');seen[i]=255;pixels++;}
 }
 for(let i=0;i<mask.length;i++)if(mask[i]!==seen[i])fail('OPACITY_SOURCE_COVERAGE_MISMATCH');
 return pixels;
}
export async function buildOriginalOpaqueGeometry(source){
 checkOriginal(source);
 const {caseId,width,height,originalRgba,originalRgbaSha256}=source;
 if(await hash(originalRgba)!==originalRgbaSha256)fail('ORIGINAL_RGBA_SHA_MISMATCH');
 const mask=new Uint8Array(width*height);let opaque=0,nonOpaque=0,partial=0,alphaZero=0;
 for(let i=0;i<mask.length;i++){const a=originalRgba[i*4+3];if(a===255){mask[i]=255;opaque++;}
  else{nonOpaque++;if(a===0)alphaZero++;else partial++;}}
 const variants=['vertical','horizontal'].map(axis=>{
  const rects=coverage(mask,width,height,axis),d=path(rects);return {axis,rects,d,bytes:utf8(d)};
 }).sort((a,b)=>a.bytes-b.bytes||a.rects.length-b.rects.length);
 const best=variants[0];if(verifyCover(best.rects,mask,width,height)!==opaque)fail('OPACITY_AREA_MISMATCH');
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}"><path d="${best.d}" fill="#000"/></svg>`;
 return {version:VERSION,caseId,width,height,originalRgbaSha256,alpha255PixelCount:opaque,
  nonOpaquePixels:nonOpaque,partialAlphaPixels:partial,alphaZeroPixels:alphaZero,
  selectedAxis:best.axis,rectangles:best.rects,explicitVertices:best.rects.length*4,
  svg,svgBytes:utf8(svg),originalAlpha255MembershipExact:true,
  opaqueBackgroundMayBeIncluded:true,alphaFringeNotPainted:true,
  bodySilhouetteNotCertified:true,semanticHumanPixelsCertified:0,
  productionSvgAuthorized:false,status:'OPAQUE_ORIGINAL_ONLY_GOLDEN_HOLD'};
}
export function stage100Hold(){return {sourceOnly:true,subjectSilhouetteVerified:false,releaseAuthorized:false};}
