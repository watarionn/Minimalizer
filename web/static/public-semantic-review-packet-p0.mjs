/** Stage21: read-only connected topology risk inventory for original RGB source observations.
 * RGB/canvas topology does NOT infer garment, hair or skin labels. No painting API.
 * Pending human review; neither digest nor old owner SHA confers semantic authority.
 */
export const VERSION='structural-p0-stage21-untrusted-semantic-review-packet-v1';
const invalid=s=>{throw new TypeError(s);};
const typed=v=>v instanceof Uint8Array||v instanceof Uint8ClampedArray;
const hex=/^[0-9a-f]{64}$/;
async function digest(v){if(!globalThis.crypto?.subtle)invalid('WEBCRYPTO_REQUIRED');return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',v))].map(b=>b.toString(16).padStart(2,'0')).join('');}
async function checked(bytes,expected,tag){if(!typed(bytes)||!hex.test(expected||'')||await digest(bytes)!==expected)invalid(tag+'_SHA_MISMATCH');}
function checkBinary(bytes,n,tag){if(!typed(bytes)||bytes.length!==n)invalid(tag+'_DIMENSION');for(const v of bytes)if(v!==0&&v!==255)invalid(tag+'_NONBINARY');}
function getComponents(mask,w,h,source,otherMasks){
 const visited=new Uint8Array(w*h),components=[];
 for(let i=0;i<mask.length;i++){
  if(!mask[i]||visited[i])continue;
  const stack=[i];visited[i]=1;let size=0,bx0=w,by0=h,bx1=0,by1=0,ownerEdge=0,faceAdj=0,backgroundAdj=0,sourceHighContrastEdge=0;
  while(stack.length){const k=stack.pop(),x=k%w,y=Math.floor(k/w);size++;bx0=Math.min(bx0,x);by0=Math.min(by0,y);bx1=Math.max(bx1,x+1);by1=Math.max(by1,y+1);
   for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
    const xx=x+dx,yy=y+dy;if(xx<0||yy<0||xx>=w||yy>=h){ownerEdge++;continue;}
    const j=yy*w+xx;if(mask[j]&&!visited[j]){visited[j]=1;stack.push(j);}
    if(!mask[j]){
     if(!otherMasks.owner[j])ownerEdge++;
     if(otherMasks.face[j])faceAdj++;
     if(otherMasks.background[j])backgroundAdj++;
     const o=4*k,q=4*j,dist=Math.abs(source[o]-source[q])+Math.abs(source[o+1]-source[q+1])+Math.abs(source[o+2]-source[q+2]);
     if(dist>=96)sourceHighContrastEdge++;
    }
   }
  }
  components.push({pixels:size,bbox:[bx0,by0,bx1,by1],touchOwnerBoundaryEdges:ownerEdge,
   touchFaceEdges:faceAdj,touchBackgroundEdges:backgroundAdj,sourceContrastBoundaryEdges:sourceHighContrastEdge});
 }
 components.sort((a,b)=>b.pixels-a.pixels||a.bbox[1]-b.bbox[1]||a.bbox[0]-b.bbox[0]);
 return components;
}
export async function buildSemanticReviewPacket({caseId,width,height,sourceRgba,sourceSha256,faceMask,faceSha256,
  backgroundMask,backgroundSha256,owners,partitions}){
 if(!['GC001','Raden'].includes(caseId)||!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000)invalid('INVALID_CASE_CANVAS');
 const n=width*height;
 if(!typed(sourceRgba)||sourceRgba.length!==4*n)invalid('SOURCE_SIZE');
 checkBinary(faceMask,n,'FACE');checkBinary(backgroundMask,n,'BACKGROUND');
 await Promise.all([[sourceRgba,sourceSha256,'SOURCE'],[faceMask,faceSha256,'FACE'],[backgroundMask,backgroundSha256,'BACKGROUND']].map(x=>checked(...x)));
 if(!Array.isArray(owners)||owners.length!==2||!Array.isArray(partitions)||!partitions.length||partitions.length>32)invalid('INVALID_OWNER_OR_OBSERVATION_SET');
 const authority=new Map(),union=new Uint8Array(n);
 for(const o of owners){
  if(!o||!['left_arm','right_arm'].includes(o.role)||authority.has(o.role))invalid('INVALID_HISTORIC_OWNER');
  checkBinary(o.mask,n,'OWNER');await checked(o.mask,o.maskSha256,'OWNER');
  if(o.evidenceLevel!=='historical_stage04_signed')invalid('MISSING_OWNER_PROVENANCE');
  const visible=new Uint8Array(n);
  for(let i=0;i<n;i++)if(o.mask[i]&&!faceMask[i]&&!backgroundMask[i]&&sourceRgba[i*4+3]===255){
   if(union[i])invalid('SIGNED_OWNER_OVERLAP');union[i]=visible[i]=255;
  }
  authority.set(o.role,visible);
 }
 const used=new Uint8Array(n),entries=[],ids=new Set();
 for(const p of partitions){
  if(!p||!/^([a-z][a-z0-9_-]{0,47})$/.test(p.id||'')||ids.has(p.id)||!authority.has(p.parentRole)||p.evidenceLevel!=='source_color_observation')invalid('INVALID_OBSERVATION_PROVENANCE');
  ids.add(p.id);checkBinary(p.mask,n,'OBSERVATION');await checked(p.mask,p.maskSha256,'OBSERVATION');
  let pixels=0;
  for(let i=0;i<n;i++)if(p.mask[i]){if(!authority.get(p.parentRole)[i]||used[i])invalid('UNAUTHORIZED_OR_DUPLICATE_OBSERVATION');used[i]=255;pixels++;}
  if(pixels<1)invalid('EMPTY_OBSERVATION');
  const components=getComponents(p.mask,width,height,sourceRgba,{owner:authority.get(p.parentRole),face:faceMask,background:backgroundMask});
  entries.push({id:p.id,parentRole:p.parentRole,sourceObservationSha256:p.maskSha256,observedPixels:pixels,
   componentCount:components.length,largestComponentPixels:components[0].pixels,
   disconnectedPixels:components.slice(1).reduce((sum,x)=>sum+x.pixels,0),
   touchingOwnerBoundaryEdges:components.reduce((sum,x)=>sum+x.touchOwnerBoundaryEdges,0),
   nearFaceEdges:components.reduce((sum,x)=>sum+x.touchFaceEdges,0),nearObservedBackgroundEdges:components.reduce((sum,x)=>sum+x.touchBackgroundEdges,0),
   sourceContrastBoundaryEdges:components.reduce((sum,x)=>sum+x.sourceContrastBoundaryEdges,0),
   components:components.slice(0,16),omittedComponentCount:Math.max(0,components.length-16),
   semanticLabel:'unknown',independentSemanticReview:'PENDING',paintAuthorized:false});
 }
 entries.sort((a,b)=>a.parentRole.localeCompare(b.parentRole)||a.id.localeCompare(b.id));
 const uncovered=[];
 for(const [role,mask] of authority){let count=0,uncoveredPixels=0;for(let i=0;i<n;i++)if(mask[i]){count++;if(!used[i])uncoveredPixels++;}
  uncovered.push({role,visibleHistoricalOwnerPixels:count,unclassifiedPixels:uncoveredPixels});}
 return {version:VERSION,caseId,width,height,sourceSha256,faceSha256,backgroundSha256,
  owners:uncovered,observations:entries,independentSemanticLabelsVerified:false,
  backgroundObserverIndependentlySigned:false,sourceOnlyTopologyObservation:true,
  productPromotionAuthorized:false,reviewStatus:'PENDING_INDEPENDENT_SEMANTIC_BOUNDARY_REVIEW'};
}
