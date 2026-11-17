import test from 'node:test';
import assert from 'node:assert/strict';
import {
 VERSION, PARTS,auditProposalPair,planManualTriage,prepareOriginalPixelAdjudication,
 auditImmutableReviewerRevision,buildSourceExactPartContours,assessMultiRepresentationCost,
 measureSourceOnlyPalette,auditFaceNoFeaturePolicy,evaluateCandidateReadiness,buildSourceFreeHandoff
} from '../../web/static/public-stage205-214-evidence-frontier-p0.mjs';
import {buildExactObservedBoundary} from '../../web/static/public-stage204-source-exact-contour-p0.mjs';
import {exactSourceRectangleCover} from '../../web/static/public-stage194-203-recovery-p0.mjs';
const sha='a'.repeat(64),pin='b'.repeat(64);
function f(){
 const a=new Uint8Array([1,1,2,2,1,6,6,1,2,2,0,9,0,1,4,3]);
 const b=new Uint8Array([1,2,2,2,1,5,6,1,2,1,6,9,0,1,4,3]);
 const alpha=new Uint8Array(16).fill(255);alpha[12]=0;
 const rgba=new Uint8Array(64);
 for(let i=0;i<16;i++)rgba.set([i*11,i*7,i*13,alpha[i]],i*4);
 return {caseId:'GC001',width:4,height:4,alpha,rgba,labelsA:a,labelsB:b,
 sourceRgbaSha256:sha,sourcePngSha256:pin};
}
test('205 original opaque ledger accounts for every pixel and pair direction',()=>{
 const x=auditProposalPair(f());
 assert.deepEqual(x.counts,{nonopaque:1,background:4,subject:6,boundary:2,taxonomy:1,abstain:1,uncertain:1});
 assert.equal(x.opaque,15);assert.equal(x.unresolved,5);
 assert.equal(x.indexes.boundary.length,2);
 assert.equal(x.confusion.reduce((a,b)=>a+b.pixels,0),15);
 assert.equal(x.semanticsVerified,false);assert.equal(x.paintAuthorized,false);
});
test('205 reject nonopaque proposals, incorrect dimensions and invalid roles',()=>{
 const a=f();a.labelsA[12]=6;assert.throws(()=>auditProposalPair(a),/NONOPAQUE/);
 const b=f();b.labelsB[1]=10;assert.throws(()=>auditProposalPair(b),/ROLE/);
 const c=f();c.width=5;assert.throws(()=>auditProposalPair(c),/PAIR/);
});
test('206 review tiles have disjoint coverage of all unresolved original pixels',()=>{
 const p=auditProposalPair(f()),t=planManualTriage({pair:p,tileSize:8});
 assert.equal(t.tiles.length,1);assert.equal(t.unresolvedCovered,5);
 assert.equal(t.tiles[0].boundary+t.tiles[0].taxonomy+t.tiles[0].abstain+t.tiles[0].uncertain,5);
 assert.equal(t.autoResolved,0);assert.equal(t.readyForPrivateManualReview,true);
});
test('206 340x340 source generates 121 worklist tiles, independent of content',()=>{
 const n=340*340,o={caseId:'Raden',width:340,height:340,alpha:new Uint8Array(n).fill(255),
 labelsA:new Uint8Array(n).fill(1),labelsB:new Uint8Array(n).fill(1)};
 const t=planManualTriage({pair:auditProposalPair(o)});
 assert.equal(t.tiles.length,121);assert.equal(t.unresolvedCovered,0);
 assert.throws(()=>planManualTriage({pair:auditProposalPair(o),tileSize:7}),/TRIAGE/);
});
test('207 each adjudication requires original RGB, reason and exactly one disputed pixel',()=>{
 const o=f(),review=auditProposalPair(o);
 const d={index:1,role:2,rgbSeen:[...o.rgba.slice(4,7)],originalImageInspected:true,reason:'Distinct visible hair edge in original'};
 const p=prepareOriginalPixelAdjudication({sourceFrame:o,review,decisions:[d]});
 assert.equal(p.proposedPixels,1);assert.equal(p.unresolvedRemaining,4);assert.equal(p.proposals[1],2);
 assert.equal(p.proposals[2],0);assert.equal(p.humanCertifiedPixels,0);assert.equal(p.releaseAuthorized,false);
 assert.throws(()=>prepareOriginalPixelAdjudication({sourceFrame:o,review,decisions:[d,d]}),/UNSUPPORTED/);
});
test('207 rejects fabricated RGB evidence, missing reason and already agreed pixels',()=>{
 const o=f(),review=auditProposalPair(o),base={index:1,role:2,rgbSeen:[...o.rgba.slice(4,7)],originalImageInspected:true,reason:'Actual original pixel boundary inspected'};
 assert.throws(()=>prepareOriginalPixelAdjudication({sourceFrame:o,review,decisions:[{...base,rgbSeen:[2,2,2]}]}),/UNSUPPORTED/);
 assert.throws(()=>prepareOriginalPixelAdjudication({sourceFrame:o,review,decisions:[{...base,reason:'short'}]}),/UNSUPPORTED/);
 assert.throws(()=>prepareOriginalPixelAdjudication({sourceFrame:o,review,decisions:[{...base,index:2}]}),/UNSUPPORTED/);
 const bad=f();bad.rgba[4*5+3]=0;assert.throws(()=>prepareOriginalPixelAdjudication({sourceFrame:bad,review,decisions:[]}),/ALPHA_MISMATCH/);
});
test('208 immutable revision captures only changes, not history erasure',async()=>{
 const o=f(),rev=new Uint8Array(o.labelsA);rev[1]=2;rev[10]=6;
 const orig=new Uint8Array(o.labelsA);
 const x=await auditImmutableReviewerRevision({sourceFrame:o,previous:o.labelsA,revised:rev,revisionTag:'A-v2'});
 assert.equal(x.changedPixels,2);assert.deepEqual(x.changedPixelIndexes,[1,10]);
 assert.notEqual(x.previousSha256,x.proposedRevisedSha256);
 assert.deepEqual([...orig],[...o.labelsA]);assert.equal(x.replacesOriginal,false);
});
test('208 reject version v1, modified nonopaque source and unchanged sha not accepted as human truth',async()=>{
 const o=f();
 await assert.rejects(auditImmutableReviewerRevision({sourceFrame:o,previous:o.labelsA,revised:o.labelsA,revisionTag:'A-v1'}));
 const rev=new Uint8Array(o.labelsA);rev[12]=2;
 await assert.rejects(auditImmutableReviewerRevision({sourceFrame:o,previous:o.labelsA,revised:rev,revisionTag:'B-v2'}),/REVISION_SOURCE/);
 const x=await auditImmutableReviewerRevision({sourceFrame:o,previous:o.labelsA,revised:o.labelsA,revisionTag:'A-v2'});
 assert.equal(x.changedPixels,0);assert.equal(x.goldenCertified,false);
});
test('209 per-role contour covers only proposal agreement and no cross-role pixels',()=>{
 const o=f(),review=auditProposalPair(o),v=buildSourceExactPartContours({sourceFrame:o,review});
 assert.equal(v.sourceSubjectPixels,6);assert.equal(v.layers.length,7);
 assert.equal(v.layers.reduce((s,l)=>s+l.sourcePixels,0),6);
 assert.ok(v.layers.every(l=>l.sourceExact&&l.approved===false&&l.fillRule==='evenodd'));
 assert.equal(v.noCrossRoleOverlap,true);assert.equal(v.releaseAuthorized,false);
});
test('209 all-background case yields empty role contours without inventing subjects',()=>{
 const n=16,o=f();o.labelsA.fill(1);o.labelsB.fill(1);o.labelsA[12]=o.labelsB[12]=0;
 const v=buildSourceExactPartContours({sourceFrame:o,review:auditProposalPair(o)});
 assert.equal(v.sourceSubjectPixels,0);assert.equal(v.totalVertices,0);assert.equal(v.layers.length,7);
});
test('210 exact three-way costs are measured using same candidate mask',()=>{
 const o=f(),review=auditProposalPair(o),p=buildSourceExactPartContours({sourceFrame:o,review});
 const mask=new Uint8Array(16);for(let i=0;i<16;i++)if(review.state[i]===2)mask[i]=255;
 const union=buildExactObservedBoundary({caseId:o.caseId,width:4,height:4,mask});
 const rectangles=exactSourceRectangleCover({width:4,height:4,mask});
 const c=assessMultiRepresentationCost({caseId:o.caseId,union,perRole:p,rectangles});
 assert.equal(c.sourcePixels,6);assert.equal(c.rows.length,3);
 assert.equal(c.minimumObservedVertices,Math.min(rectangles.explicitVertices,union.explicitVertices,p.totalVertices));
 assert.equal(c.fullBodySemanticsCertified,false);
});
test('210 rejects masks from different subject domains',()=>{
 const o=f(),review=auditProposalPair(o),p=buildSourceExactPartContours({sourceFrame:o,review});
 const mask=new Uint8Array(16);
 const union=buildExactObservedBoundary({caseId:o.caseId,width:4,height:4,mask});
 const rectangles=exactSourceRectangleCover({width:4,height:4,mask});
 assert.throws(()=>assessMultiRepresentationCost({caseId:o.caseId,union,perRole:p,rectangles}),/INCOMPARABLE/);
});
test('211 sampled palette only contains observed source colors',()=>{
 const o=f(),review=auditProposalPair(o);
 const p=measureSourceOnlyPalette({sourceFrame:o,review,maximumColors:1});
 assert.equal(p.agreedSubjectPixels,6);assert.equal(p.originalColorsOnly,true);
 assert.equal(p.totalRgbMismatchPixels,p.roles.reduce((s,r)=>s+r.originalRgbMismatchPixels,0));
 assert.ok(p.roles.every(r=>r.colorsInvented===0&&r.palette.length<=1));
 for(const r of p.roles)for(const hex of r.palette){
  const rgb=hex.match(/[0-9a-f]{2}/g).map(h=>parseInt(h,16));
  const present=[...Array(16).keys()].some(i=>review.state[i]===2&&review.agreedLabel[i]===r.role&&
   rgb.every((v,k)=>o.rgba[4*i+k]===v));
  assert.ok(present);
 }
});
test('211 palette cap fails out of range and RGB alpha mismatch',()=>{
 const o=f(),p=auditProposalPair(o);
 assert.throws(()=>measureSourceOnlyPalette({sourceFrame:o,review:p,maximumColors:0}));
 o.rgba[4*2+3]=0;assert.throws(()=>measureSourceOnlyPalette({sourceFrame:o,review:p}),/ALPHA_MISMATCH/);
});
test('212 face policy never introduces eyes nose mouth',()=>{
 const o=f(),p=auditProposalPair(o),r=auditFaceNoFeaturePolicy({sourceFrame:o,review:p,featureRequests:['face_region']});
 assert.equal(r.proposedFaceRegionPixels,1);
 assert.equal(r.eyesGenerated,0);assert.equal(r.noseGenerated,0);assert.equal(r.mouthGenerated,0);
 assert.equal(r.releaseAuthorized,false);
});
test('212 invented face feature proposals must be rejected',()=>{
 const o=f();assert.throws(()=>auditFaceNoFeaturePolicy({sourceFrame:o,review:auditProposalPair(o),featureRequests:['draw_nose']}),/FACE_FEATURE/);
});
test('213 explicit full-green fake flags still cannot autonomously authorize production',()=>{
 const good={sourceExact:true,opaqueUnresolved:0,numericBudgetPassed:true};
 const x=evaluateCandidateReadiness({cases:[{caseId:'GC001',...good},{caseId:'Raden',...good}],
 humanAdjudicated:true,goldenHumanSigned:true,verifiedFullBody:true,sourceRgbWithinPolicy:true,
 realIphoneSafariPass:true,realRollbackPass:true,explicitOwnerReleaseApproval:true});
 assert.equal(x.technicalSignalsSatisfied,true);assert.equal(x.automaticGolden,false);assert.equal(x.releaseAuthorized,false);
});
test('213 real proposal history remains blocked for known unresolved pixels and device',()=>{
 const x=evaluateCandidateReadiness({cases:[{caseId:'GC001',sourceExact:true,opaqueUnresolved:7072,numericBudgetPassed:false},{caseId:'Raden',sourceExact:true,opaqueUnresolved:22690,numericBudgetPassed:false}]});
 assert.ok(x.missing.includes('CLASSIFICATION_GC001'));
 assert.ok(x.missing.includes('VERTEX_BUDGET_Raden'));
 assert.ok(x.missing.includes('realIphoneSafariPass'));assert.ok(x.missing.includes('realRollbackPass'));
 assert.equal(x.releaseAuthorized,false);
});
test('214 handoff checkpoint preserves actual branch/hash/CI and no release promise',()=>{
 const data=buildSourceFreeHandoff({repository:'watarionn/Minimalizer',prNumber:393,
 branch:'research/minimalizerpublic-p0-stage136-155-20261013',commitSha:'1'.repeat(40),
 stageRange:[205,214],summary:'Maintained source-only P0 with all manual adjudications pending.',
 blocked:['Original pixel classifications unresolved','Fullbody vertex cap fails'],
 ci:{runId:98765,pass:700,fail:0}});
 assert.equal(data.format,'MinimalizerPublic-P0-handoff-v1');
 assert.equal(data.prDraftExpected,true);assert.equal(data.releaseAuthorized,false);
 assert.equal(data.originalFilesInPublicRepo,false);
});
test('214 invalid handoff identity or artifact pin rejected',()=>{
 const b={repository:'watarionn/Minimalizer',prNumber:393,
 branch:'research/minimalizerpublic-p0-stage136-155-20261013',commitSha:'1'.repeat(40),
 stageRange:[205,214],summary:'Maintained source-only P0 research.',
 blocked:['Pending owner pixel inspection'],ci:{runId:123,pass:678,fail:0}};
 assert.throws(()=>buildSourceFreeHandoff({...b,commitSha:'not-a-sha'}));
 assert.throws(()=>buildSourceFreeHandoff({...b,stageRange:[203,204]}));
 assert.throws(()=>buildSourceFreeHandoff({...b,prNumber:400}));
});
