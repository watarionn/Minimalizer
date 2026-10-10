// MinimalizerPublic StructuralRecovery P0 Stage3. Source-signed selective apparel
// plane replay. Experimental, non-generative, not imported into a product route.
export const VERSION='public-apparel-selective-p0-stage3-v1';
const MAX=400*400;
const MATERIALS=['dark_uniform','white_shirt','green_necktie'];
const PRECISION={dark_uniform:.60,white_shirt:.74,green_necktie:.82};
const MIN_GAIN=.008;
function fail(code){throw new TypeError(code);}
function maskCheck(a,n,label,allowEmpty=false){
 if(!(a instanceof Uint8Array||a instanceof Uint8ClampedArray)||a.length!==n)fail(label+':invalid_mask');
 let count=0;for(const x of a){if(x!==0&&x!==255)fail(label+':not_binary');if(x)count++;}
 if(!allowEmpty&&!count)fail(label+':empty');return count;
}
function rgbaCheck(a,n,label){if(!(a instanceof Uint8Array||a instanceof Uint8ClampedArray)||a.length!==n*4)fail(label+':invalid_RGBA');}
function pinCheck(p){if(typeof p!=='string'||!/^[0-9a-f]{64}$/.test(p))fail('invalid_sha256_pin');}
async function digest(x){if(!globalThis.crypto?.subtle)fail('SHA256_unavailable');
 return Array.from(new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',x)),
  v=>v.toString(16).padStart(2,'0')).join('');}
async function requirePin(bytes,pin){pinCheck(pin);if(await digest(bytes)!==pin)fail('SHA256_mismatch');}
function inClass(src,o,material){let r=src[o],g=src[o+1],b=src[o+2];
 if(material==='dark_uniform')return Math.max(r,g,b)<115;
 if(material==='white_shirt')return Math.min(r,g,b)>175&&Math.max(r,g,b)-Math.min(r,g,b)<55;
 return g>r+30&&g>b+25;
}
function validColor(value){return Array.isArray(value)&&value.length===3&&value.every(v=>Number.isInteger(v)&&v>=0&&v<=255);}
function distance(a,off,c){let r=a[off]-c[0],g=a[off+1]-c[1],b=a[off+2]-c[2];return r*r+g*g+b*b;}
/**
 * Replay only preexisting, externally authored polygons rasterized to binary masks.
 * The source PNG SHA, signed Stage8 owner PNG SHA and historical SA10.36 plan
 * SHA must be verified by the calling provenance runner before this function.
 * Here additionally pin the decoded source, baseline, face and owner bytes.
 * An author supplied 'evidenceRef' is not proof of independent approval.
 * No polygon or semantic part is inferred. No source image is ever returned.
 */
