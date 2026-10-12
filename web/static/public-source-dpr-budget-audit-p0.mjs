/** Stage48: source-mask SHA and exact 340/680 lattice audit for research paths.
 * No semantic labels, painting, automatic promotion, or inferred geometry.
 */
export const VERSION='p0-stage48-dual-lattice-source-svg-budget-v1';
function rasterGeneral(rings,width,height,scale){
 const w=width*scale,h=height*scale,mask=new Uint8Array(w*h);
 for(let y=0;y<h;y++){
  const cy=y+.5,crosses=[];
  for(const ring of rings)for(let i=0;i<ring.length;i++){
   const a=ring[i],b=ring[(i+1)%ring.length];
   if((a[1]<=cy&&cy<b[1])||(b[1]<=cy&&cy<a[1]))crosses.push(a[0]+(cy-a[1])*(b[0]-a[0])/(b[1]-a[1]));
  }
  crosses.sort((a,b)=>a-b);
  if(crosses.length%2)throw new TypeError('ODD_DPR_PARITY');
  for(let k=0;k<crosses.length;k+=2){
   const start=Math.max(0,Math.ceil(crosses[k]-.5));
   const end=Math.min(w,Math.ceil(crosses[k+1]-.5));
   if(end<start)throw new TypeError('INVALID_DPR_SCANLINE');
   mask.fill(255,y*w+start,y*w+end);
  }
 }
 return mask;
}
const fail=s=>{throw new TypeError(s);};
const isArr=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const hex=/^[a-f0-9]{64}$/;
async function sha(x){if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',x))].map(b=>b.toString(16).padStart(2,'0')).join('');}
export async function auditSourceSvgVertexBudget({width,height,features,budget}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000||!Array.isArray(features)||!features.length||features.length>12||!Number.isInteger(budget)||budget<4)fail('INVALID_SVG_BUDGET_INPUT');
 const n=width*height,rows=[],seen=new Uint8Array(n);let total=0;
 for(const p of features){
  if(!p||typeof p.id!=='string'||!p.id||p.evidenceLevel!=='research_observation'||!isArr(p.sourceMask)||p.sourceMask.length!==n||!hex.test(p.sourceMaskSha256||'')||!Array.isArray(p.rings)||!p.rings.length)fail('INVALID_SOURCE_FEATURE');
  if(await sha(p.sourceMask)!==p.sourceMaskSha256)fail('SOURCE_FEATURE_SHA_MISMATCH');
  const vertices=p.rings.reduce((s,r)=>s+(Array.isArray(r)?r.length:0),0);
  if(vertices<4)fail('INVALID_VECTOR_GEOMETRY');
  const scaled=p.rings.map(r=>r.map(point=>{if(!Array.isArray(point)||point.length!==2||!point.every(Number.isInteger)||point[0]<0||point[0]>width||point[1]<0||point[1]>height)fail('INVALID_VECTOR_GEOMETRY');return [point[0]*2,point[1]*2];}));
  const raster1=rasterGeneral(p.rings,width,height,1);
  const raster2=rasterGeneral(scaled,width,height,2);
  let mismatch1=0,mismatch2=0,spill1=0,spill2=0,observed=0;
  for(let i=0;i<n;i++){
   const v=p.sourceMask[i];if(v!==0&&v!==255)fail('NONBINARY_SOURCE_FEATURE');if(v){observed++;if(seen[i])fail('SOURCE_FEATURE_OVERLAP');seen[i]=1;}
   const m1=raster1[i]?255:0;if(m1!==v)mismatch1++;if(m1&&!v)spill1++;
   const x=i%width,y=Math.floor(i/width);
   for(let dy=0;dy<2;dy++)for(let dx=0;dx<2;dx++){
    const m2=raster2[(y*2+dy)*width*2+x*2+dx]?255:0;
    if(m2!==v)mismatch2++;if(m2&&!v)spill2++;
   }
  }
  total+=vertices;rows.push({id:p.id,observedPixels:observed,vertices,mismatch1x:mismatch1,mismatch2x:mismatch2,spill1x:spill1,spill2x:spill2,exact2x:mismatch1===0&&mismatch2===0});
 }
 return {version:VERSION,width,height,vertexBudget:budget,totalVertices:total,overBy:Math.max(0,total-budget),withinBudget:total<=budget,
   sourceGeometryExact:rows.every(x=>x.exact2x),parts:rows,
   browserRasterParityVerified:false,semanticAnatomyVerified:false,fullCharacterVerified:false,
   productionReleaseAuthorized:false,productPromotionAuthorized:false,
   status:total<=budget&&rows.every(x=>x.exact2x)?'SOURCE_FEATURE_SUBSET_ONLY_HOLD':'SVG_BUDGET_OR_PIXEL_PARITY_HOLD'};
}
