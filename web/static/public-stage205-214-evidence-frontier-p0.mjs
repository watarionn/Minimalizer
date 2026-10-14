/** MinimalizerPublic P0 Stages205-214: proposal-only, source-bound recovery checks.
 * No network, private image assets, fake reviewer attestation, model inference,
 * autonomous semantic choice, or production paint authorization.
 */
import {buildExactObservedBoundary} from './public-stage204-source-exact-contour-p0.mjs';
export const VERSION='p0-stage205-214-source-bound-hold-v1';
export const PARTS=Object.freeze(['unreviewed','background','hair','face','skin','sleeve','garment','neckwear','accessory','uncertain']);
const die=m=>{throw new TypeError(m)};
const bytes=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
const hash=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
function source(o,{needRgba=false}={}){
 if(!o||!['GC001','Raden'].includes(o.caseId)||!Number.isInteger(o.width)||!Number.isInteger(o.height)||o.width<=0||o.height<=0||o.width*o.height>160000)die('INVALID_FRAME');
 const n=o.width*o.height;
 if(!bytes(o.labelsA)||!bytes(o.labelsB)||!bytes(o.alpha)||[o.labelsA,o.labelsB,o.alpha].some(a=>a.length!==n))die('INVALID_PAIR');
 if(needRgba&&(!bytes(o.rgba)||o.rgba.length!==4*n))die('INVALID_RGBA');
 for(let i=0;i<n;i++){
  const a=o.labelsA[i],b=o.labelsB[i],al=o.alpha[i];
  if(a>9||b>9)die('INVALID_ROLE');
  if(al!==255&&(a||b))die('NONOPAQUE_REVIEW');
  if(needRgba&&o.rgba[4*i+3]!==al)die('SOURCE_ALPHA_MISMATCH');
 }
 return n;
}
function stateAt(a,b){
 if(!a||!b)return 'abstain';
 if(a===9||b===9)return 'uncertain';
 if(a===b)return a===1?'background':'subject';
 if(a===1||b===1)return 'boundary';
 return 'taxonomy';
}
//205: private class-pair statistics, unverified semantic data
export function auditProposalPair(o){
 const n=source(o),counts={nonopaque:0,background:0,subject:0,boundary:0,taxonomy:0,abstain:0,uncertain:0};
 const confusion=new Map(),state=new Uint8Array(n),agreedLabel=new Uint8Array(n),indexes={boundary:[],taxonomy:[],abstain:[],uncertain:[]};
 const types=['nonopaque','background','subject','boundary','taxonomy','abstain','uncertain'];
 for(let i=0;i<n;i++){
  if(o.alpha[i]!==255){counts.nonopaque++;continue}
  const a=o.labelsA[i],b=o.labelsB[i],kind=stateAt(a,b),code=types.indexOf(kind);
  counts[kind]++;state[i]=code;
  if(kind==='subject'||kind==='background')agreedLabel[i]=a;
  else indexes[kind].push(i);
  const pair=a+'>'+b;confusion.set(pair,(confusion.get(pair)||0)+1);
 }
 const opaque=n-counts.nonopaque;
 const uncertain=counts.boundary+counts.taxonomy+counts.abstain+counts.uncertain;
 if(counts.subject+counts.background+uncertain!==opaque)die('PIXEL_ACCOUNTING');
 return {version:VERSION,caseId:o.caseId,width:o.width,height:o.height,counts,opaque,unresolved:uncertain,
  confusion:[...confusion.entries()].map(([pair,pixels])=>({pair,pixels})).sort((a,b)=>b.pixels-a.pixels||a.pair.localeCompare(b.pair)),
  state,agreedLabel,indexes,semanticsVerified:false,paintAuthorized:false};
}
//206: deterministic priority worklist, no automatic semantics
export function planManualTriage({pair,tileSize=32}={}){
 if(!pair||!bytes(pair.state)||pair.state.length!==pair.width*pair.height||!Number.isInteger(tileSize)||tileSize<8||tileSize>64)die('INVALID_TRIAGE');
 const tiles=[],visited=new Uint8Array(pair.state.length);let todo=0;
 for(let y=0;y<pair.height;y+=tileSize)for(let x=0;x<pair.width;x+=tileSize){
  const bbox=[x,y,Math.min(x+tileSize,pair.width),Math.min(y+tileSize,pair.height)];
  const count={boundary:0,taxonomy:0,abstain:0,uncertain:0};
  for(let py=y;py<bbox[3];py++)for(let px=x;px<bbox[2];px++){
   const k=py*pair.width+px,s=pair.state[k];
   if(s>2){count[['','','','boundary','taxonomy','abstain','uncertain'][s]]++;todo++;visited[k]++}
  }
  tiles.push({tileId:'T'+String(tiles.length+1).padStart(3,'0'),bbox,...count,unresolved:Object.values(count).reduce((a,b)=>a+b,0),
   priority:count.boundary*100+count.uncertain*30+count.taxonomy*10+count.abstain});
 }
 if(todo!==pair.unresolved||visited.some(v=>v>1))die('TRIAGE_LOSS');
 tiles.sort((a,b)=>b.priority-a.priority||a.tileId.localeCompare(b.tileId));
 return {caseId:pair.caseId,tiles,unresolvedCovered:todo,autoResolved:0,readyForPrivateManualReview:true,
  sourceOriginalRequiredForEveryCorrection:true};
}
//207: manual evidence claim is traceable, never self-certifying
export function prepareOriginalPixelAdjudication({sourceFrame,review,decisions=[]}={}){
 const n=source(sourceFrame,{needRgba:true});
 if(!review||review.caseId!==sourceFrame.caseId||!bytes(review.state)||review.state.length!==n||!Array.isArray(decisions)||
 !hash(sourceFrame.sourceRgbaSha256)||!hash(sourceFrame.sourcePngSha256))die('INVALID_ADJUDICATION');
 const proposals=new Uint8Array(n),attested=new Uint8Array(n),seen=new Set(),reasons=[];
 for(const d of decisions){
  if(!d||!Number.isInteger(d.index)||d.index<0||d.index>=n||seen.has(d.index)||
  review.state[d.index]<=2||sourceFrame.alpha[d.index]!==255||
  !Number.isInteger(d.role)||d.role<1||d.role>8||
  d.originalImageInspected!==true||typeof d.reason!=='string'||d.reason.trim().length<12||
  !Array.isArray(d.rgbSeen)||d.rgbSeen.length!==3||d.rgbSeen.some((v,k)=>v!==sourceFrame.rgba[4*d.index+k]))die('UNSUPPORTED_PIXEL_DECISION');
  seen.add(d.index);attested[d.index]=255;proposals[d.index]=d.role;
  reasons.push({index:d.index,role:d.role,reason:d.reason.trim(),originalImageInspected:true});
 }
 return {version:VERSION,caseId:sourceFrame.caseId,sourceRgbaSha256:sourceFrame.sourceRgbaSha256,sourcePngSha256:sourceFrame.sourcePngSha256,
  proposals,attested,reasons,proposedPixels:seen.size,unresolvedRemaining:review.unresolved-seen.size,
  humanCertifiedPixels:0,sourceOriginalsChanged:false,originalReviewerFilesChanged:false,releaseAuthorized:false};
}
//208: separate fingerprinted review revisions and detect unreviewed/private mask growth
const sha=async data=>{
 if(!globalThis.crypto?.subtle)die('WEBCRYPTO_UNAVAILABLE');
 return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',data))].map(b=>b.toString(16).padStart(2,'0')).join('');
};
export async function auditImmutableReviewerRevision({sourceFrame,previous,revised,revisionTag}={}){
 const n=source(sourceFrame);
 if(!bytes(previous)||!bytes(revised)||previous.length!==n||revised.length!==n||
 typeof revisionTag!=='string'||!/^(A|B)-v[2-9][0-9]*$/.test(revisionTag))die('INVALID_REVISION_VERSION');
 const changes=[];const transitions=new Map();
 for(let i=0;i<n;i++){
  const a=previous[i],b=revised[i];
  if(a>9||b>9||sourceFrame.alpha[i]!==255&&(a||b))die('INVALID_REVISION_SOURCE');
  if(a===b)continue;
  changes.push(i);const id=a+'>'+b;transitions.set(id,(transitions.get(id)||0)+1);
 }
 return {version:VERSION,caseId:sourceFrame.caseId,revisionTag,previousSha256:await sha(previous),
  proposedRevisedSha256:await sha(revised),changedPixels:changes.length,changedPixelIndexes:changes,
  transitions:[...transitions].map(([fromTo,pixels])=>({fromTo,pixels})),replacesOriginal:false,
  goldenCertified:false,sourceFrameUnaffected:true};
}
//209: per-role exact contour, no overlapping paint and unresolved stays empty
export function buildSourceExactPartContours({sourceFrame,review}={}){
 const n=source(sourceFrame);if(!review||review.caseId!==sourceFrame.caseId||!bytes(review.agreedLabel)||review.agreedLabel.length!==n||!bytes(review.state)||review.state.length!==n)die('INVALID_ROLE_GEOMETRY');
 const layers=[];let pixels=0,vertices=0;
 for(let role=2;role<=8;role++){
  const mask=new Uint8Array(n);let count=0;
  for(let i=0;i<n;i++)if(review.state[i]===2&&review.agreedLabel[i]===role){
   if(sourceFrame.alpha[i]!==255)die('NONOPAQUE_PART');mask[i]=255;count++;
  }
  const c=buildExactObservedBoundary({caseId:sourceFrame.caseId,width:sourceFrame.width,height:sourceFrame.height,mask});
  if(c.sourcePixels!==count||c.lostPixels||c.spilledPixels)die('PART_REPLAY_FAILED');
  layers.push({role,name:PARTS[role],sourcePixels:count,vertices:c.explicitVertices,loops:c.loops,
    pathD:c.pathD,fillRule:c.fillRule,sourceExact:true,approved:false});
  pixels+=count;vertices+=c.explicitVertices;
 }
 if(pixels!==review.counts.subject)die('PART_COVERAGE_FAIL');
 return {version:VERSION,caseId:sourceFrame.caseId,layers,sourceSubjectPixels:pixels,
  totalVertices:vertices,noCrossRoleOverlap:true,zeroPixelSpill:true,wholeBodyGolden:false,releaseAuthorized:false};
}
//210: no false equivalence between silhouette and layered contour budget
export function assessMultiRepresentationCost({caseId,union,perRole,rectangles}={}){
 if(!['GC001','Raden'].includes(caseId)||!union||!perRole||!rectangles||union.caseId!==caseId||perRole.caseId!==caseId||
 union.sourcePixels!==perRole.sourceSubjectPixels||union.sourcePixels!==rectangles.sourcePixels||
 !union.exactRasterReplay||!rectangles.exactReplayPassed||!perRole.zeroPixelSpill)die('INCOMPARABLE_COST_INPUTS');
 const cap=caseId==='GC001'?1887:1412;
 const rows=[
  {encoding:'exact_rectangles',vertices:rectangles.explicitVertices},
  {encoding:'exact_subject_union_contour',vertices:union.explicitVertices},
  {encoding:'exact_role_layer_contours',vertices:perRole.totalVertices}
 ].map(row=>({...row,overCap:Math.max(0,row.vertices-cap),withinBudget:row.vertices<=cap}));
 return {version:VERSION,caseId,sourcePixels:union.sourcePixels,historicVertexCap:cap,rows,
  minimumObservedVertices:Math.min(...rows.map(r=>r.vertices)),noClaimOfGlobalOptimum:true,
  fullBodySemanticsCertified:false,releaseAuthorized:false};
}
//211: strictly original-color sampled medoid palette, with measured L1 error
export function measureSourceOnlyPalette({sourceFrame,review,maximumColors=4}={}){
 const n=source(sourceFrame,{needRgba:true});
 if(!review||!bytes(review.state)||review.state.length!==n||!bytes(review.agreedLabel)||review.agreedLabel.length!==n||
 !Number.isInteger(maximumColors)||maximumColors<1||maximumColors>16)die('INVALID_PALETTE_AUDIT');
 const roles=[];let touched=0;
 for(let role=2;role<=8;role++){
  const hist=new Map(),pix=[];
  for(let i=0;i<n;i++)if(review.state[i]===2&&review.agreedLabel[i]===role){
   if(sourceFrame.alpha[i]!==255)die('NONOPAQUE_COLOR');const v=[sourceFrame.rgba[4*i],sourceFrame.rgba[4*i+1],sourceFrame.rgba[4*i+2]],key=v.join(',');
   hist.set(key,(hist.get(key)||0)+1);pix.push(v);
  }
  if(!pix.length)continue;
  // Select only colors physically present in the reviewed original pixels.
  const palette=[...hist].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,maximumColors).map(([s])=>s.split(',').map(Number));
  let matched=0,l1=0;
  for(const p of pix){
   let best=Infinity;for(const c of palette){const d=Math.abs(p[0]-c[0])+Math.abs(p[1]-c[1])+Math.abs(p[2]-c[2]);best=Math.min(best,d)}
   l1+=best;if(best===0)matched++;
  }
  touched+=pix.length;roles.push({role,name:PARTS[role],pixels:pix.length,distinctObservedColors:hist.size,
   palette:palette.map(c=>'#'+c.map(v=>v.toString(16).padStart(2,'0')).join('')),
   exactOriginalRgbPixels:matched,originalRgbMismatchPixels:pix.length-matched,totalRgbL1Error:l1,colorsInvented:0});
 }
 if(touched!==review.counts.subject)die('PALETTE_ROLE_MISMATCH');
 return {version:VERSION,caseId:sourceFrame.caseId,agreedSubjectPixels:touched,roles,originalColorsOnly:true,
  totalRgbMismatchPixels:roles.reduce((s,r)=>s+r.originalRgbMismatchPixels,0),
  fullSceneRgbCertified:false,releaseAuthorized:false};
}
//212: preserving no face detail invention is a hard boundary, even with review maps
export function auditFaceNoFeaturePolicy({sourceFrame,review,featureRequests=[]}={}){
 source(sourceFrame);
 if(!review||review.caseId!==sourceFrame.caseId||!bytes(review.state)||review.state.length!==sourceFrame.width*sourceFrame.height||
 !Array.isArray(featureRequests)||featureRequests.some(x=>!['face_region','observed_skin_tone'].includes(x)))die('FORBIDDEN_FACE_FEATURE');
 let proposedFace=0;
 for(let i=0;i<review.state.length;i++)if(review.state[i]===2&&review.agreedLabel[i]===3)proposedFace++;
 return {version:VERSION,caseId:sourceFrame.caseId,proposedFaceRegionPixels:proposedFace,
  eyesGenerated:0,noseGenerated:0,mouthGenerated:0,facialFeaturesInferred:false,
  sourceVisibleGeometryOnly:true,reviewedFaceSemanticsCertified:false,releaseAuthorized:false};
}
//213: explicit gate fail-closed, even when every flag has been set
export function evaluateCandidateReadiness({cases=[],humanAdjudicated=false,goldenHumanSigned=false,
 verifiedFullBody=false,sourceRgbWithinPolicy=false,realIphoneSafariPass=false,realRollbackPass=false,
 explicitOwnerReleaseApproval=false}={}){
 const statuses=new Map(cases.map(c=>[c?.caseId,c]));
 const missing=[];
 if(cases.length!==2||statuses.size!==2||!statuses.has('GC001')||!statuses.has('Raden'))missing.push('TWO_CASES');
 for(const x of ['GC001','Raden']){
  const c=statuses.get(x);
  if(!c||c.sourceExact!==true)missing.push('SOURCE_EXACT_'+x);
  if(!c||c.opaqueUnresolved!==0)missing.push('CLASSIFICATION_'+x);
  if(!c||c.numericBudgetPassed!==true)missing.push('VERTEX_BUDGET_'+x);
 }
 for(const [k,v] of Object.entries({humanAdjudicated,goldenHumanSigned,verifiedFullBody,sourceRgbWithinPolicy,realIphoneSafariPass,realRollbackPass,explicitOwnerReleaseApproval}))
  if(v!==true)missing.push(k);
 return {version:VERSION,missing,technicalSignalsSatisfied:missing.length===0,
  automaticGolden:false,releaseAuthorized:false,
  action:'REQUIRE_SEPARATE_MANUAL_HUMAN_RELEASE_DECISION',stage214HandoffRequired:true};
}
//214: machine-readable, source-free handoff checkpoint; no secrets or image pixels
export function buildSourceFreeHandoff({repository,prNumber,branch,commitSha,stageRange,summary,blocked=[],ci}={}){
 if(repository!=='watarionn/Minimalizer'||prNumber!==393||typeof branch!=='string'||!branch.startsWith('research/')||
 !/^[a-f0-9]{40}$/.test(commitSha||'')||!Array.isArray(stageRange)||stageRange[0]!==205||stageRange[1]!==214||
 typeof summary!=='string'||summary.length<20||!Array.isArray(blocked)||blocked.some(x=>typeof x!=='string'||x.length<3)||
 !ci||typeof ci.runId!=='number'||!Number.isInteger(ci.pass)||!Number.isInteger(ci.fail))die('INVALID_HANDOFF');
 return {format:'MinimalizerPublic-P0-handoff-v1',stageRange,repository,prNumber,branch,commitSha,
  summary,blocked,ci,originalFilesInPublicRepo:false,reviewerLabelsInPublicRepo:false,
  reviewHumanCertificationDone:false,stage204GoldenHold:true,prDraftExpected:true,releaseAuthorized:false};
}
