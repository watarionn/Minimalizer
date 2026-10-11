/**
 * P0 Stage7: observed-pixel-inscribed rectangles only. Research preview.
 * This is deliberately conservative: an axis-aligned rectangle may be used
 * only if EVERY pixel is in a SHA-pinned source-observation mask. No dilation,
 * inferred bridges, contour hallucination, source bitmap embedding or semantic
 * signing. The original silhouette remains separately unresolved.
 */
export const VERSION='structural-p0-stage7-source-exact-rectangles-v1';
const fail=x=>{throw new TypeError(x);};
const typed=a=>a instanceof Uint8Array||a instanceof Uint8ClampedArray;
const hex=/^[0-9a-f]{64}$/;
async function digest(a){return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');}
function bestRectangle(m,w,h){
 const histogram=new Int32Array(w);let best=null;
 for(let y=0;y<h;y++){
  const stack=[];
  for(let x=0;x<=w;x++){
   const height=x===w?0:(m[y*w+x]?++histogram[x]:(histogram[x]=0));
   let start=x;
   while(stack.length&&stack[stack.length-1].height>height){
    const bar=stack.pop();const a=bar.height*(x-bar.start);
    const candidate=[bar.start,y-bar.height+1,x,y+1];
    if(a>0&&(!best||a>best.area||(a===best.area&&(
      candidate[1]<best.rect[1]||(candidate[1]===best.rect[1]&&candidate[0]<best.rect[0])))))
      best={rect:candidate,area:a};
    start=bar.start;
   }
   if(height>0&&(!stack.length||stack[stack.length-1].height<height))stack.push({start,height});
  }
 }
 return best;
}
/** Only research-observed masks are accepted, never claims semantic attestation. */
export async function proposeSourceRectangles({width,height,faceMask,features,maxRectsPerFeature=8,
 minRectPixels=20,maxTotalVertices=160}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000)fail('invalid_dimensions');
 const n=width*height;
 if(!typed(faceMask)||faceMask.length!==n)fail('invalid_face_mask');
 if(!globalThis.crypto?.subtle)fail('SHA256_unavailable');
 if(!Array.isArray(features)||features.length<1||features.length>8)fail('invalid_features');
 if(!Number.isInteger(maxRectsPerFeature)||maxRectsPerFeature<1||maxRectsPerFeature>16||
 !Number.isInteger(minRectPixels)||minRectPixels<4||!Number.isInteger(maxTotalVertices)||maxTotalVertices<4||maxTotalVertices>256)fail('invalid_budget');
 const seen=new Uint8Array(n),ids=new Set(),records=[];let vertices=0;
 for(const v of faceMask)if(v!==0&&v!==255)fail('nonbinary_face');
 for(const f of features){
  if(!f||!f.id||ids.has(f.id)||f.evidenceLevel!=='research_observation'||!typed(f.mask)||f.mask.length!==n||
    typeof f.maskSha256!=='string'||!hex.test(f.maskSha256))fail('unverified_feature');
  ids.add(f.id);
  if(await digest(f.mask)!==f.maskSha256)fail('mask_SHA_mismatch');
  let original=0;for(let i=0;i<n;i++){
   const v=f.mask[i];if(v!==0&&v!==255)fail('nonbinary_feature');
   if(v){original++;if(faceMask[i])fail('face_collision');if(seen[i])fail('unresolved_feature_overlap');}
  }
  if(original<minRectPixels)fail('insufficient_observation');
  for(let i=0;i<n;i++)if(f.mask[i])seen[i]=1;
  const remaining=f.mask.slice();const rects=[];let area=0;
  while(rects.length<maxRectsPerFeature&&vertices+4<=maxTotalVertices){
   const v=bestRectangle(remaining,width,height);
   if(!v||v.area<minRectPixels)break;
   const [x0,y0,x1,y1]=v.rect;
   for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
    const i=y*width+x;if(f.mask[i]!==255||faceMask[i])throw Error('rectangle_outside_original_source_evidence');
    remaining[i]=0;
   }
   rects.push(v.rect);area+=v.area;vertices+=4;
  }
  records.push({id:f.id,role:f.role,rects,observedPixels:original,containedPixels:area,
   coverage:area/original,discardedPixels:original-area,vertices:rects.length*4,
   semanticAuthority:'research_observation_not_signed',previewOnly:true});
 }
 return {version:VERSION,parts:records,totalVertices:vertices,allGeometrySourceContained:true,
  originalMaskMutation:false,artisticQualityApproved:false,productPromotionAuthorized:false};
}