export async function replaySelectiveApparel({width,height,sourceRgba,sourceRgbaSha256,
 baselineRgba,baselineRgbaSha256,parentMask,parentMaskSha256,
 protectedMask,protectedMaskSha256,panels=[],maxAdditionalVertices=48}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>MAX)fail('invalid_dimensions');
 const n=width*height;
 rgbaCheck(sourceRgba,n,'source');rgbaCheck(baselineRgba,n,'baseline');
 maskCheck(parentMask,n,'parent');maskCheck(protectedMask,n,'protected',true);
 await Promise.all([[sourceRgba,sourceRgbaSha256],[baselineRgba,baselineRgbaSha256],
   [parentMask,parentMaskSha256],[protectedMask,protectedMaskSha256]].map(([b,h])=>requirePin(b,h)));
 if(!Array.isArray(panels)||panels.length>8)fail('invalid_panels');
 if(!Number.isInteger(maxAdditionalVertices)||maxAdditionalVertices<0||maxAdditionalVertices>128)fail('invalid_vertex_cap');
 let vertices=0,previous=-1;
 const out=new Uint8ClampedArray(baselineRgba);const changed=new Uint8Array(n);const audits=[];
 for(let k=0;k<panels.length;k++){
  const p=panels[k];if(!p||!MATERIALS.includes(p.material))fail('unknown_material');
  const rank=MATERIALS.indexOf(p.material);if(rank<previous)fail('source_panel_order_violation');previous=rank;
  if(p.owner!=='lower_body'||typeof p.evidenceRef!=='string'||!p.evidenceRef.trim()||
    p.semanticApproval===true)fail('unsigned_semantic_authority');
  if(!Number.isInteger(p.vertexCount)||p.vertexCount<3||p.vertexCount>16)fail('invalid_polygon_budget');
  vertices+=p.vertexCount;if(vertices>maxAdditionalVertices)fail('vertex_budget_exceeded');
  if(!validColor(p.colorRgbObserved))fail('source_RGB_required');
  maskCheck(p.mask,n,'panel');await requirePin(p.mask,p.maskSha256);
  let count=0,match=0,colorSeen=false,before=0,after=0;
  for(let i=0;i<n;i++)if(p.mask[i]){
   if(!parentMask[i]||protectedMask[i]||sourceRgba[i*4+3]!==255)fail('outside_source_owned_boundary');
   const o=i*4;let valid=inClass(sourceRgba,o,p.material);
   match+=Number(valid);count++;
   if(valid && sourceRgba[o]===p.colorRgbObserved[0]&&
    sourceRgba[o+1]===p.colorRgbObserved[1]&&sourceRgba[o+2]===p.colorRgbObserved[2])colorSeen=true;
   before+=distance(out,o,[sourceRgba[o],sourceRgba[o+1],sourceRgba[o+2]]);
   const c=p.colorRgbObserved;
   after+=distance(sourceRgba,o,c);
  }
  const precision=match/count;
  if(!colorSeen)fail('source_RGB_color_not_present_in_matched_panel');
  if(precision<PRECISION[p.material])fail('source_color_precision_below_floor');
  // Source-shaped green tie cannot swell against actual observed green owner.
  if(p.material==='green_necktie'){
   let green=0,lo=width,hi=-1,polyLo=width,polyHi=-1;
   for(let i=0;i<n;i++){
    if(parentMask[i]&&!protectedMask[i]&&sourceRgba[i*4+3]===255&&inClass(sourceRgba,i*4,p.material)){
      green++;lo=Math.min(lo,i%width);hi=Math.max(hi,i%width);
    }
    if(p.mask[i]){polyLo=Math.min(polyLo,i%width);polyHi=Math.max(polyHi,i%width);}
   }
   if(count>green*1.10||polyLo<lo-2||polyHi>hi+2)fail('necktie_growth');
  }
  const improved=before>0&&after<before*(1-MIN_GAIN);
  if(improved)for(let i=0;i<n;i++)if(p.mask[i]){
   const off=i*4,c=p.colorRgbObserved;
   out[off]=c[0];out[off+1]=c[1];out[off+2]=c[2];changed[i]=255;
  }
  audits.push({material:p.material,evidenceRef:p.evidenceRef,pixels:count,
   materialPrecision:Number(precision.toFixed(6)),vertices:p.vertexCount,
   originalSquaredRgbError:before,proposedSquaredRgbError:after,
   sourceColorFromOriginal:true,accepted:improved,
   reason:improved?'SOURCE_ERROR_IMPROVES':'SOURCE_ERROR_NOT_IMPROVED'});
 }
 let beforeTotal=0,afterTotal=0,changedPixels=0;
 for(let i=0;i<n;i++){
  const o=i*4;
  if(out[o+3]!==baselineRgba[o+3])throw new Error('alpha_changed');
  if((!parentMask[i]||protectedMask[i]||sourceRgba[o+3]!==255)&&
   (out[o]!==baselineRgba[o]||out[o+1]!==baselineRgba[o+1]||out[o+2]!==baselineRgba[o+2]))throw new Error('outside_owner_changed');
  if(parentMask[i]&&!protectedMask[i]&&sourceRgba[o+3]===255){
   beforeTotal+=distance(sourceRgba,o,[baselineRgba[o],baselineRgba[o+1],baselineRgba[o+2]]);
   afterTotal+=distance(sourceRgba,o,[out[o],out[o+1],out[o+2]]);
  }
  if(changed[i]&&(out[o]!==baselineRgba[o]||out[o+1]!==baselineRgba[o+1]||out[o+2]!==baselineRgba[o+2]))changedPixels++;
 }
 if(afterTotal>beforeTotal)throw new Error('source_error_regressed');
 return {rgba:out,audit:{version:VERSION,previewOnly:true,productPromotionAuthorized:false,
  geometryGenerated:false,sourcePixelColorsOnly:true,requiresExternalOriginalPngLineage:true,
  additionalGeometricVerticesProposed:vertices,sourceSquaredErrorBefore:beforeTotal,
  sourceSquaredErrorAfter:afterTotal,changedPixels,panels:audits}};
}
