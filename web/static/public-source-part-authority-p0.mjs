// MinimalizerPublic StructuralRecovery P0 Stage2, research-only.
// Explicit owner evidence + overlap ordering; never infers semantic identity or writes pixels.
export const VERSION = 'public-source-part-authority-p0-stage2-v1';
const ROLES = new Set(['left_arm', 'right_arm', 'tie_or_neckwear', 'collar',
  'eyewear', 'bow', 'corset_lacing', 'sleeve_ruffle', 'held_object', 'major_accessory']);
const LIMIT = 400 * 400;
const SHA = /^[a-f0-9]{64}$/;
const ID = /^[a-z][a-z0-9_-]{0,47}$/;
const MASK_ACCEPT = 'independently_attested';
function deny(s){throw new TypeError(s);}
function binary(mask,n,name){
 if (!(mask instanceof Uint8Array || mask instanceof Uint8ClampedArray) || mask.length!==n)deny(name+': invalid mask');
 let count=0;
 for(const b of mask){if(b!==0&&b!==255)deny(name+': nonbinary mask');if(b)count++;}
 if(!count)deny(name+': empty mask');
 return count;
}
async function sha(bytes){
 if(!globalThis.crypto?.subtle)deny('SHA-256 unavailable (fail closed)');
 return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))]
   .map(x=>x.toString(16).padStart(2,'0')).join('');
}
function validateHex(expected,name){if(typeof expected!=='string'||!SHA.test(expected))deny(name+': SHA pin required');}
function stableOrder(owners,edges){
 const ids=owners.map(o=>o.id);
 const incoming=new Map(ids.map(id=>[id,new Set()]));
 const outgoing=new Map(ids.map(id=>[id,new Set()]));
 if(!Array.isArray(edges)||edges.length>64)deny('invalid depth edges');
 for(const e of edges){
  if(!e||typeof e.front!=='string'||typeof e.behind!=='string'||
   !incoming.has(e.front)||!incoming.has(e.behind)||e.front===e.behind)
   deny('unknown or self occlusion');
  if(typeof e.evidenceRef!=='string'||!e.evidenceRef.trim())deny('depth evidence required');
  incoming.get(e.behind).add(e.front);
  outgoing.get(e.front).add(e.behind);
 }
 const indegree=new Map(ids.map(id=>[id,incoming.get(id).size]));
 const ready=ids.filter(id=>indegree.get(id)===0).sort();
 const order=[];
 while(ready.length){
  const id=ready.shift();order.push(id);
  for(const later of outgoing.get(id)){
   indegree.set(later,indegree.get(later)-1);
   if(indegree.get(later)===0){ready.push(later);ready.sort();}
  }
 }
 if(order.length!==ids.length)deny('cyclic occlusion');
 const reach=new Map();
 for(const id of ids){
  const seen=new Set(),todo=[...outgoing.get(id)];
  while(todo.length){const key=todo.pop();if(seen.has(key))continue;
   seen.add(key);todo.push(...outgoing.get(key));}
  reach.set(id,seen);
 }
 return {order,reach};
}
/**
 * Returns research candidate metrics and visible partitions ONLY. The caller
 * must separately verify source file SHA (PNG bytes), mask PNG provenance,
 * and independent human semantic authority. An 'attested' string alone is NOT
 * cryptographic authority and does not permit product integration.
 */
