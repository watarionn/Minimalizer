/** MinimalizerPublic P0 Stage193: source-free, research-only adjudication queue.
 * Candidate agreement NEVER certifies semantic truth. The private labels, sources
 * and generated queue MUST NOT be uploaded to public GitHub or production.
 */
export const VERSION='p0-stage193-private-adjudication-hold-v1';
const FAIL=s=>{throw new TypeError(s)};
const NAMES=['unreviewed','background','hair','face','skin','sleeve','garment','neckwear','accessory','uncertain'];
const bytes=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
export function recordOutOfBandIndependence({confirmed,statement,date}={}){
 if(confirmed!==true||typeof statement!=='string'||statement.trim().length<8||
 !/^\d{4}-\d{2}-\d{2}$/.test(date||''))FAIL('INDEPENDENCE_ATTESTATION_REQUIRED');
 return {version:VERSION,operatorReportedIndependentReviews:true,statement:statement.trim(),
 date,evidenceType:'USER_OUT_OF_BAND_CONFIRMATION',softwareIdentityVerified:false,
 semanticPixelsCertified:0,goldenApproved:false,paintAuthorized:false,releaseAuthorized:false};
}
export function buildPrivateAdjudicationQueue({caseId,width,height,sourceAlpha,labelsA,labelsB}={}){
 if(!['GC001','Raden'].includes(caseId)||!Number.isInteger(width)||!Number.isInteger(height)||
 width<1||height<1||width*height>160000)FAIL('INVALID_SOURCE_FRAME');
 const n=width*height;
 if(!bytes(sourceAlpha)||!bytes(labelsA)||!bytes(labelsB)||
 sourceAlpha.length!==n||labelsA.length!==n||labelsB.length!==n)FAIL('INVALID_PIXEL_ARRAY');
 const status=new Uint8Array(n),visited=new Uint8Array(n);
 let opaque=0,agree=0,disagree=0,abstain=0,uncertain=0;
 const kind=(a,b)=>a===0||b===0?'ABSTENTION':a===9||b===9?'UNCERTAIN':
  a===b?'AGREE':a===1||b===1?'BACKGROUND_OWNERSHIP':'PART_TAXONOMY';
 for(let i=0;i<n;i++){
  const a=labelsA[i],b=labelsB[i],alpha=sourceAlpha[i];
  if(a>9||b>9)FAIL('INVALID_REVIEW_CLASS');
  if(alpha!==255){if(a||b)FAIL('NONOPAQUE_CLASSIFICATION');continue}
  opaque++;const k=kind(a,b);
  if(k==='AGREE'){agree++;continue}
  status[i]=1;
  if(k==='ABSTENTION')abstain++;else if(k==='UNCERTAIN')uncertain++;else disagree++;
 }
 const components=[];
 for(let i=0;i<n;i++){
  if(!status[i]||visited[i])continue;
  const a=labelsA[i],b=labelsB[i],k=kind(a,b),stack=[i];
  let minX=width,minY=height,maxX=0,maxY=0,count=0;visited[i]=1;
  while(stack.length){
   const j=stack.pop(),x=j%width,y=Math.floor(j/width);
   count++;minX=Math.min(minX,x);maxX=Math.max(maxX,x+1);
   minY=Math.min(minY,y);maxY=Math.max(maxY,y+1);
   const neighbors=[x?j-1:-1,x+1<width?j+1:-1,y?j-width:-1,y+1<height?j+width:-1];
   for(const q of neighbors){
    if(q<0||!status[q]||visited[q]||labelsA[q]!==a||labelsB[q]!==b)continue;
    visited[q]=1;stack.push(q);
   }
  }
  components.push({componentId:caseId+'-C'+String(components.length+1).padStart(5,'0'),
   caseId,kind:k,labelAId:a,labelBId:b,labelA:NAMES[a],labelB:NAMES[b],pixels:count,
   bbox:[minX,minY,maxX,maxY],decision:'PENDING',semanticTruthCertified:false});
 }
 const reviewPixels=disagree+abstain+uncertain;
 if(opaque!==agree+reviewPixels||
 components.reduce((s,x)=>s+x.pixels,0)!==reviewPixels)FAIL('COMPONENT_ACCOUNTING_FAILED');
 const priorities={BACKGROUND_OWNERSHIP:200000,UNCERTAIN:100000,ABSTENTION:50000,PART_TAXONOMY:0};
 const ordered=components.slice().sort((a,b)=>{
  const special=x=>[['garment','sleeve'],['garment','accessory'],['garment','neckwear']].some(
   pair=>pair[0]===x.labelA&&pair[1]===x.labelB)?10000:0;
  return (priorities[b.kind]+b.pixels+special(b))-(priorities[a.kind]+a.pixels+special(a))
   ||a.componentId.localeCompare(b.componentId);
 });
 return {version:VERSION,caseId,width,height,originalOpaquePixels:opaque,agreePixels:agree,
  disagreePixels:disagree,abstainPixels:abstain,uncertainPixels:uncertain,
  reviewPixels,reviewComponents:ordered,allReviewPixelsAccounted:true,
  outOfBandIndependenceReportedSeparately:false,sourcePixelsAltered:0,
  semanticPixelsCertified:0,autoPromotedPixels:0,goldenApproved:false,paintAuthorized:false,
  releaseAuthorized:false,status:'MANUAL_ORIGINAL_SOURCE_ADJUDICATION_REQUIRED'};
}
export function registerManualDecisions({queue,decisions}={}){
 if(!queue||queue.version!==VERSION||!Array.isArray(queue.reviewComponents)||!Array.isArray(decisions))
  FAIL('INVALID_MANUAL_DECISIONS');
 const known=new Map(queue.reviewComponents.map(c=>[c.componentId,c])),seen=new Set();
 let accepted=0,deferred=0;
 for(const item of decisions){
  if(!item||!known.has(item.componentId)||seen.has(item.componentId)||
  !['A','B','DEFER'].includes(item.choice)||typeof item.reason!=='string'||
  item.reason.trim().length<4)FAIL('INVALID_REVIEW_DECISION');
  seen.add(item.componentId);
  if(item.choice==='DEFER')deferred+=known.get(item.componentId).pixels;
  else accepted+=known.get(item.componentId).pixels;
 }
 return {version:VERSION,caseId:queue.caseId,decidedComponents:seen.size,
   totalComponents:known.size,manualCandidatePixels:accepted,deferredPixels:deferred,
   notYetReviewedPixels:queue.reviewPixels-accepted-deferred,sourcePixelsAltered:0,
   semanticPixelsCertified:0,automaticGolden:false,paintAuthorized:false,releaseAuthorized:false,
   status:'CANDIDATE_DECISIONS_REQUIRE_PIXEL_ACCURATE_SOURCE_VERIFICATION'};
}