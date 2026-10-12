/**
 * MinimalizerPublic P0 Stage5 — source-observed large feature preservation.
 * Research-only candidate, never import into Public route without human Golden.
 * Inputs: SHA-pinned decoded original and frozen Public RGBA, historically signed
 * face mask, and individual SHA-pinned SOURCE-CLASS observation masks.
 * The observer decides only whether source pixel evidence exists. Color cannot
 * grant semantic authority: goggles/bows/corsets need independent human review.
 * No image generation, pixels from original color medoids only, no textures.
 */
export const VERSION = 'public-source-feature-preservation-p0-stage5-v1';
const ROLES=new Set(['eyewear','bow','corset_lacing','sleeve_ruffle','collar','held_object']);
const CLASSES=new Set(['high_neutral','low_dark','mid_neutral','cool_mid']);
const SHA=/^[0-9a-f]{64}$/;
const ID=/^[a-z][a-z0-9_-]{0,47}$/;
const MAX=400*400;
const fail=code=>{throw new TypeError(code);};
function checkRgba(a,n,role){if(!(a instanceof Uint8Array||a instanceof Uint8ClampedArray)||a.length!==4*n)fail(role+':invalid_RGBA');}
function checkMask(a,n,role,{allowEmpty=false}={}){
 if(!(a instanceof Uint8Array||a instanceof Uint8ClampedArray)||a.length!==n)fail(role+':invalid_mask');
 let count=0;for(const v of a){if(v!==0&&v!==255)fail(role+':nonbinary_mask');if(v)count++;}
 if(!allowEmpty&&!count)fail(role+':empty_mask');return count;
}
async function pin(bytes,digest,role){
 if(typeof digest!=='string'||!SHA.test(digest))fail(role+':invalid_SHA_pin');
 if(!globalThis.crypto?.subtle)fail('SHA256_not_available');
 const got=[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))]
  .map(v=>v.toString(16).padStart(2,'0')).join('');
 if(got!==digest)fail(role+':SHA_mismatch');
}
function inClass(a,o,k){
 const r=a[o],g=a[o+1],b=a[o+2];const mn=Math.min(r,g,b),mx=Math.max(r,g,b);
 if(k==='high_neutral')return mn>155&&(mx-mn)*255<=125*mx;
 if(k==='low_dark')return mx<85;
 if(k==='mid_neutral')return mx>69&&mx<151&&(mx-mn)*255<90*mx;
 if(k==='cool_mid')return g>=90&&b>=80&&r<175&&b>r+5;
 return false;
}
function sqDiff(c,a,o){const x=c[0]-a[o],y=c[1]-a[o+1],z=c[2]-a[o+2];return x*x+y*y+z*z;}
function medoid(a,pixelIndices){
 // True source-pixel medoid nearest the per-channel median. Never an RGB mean.
 const n=pixelIndices.length;
 const channels=[[],[],[]];for(const i of pixelIndices){const o=i*4;for(let k=0;k<3;k++)channels[k].push(a[o+k]);}
 const mid=channels.map(t=>{t.sort((x,y)=>x-y);return (t[(n-1)>>1]+t[n>>1])/2;});
 let best=-1,err=Infinity;for(const i of pixelIndices){const o=i*4;
  const d=(a[o]-mid[0])**2+(a[o+1]-mid[1])**2+(a[o+2]-mid[2])**2;
  if(d<err){err=d;best=i;}
 }
 const off=best*4;return [a[off],a[off+1],a[off+2]];
}
/**
 * Candidate masks are externally observed and NOT sufficient evidence of
 * semantic signing. Bounding boxes reject unbounded painting, but do not prove
 * e.g. that a dark bow mask is not hair. Golden must decide that separately.
 * Mask classes are checked against *every original source pixel*, not a sample.
 */
