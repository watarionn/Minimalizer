import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {probeNativeReviewOrigin} from '../../web/static/public-review-secure-origin-guard-p0.mjs';
import {auditSourceSvgVertexBudget} from '../../web/static/public-source-dpr-budget-audit-p0.mjs';
import {exactSourceRectangleCover,compareExactCoverBudget} from '../../web/static/public-source-exact-rect-cover-p0.mjs';
import {inventorySourceFidelity} from '../../web/static/public-source-fidelity-ledger-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=a=>createHash('sha256').update(a).digest('hex');
const W=12,H=12,N=W*H;
function fixture(){
 const mask=new Uint8Array(N),source=new Uint8Array(4*N),baseline=new Uint8Array(4*N),face=new Uint8Array(N),background=new Uint8Array(N),left=new Uint8Array(N),right=new Uint8Array(N);
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){const i=y*W+x;source.set([x*9,y*11,24,255],4*i);baseline.set([x*9,y*11,24,255],4*i);}
 for(let y=3;y<8;y++)for(let x=2;x<6;x++)mask[y*W+x]=left[y*W+x]=255;
 for(let y=3;y<8;y++)for(let x=8;x<11;x++)right[y*W+x]=255;
 face[4*W+7]=255;background[0]=255;baseline[4*(5*W+3)]=231;
 const rings=[[[2,3],[6,3],[6,8],[2,8]]];
 return {mask,source,baseline,face,background,left,right,rings};
}
function feat(f){return {width:W,height:H,budget:16,features:[{id:'observed',evidenceLevel:'research_observation',sourceMask:f.mask,sourceMaskSha256:sha(f.mask),rings:f.rings}]};}
function fidal(f){return {width:W,height:H,sourceRgba:f.source,sourceSha256:sha(f.source),baselineRgba:f.baseline,baselineSha256:sha(f.baseline),leftArmMask:f.left,leftSha256:sha(f.left),rightArmMask:f.right,rightSha256:sha(f.right),faceMask:f.face,faceSha256:sha(f.face),observedBackground:f.background,backgroundSha256:sha(f.background)};}
// 47: a capability readout is not a trusted reviewer or real production Safari proof.
test('S47 node context cannot claim real HTTPS browser verification',()=>{const r=probeNativeReviewOrigin();assert.equal(r.nativeSecureReviewUsable,false);assert.equal(r.iphoneSafariVerified,false);assert.equal(r.productPromotionAuthorized,false);});
test('S47 probe is a no-input/no-paint operation',()=>{const a=probeNativeReviewOrigin(),b=probeNativeReviewOrigin();assert.deepEqual(a,b);assert.equal(a.realProductionOriginTested,false);});
// 48: verified 1x/2x parity.
test('S48 source aligned rectangle has zero 1x and 2x errors',async()=>{const r=await auditSourceSvgVertexBudget(feat(fixture()));assert.equal(r.totalVertices,4);assert(r.sourceGeometryExact);assert.equal(r.parts[0].mismatch2x,0);});
test('S48 vertex cap applies even if raster exact',async()=>{const f=fixture(),r=await auditSourceSvgVertexBudget({...feat(f),budget:4});assert(r.withinBudget);assert(!r.fullCharacterVerified);});
test('S48 source RGB is never encoded in report',async()=>{const r=await auditSourceSvgVertexBudget(feat(fixture()));assert(!('sourceRgba' in r));assert.equal(r.productPromotionAuthorized,false);});
test('S48 1px shifted ring produces parity errors',async()=>{const f=fixture();f.rings=[[[3,3],[7,3],[7,8],[3,8]]];const r=await auditSourceSvgVertexBudget(feat(f));assert.equal(r.sourceGeometryExact,false);assert(r.parts[0].mismatch2x>0);});
test('S48 small manual vertex cap is independent of parity',async()=>{const f=fixture(),r=await auditSourceSvgVertexBudget({...feat(f),features:[{id:'observed',evidenceLevel:'research_observation',sourceMask:f.mask,sourceMaskSha256:sha(f.mask),rings:[[[2,3],[6,3],[6,5],[6,8],[2,8]]]}],budget:4});assert(r.totalVertices===5);assert(r.overBy===1);});
test('S48 bit-corrupted original mask rejects',async()=>{const f=fixture(),q=feat(f);q.features[0].sourceMaskSha256='0'.repeat(64);await assert.rejects(()=>auditSourceSvgVertexBudget(q),/SOURCE_FEATURE_SHA_MISMATCH/);});
test('S48 observed label is not actual trusted anatomy',async()=>{const f=fixture(),q=feat(f);q.features[0].evidenceLevel='reviewer_verified';await assert.rejects(()=>auditSourceSvgVertexBudget(q),/INVALID_SOURCE_FEATURE/);});
test('S48 overlapping independent masks are rejected',async()=>{const q=feat(fixture());q.features.push({...q.features[0],id:'copy'});await assert.rejects(()=>auditSourceSvgVertexBudget(q),/SOURCE_FEATURE_OVERLAP/);});
test('S48 negative coordinate cannot become paint geometry',async()=>{const f=fixture();f.rings=[[[-1,3],[6,3],[6,8],[2,8]]];await assert.rejects(()=>auditSourceSvgVertexBudget(feat(f)),/INVALID_VECTOR_GEOMETRY/);});
// 49: exact disjoint run rectangles.
test('S49 one square is exactly one rectangle',()=>{const r=exactSourceRectangleCover({width:W,height:H,sourceMask:fixture().mask});assert.equal(r.rectangleCount,1);assert.deepEqual(r.rectangles[0],[2,3,6,8]);assert.equal(r.explicitVertexCost,4);});
test('S49 disconnected islands not joined',()=>{const f=fixture();f.mask[9*W+9]=255;const r=exactSourceRectangleCover({width:W,height:H,sourceMask:f.mask});assert.equal(r.rectangleCount,2);assert.equal(r.observedPixels,21);});
test('S49 alternating stripes remain disjoint and budgeted',()=>{const m=new Uint8Array(16);for(let i=0;i<16;i+=2)m[i]=255;const r=exactSourceRectangleCover({width:16,height:1,sourceMask:m});assert.equal(r.rectangleCount,8);});
test('S49 repeated row intervals merge vertically',()=>{const m=new Uint8Array(36);m.fill(255);const r=exactSourceRectangleCover({width:6,height:6,sourceMask:m});assert.equal(r.rectangleCount,1);});
test('S49 malicious nonbinary mask refused',()=>{const f=fixture();f.mask[0]=8;assert.throws(()=>exactSourceRectangleCover({width:W,height:H,sourceMask:f.mask}),/NONBINARY_RECT_SOURCE/);});
test('S49 cap refuses to truncate exact rectangles',()=>{const m=new Uint8Array(16);for(let i=0;i<16;i+=2)m[i]=255;assert.throws(()=>exactSourceRectangleCover({width:16,height:1,sourceMask:m,maxRectangles:2}),/RECT_BUDGET_EXCEEDED/);});
test('S49 budget cannot be certified by mere rectangle count',()=>{const a=exactSourceRectangleCover({width:W,height:H,sourceMask:fixture().mask});const b=compareExactCoverBudget({contourVertices:4,rectCover:a,hardBudget:4});assert.equal(b.rectanglePreferred,false);assert.equal(b.adopted,false);});
test('S49 rectangle is better only when vertex cost truly lower',()=>{const a=exactSourceRectangleCover({width:W,height:H,sourceMask:fixture().mask});const b=compareExactCoverBudget({contourVertices:8,rectCover:a,hardBudget:4});assert.equal(b.savedVertices,4);assert(b.rectanglePreferred);assert(!b.adopted);});
// 50: metrics never infer skin/hair/color labels.
test('S50 144 original pixels all accounted for',async()=>{const r=await inventorySourceFidelity(fidal(fixture()));assert.equal(r.accountedPixels,N);});
test('S50 historical owner difference is counted but never adopted',async()=>{const r=await inventorySourceFidelity(fidal(fixture()));assert.equal(r.zones.visibleHistoricalArms.rgbDifferent,1);assert.equal(r.independentSemanticLabels,0);assert.equal(r.candidatePaintAuthorized,false);});
test('S50 face and background are kept separate from arms',async()=>{const r=await inventorySourceFidelity(fidal(fixture()));assert.equal(r.zones.protectedFace.pixels,1);assert.equal(r.zones.observedBackground.pixels,1);});
test('S50 source mutation rejects without SHA pin',async()=>{const f=fixture(),q=fidal(f);q.sourceRgba[0]^=1;await assert.rejects(()=>inventorySourceFidelity(q),/SOURCE_SHA_MISMATCH/);});
test('S50 baseline mutation rejects without SHA pin',async()=>{const q=fidal(fixture());q.baselineRgba[4]^=1;await assert.rejects(()=>inventorySourceFidelity(q),/BASELINE_SHA_MISMATCH/);});
test('S50 unsigned observed background cannot be promoted as truth',async()=>{const r=await inventorySourceFidelity(fidal(fixture()));assert.equal(r.backgroundIndependentTruth,false);assert.equal(r.measuresVisualQuality,false);});
test('S50 source masks ownership collision detected',async()=>{const q=fidal(fixture());q.rightArmMask[3*W+2]=255;q.rightSha256=sha(q.rightArmMask);await assert.rejects(()=>inventorySourceFidelity(q),/HISTORIC_OWNER_OVERLAP/);});
test('S50 nonbinary observed background rejects',async()=>{const q=fidal(fixture());q.observedBackground[2]=10;q.backgroundSha256=sha(q.observedBackground);await assert.rejects(()=>inventorySourceFidelity(q),/NONBINARY_OBSERVATION/);});
