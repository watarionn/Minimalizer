import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {traceSourceContours,rasterizeSourceRings} from '../../web/static/public-source-contour-p0.mjs';
import {simplifySignedObservationContours,rasterizeSlopedRings,auditContourCandidate} from '../../web/static/public-safe-contour-simplify-p0.mjs';
import {evaluateSvgSourceParity} from '../../web/static/public-svg-dpr-guard-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=x=>createHash('sha256').update(x).digest('hex');
const fixture=(hole=false)=>{
 const width=24,height=24,face=new Uint8Array(width*height),mask=new Uint8Array(width*height);
 for(let y=4;y<18;y++)for(let x=3;x<19;x++)mask[y*width+x]=255;
 if(hole)for(let y=7;y<14;y++)for(let x=8;x<15;x++)mask[y*width+x]=0;
 face[20*width+4]=255;
 const f={id:'test_feature',role:'eyewear',mask,maskSha256:sha(mask),evidenceLevel:'research_observation',evidenceRef:'unit-fixture-source'};
 return {width,height,faceMask:face,features:[f],f};
};
async function run(x=fixture()){return traceSourceContours({...x,maxVertices:5000});}
test('S12 contiguous rectangle encoded with 4 vertices and 100% coverage',async()=>{const x=fixture(),r=await run(x);assert.equal(r.parts[0].vertexCount,4);assert.equal(r.parts[0].coverage,1);assert.equal(r.totalVertices,4);});
test('S12 hole remains transparent, source rings parity exact',async()=>{const x=fixture(true),r=await run(x);assert.equal(r.parts[0].rings.length,2);const p=rasterizeSourceRings({width:x.width,height:x.height,rings:r.parts[0].rings});assert.deepEqual(p,x.f.mask);});
test('S12 diagonally touching pixels keep correct separate boundary',async()=>{const x=fixture();x.f.mask.fill(0);x.f.mask[5*24+5]=255;x.f.mask[6*24+6]=255;x.f.maskSha256=sha(x.f.mask);await assert.rejects(()=>run(x),/TINY_UNSUPPORTED/);for(let y=5;y<9;y++)for(let k=5;k<9;k++)x.f.mask[y*24+k]=255;for(let y=10;y<14;y++)for(let k=10;k<14;k++)x.f.mask[y*24+k]=255;x.f.maskSha256=sha(x.f.mask);const z=await run(x);assert.deepEqual(rasterizeSourceRings({width:24,height:24,rings:z.parts[0].rings}),x.f.mask);});
test('S12 does not mutate original observation mask',async()=>{const x=fixture(true),before=x.f.mask.slice();await run(x);assert.deepEqual(x.f.mask,before);});
test('S12 refuses tampered SHA pin',async()=>{const x=fixture();x.f.mask[0]=255;await assert.rejects(()=>run(x),/MASK_SHA_MISMATCH/);});
test('S12 refuses overlap of face and observation',async()=>{const x=fixture();x.faceMask[4*24+3]=255;await assert.rejects(()=>run(x),/FACE_CONFLICT/);});
test('S12 refuses cross-feature overlap',async()=>{const x=fixture();x.features.push({...x.f,id:'copy'});await assert.rejects(()=>run(x),/CROSS_FEATURE_OVERLAP/);});
test('S12 refuses unproven semantics and bad masks',async()=>{const x=fixture();x.f.evidenceLevel='signed';await assert.rejects(()=>run(x),/UNSIGNED_OBSERVATION/);x.f.evidenceLevel='research_observation';x.f.mask[3]=128;x.f.maskSha256=sha(x.f.mask);await assert.rejects(()=>run(x),/NONBINARY_FEATURE_MASK/);});
test('S12 refuses impossible vertex budget',async()=>{const x=fixture(true);await assert.rejects(()=>traceSourceContours({...x,maxVertices:4}),/EXPLICIT_SOURCE_RING_VERTEX_BUDGET/);});
test('S13 raster audit refuses inventing new pixels',async()=>{const x=fixture();const q=auditContourCandidate({width:24,height:24,sourceMask:x.f.mask,rings:[[[0,0],[5,0],[5,5],[0,5]]]});assert(q.spillPixels>0);assert(!q.sourceOnlyPass);});
test('S13 only uses an exact-source candidate, no Golden promotion',async()=>{const x=fixture(true),r=await run(x),q=simplifySignedObservationContours({width:24,height:24,parts:r.parts,sourceMasks:{test_feature:x.f.mask},maxTotalVertices:50});assert(q.passSourceExactness);assert.equal(q.parts[0].coverage,1);assert.equal(q.productPromotionAuthorized,false);});
test('S13 source cardinality remains exact on ring raster',async()=>{const x=fixture(true),z=await run(x),p=z.parts[0].rings;assert.deepEqual(rasterizeSlopedRings({rings:p,width:24,height:24}),x.f.mask);});
test('S14 accepts exact alpha at 1x and 2x',()=>{const w=3,h=3,m=new Uint8Array(9);m[4]=255;const a=m.slice(),b=new Uint8Array(36);for(let y=2;y<4;y++)for(let x=2;x<4;x++)b[y*6+x]=255;const z=evaluateSvgSourceParity({width:w,height:h,sourceMask:m,renderedAlpha340:a,renderedAlpha680:b});assert(z.exact340and680);assert.equal(z.spill680,0);});
test('S14 rejects DPR2 bleed invisible at 1x',()=>{const w=3,h=3,m=new Uint8Array(9);m[4]=255;const a=m.slice(),b=new Uint8Array(36);for(let y=2;y<4;y++)for(let x=2;x<4;x++)b[y*6+x]=255;b[1*6+2]=128;const z=evaluateSvgSourceParity({width:w,height:h,sourceMask:m,renderedAlpha340:a,renderedAlpha680:b});assert.equal(z.mismatch340,0);assert(!z.exact340and680);assert(z.spill680>0);});
test('S14 rejects partial alpha inside footprint',()=>{const m=new Uint8Array([255]),a=new Uint8Array([255]),b=new Uint8Array([255,200,255,255]);const z=evaluateSvgSourceParity({width:1,height:1,sourceMask:m,renderedAlpha340:a,renderedAlpha680:b});assert(!z.exact340and680);assert.equal(z.antialias680,1);});
test('S14 refuses nonbinary original mask',()=>{assert.throws(()=>evaluateSvgSourceParity({width:1,height:1,sourceMask:new Uint8Array([128]),renderedAlpha340:new Uint8Array(1),renderedAlpha680:new Uint8Array(4)}),/SOURCE_MASK_NONBINARY/);});
import {evaluateContourResearchGate} from '../../web/static/public-contour-research-gate-p0.mjs';
test('S15 fails closed on historical original ring budgets',()=>{const gate=evaluateContourResearchGate({cases:[
 {case:'GC001',originalStage8Vertices:3604,maxStage8Vertices:1887,exactFeatureVertices:398,exactDprMaskParity:true,sourceMaskProof:true,sourceColorProvenance:true,simplifiedDprMaskParity:false},
 {case:'Raden',originalStage8Vertices:2370,maxStage8Vertices:1412,exactFeatureVertices:1968,exactDprMaskParity:true,sourceMaskProof:true,sourceColorProvenance:true,simplifiedDprMaskParity:false}]});
 assert.equal(gate.expectedStatus,'DRAFT_HOLD');assert.equal(gate.productPromotionAuthorized,false);
 assert.equal(gate.cases[0].conservativeTotal,4002);assert.equal(gate.cases[1].conservativeTotal,4338);
 assert(gate.blockerCount>=12);});
test('S15 never promotes unsigned or incomplete two-case evidence',()=>{assert.throws(()=>evaluateContourResearchGate({cases:[]}),/REQUIRE_TWO_DISTINCT_SIGNED_CASES/);});