export async function replaySourceFeatureSurfaces({width,height,sourceRgba,sourceRgbaSha256,
 baselineRgba,baselineRgbaSha256,faceMask,faceMaskSha256,
 features,maxChangedPixels=20000}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>MAX)fail('invalid_dimensions');
 const n=width*height;checkRgba(sourceRgba,n,'source');checkRgba(baselineRgba,n,'baseline');
 checkMask(faceMask,n,'face');
 await Promise.all([[sourceRgba,sourceRgbaSha256,'source'],[baselineRgba,baselineRgbaSha256,'baseline'],[faceMask,faceMaskSha256,'face']].map(x=>pin(...x)));
 if(!Array.isArray(features)||features.length<1||features.length>8)fail('invalid_feature_count');
 if(!Number.isInteger(maxChangedPixels)||maxChangedPixels<0||maxChangedPixels>n)fail('invalid_pixel_budget');
 const output=new Uint8ClampedArray(baselineRgba),ownerSeen=new Uint8Array(n),observedSeen=new Uint8Array(n),ids=new Set();let changed=0;
 const records=[];
 for(const f of features){
  if(!f||typeof f.id!=='string'||!ID.test(f.id)||ids.has(f.id)||!ROLES.has(f.role)||!CLASSES.has(f.colorClass))fail('invalid_role_or_id');
  ids.add(f.id);
  if(f.evidenceLevel!=='research_observation'||typeof f.evidenceRef!=='string'||!f.evidenceRef.trim())fail('unsigned_feature_evidence');
  if(!Array.isArray(f.bbox)||f.bbox.length!==4||!f.bbox.every(Number.isInteger))fail('bbox_required');
  const [x0,y0,x1,y1]=f.bbox;
  if(x0<0||y0<0||x1>width||y1>height||x0>=x1||y0>=y1||
    (x1-x0)*(y1-y0)>Math.round(n*.25))fail('invalid_feature_roi');
  const count=checkMask(f.mask,n,f.id);await pin(f.mask,f.maskSha256,f.id);
  if(!Number.isInteger(f.maxPixels)||f.maxPixels<20||f.maxPixels>n||count<20||count>f.maxPixels)fail('feature_pixel_budget');
  const indices=[];
  for(let i=0;i<n;i++)if(f.mask[i]){
   const x=i%width,y=(i/width)|0,o=i*4;
   if(x<x0||x>=x1||y<y0||y>=y1)fail('pixel_outside_source_roi');
   if(faceMask[i])fail('facial_feature_guard');
   if(observedSeen[i])fail('feature_overlap_unresolved');
   if(sourceRgba[o+3]!==255||baselineRgba[o+3]!==255)fail('unsupported_alpha');
   if(!inClass(sourceRgba,o,f.colorClass))fail('not_original_source_color_class');
   indices.push(i);
  }
  for(const i of indices)observedSeen[i]=1;
  const color=medoid(sourceRgba,indices);
  let before=0,after=0;
  for(const i of indices){const o=i*4;before+=sqDiff([baselineRgba[o],baselineRgba[o+1],baselineRgba[o+2]],sourceRgba,o);
    after+=sqDiff(color,sourceRgba,o);}
  const improved=before>0&&after<before*.99;
  if(improved){for(const i of indices){const o=i*4;
    if(output[o]!==color[0]||output[o+1]!==color[1]||output[o+2]!==color[2])changed++;
    output[o]=color[0];output[o+1]=color[1];output[o+2]=color[2];ownerSeen[i]=1;
  }}
  records.push({id:f.id,role:f.role,sourceColorClass:f.colorClass,
    evidenceRef:f.evidenceRef,observedPixels:count,rgbSourceMedoid:color,
    baselineSourceSquaredError:before,candidateSourceSquaredError:after,
    acceptedAsResearchPreview:improved,semanticApproval:false,
    reason:improved?'SOURCE_COLOR_FIT_AND_GUARDS_PASS':'ABSTAIN_NO_RGB_GAIN'});
 }
 if(changed>maxChangedPixels)fail('total_pixel_budget_exceeded');
 for(let i=0;i<n;i++){
  const o=i*4;
  if(output[o+3]!==baselineRgba[o+3])throw Error('alpha_changed');
  if((faceMask[i]||!ownerSeen[i])&&
    (output[o]!==baselineRgba[o]||output[o+1]!==baselineRgba[o+1]||output[o+2]!==baselineRgba[o+2]))throw Error('outside_owner_or_face_changed');
 }
 return {rgba:output,audit:{version:VERSION,features:records,pixelsChanged:changed,
  originalSourceOnly:true,syntheticRGB:false,featureSourceObservationNotSemanticApproval:true,
  productPromotionAuthorized:false,productionRouteChanged:false,previewOnly:true}};
}
