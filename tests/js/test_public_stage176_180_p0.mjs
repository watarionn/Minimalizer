import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {buildHumanReviewQueue} from '../../web/static/public-human-review-queue-p0.mjs';
import {encodeFullFrameDraftRle} from '../../web/static/public-fullframe-review-p0.mjs';
import {buildPrivateHumanReviewTriage,privateTriageReleaseGate} from '../../web/static/public-human-review-triage-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=x=>createHash('sha256').update(x).digest('hex');
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
async function fixture(width=8,height=8,caseId='GC001'){
 const n=width*height,rgba=new Uint8Array(n*4),face=new Uint8Array(n),bg=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
 for(let i=0;i<n;i++)rgba.set([i%255,(i*2)%255,30,255],4*i);
 rgba[4*(n-1)+3]=0;face[2]=255;bg[3]=255;left[1]=255;right[width+1]=255;
 const source={caseId,width,height,sourceRgba:rgba,sourceRgbaSha256:sha(rgba),
 sourcePngSha256:'e'.repeat(64),faceMask:face,faceSha256:sha(face),
 backgroundMask:bg,backgroundSha256:sha(bg),
 owners:{left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}}};
 const q=await buildHumanReviewQueue(source);
 const a=new Uint8Array(n),b=new Uint8Array(n);
 a[1]=5;b[1]=6;a[2]=7;b[2]=7;a[3]=1;b[3]=0;b[4]=1;
 const base={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId,dimensions:[width,height],
 sourcePngSha256:source.sourcePngSha256,sourceRgbaSha256:source.sourceRgbaSha256,
 sourceEligibilitySha256:q.eligibilitySha256,status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',
 approved:false,paintAuthorized:false,reviewerAuthenticated:false,roles};
 const drafts=[a,b].map(labels=>({...base,rle:encodeFullFrameDraftRle(labels)}));
 return{source,drafts};
}
test('176 source-pinned triage validates original and never certifies humans',async()=>{
 const {source,drafts}=await fixture(),v=await buildPrivateHumanReviewTriage({source,drafts});
 assert.equal(v.sourceRgbaSha256,source.sourceRgbaSha256);assert.equal(v.independentHumansAuthenticated,0);
 assert.equal(v.independentlyApprovedSourcePixels,0);assert.equal(v.paintAuthorized,false);
});
test('176 case original mutation is rejected before computing anything',async()=>{
 const {source,drafts}=await fixture();source.sourceRgba[0]^=1;
 await assert.rejects(()=>buildPrivateHumanReviewTriage({source,drafts}),/SOURCE_PIN_MISMATCH/);
});
test('177 every original pixel contributes to one and only one count',async()=>{
 const {source,drafts}=await fixture(),v=await buildPrivateHumanReviewTriage({source,drafts});
 assert.deepEqual(v.totals,{untrustedAgree:1,untrustedDisputed:1,unreviewedOrAbstained:62});
 assert.equal(v.tiles.reduce((n,t)=>n+t.pixels,0),64);
 assert.equal(v.allOriginalPixelsCounted,true);
});
test('177 complete 340x340 original has 121 tiles, including unreviewed backdrop',async()=>{
 const {source,drafts}=await fixture(340,340),v=await buildPrivateHumanReviewTriage({source,drafts});
 assert.equal(v.originalPixels,115600);assert.equal(v.originalTiles,121);
 assert.equal(v.totals.unreviewedOrAbstained,115598);
});
test('178 disagreement class pair is symmetric and exact, not semantic truth',async()=>{
 const {source,drafts}=await fixture(),v=await buildPrivateHumanReviewTriage({source,drafts});
 assert.deepEqual(v.rolePairs,[{pair:'garment_proposal <-> sleeve_proposal',untrustedDisputedPixels:1}]);
 assert.equal(v.roleAgreement.neckwear_proposal,1);assert.equal(v.authenticatedFullbodyGolden,false);
});
test('179 triage tiles prioritized deterministically and fully counted',async()=>{
 const {source,drafts}=await fixture(64,32),v=await buildPrivateHumanReviewTriage({source,drafts,tileSize:16});
 assert.equal(v.originalTiles,8);
 assert(v.tiles.every((t,i)=>i===0||v.tiles[i-1].triagePriority>=t.triagePriority));
 assert.equal(v.tiles.reduce((n,t)=>n+t.untrustedDisputed,0),1);
 assert(v.tiles.every(t=>t.authenticatedReviewers===0&&t.humanAdjudicatedPixels===0));
});
test('179 identical drafts never count as two independent reviewers',async()=>{
 const {source,drafts}=await fixture();await assert.rejects(()=>buildPrivateHumanReviewTriage({source,drafts:[drafts[0],drafts[0]]}),/IDENTICAL_DRAFTS_CANNOT_PROVE_INDEPENDENCE/);
});
test('179 source-nonopaque proposal cannot pass review triage',async()=>{
 const {source,drafts}=await fixture();const labels=new Uint8Array(source.width*source.height);
 labels[labels.length-1]=5;drafts[1]={...drafts[1],rle:encodeFullFrameDraftRle(labels)};
 await assert.rejects(()=>buildPrivateHumanReviewTriage({source,drafts}),/FULLFRAME_NONOPAQUE_PROPOSAL/);
});
test('179 self-declared approval is rejected by trusted source draft validator',async()=>{
 const {source,drafts}=await fixture();drafts[1].approved=true;
 await assert.rejects(()=>buildPrivateHumanReviewTriage({source,drafts}),/UNTRUSTED_FULLFRAME_DRAFT_IDENTITY/);
});
test('180 release gate holds even with both case ids and fake approvals',()=>{
 const g=privateTriageReleaseGate({cases:[{caseId:'GC001',approved:true},{caseId:'Raden',approved:true}]});
 assert.equal(g.productionAuthorized,false);assert.equal(g.humanIdentitiesAuthenticated,0);
 assert.equal(g.trueFullbodyGeometryAccepted,false);assert.equal(g.status,'GOLDEN_HOLD');
});
test('180 release gate rejects duplicated and invalid cases',()=>{
 assert.throws(()=>privateTriageReleaseGate({cases:[{caseId:'GC001'},{caseId:'GC001'}]}),/INVALID_PRIVATE_TRIAGE_CASES/);
 assert.throws(()=>privateTriageReleaseGate({cases:[{caseId:'wrong'}]}),/INVALID_PRIVATE_TRIAGE_CASES/);
});
test('180 no release with one or zero cases and no user-supplied trust',()=>{
 assert.deepEqual(privateTriageReleaseGate().missingCases,['GC001','Raden']);
 assert.deepEqual(privateTriageReleaseGate({cases:[{caseId:'Raden'}]}).missingCases,['GC001']);
});
