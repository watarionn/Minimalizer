/** Stage13: simplify *observed* contour rings with strict raster proof.
 * Outward painted pixels are forbidden. Lost pixels are measured, never hidden.
 * No inferred bridges; rejected candidates leave Stage12 exact paths unchanged.
 */
export const VERSION='structural-p0-stage13-raster-audited-contour-simplification-v1';
const fail=s=>{throw new TypeError(s);};
const distSq=(p,a,b)=>{const x=b[0]-a[0],y=b[1]-a[1],len=x*x+y*y;if(!len)return (p[0]-a[0])**2+(p[1]-a[1])**2;
 const t=Math.max(0,Math.min(1,((p[0]-a[0])*x+(p[1]-a[1])*y)/len));return (p[0]-a[0]-t*x)**2+(p[1]-a[1]-t*y)**2;};
function simplifyLine(pts,e2){
 const keep=new Uint8Array(pts.length);keep[0]=keep[pts.length-1]=1;const stack=[[0,pts.length-1]];
 while(stack.length){const [a,b]=stack.pop();let max=e2,at=-1;
  for(let i=a+1;i<b;i++){const d=distSq(pts[i],pts[a],pts[b]);if(d>max){at=i;max=d;}}
  if(at!==-1){keep[at]=1;stack.push([a,at],[at,b]);}
 }
 return pts.filter((p,i)=>keep[i]);
}
function closedSimplify(pts,epsilon){
 if(pts.length<=4)return pts.map(x=>x.slice());
 let far=1,d=-1;for(let i=1;i<pts.length;i++){
  const x=pts[i][0]-pts[0][0],y=pts[i][1]-pts[0][1],len=x*x+y*y;
  if(len>d){d=len;far=i;}}
 const a=simplifyLine(pts.slice(0,far+1),epsilon**2);
 const b=simplifyLine([...pts.slice(far),pts[0]],epsilon**2);
 const out=[...a.slice(0,-1),...b.slice(0,-1)];return out.length>=3?out:pts.map(x=>x.slice());
}
export function rasterizeSlopedRings({rings,width,height}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000||!Array.isArray(rings))fail('INVALID_RINGS');
 const result=new Uint8Array(width*height);
 for(let y=0;y<height;y++){
  const cy=y+.5,cross=[];
  for(const pts of rings)for(let j=0;j<pts.length;j++){
   const a=pts[j],b=pts[(j+1)%pts.length];
   if(!Array.isArray(a)||a.length!==2||!Array.isArray(b)||b.length!==2||!a.every(Number.isFinite)||!b.every(Number.isFinite))fail('BAD_VERTEX');
   if((a[1]<=cy&&cy<b[1])||(b[1]<=cy&&cy<a[1]))cross.push(a[0]+(cy-a[1])*(b[0]-a[0])/(b[1]-a[1]));
  }
  cross.sort((a,b)=>a-b);if(cross.length%2)fail('ODD_RASTER_PARITY');
  for(let j=0;j<cross.length;j+=2){
   const start=Math.max(0,Math.ceil(cross[j]-.5)),end=Math.min(width,Math.ceil(cross[j+1]-.5));
   for(let x=start;x<end;x++)result[y*width+x]=255;
  }
 }
 return result;
}
const path=rings=>rings.map(r=>'M'+r.map(([x,y])=>`${x} ${y}`).join('L')+'Z').join('');
export function auditContourCandidate({width,height,sourceMask,rings}){
 if(!(sourceMask instanceof Uint8Array||sourceMask instanceof Uint8ClampedArray)||sourceMask.length!==width*height)fail('INVALID_SOURCE_MASK');
 const png=rasterizeSlopedRings({rings,width,height});let spill=0,cover=0,positive=0;
 for(let i=0;i<png.length;i++){if(sourceMask[i])positive++;if(png[i]){if(sourceMask[i]!==255)spill++;else cover++;}}
 return {sourcePixels:positive,paintedSourcePixels:cover,spillPixels:spill,discardedSourcePixels:positive-cover,coverage:positive?cover/positive:0,sourceOnlyPass:spill===0};
}
/** Exact Stage12 rings are the canonical fallback. Never approve by MSE alone. */
export function simplifySignedObservationContours({width,height,parts,sourceMasks,
 epsilons=[.5,.75,1,1.5,2,3,4],minCoverage=.90,maxTotalVertices=1800}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000||
 !Array.isArray(parts)||!parts.length||!sourceMasks||!(minCoverage>=0&&minCoverage<=1)||
 !Number.isInteger(maxTotalVertices)||maxTotalVertices<4)fail('INVALID_SIMPLIFICATION_INPUT');
 const results=[];let total=0;
 for(const item of parts){
  const mask=sourceMasks[item.id];if(!mask||!Array.isArray(item.rings))fail('SOURCE_CONTOUR_AUTHORITY_MISSING');
  const baseline=auditContourCandidate({width,height,sourceMask:mask,rings:item.rings});
  if(baseline.spillPixels!==0||baseline.coverage!==1)fail('STAGE12_NOT_SOURCE_EXACT');
  const candidates=[{epsilon:0,rings:item.rings,vertices:item.vertexCount,metric:baseline}];
  for(const eps of epsilons){
   if(!Number.isFinite(eps)||eps<=0||eps>8)fail('INVALID_EPSILON');
   const rings=item.rings.map(r=>closedSimplify(r,eps));
   const vertices=rings.reduce((a,r)=>a+r.length,0);
   if(vertices>=item.vertexCount)continue;
   const metric=auditContourCandidate({width,height,sourceMask:mask,rings});
   if(metric.spillPixels===0&&metric.coverage>=minCoverage)candidates.push({epsilon:eps,rings,vertices,metric});
  }
  // Avoid discarding more source pixels merely to save one vertex: maximize coverage,
  // then prefer smaller vector complexity within exact same retained area.
  candidates.sort((a,b)=>b.metric.coverage-a.metric.coverage||a.vertices-b.vertices||a.epsilon-b.epsilon);
  const accepted=candidates[0];total+=accepted.vertices;
  results.push({id:item.id,role:item.role,sourceMaskSha256:item.sourceMaskSha256,
   rings:accepted.rings,pathD:path(accepted.rings),epsilon:accepted.epsilon,
   vertexCount:accepted.vertices,...accepted.metric,allowedWithoutGolden:false,
   trialMetrics:candidates.map(x=>({epsilon:x.epsilon,vertices:x.vertices,coverage:x.metric.coverage,spill:x.metric.spillPixels}))});
 }
 return {version:VERSION,parts:results,totalVertices:total,
  passSourceExactness:results.every(x=>x.spillPixels===0),
  insideTotalVertexBudget:total<=maxTotalVertices,explicitVertexBudget:maxTotalVertices,
  curvatureApproved:false,sourceObserverSemanticApproved:false,
  productPromotionAuthorized:false,previewOnly:true};
}