export async function prepareSourceOwnedParts({width,height,sourceRgba,sourceRgbaSha256,
 faceMask,faceMaskSha256,owners,occlusionEdges=[],maxVisiblePixels=LIMIT}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||
    width*height>LIMIT)deny('invalid dimensions');
 const n=width*height;
 if(!(sourceRgba instanceof Uint8Array||sourceRgba instanceof Uint8ClampedArray)||
    sourceRgba.length!==n*4)deny('invalid source RGBA');
 validateHex(sourceRgbaSha256,'source');
 if(await sha(sourceRgba)!==sourceRgbaSha256)deny('source SHA mismatch');
 binary(faceMask,n,'face');validateHex(faceMaskSha256,'face');
 if(await sha(faceMask)!==faceMaskSha256)deny('face mask SHA mismatch');
 if(!Array.isArray(owners)||!owners.length||owners.length>16)deny('missing owner evidence');
 if(!Number.isInteger(maxVisiblePixels)||maxVisiblePixels<1||maxVisiblePixels>LIMIT)
  deny('invalid visible pixel budget');
 const ids=new Set(),prepared=[];
 for(const o of owners){
  if(!o||typeof o.id!=='string'||!ID.test(o.id)||ids.has(o.id)||!ROLES.has(o.role))
   deny('duplicate/unknown owner');
  ids.add(o.id);
  if(typeof o.evidenceRef!=='string'||!o.evidenceRef.trim())deny('owner evidenceRef required');
  if(o.evidenceLevel!=='research_observation'&&o.evidenceLevel!==MASK_ACCEPT)
   deny('explicit evidence level required');
  const pixels=binary(o.mask,n,o.id);validateHex(o.maskSha256,o.id);
  if(await sha(o.mask)!==o.maskSha256)deny(o.id+': mask SHA mismatch');
  let facialOverlap=0,transparentOverlap=0;
  for(let i=0;i<n;i++)if(o.mask[i]){
   if(faceMask[i])facialOverlap++;
   if(sourceRgba[i*4+3]!==255)transparentOverlap++;
  }
  if(facialOverlap)deny(o.id+': face mask collision');
  if(transparentOverlap)deny(o.id+': unsupported source-alpha pixels');
  prepared.push({id:o.id,role:o.role,mask:o.mask,sourcePixels:pixels,
   evidenceLevel:o.evidenceLevel,evidenceRef:o.evidenceRef,
   safeForAutomaticPromotion:false});
 }
 // Reject any binary mask collision whose *source* depth relation is unresolved.
 const {order,reach}=stableOrder(prepared,occlusionEdges);
 const collisions=[];
 for(let a=0;a<prepared.length;a++)for(let b=a+1;b<prepared.length;b++){
  const u=prepared[a],v=prepared[b];let overlap=0;
  for(let i=0;i<n;i++)if(u.mask[i]&&v.mask[i])overlap++;
  if(!overlap)continue;
  if(!reach.get(u.id).has(v.id)&&!reach.get(v.id).has(u.id))
   deny('unresolved source ownership overlap: '+u.id+' / '+v.id);
  collisions.push({parts:[u.id,v.id],pixels:overlap,
   front:reach.get(u.id).has(v.id)?u.id:v.id});
 }
 const seen=new Uint8Array(n),visible=new Map();
 for(const id of order){
  const part=prepared.find(x=>x.id===id);
  const mask=new Uint8Array(n);let pixels=0;
  for(let i=0;i<n;i++)if(part.mask[i]&&!seen[i]){
    mask[i]=255;seen[i]=1;pixels++;
  }
  visible.set(id,{mask,pixels});
 }
 const visiblePixels=prepared.reduce((n,p)=>n+visible.get(p.id).pixels,0);
 if(visiblePixels>maxVisiblePixels)deny('visible pixel budget exceeded');
 const result=order.map(id=>prepared.find(p=>p.id===id)).map(p=>Object.freeze({id:p.id,role:p.role,
  sourcePixels:p.sourcePixels,visiblePixels:visible.get(p.id).pixels,
  occludedPixels:p.sourcePixels-visible.get(p.id).pixels,
  evidenceLevel:p.evidenceLevel,evidenceRef:p.evidenceRef,
  // A separately authorized reviewer is still necessary even when metadata says attested.
  productPromotionAuthorized:false}));
 return Object.freeze({version:VERSION,sourceRgbaSha256,
  visibleParts:result,visibleMasks:Object.fromEntries(prepared.map(p=>[p.id,visible.get(p.id).mask])),
  frontToBack:order,collisions,visiblePixels,
  previewOnly:true,productPromotionAuthorized:false,
  pixelsChanged:0,sourceAndMasksReadOnly:true});
}
