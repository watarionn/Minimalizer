/** Stages176-180: PRIVATE full-original manual review triage, not human authentication.
 * Only code is public. Inputs and returned source-derived diagnostics must stay private.
 * The two drafts are untrusted. Agreement and RGB boundaries are not anatomy truth.
 */
import {buildFullFrameReviewWorklist,validateUntrustedFullFrameDraft} from './public-fullframe-review-p0.mjs';

export const VERSION='p0-stage176-180-private-fullframe-triage-v1';
const fail=s=>{throw new TypeError(s);};
const ROLES=Object.freeze(['unreviewed','background_proposal','hair_proposal','face_proposal',
 'skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject']);
const CRITICAL=Object.freeze(['background_proposal','hair_proposal','face_proposal','skin_proposal',
 'sleeve_proposal','garment_proposal','neckwear_proposal','uncertain_subject']);

/** Build an exhaustive comparison using the ORIGINAL SHA-checked image and two drafts.
 * Never export the result as public evidence or treat a pair of files as two humans.
 */
export async function buildPrivateHumanReviewTriage({source,drafts,tileSize=32}){
 if(!source||!Array.isArray(drafts)||drafts.length!==2)fail('TWO_ORIGINAL_DRAFTS_REQUIRED');
 const q=await buildFullFrameReviewWorklist({...source,tileSize});
 const [a,b]=await Promise.all(drafts.map(draft=>validateUntrustedFullFrameDraft({...source,draft})));
 if(a.labelsSha256===b.labelsSha256)fail('IDENTICAL_DRAFTS_CANNOT_PROVE_INDEPENDENCE');
 const cols=Math.ceil(q.width/tileSize),counts={agree:0,disputed:0,abstained:0};
 const roleAgreement=Object.fromEntries(ROLES.slice(1).map(role=>[role,0]));
 const confusion=new Map(),tiles=q.tiles.map(t=>({
  tileId:t.tileId,bbox:[...t.bbox],pixels:t.pixels,
  sourceHighContrastEdges:t.sourceHighContrastEdges,
  untrustedAgree:0,untrustedDisputed:0,unreviewedOrAbstained:0,
  roleDisagreements:{},triagePriority:0,
  humanAdjudicatedPixels:0,authenticatedReviewers:0
 }));
 for(let i=0;i<q.totalPixels;i++){
  const x=i%q.width,y=Math.floor(i/q.width),t=tiles[Math.floor(y/tileSize)*cols+Math.floor(x/tileSize)];
  const u=a.labels[i],v=b.labels[i];
  if(u===0||v===0){counts.abstained++;t.unreviewedOrAbstained++;continue;}
  if(u===v){counts.agree++;t.untrustedAgree++;roleAgreement[ROLES[u]]++;continue;}
  counts.disputed++;t.untrustedDisputed++;
  const pair=[ROLES[u],ROLES[v]].sort().join(' <-> ');
  confusion.set(pair,(confusion.get(pair)||0)+1);
  t.roleDisagreements[pair]=(t.roleDisagreements[pair]||0)+1;
 }
 const sum=t=>t.untrustedAgree+t.untrustedDisputed+t.unreviewedOrAbstained;
 if(counts.agree+counts.disputed+counts.abstained!==q.totalPixels ||
  tiles.some(t=>sum(t)!==t.pixels) ||
  tiles.reduce((n,t)=>n+sum(t),0)!==q.totalPixels)fail('ORIGINAL_FULLFRAME_TRIAGE_COVERAGE_MISMATCH');
 const totalConfusion=[...confusion.values()].reduce((n,v)=>n+v,0);
 if(totalConfusion!==counts.disputed)fail('TRIAGE_CONFUSION_MISMATCH');
 for(const t of tiles)t.triagePriority=t.untrustedDisputed*8+t.unreviewedOrAbstained*3+t.sourceHighContrastEdges;
 tiles.sort((u,v)=>v.triagePriority-u.triagePriority||u.tileId-v.tileId);
 const rolePairs=[...confusion].map(([pair,pixels])=>({pair,untrustedDisputedPixels:pixels}))
   .sort((a,b)=>b.untrustedDisputedPixels-a.untrustedDisputedPixels||a.pair.localeCompare(b.pair,'en'));
 return {version:VERSION,caseId:q.caseId,sourceRgbaSha256:q.sourceRgbaSha256,
  sourcePngSha256:q.sourcePngSha256,sourceEligibilitySha256:q.sourceEligibilitySha256,
  firstDraftLabelsSha256:a.labelsSha256,secondDraftLabelsSha256:b.labelsSha256,
  originalWidth:q.width,originalHeight:q.height,originalPixels:q.totalPixels,
  originalTiles:tiles.length,allOriginalPixelsCounted:true,
  sourcePixelMutation:false,tiles,totals:{
   untrustedAgree:counts.agree,untrustedDisputed:counts.disputed,unreviewedOrAbstained:counts.abstained
  },roleAgreement,rolePairs,manualReviewCategories:[...CRITICAL],
  independentHumansAuthenticated:0,independentlyApprovedSourcePixels:0,
  authenticatedFullbodyGolden:false,vertexBudgetGatePassed:false,
  realIphoneSafariHttpsPassed:false,rollbackRehearsed:false,
  paintAuthorized:false,productReleaseAuthorized:false,
  status:'PRIVATE_TRIAGE_ONLY_AWAITING_REAL_INDEPENDENT_HUMAN_REVIEW'};
}

/** Stage180: never accept self-declared approval flags or release via private triage. */
export function privateTriageReleaseGate({cases=[]}={}){
 if(!Array.isArray(cases)||cases.length>2||cases.some(x=>!x||!['GC001','Raden'].includes(x.caseId))||
  new Set(cases.map(x=>x.caseId)).size!==cases.length)fail('INVALID_PRIVATE_TRIAGE_CASES');
 return {version:VERSION,missingCases:['GC001','Raden'].filter(id=>!cases.some(c=>c.caseId===id)),
  humanIdentitiesAuthenticated:0,independentlyGoldReviewedPixels:0,
  trueFullbodyGeometryAccepted:false,sourceColorGoldenAccepted:false,
  realIphoneSafariHttpsAccepted:false,rollbackAccepted:false,
  paintAuthorized:false,productionAuthorized:false,status:'GOLDEN_HOLD'};
}
