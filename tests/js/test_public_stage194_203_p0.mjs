import test from 'node:test';
import assert from 'node:assert/strict';
import {
 VERSION, LABELS, makePartTaxonomy, classifyPairedLabels,rankReviewTiles,
 auditVersionedReviewerCorrection,prepareManualPixelCorrections,
 deriveConservativeSubjectEvidence, exactSourceRectangleCover,
 extractObservedRoleColors,auditExactWholeSubjectBudget,evaluateStage203ReleaseGate
} from '../../web/static/public-stage194-203-recovery-p0.mjs';
const fixture=()=>({
 caseId:'GC001',width:4,height:3,
 alpha:new Uint8Array([255,255,255,0,255,255,255,255,255,255,255,255]),
 labelsA:new Uint8Array([1,6,6,0,1,2,6,0,6,5,0,9]),
 labelsB:new Uint8Array([1,5,6,0,6,2,1,0,0,5,2,4])
});
const pins={sourcePngSha256:'1'.repeat(64),sourceRgbaSha256:'2'.repeat(64)};
const rgba=(alpha)=>{const out=new Uint8Array(alpha.length*4);for(let i=0;i<alpha.length;i++){out.set([i*10,i*7,i*3,alpha[i]],i*4)}return out};
test('194: taxonomy distinguishes sleeve, garment, neckwear and accessory, no automatic relabel',()=>{
 const t=makePartTaxonomy();
 for(const k of ['sleeve','garment','accessory','neckwear','background','hair','skin','face'])assert.ok(t.roles[k].length>20);
 assert.equal(t.automaticRoleRelabeling,false);assert.equal(t.golden,false);assert.equal(LABELS.length,10);
});
test('195: all source-opaque pixels accounted and no Golden',()=>{
 const q=classifyPairedLabels(fixture());
 assert.equal(q.counts.nonopaque,1);
 assert.deepEqual([q.counts.background,q.counts.subject,q.counts.roleConflict,
 q.counts.backgroundConflict,q.counts.abstain,q.counts.uncertain],[1,3,1,2,3,1]);
 assert.equal(q.opaque,11);assert.equal(q.semanticCertified,false);
 assert.deepEqual([...q.state],[1,3,2,0,4,2,4,5,5,2,5,6]);
});
test('195: strict unknown labels and no nonopaque painting',()=>{
 for(const key of ['labelsA','labelsB']){
  const f=fixture();f[key]=new Uint8Array(f[key]);f[key][3]=2;assert.throws(()=>classifyPairedLabels(f),/NONOPAQUE/);
  const g=fixture();g[key]=new Uint8Array(g[key]);g[key][1]=10;assert.throws(()=>classifyPairedLabels(g),/UNKNOWN/);
 }
});
test('195: dimension mismatch, rejected case, wrong alpha',()=>{
 const f=fixture();assert.throws(()=>classifyPairedLabels({...f,width:5}));
 assert.throws(()=>classifyPairedLabels({...f,caseId:'NONEXISTENT'}));
 assert.throws(()=>classifyPairedLabels({...f,alpha:new Uint8Array(10)}));
});
test('196: tile audit counts all unresolved pixels',()=>{
 const f=fixture(), q=classifyPairedLabels(f);
 const tiles=rankReviewTiles(q,{tileSize:8});
 assert.equal(tiles.tiles.length,1);
 assert.equal(tiles.sourceOpaqueUnresolved,q.counts.roleConflict+q.counts.backgroundConflict+q.counts.abstain+q.counts.uncertain);
 assert.equal(tiles.fullCoverage,true);
});
test('196: full original 340x340 has exactly 121 tiles',()=>{
 const n=340*340,q=classifyPairedLabels({
 caseId:'Raden',width:340,height:340,alpha:new Uint8Array(n).fill(255),
 labelsA:new Uint8Array(n).fill(1),labelsB:new Uint8Array(n).fill(1)
 });
 assert.equal(rankReviewTiles(q).tiles.length,121);
 assert.equal(rankReviewTiles(q).sourceOpaqueUnresolved,0);
});
test('196: priority emphasizes silhouette ownership',()=>{
 const f=fixture(),q=classifyPairedLabels(f);
 assert.throws(()=>rankReviewTiles(q,{tileSize:7}));
 assert.ok(rankReviewTiles(q).tiles[0].priority>0);
});
test('197: correction retains original sha and explicit change matrix',async()=>{
 const a=new Uint8Array([1,2,6,0]),b=new Uint8Array([1,5,6,0]);
 const q=await auditVersionedReviewerCorrection({caseId:'GC001',width:2,height:2,
 alpha:new Uint8Array([255,255,255,0]),previous:a,next:b,...pins});
 assert.equal(q.changedPixels,1);assert.equal(q.changesByClass['2>5'],1);
 assert.notEqual(q.originalLabelsSha256,q.revisedLabelsSha256);
 assert.equal(q.originalReplaced,false);assert.equal(q.releaseAuthorized,false);
});
test('197: reject nonopaque revision and invalid source pins',async()=>{
 const a=new Uint8Array([1,0,6,0]),b=new Uint8Array([1,2,6,0]),alpha=new Uint8Array([255,0,255,0]);
 await assert.rejects(auditVersionedReviewerCorrection({caseId:'GC001',width:2,height:2,alpha,previous:a,next:b,...pins}),/INVALID_REVISION_PIXEL/);
 await assert.rejects(auditVersionedReviewerCorrection({caseId:'GC001',width:2,height:2,alpha,previous:a,next:a,sourcePngSha256:'wrong',sourceRgbaSha256:pins.sourceRgbaSha256}));
});
test('197: identity unchanged for revision with no edits',async()=>{
 const a=new Uint8Array([1,1]),q=await auditVersionedReviewerCorrection({caseId:'Raden',width:2,height:1,alpha:new Uint8Array([255,255]),previous:a,next:new Uint8Array(a),...pins});
 assert.equal(q.changedPixels,0);assert.equal(q.originalLabelsSha256,q.revisedLabelsSha256);
});
test('198: per-pixel, source-inspected correction is only a proposal',()=>{
 const f=fixture(),pair=classifyPairedLabels(f);
 const r=prepareManualPixelCorrections({pair,alpha:f.alpha,sourceInspected:true,decisions:[{index:1,role:5,reason:'Saw sleeve edge on source',originalImageInspected:true}]});
 assert.equal(r.labels[1],5);assert.equal(r.manualPixelProposals,1);
 assert.equal(r.labels[2],6);assert.equal(r.originalSourceModified,false);
 assert.equal(r.independentlyCertifiedPixels,0);assert.equal(r.releaseAuthorized,false);
});
test('198: missing source witness, duplicate pixel and short reason fail closed',()=>{
 const f=fixture(),pair=classifyPairedLabels(f);
 const d={index:1,role:5,reason:'Direct original image inspection',originalImageInspected:true};
 assert.throws(()=>prepareManualPixelCorrections({pair,alpha:f.alpha,decisions:[d]}));
 assert.throws(()=>prepareManualPixelCorrections({pair,alpha:f.alpha,sourceInspected:true,decisions:[d,d]}));
 assert.throws(()=>prepareManualPixelCorrections({pair,alpha:f.alpha,sourceInspected:true,decisions:[{...d,reason:'no'}]}));
 assert.throws(()=>prepareManualPixelCorrections({pair,alpha:f.alpha,sourceInspected:true,decisions:[{...d,index:3}]}));
});
test('199: unknown pixels must never be silently painted',()=>{
 const q=classifyPairedLabels(fixture()),r=deriveConservativeSubjectEvidence(q);
 assert.equal(r.agreeingSubjectPixels,q.counts.subject);
 assert.equal(r.agreeingBackgroundPixels,q.counts.background);
 assert.equal(r.unknownOpaquePixels,q.opaque-r.agreeingSubjectPixels-r.agreeingBackgroundPixels);
 assert.equal(r.knownSubject[1],0);assert.equal(r.unknown[1],255);
 assert.equal(r.knownSubject[2],255);assert.equal(r.knownBackground[0],255);
 assert.equal(r.wholeBodySemanticsCertified,false);
});
test('199: whole scene agreed by reviewers still not independently certified',()=>{
 const q=classifyPairedLabels({caseId:'Raden',width:2,height:1,alpha:new Uint8Array([255,255]),labelsA:new Uint8Array([1,5]),labelsB:new Uint8Array([1,5])});
 const x=deriveConservativeSubjectEvidence(q);
 assert.equal(x.unknownOpaquePixels,0);assert.equal(x.wholeBodySemanticsCertified,false);
});
test('200: exact source rectangles merge identical column runs vertically',()=>{
 const mask=new Uint8Array([
  0,255,255,0,
  0,255,255,0,
  255,255,0,0,
  255,255,0,0
 ]);
 const r=exactSourceRectangleCover({width:4,height:4,mask});
 assert.equal(r.sourcePixels,8);assert.equal(r.rectangles.length,2);
 assert.equal(r.explicitVertices,8);assert.equal(r.spilledPixels,0);assert.equal(r.lostPixels,0);
});
test('200: empty source mask has zero polygons and no fabrication',()=>{
 const r=exactSourceRectangleCover({width:4,height:3,mask:new Uint8Array(12)});
 assert.equal(r.rectangles.length,0);assert.equal(r.sourcePixels,0);
});
test('200: fuzz small rectangle replay is exact',()=>{
 for(let j=0;j<40;j++){
  const w=7,h=6,mask=new Uint8Array(w*h);
  for(let i=0;i<mask.length;i++)mask[i]=((i*19+j*23)%11<5)?255:0;
  const r=exactSourceRectangleCover({width:w,height:h,mask});
  assert.equal(r.sourcePixels,mask.filter(x=>x===255).length);assert.ok(r.exactReplayPassed);
 }
});
test('200: malformed binary source mask is rejected',()=>{
 assert.throws(()=>exactSourceRectangleCover({width:2,height:1,mask:new Uint8Array([1,255])}),/NONBINARY/);
});
test('201: palette colors are actual source RGB and counted only for agreeing subject',()=>{
 const f=fixture(),p=classifyPairedLabels(f),source=rgba(f.alpha);
 const r=extractObservedRoleColors({pair:p,rgba:source,maxColors:3});
 assert.equal(r.colorsInvented,0);
 assert.equal(r.roles.reduce((s,t)=>s+t.observedPixels,0),p.counts.subject);
 assert.ok(r.roles.every(t=>t.colors.every(c=>/^#[0-9a-f]{6}$/.test(c.rgb))));
 assert.equal(r.roleBoundaryCertified,false);
});
test('201: nonopaque RGB mismatch is rejected on agreed subject',()=>{
 const f=fixture(),p=classifyPairedLabels(f),source=rgba(f.alpha);source[2*4+3]=0;
 assert.throws(()=>extractObservedRoleColors({pair:p,rgba:source}),/NONOPAQUE/);
});
test('201: invalid palette cap rejected',()=>{
 const f=fixture(),p=classifyPairedLabels(f);
 assert.throws(()=>extractObservedRoleColors({pair:p,rgba:rgba(f.alpha),maxColors:17}));
});
test('202: cost is actually calculated from exact source rectangles and strict hold',()=>{
 const f=fixture(),p=classifyPairedLabels(f),s=deriveConservativeSubjectEvidence(p),
 rect=exactSourceRectangleCover({width:f.width,height:f.height,mask:s.knownSubject});
 const x=auditExactWholeSubjectBudget({caseId:f.caseId,rectangles:rect,consensus:s});
 assert.equal(x.exactObservedVertexCost,rect.explicitVertices);
 assert.equal(x.historicVertexLimit,1887);
 assert.equal(x.unknownOpaquePixels,s.unknownOpaquePixels);
 assert.equal(x.wholeBodyVerified,false);assert.equal(x.goldenApproved,false);
});
test('202: numbers alone never prove complete silhouette',()=>{
 const f=fixture(),p=classifyPairedLabels(f),s=deriveConservativeSubjectEvidence(p);
 const rect=exactSourceRectangleCover({width:f.width,height:f.height,mask:s.knownSubject});
 assert.equal(auditExactWholeSubjectBudget({caseId:'GC001',rectangles:rect,consensus:s}).withinHistoricNumericLimit,true);
 assert.equal(auditExactWholeSubjectBudget({caseId:'GC001',rectangles:rect,consensus:s}).wholeBodyVerified,false);
});
test('203: all optimistic flags cannot auto-release',()=>{
 const base={withinHistoricNumericLimit:true,wholeBodyVerified:true};
 const r=evaluateStage203ReleaseGate({gc001:{...base,caseId:'GC001'},raden:{...base,caseId:'Raden'},
 manualAllPixelsReviewed:true,sourceIntegrityVerified:true,realIphoneSafariPassed:true,
 rollbackPassed:true,fullSceneRgbAuditPassed:true,independentGoldenCertified:true});
 assert.deepEqual(r.missingGates,[]);assert.equal(r.automaticReleaseAllowed,false);
 assert.equal(r.productionReleaseAuthorized,false);
});
test('203: unresolved gates are explicitly listed with missing source cases',()=>{
 const r=evaluateStage203ReleaseGate({});
 assert.ok(r.missingGates.includes('TWO_CASES'));
 assert.ok(r.missingGates.includes('PIXEL_ADJUDICATION'));
 assert.ok(r.missingGates.includes('REAL_IPHONE_SAFARI'));
 assert.ok(r.missingGates.includes('ROLLBACK'));
 assert.equal(r.gateStatus,'GOLDEN_HOLD_MANUAL_APPROVAL_REQUIRED');
});
test('203: real failure of numeric vertex budget is not glossed over',()=>{
 const r=evaluateStage203ReleaseGate({gc001:{caseId:'GC001',withinHistoricNumericLimit:false,wholeBodyVerified:false},raden:{caseId:'Raden',withinHistoricNumericLimit:true,wholeBodyVerified:true}});
 assert.ok(r.missingGates.includes('EXACT_VERTEX_BUDGET'));
 assert.ok(r.missingGates.includes('WHOLEBODY'));assert.equal(r.releaseAuthorized,undefined);
});
