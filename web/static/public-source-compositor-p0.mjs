/** Stage8: replay source-exact geometry using Stage5 color and Stage6 face guards. */
import {replaySourceFeatureSurfaces} from './public-source-feature-preservation-p0.mjs';
import {blankSignedFace} from './public-signed-face-blank-p0.mjs';
export const VERSION='structural-p0-stage8-conservative-compositor-v1';
const fail=s=>{throw new TypeError(s);};
const sha=async bytes=>[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
export async function compositeSourceGeometry({width,height,sourceRgba,sourceRgbaSha256,baselineRgba,baselineRgbaSha256,
 faceMask,faceMaskSha256,features,geometry,maxChangedPixels=20000,flatFace=true}){
 if(!geometry?.allGeometrySourceContained||!Array.isArray(geometry.parts)||geometry.parts.length!==features.length)fail('invalid_geometry');
 const n=width*height;if(!Number.isInteger(n)||n<1||n>160000)fail('invalid_dimensions');
 const featureById=new Map(features.map(x=>[x.id,x]));if(featureById.size!==features.length)fail('duplicate_feature_ids');
 const used=new Uint8Array(n),converted=[];let vertices=0;
 for(const part of geometry.parts){
  const f=featureById.get(part.id);if(!f||f.role!==part.role||!Array.isArray(part.rects)||part.rects.length>16)fail('geometry_owner_missing');
  const mask=new Uint8Array(n);let pixels=0;
  for(const rect of part.rects){
   if(!Array.isArray(rect)||rect.length!==4||!rect.every(Number.isInteger))fail('invalid_rectangle');
   const [x0,y0,x1,y1]=rect;if(x0<0||y0<0||x1>width||y1>height||x1<=x0||y1<=y0)fail('off_canvas_geometry');
   for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
    const i=y*width+x;
    if(f.mask[i]!==255)fail('geometry_not_in_observed_source');
    if(faceMask[i])fail('face_collision');
    if(used[i])fail('geometry_overlap_unresolved');
    used[i]=mask[i]=255;pixels++;
   }
   vertices+=4;
  }
  if(pixels!==part.containedPixels||pixels>part.observedPixels)fail('geometry_pixel_accounting');
  if(!pixels)continue;
  converted.push({...f,mask,maskSha256:await sha(mask),maxPixels:Math.max(pixels,f.maxPixels)});
 }
 if(vertices!==geometry.totalVertices)fail('geometry_vertex_accounting');
 let surfaces={rgba:new Uint8ClampedArray(baselineRgba),audit:{features:[],pixelsChanged:0}};
 if(converted.length){surfaces=await replaySourceFeatureSurfaces({width,height,sourceRgba,sourceRgbaSha256,
  baselineRgba,baselineRgbaSha256,faceMask,faceMaskSha256,features:converted,maxChangedPixels});}
 let face=null;
 if(flatFace){face=await blankSignedFace({width,height,sourceRgba,sourceRgbaSha256,
   baselineRgba:surfaces.rgba,baselineRgbaSha256:await sha(surfaces.rgba),
   signedFaceMask:faceMask,signedFaceMaskSha256:faceMaskSha256});}
 const rgba=face?face.rgba:surfaces.rgba;
 for(let i=0;i<n;i++){
  const o=i*4;if(rgba[o+3]!==baselineRgba[o+3])throw Error('alpha_mutation');
  if(!used[i]&&!faceMask[i]&&(rgba[o]!==baselineRgba[o]||rgba[o+1]!==baselineRgba[o+1]||rgba[o+2]!==baselineRgba[o+2]))throw Error('outside_authority_color_change');
 }
 return {rgba,audit:{version:VERSION,geometryVertices:vertices,featurePixelsChanged:surfaces.audit.pixelsChanged,
  faceFlattened:!!flatFace,facePixels:face?.audit?.facePixels||0,
  featureAudit:surfaces.audit.features,externalFaceFragmentsResolved:false,
  semanticAttestation:false,svgClipParityVerified:false,productPromotionAuthorized:false}};
}
