import test from 'node:test';
import assert from 'node:assert/strict';
import {VERSION,recordOutOfBandIndependence,buildPrivateAdjudicationQueue,registerManualDecisions}
 from '../../web/static/public-review-adjudication-stage193-p0.mjs';
const alpha=n=>new Uint8Array(n).fill(255);
test('out-of-band confirmation is recorded but not software identity proof',()=>{
 const x=recordOutOfBandIndependence({confirmed:true,statement:'Reviewer A and B did not see each others work',date:'2026-10-14'});
 assert.equal(x.operatorReportedIndependentReviews,true);
 assert.equal(x.softwareIdentityVerified,false);
 assert.equal(x.semanticPixelsCertified,0);
 assert.equal(x.goldenApproved,false);
 assert.throws(()=>recordOutOfBandIndependence({confirmed:false,statement:'reviewed independently',date:'2026-10-14'}));
 assert.throws(()=>recordOutOfBandIndependence({confirmed:true,statement:'reviewed independently',date:'yesterday'}));
});
test('fully account for agreement, dispute, abstention, uncertainty',()=>{
 const a=new Uint8Array([1,6,6,6,1,2,2,9,0,2,0,2]);
 const b=new Uint8Array([1,5,6,0,6,2,1,4,1,2,2,2]);
 const q=buildPrivateAdjudicationQueue({caseId:'GC001',width:4,height:3,sourceAlpha:alpha(12),labelsA:a,labelsB:b});
 assert.deepEqual([q.originalOpaquePixels,q.agreePixels,q.disagreePixels,q.abstainPixels,q.uncertainPixels],[12,5,3,3,1]);
 assert.equal(q.reviewPixels,7);
 assert.equal(q.reviewComponents.reduce((s,c)=>s+c.pixels,0),7);
 assert.equal(q.allReviewPixelsAccounted,true);assert.equal(q.goldenApproved,false);
 assert.ok(q.reviewComponents.every(x=>x.decision==='PENDING'));
});
test('component four-connectivity and fixed directed class pairs, not diagonal bridge',()=>{
 const a=new Uint8Array([6,6,1,6,1,1,1,1,6]);
 const b=new Uint8Array([5,5,1,1,1,1,1,1,5]);
 const q=buildPrivateAdjudicationQueue({caseId:'Raden',width:3,height:3,sourceAlpha:alpha(9),labelsA:a,labelsB:b});
 assert.equal(q.reviewPixels,4);assert.deepEqual(q.reviewComponents.map(x=>x.pixels).sort(),[1,1,2]);
});
test('nonopaque source never gets semantic class or review pixel',()=>{
 const sourceAlpha=new Uint8Array([255,0,255,255]),a=new Uint8Array([1,0,6,0]),b=new Uint8Array([1,0,5,0]);
 const q=buildPrivateAdjudicationQueue({caseId:'GC001',width:2,height:2,sourceAlpha,labelsA:a,labelsB:b});
 assert.equal(q.originalOpaquePixels,3);assert.equal(q.reviewPixels,2);
 const bad=new Uint8Array(a);bad[1]=1;
 assert.throws(()=>buildPrivateAdjudicationQueue({caseId:'GC001',width:2,height:2,sourceAlpha,labelsA:bad,labelsB:b}),/NONOPAQUE/);
});
test('reject unsupported cases, lengths and class ids',()=>{
 const z={caseId:'GC001',width:2,height:2,sourceAlpha:alpha(4),labelsA:new Uint8Array(4),labelsB:new Uint8Array(4)};
 assert.throws(()=>buildPrivateAdjudicationQueue({...z,caseId:'Other'}));
 assert.throws(()=>buildPrivateAdjudicationQueue({...z,labelsB:new Uint8Array(3)}));
 assert.throws(()=>buildPrivateAdjudicationQueue({...z,labelsB:new Uint8Array([10,0,0,0])}));
});
test('manual decision logging requires explicit reason, no auto Golden',()=>{
 const q=buildPrivateAdjudicationQueue({caseId:'GC001',width:2,height:2,sourceAlpha:alpha(4),
  labelsA:new Uint8Array([6,6,1,1]),labelsB:new Uint8Array([5,5,1,2])});
 const [first,second]=q.reviewComponents;
 const decisions=[{componentId:first.componentId,choice:'A',reason:'Original source consulted'},
 {componentId:second.componentId,choice:'DEFER',reason:'Insufficient visual evidence'}];
 const result=registerManualDecisions({queue:q,decisions});
 assert.equal(result.notYetReviewedPixels,0);
 assert.equal(result.manualCandidatePixels+result.deferredPixels,q.reviewPixels);
 assert.equal(result.paintAuthorized,false);assert.equal(result.semanticPixelsCertified,0);
 assert.throws(()=>registerManualDecisions({queue:q,decisions:[decisions[0],decisions[0]]}));
 assert.throws(()=>registerManualDecisions({queue:q,decisions:[{componentId:'wrong',choice:'A',reason:'reviewed'}]}));
 assert.throws(()=>registerManualDecisions({queue:q,decisions:[{componentId:first.componentId,choice:'A',reason:''}]}));
});
test('even two completely matching arrays never become Golden automatically',()=>{
 const a=new Uint8Array([1,2,3,4]);
 const q=buildPrivateAdjudicationQueue({caseId:'Raden',width:2,height:2,sourceAlpha:alpha(4),labelsA:a,labelsB:new Uint8Array(a)});
 assert.equal(q.reviewPixels,0);assert.equal(q.reviewComponents.length,0);
 assert.equal(q.goldenApproved,false);assert.equal(q.autoPromotedPixels,0);assert.equal(q.version,VERSION);
});