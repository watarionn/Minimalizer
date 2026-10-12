import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {proposeSourceRectangles} from '../../web/static/public-source-geometry-p0.mjs';
import {compositeSourceGeometry} from '../../web/static/public-source-compositor-p0.mjs';
import {auditStructuralCandidate} from '../../web/static/public-structural-qa-p0.mjs';
import {evaluateStructuralPromotion} from '../../web/static/public-structural-release-gate-p0.mjs';
if(!globalThis.crypto)globalThis.crypto=webcrypto;
const sha=a=>createHash('sha256').update(a).digest('hex');
const expectError=(fn,msg)=>assert.rejects(fn,new RegExp(msg));
const s=()=>{
 const width=40,height=40,n=width*height,src=new Uint8Array(n*4),base=new Uint8Array(n*4),face=new Uint8Array(n),mask=new Uint8Array(n);
 for(let i=0;i<n;i++){src.set([40,45,65,255],4*i);base.set([60,50,40,255],4*i);}
 for(let y=3;y<12;y++)for(let x=3;x<17;x++){const i=y*width+x;src.set([239,242,245,255],i*4);mask[i]=255;}
 for(let y=12;y<19;y++)for(let x=3;x<9;x++){const i=y*width+x;src.set([239,242,245,255],i*4);mask[i]=255;}
 for(let y=22;y<30;y++)for(let x=17;x<25;x++){const i=y*width+x;src.set([224,180,156,255],i*4);face[i]=255;}
 const f={id:'eyewear_test',role:'eyewear',evidenceLevel:'research_observation',evidenceRef:'private-fixture',
  colorClass:'high_neutral',bbox:[3,3,17,19],mask,maskSha256:sha(mask),maxPixels:200};
 return {width,height,sourceRgba:src,sourceRgbaSha256:sha(src),baselineRgba:base,baselineRgbaSha256:sha(base),
  faceMask:face,faceMaskSha256:sha(face),features:[f],maxChangedPixels:500};
};
const geom=a=>proposeSourceRectangles({width:a.width,height:a.height,faceMask:a.faceMask,features:a.features,maxRectsPerFeature:5,minRectPixels:8,maxTotalVertices:24});
test('Stage7 source exact shapes and deterministic',async()=>{
 const a=s(),b=await geom(a),c=await geom(a);assert.deepEqual(b,c);assert(b.parts[0].rects.length>0);
 const covered=new Uint8Array(a.width*a.height);for(const [x0,y0,x1,y1] of b.parts[0].rects)for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){let i=y*a.width+x;assert.equal(a.features[0].mask[i],255);assert(!covered[i]);covered[i]=1;}
 assert.equal(covered.reduce((x,y)=>x+y,0),b.parts[0].containedPixels);
});
test('Stage7 rejects unsigned observation',async()=>{const a=s();a.features[0].evidenceLevel='signed';await expectError(()=>geom(a),'unverified_feature');});
test('Stage7 rejects tampered SHA',async()=>{const a=s();a.features[0].mask[1]=255;await expectError(()=>geom(a),'mask_SHA_mismatch');});
test('Stage7 rejects face overlap',async()=>{const a=s();a.faceMask[3*40+4]=255;await expectError(()=>geom(a),'face_collision');});
test('Stage7 rejects disjoint duplicate feature overlap',async()=>{const a=s();a.features.push({...a.features[0],id:'bow_other'});await expectError(()=>geom(a),'unresolved_feature_overlap');});
test('Stage7 rejects insufficient global vertices',async()=>{const a=s();const g=await proposeSourceRectangles({width:40,height:40,faceMask:a.faceMask,features:a.features,maxRectsPerFeature:8,minRectPixels:8,maxTotalVertices:4});assert.equal(g.totalVertices,4);});
test('Stage7 rejects nonbinary source mask',async()=>{const a=s();a.features[0].mask[1]=128;a.features[0].maskSha256=sha(a.features[0].mask);await expectError(()=>geom(a),'nonbinary_feature');});
test('Stage7 rejects nonbinary face mask',async()=>{const a=s();a.faceMask[0]=1;await expectError(()=>geom(a),'nonbinary_face');});
test('Stage8 retained feature & protected face reuses actual source RGB',async()=>{
 const a=s(),g=await geom(a),r=await compositeSourceGeometry({...a,geometry:g});
 assert.equal(r.audit.productPromotionAuthorized,false);assert.equal(r.audit.faceFlattened,true);assert(r.audit.featurePixelsChanged>0);
 const skin=[...r.rgba.slice((22*40+17)*4,(22*40+17)*4+3)];
 for(let i=0;i<1600;i++){
  const o=4*i;assert.equal(r.rgba[o+3],255);
  if(a.faceMask[i])assert.deepEqual([...r.rgba.slice(o,o+3)],skin);
  else if(!a.features[0].mask[i])assert.deepEqual([...r.rgba.slice(o,o+3)],[...a.baselineRgba.slice(o,o+3)]);
 }
});
test('Stage8 refuses invented rectangle outside original source mask',async()=>{
 const a=s(),g=await geom(a);g.parts[0].rects[0]=[0,0,8,8];await expectError(()=>compositeSourceGeometry({...a,geometry:g}),'geometry_not_in_observed_source');
});
test('Stage8 refuses face crossing',async()=>{const a=s(),g=await geom(a);a.faceMask[3*40+4]=255;
 await expectError(()=>compositeSourceGeometry({...a,geometry:g}),'face_collision');});
