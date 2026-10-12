import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {buildSourceStrokeCover,renderStrokeCoverSvg} from '../../web/static/public-source-stroke-cover-p0.mjs';
import {buildSourceStrokeResearchBundle} from '../../web/static/public-source-stroke-bundle-p0.mjs';
globalThis.crypto||=webcrypto;
const hash=a=>createHash('sha256').update(a).digest('hex');
function fixture(){const width=8,height=8,mask=new Uint8Array(64),face=new Uint8Array(64);for(let y=1;y<=4;y++)for(let x=1;x<=3;x++)mask[8*y+x]=255;face[62]=255;return {width,height,mask,face};}
async function cover(f=fixture(),orientation='best'){return buildSourceStrokeCover({width:f.width,height:f.height,sourceMask:f.mask,sourceMaskSha256:hash(f.mask),orientation});}
function feature(f=fixture()){return {id:'source_observed',evidenceLevel:'research_observation',sourceMask:f.mask,sourceMaskSha256:hash(f.mask),contourVertices:10};}
async function bundle(f=fixture(),features=[feature(f)]){return buildSourceStrokeResearchBundle({caseId:'GC001',width:f.width,height:f.height,faceMask:f.face,faceMaskSha256:hash(f.face),features});}

test('S52 exact 3x4 source rectangle encoded as one stroke',async()=>{const c=await cover();assert.equal(c.strokeCount,1);assert.equal(c.endpointCount,2);assert.equal(c.observedPixels,12);});
test('S52 binary source mask never changed',async()=>{const f=fixture(),original=f.mask.slice();await cover(f);assert.deepEqual(f.mask,original);});
test('S52 valid horizontal produces 1 segment',async()=>{const c=await cover(fixture(),'horizontal');assert.equal(c.strokeCount,1);assert.equal(c.orientation,'horizontal');});
test('S52 valid vertical produces 1 segment',async()=>{const c=await cover(fixture(),'vertical');assert.equal(c.strokeCount,1);assert.equal(c.orientation,'vertical');});
test('S52 best chooses orientation with fewer lines',async()=>{const f=fixture();for(let y=0;y<8;y++)for(let x=0;x<8;x++)f.mask[y*8+x]=y%2?255:0;const v=await cover(f,'vertical'),h=await cover(f,'horizontal'),b=await cover(f);assert.equal(b.strokeCount,Math.min(v.strokeCount,h.strokeCount));});
test('S52 sparse disconnected pixels remain separate',async()=>{const f=fixture();f.mask.fill(0);f.mask[0]=255;f.mask[63]=255;const r=await cover(f);assert.equal(r.strokeCount,2);assert.equal(r.observedPixels,2);});
test('S52 a central hole stays unpainted by exact run cover',async()=>{const f=fixture();f.mask[2*8+2]=0;const r=await cover(f);assert.equal(r.observedPixels,11);assert(r.strokeCount>=2);});
test('S52 hash mismatch cannot be bypassed',async()=>{const f=fixture();await assert.rejects(()=>buildSourceStrokeCover({width:8,height:8,sourceMask:f.mask,sourceMaskSha256:'a'.repeat(64)}),/SOURCE_STROKE_MASK_SHA_MISMATCH/);});
test('S52 malformed source mask rejected',async()=>{const f=fixture();f.mask[5]=1;await assert.rejects(()=>cover(f),/NONBINARY_STROKE_SOURCE/);});
test('S52 all zero source refuses invention',async()=>{const f=fixture();f.mask.fill(0);await assert.rejects(()=>cover(f),/EMPTY_SOURCE_STROKE/);});
test('S52 source dimensions mismatch rejects',async()=>{const f=fixture();await assert.rejects(()=>buildSourceStrokeCover({width:7,height:8,sourceMask:f.mask,sourceMaskSha256:hash(f.mask)}),/INVALID_SOURCE_STROKE_INPUT/);});
test('S52 strict stroke limit refuses truncation',async()=>{const f=fixture();f.mask.fill(0);f.mask[1]=255;f.mask[17]=255;await assert.rejects(()=>buildSourceStrokeCover({width:8,height:8,sourceMask:f.mask,sourceMaskSha256:hash(f.mask),maxStrokes:1}),/STROKE_SOURCE_BUDGET_EXCEEDED/);});
test('S52 no automatic approval or comparable budget',async()=>{const c=await cover();assert.equal(c.productPromotionAuthorized,false);assert.equal(c.endpointCostComparableToPolygonVertexBudget,false);assert.equal(c.browserDpr2Verified,false);});
test('S53 clean SVG string contains no embedded raster or script',async()=>{const c=await cover(),s=renderStrokeCoverSvg(c);assert.match(s,/stroke-linecap="butt"/);assert(!s.includes('<image'));assert(!s.includes('<script'));});
test('S53 forged XML path content cannot become SVG',async()=>{const c=await cover();c.svgPaths+='<script>alert(1)</script>';assert.throws(()=>renderStrokeCoverSvg(c),/UNTRUSTED_SVG_SOURCE/);});
test('S53 tampered endpoints cannot become SVG',async()=>{const c=await cover();c.strokes[0].a[0]+=1;assert.throws(()=>renderStrokeCoverSvg(c),/INVALID_SOURCE_STROKE_COVER/);});
test('S53 forged width cannot become SVG',async()=>{const c=await cover();c.strokes[0].width=999;assert.throws(()=>renderStrokeCoverSvg(c),/INVALID_SOURCE_STROKE_COVER/);});
test('S53 fake or missing orientation refused',async()=>{const c=await cover();c.orientation='diagonal';assert.throws(()=>renderStrokeCoverSvg(c),/INVALID_SOURCE_STROKE_COVER/);});
test('S53 no unexpected changes across rerun',async()=>{const a=await cover(),b=await cover();assert.deepEqual(a,b);});
test('S55 single feature bundle observes exactly 12 pixels',async()=>{const r=await bundle();assert.equal(r.observedSourcePixels,12);assert.equal(r.strokeEndpoints,2);assert.equal(r.sourceContourVertices,10);});
test('S55 no release and no Golden from feature source',async()=>{const r=await bundle();assert.equal(r.status,'RESEARCH_ONLY_DRAFT_HOLD');assert.equal(r.vertexBudgetCertified,false);assert.equal(r.paintAuthorized,false);});
test('S55 forged reviewer evidence is rejected',async()=>{const f=fixture(),featureObj=feature(f);featureObj.evidenceLevel='reviewer_verified';await assert.rejects(()=>bundle(f,[featureObj]),/INVALID_STROKE_FEATURE/);});
test('S55 cannot paint protected face',async()=>{const f=fixture();f.face[8+1]=255;await assert.rejects(()=>bundle(f),/FACE_CONFLICT/);});
test('S55 feature overlap rejected',async()=>{const f=fixture();await assert.rejects(()=>bundle(f,[feature(f),{...feature(f),id:'other_feature'}]),/CROSS_FEATURE_OVERLAP/);});
test('S55 signed face cannot be altered',async()=>{const f=fixture();await assert.rejects(()=>buildSourceStrokeResearchBundle({caseId:'GC001',width:8,height:8,faceMask:f.face,faceMaskSha256:'a'.repeat(64),features:[feature(f)]}),/FACE_MASK_PIN_MISMATCH/);});
test('S55 unrecognized feature name cannot become SVG injection',async()=>{const f=fixture(),g=feature(f);g.id='<svg>';await assert.rejects(()=>bundle(f,[g]),/INVALID_STROKE_FEATURE/);});
test('S55 wrong image identity is rejected',async()=>{const f=fixture();await assert.rejects(()=>buildSourceStrokeResearchBundle({caseId:'other',width:8,height:8,faceMask:f.face,faceMaskSha256:hash(f.face),features:[feature(f)]}),/INVALID_STROKE_BUNDLE/);});
test('S55 signed source feature hash mismatch rejects',async()=>{const f=fixture(),g=feature(f);g.sourceMaskSha256='b'.repeat(64);await assert.rejects(()=>bundle(f,[g]),/SOURCE_STROKE_MASK_SHA_MISMATCH/);});
test('S55 duplicate feature IDs rejected',async()=>{const f=fixture();await assert.rejects(()=>bundle(f,[feature(f),feature(f)]),/INVALID_STROKE_FEATURE/);});

test('S55 nonbinary signed face map refused',async()=>{const f=fixture();f.face[1]=4;await assert.rejects(()=>bundle(f),/NONBINARY_FACE_MASK/);});
