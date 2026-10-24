/** MinimalizerPublic research P0 Stages194-203.
 * Source-only evidence/experiment toolkit. Private originals and label arrays
 * must NEVER be stored in GitHub, Actions artifacts, public site, or telemetry.
 * Both reviewer annotations are proposals, not Golden truth.
 */
export const VERSION='p0-stage194-203-source-only-recovery-hold-v1';
export const LABELS=Object.freeze(['unreviewed','background','hair','face','skin','sleeve','garment','neckwear','accessory','uncertain']);
const fail=s=>{throw new TypeError(s)};
const byte=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const pin=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
function dimensions(o){if(!o||!['GC001','Raden'].includes(o.caseId)||!Number.isInteger(o.width)||!Number.isInteger(o.height)||o.width<1||o.height<1||o.width*o.height>160000)fail('INVALID_CASE_DIMENSIONS');return o.width*o.height}
function inputs(o,withRgba=false){
 const n=dimensions(o);
 if(!byte(o.labelsA)||!byte(o.labelsB)||o.labelsA.length!==n||o.labelsB.length!==n||!byte(o.alpha)||o.alpha.length!==n)fail('INVALID_REVIEW_ARRAYS');
 if(withRgba&&(!byte(o.rgba)||o.rgba.length!==4*n))fail('INVALID_SOURCE_RGBA');
 for(let i=0;i<n;i++){
  if(o.labelsA[i]>9||o.labelsB[i]>9)fail('UNKNOWN_SEMANTIC_LABEL');
  if(o.alpha[i]!==255&&(o.labelsA[i]!==0||o.labelsB[i]!==0))fail('NONOPAQUE_PROPOSAL');
  if(withRgba&&o.alpha[i]!==o.rgba[4*i+3])fail('SOURCE_ALPHA_MISMATCH');
 }
 return n;
}
// Stage194: taxonomy guidelines, never automatic region relabeling.
export function makePartTaxonomy(){
 return {version:VERSION,roles:Object.freeze({
  sleeve:'Visible sleeve fabric, including an attached sleeve flounce; separate from bodice if depicted.',
  garment:'Visible bodice/skirt/outerwear cloth outside separable sleeves, neckwear and accessories.',
  neckwear:'Visible tie, ribbon, bow or scarf distinct from surrounding clothing.',
  accessory:'Visible detachable or individually depicted badge, ornament, strap, buckle or equipment.',
  hair:'Only visible depicted strands; never complete hidden hair from inference.',
  background:'Only depicted backdrop; color alone cannot decide object ownership.',
  skin:'Only directly visible source skin; never infer anatomy beneath clothing.',
  face:'Visible face region; no mandatory eyes, nose or mouth extraction.'
 }),operatorMustInspectSource:true,automaticRoleRelabeling:false,golden:false};
}
// Stage195: five-way source-opaque classification with zero unaccounted pixels.
export function classifyPairedLabels(o){
 const n=inputs(o),state=new Uint8Array(n),consensus=new Uint8Array(n),counts={nonopaque:0,background:0,subject:0,roleConflict:0,backgroundConflict:0,abstain:0,uncertain:0};
 for(let i=0;i<n;i++){
  if(o.alpha[i]!==255){counts.nonopaque++;continue}
  const a=o.labelsA[i],b=o.labelsB[i];
  if(!a||!b){state[i]=5;counts.abstain++}
  else if(a===9||b===9){state[i]=6;counts.uncertain++}
  else if(a===b){consensus[i]=a;if(a===1){state[i]=1;counts.background++}else{state[i]=2;counts.subject++}}
  else if(a===1||b===1){state[i]=4;counts.backgroundConflict++}
  else{state[i]=3;counts.roleConflict++}
 }
 const opaque=n-counts.nonopaque;
 if(opaque!==counts.background+counts.subject+counts.roleConflict+counts.backgroundConflict+counts.abstain+counts.uncertain)fail('PAIR_CLASS_ACCOUNTING');
 return {version:VERSION,caseId:o.caseId,width:o.width,height:o.height,state,consensus,counts,opaque,proposedSourceOnly:true,semanticCertified:false};
}
// Stage196: prioritize 32x32 original-source tiles without suppressing small conflicts.
export function rankReviewTiles(p,{tileSize=32}={}){
 if(!p||!byte(p.state)||p.state.length!==p.width*p.height||!Number.isInteger(tileSize)||tileSize<8||tileSize>64)fail('INVALID_TILE_PRIORITY');
 const tiles=[];let accounted=0;
 for(let y=0;y<p.height;y+=tileSize)for(let x=0;x<p.width;x+=tileSize){
  const counts=[0,0,0,0,0,0,0];
  for(let j=y;j<Math.min(y+tileSize,p.height);j++)for(let i=x;i<Math.min(x+tileSize,p.width);i++)counts[p.state[j*p.width+i]]++;
  const unresolved=counts[3]+counts[4]+counts[5]+counts[6];accounted+=unresolved;
  tiles.push({id:tiles.length,bbox:[x,y,Math.min(x+tileSize,p.width),Math.min(y+tileSize,p.height)],
   roleConflict:counts[3],backgroundConflict:counts[4],abstain:counts[5],uncertain:counts[6],unresolved,
   priority:100*counts[4]+20*counts[6]+10*counts[3]+counts[5],decision:'PENDING'});
 }
 if(accounted!==p.counts.roleConflict+p.counts.backgroundConflict+p.counts.abstain+p.counts.uncertain)fail('TILE_MISCOUNT');
 return {caseId:p.caseId,tiles:tiles.sort((a,b)=>b.priority-a.priority||a.id-b.id),sourceOpaqueUnresolved:accounted,fullCoverage:true};
}
const digest=async a=>{
 if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');
 return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');
};
// Stage197: immutable original and source-pinned draft revision comparison.
export async function auditVersionedReviewerCorrection({previous,next,sourcePngSha256,sourceRgbaSha256,caseId,width,height,alpha}={}){
 const n=dimensions({caseId,width,height});
 if(!byte(previous)||!byte(next)||previous.length!==n||next.length!==n||!byte(alpha)||alpha.length!==n||!pin(sourcePngSha256)||!pin(sourceRgbaSha256))fail('INVALID_REVISION_AUDIT');
 let changed=0;const matrix={};
 for(let i=0;i<n;i++){
  const a=previous[i],b=next[i];
  if(a>9||b>9||alpha[i]!==255&&(a!==0||b!==0))fail('INVALID_REVISION_PIXEL');
  if(a!==b){changed++;matrix[a+'>'+b]=(matrix[a+'>'+b]||0)+1}
 }
 return {version:VERSION,caseId,sourcePngSha256,sourceRgbaSha256,
  originalLabelsSha256:await digest(previous),revisedLabelsSha256:await digest(next),
  changedPixels:changed,changesByClass:matrix,originalReplaced:false,
  independentlyCertifiedPixels:0,releaseAuthorized:false};
}
// Stage198: evidence-backed pixel overrides, NEVER bulk-approve a mixed component.
export function prepareManualPixelCorrections({pair,alpha,decisions=[],sourceInspected=false}={}){
 if(!pair||!byte(pair.state)||!byte(pair.consensus)||!byte(alpha)||alpha.length!==pair.state.length||!Array.isArray(decisions))fail('INVALID_CORRECTION_INPUT');
 const result=new Uint8Array(pair.consensus),verified=new Uint8Array(result.length),seen=new Set();let corrected=0;
 for(const d of decisions){
  if(!sourceInspected||!d||!Number.isInteger(d.index)||d.index<0||d.index>=result.length||seen.has(d.index)||
   !Number.isInteger(d.role)||d.role<1||d.role>8||
   typeof d.reason!=='string'||d.reason.trim().length<8||
   d.originalImageInspected!==true||alpha[d.index]!==255)fail('INSUFFICIENT_MANUAL_PIXEL_PROOF');
  seen.add(d.index);verified[d.index]=255;result[d.index]=d.role;corrected++;
 }
 // Agreement remains only A/B candidate; corrected pixel remains only operator-proposed.
 return {version:VERSION,labels:result,manuallyInspectedPixels:verified,
  manualPixelProposals:corrected,operatorPixelAttestationReceived:sourceInspected,
  originalSourceModified:false,reviewerOriginalsModified:false,
  independentlyCertifiedPixels:0,automaticGolden:false,releaseAuthorized:false};
}
// Stage199: conservative tri-state silhouette: disputed area is UNKNOWN, not painted.
export function deriveConservativeSubjectEvidence(p){
 if(!p||!byte(p.state)||!byte(p.consensus)||p.state.length!==p.consensus.length)fail('INVALID_CONSENSUS');
 const knownSubject=new Uint8Array(p.state.length),knownBackground=new Uint8Array(p.state.length),unknown=new Uint8Array(p.state.length);
 let subject=0,background=0,unresolved=0;
 for(let i=0;i<p.state.length;i++){
  if(p.state[i]===2){knownSubject[i]=255;subject++}
  else if(p.state[i]===1){knownBackground[i]=255;background++}
  else if(p.state[i]>2){unknown[i]=255;unresolved++}
 }
 if(subject+background+unresolved!==p.opaque)fail('SILHOUETTE_ACCOUNTING');
 return {caseId:p.caseId,width:p.width,height:p.height,knownSubject,knownBackground,unknown,
  agreeingSubjectPixels:subject,agreeingBackgroundPixels:background,
  unknownOpaquePixels:unresolved,wholeBodySemanticsCertified:false};
}
// Stage200: lossless source-observed rectangle cover, vertical merge with exact replay.
export function exactSourceRectangleCover({width,height,mask}={}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>160000||!byte(mask)||mask.length!==width*height)fail('INVALID_SOURCE_MASK');
 const rectangles=[],active=new Map();let observed=0;
 for(let y=0;y<height;y++){
  const row=[],next=new Map();
  for(let x=0;x<width;){
   const index=y*width+x;
   if(mask[index]!==0&&mask[index]!==255)fail('NONBINARY_SOURCE_MASK');
   if(!mask[index]){x++;continue}
   const left=x;while(x<width&&mask[y*width+x]===255){observed++;x++}row.push([left,x]);
  }
  for(const [x0,x1] of row){
   const key=x0+':'+x1,existing=active.get(key);
   if(existing){existing[3]++;next.set(key,existing)}
   else{const rect=[x0,y,x1,y+1];rectangles.push(rect);next.set(key,rect)}
  }
  active.clear();for(const [k,v] of next)active.set(k,v);
 }
 let covered=0;const replay=new Uint8Array(mask.length);
 for(const [x0,y0,x1,y1] of rectangles)for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){
  const i=y*width+x;if(replay[i])fail('RECTANGLE_OVERLAP');replay[i]=255;covered++;
 }
 if(covered!==observed||replay.some((v,i)=>v!==mask[i]))fail('SOURCE_PIXEL_REPLAY_FAIL');
 return {version:VERSION,width,height,rectangles,sourcePixels:observed,replayPixels:covered,
  spilledPixels:0,lostPixels:0,explicitVertices:rectangles.length*4,
  exactReplayPassed:true,semanticGold:false};
}
// Stage201: source-only palette extraction from exactly observed source RGB.
export function extractObservedRoleColors({pair,rgba,maxColors=8}={}){
 if(!pair||!byte(pair.consensus)||!byte(pair.state)||!byte(rgba)||rgba.length!==4*pair.consensus.length||
 !Number.isInteger(maxColors)||maxColors<1||maxColors>16)fail('INVALID_COLOR_OBSERVATION');
 const histogram=new Map(),roleCounts=new Map();
 for(let i=0;i<pair.state.length;i++){
  if(pair.state[i]!==2)continue;
  if(rgba[4*i+3]!==255)fail('NONOPAQUE_SOURCE_PALETTE');
  const role=pair.consensus[i],rgb=[rgba[4*i],rgba[4*i+1],rgba[4*i+2]];
  if(!histogram.has(role))histogram.set(role,new Map());
  const hex='#'+rgb.map(v=>v.toString(16).padStart(2,'0')).join('');
  const h=histogram.get(role);h.set(hex,(h.get(hex)||0)+1);
  roleCounts.set(role,(roleCounts.get(role)||0)+1);
 }
 const roles=[...histogram.entries()].sort((a,b)=>a[0]-b[0]).map(([role,h])=>({
  role,roleName:LABELS[role],observedPixels:roleCounts.get(role),uniqueSourceColors:h.size,
  colors:[...h.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,maxColors).map(([rgb,sourcePixels])=>({rgb,sourcePixels}))
 }));
 if(roles.reduce((s,r)=>s+r.observedPixels,0)!==pair.counts.subject)fail('COLOR_SOURCE_ACCOUNTING');
 return {version:VERSION,roles,colorsInvented:0,paletteFromOriginalPixelsOnly:true,
  roleBoundaryCertified:false,releaseAuthorized:false};
}
// Stage202: budget report measures an actual exact subject candidate; it cannot waive silhouette failures.
export function auditExactWholeSubjectBudget({caseId,rectangles,consensus}={}){
 if(!['GC001','Raden'].includes(caseId)||!rectangles||!consensus)fail('INVALID_BUDGET_SOURCE');
 const limit=caseId==='GC001'?1887:1412;
 if(rectangles.exactReplayPassed!==true||consensus.knownSubject.length!==rectangles.width*rectangles.height)fail('BUDGET_CANDIDATE_UNVERIFIED');
 const vertices=rectangles.explicitVertices,unknown=consensus.unknownOpaquePixels;
 return {version:VERSION,caseId,historicVertexLimit:limit,exactObservedVertexCost:vertices,
  vertexOverage:Math.max(0,vertices-limit),withinHistoricNumericLimit:vertices<=limit,
  unknownOpaquePixels:unknown,wholeBodyVerified:unknown===0&&consensus.wholeBodySemanticsCertified===true,
  goldenApproved:false,releaseAuthorized:false};
}
// Stage203: fail-closed promotion gate, never equate proposed reviewers with authenticated Golden.
export function evaluateStage203ReleaseGate({gc001,raden,manualAllPixelsReviewed=false,
 sourceIntegrityVerified=false,realIphoneSafariPassed=false,rollbackPassed=false,
 fullSceneRgbAuditPassed=false,independentGoldenCertified=false}={}){
 const missing=[];
 if(!gc001||!raden||gc001.caseId!=='GC001'||raden.caseId!=='Raden')missing.push('TWO_CASES');
 if(!manualAllPixelsReviewed)missing.push('PIXEL_ADJUDICATION');
 if(!sourceIntegrityVerified)missing.push('SOURCE_INTEGRITY');
 if(!realIphoneSafariPassed)missing.push('REAL_IPHONE_SAFARI');
 if(!rollbackPassed)missing.push('ROLLBACK');
 if(!fullSceneRgbAuditPassed)missing.push('FULL_SCENE_RGB');
 if(!independentGoldenCertified)missing.push('INDEPENDENT_GOLDEN');
 if(gc001&&!gc001.withinHistoricNumericLimit||raden&&!raden.withinHistoricNumericLimit)missing.push('EXACT_VERTEX_BUDGET');
 if(gc001&&!gc001.wholeBodyVerified||raden&&!raden.wholeBodyVerified)missing.push('WHOLEBODY');
 return {version:VERSION,missingGates:[...new Set(missing)],
  automaticReleaseAllowed:false,paintAuthorized:false,productionReleaseAuthorized:false,
  gateStatus:'GOLDEN_HOLD_MANUAL_APPROVAL_REQUIRED'};
}