test('Stage8 refuses lying vertex counts',async()=>{const a=s(),g=await geom(a);g.totalVertices++;
 await expectError(()=>compositeSourceGeometry({...a,geometry:g}),'geometry_vertex_accounting');});
test('Stage9 metric is non-promoting and outside evidence is zero',async()=>{
 const a=s(),g=await geom(a),r=await compositeSourceGeometry({...a,geometry:g});
 const q=auditStructuralCandidate({width:a.width,height:a.height,sourceRgba:a.sourceRgba,baselineRgba:a.baselineRgba,
 candidateRgba:r.rgba,faceMask:a.faceMask,observations:a.features,geometry:g});
 assert.equal(q.offObservation,0);assert.equal(q.alphaChanges,0);assert(q.improvesOriginalRGB);assert.equal(q.productPromotionAuthorized,false);
});
test('Stage9 rejects fake QA dimensions',()=>{assert.throws(()=>auditStructuralCandidate({width:0,height:1}),/INVALID_QA_INPUT/);});
test('Stage11 real known structural blockers cannot promote',()=>{
 const e={cases:[{case:'GC001',originalVertices:3604,allowedVertices:1887,sourcePixelAuthorityPassed:true},
 {case:'Raden',originalVertices:2370,allowedVertices:1412,sourcePixelAuthorityPassed:true}]};
 const r=evaluateStructuralPromotion(e);assert.equal(r.productPromotionAuthorized,false);assert(r.blockerCount>=11);
 assert(r.blockers.some(x=>x.includes('GC001_ORIGINAL_STAGE8_OVER_BUDGET')));
});
test('Stage11 duplicate cases rejected',()=>{assert.throws(()=>evaluateStructuralPromotion({cases:[{case:'Raden'},{case:'Raden'}]}),/REQUIRE_GC001_AND_RADEN/);});
test('Stage11 no silent default budget',()=>{assert.throws(()=>evaluateStructuralPromotion({cases:[{case:'GC001'},{case:'Raden'}]}),/INVALID_STAGE8_COUNT/);});
import {vetoRegressingGeometry} from '../../web/static/public-structural-qa-p0.mjs';
test('Stage9 rejects sparse new geometry even if raw RGB error improves',()=>{
 const got=vetoRegressingGeometry({candidate:{sourceOnlyPass:true,sourceEvidenceCoverage:.43,percentGain:.024},
 prior:{percentGain:.15}});assert.equal(got.adoptNewCandidate,false);
 assert(got.reasonCodes.includes('SOURCE_STRUCTURE_LOST'));
 assert(got.reasonCodes.includes('REGRESSION_AGAINST_PREVIOUS_CANDIDATE'));
});
test('Stage9 veto passes engineering criteria but NEVER signs human Golden',()=>{
 const got=vetoRegressingGeometry({candidate:{sourceOnlyPass:true,sourceEvidenceCoverage:.80,percentGain:3},prior:{percentGain:2}});
 assert.equal(got.adoptNewCandidate,true);assert.equal(got.humanGoldenApproved,false);
});
test('Stage9 refuses unauthorized boundary regardless of pixel gain',()=>{
 const got=vetoRegressingGeometry({candidate:{sourceOnlyPass:false,sourceEvidenceCoverage:1,percentGain:5},prior:{percentGain:2}});
 assert.equal(got.adoptNewCandidate,false);assert(got.reasonCodes.includes('SOURCE_BOUNDARY_CHANGED'));
});
