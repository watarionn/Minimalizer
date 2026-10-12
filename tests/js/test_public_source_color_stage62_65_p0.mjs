import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {observeSourceColorOwners} from '../../web/static/public-source-color-observation-p0.mjs';
import {partitionObservedSourceColors} from '../../web/static/public-source-medoid-partition-p0.mjs';
import {evaluateObservedColorBoundaries,runSourceColorDiagnostic} from '../../web/static/public-source-color-boundary-gate-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=b=>createHash('sha256').update(b).digest('hex');
function fixture(){const width=12,height=12,n=width*height,originalRgba=new Uint8Array(n*4),baselineRgba=new Uint8Array(n*4),faceMask=new Uint8Array(n),backgroundMask=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){const i=y*width+x,v=x<6?[222,150,119,255]:[35,43,78,255];originalRgba.set(v,4*i);baselineRgba.set([85,88,88,255],4*i);if(y>=2&&y<10&&x>=1&&x<=5)left[i]=255;if(y>=2&&y<10&&x>=7&&x<=11)right[i]=255;}
 faceMask[2*width+2]=255;backgroundMask[3*width+3]=255;originalRgba[(4*width+4)*4+3]=0;
 for(let y=2;y<10;y++){originalRgba.set(y<6?[255,212,188,255]:[24,29,60,255],4*(y*width+5));originalRgba.set(y<6?[49,51,55,255]:[248,205,185,255],4*(y*width+7));}
 const input={width,height,originalRgba,originalSha256:sha(originalRgba),baselineRgba,baselineSha256:sha(baselineRgba),faceMask,faceSha256:sha(faceMask),backgroundMask,backgroundSha256:sha(backgroundMask),arms:{left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}}};return input;}
async function get(){return observeSourceColorOwners(fixture());}
function rgb(){return Uint8Array.from([10,20,30,12,22,32,11,21,31,210,201,190,209,200,192,211,202,190]);}
// Stage62
 test('62 source and frozen baseline pinned and enumerated',async()=>{const z=await get();assert.equal(z.zones.length,2);assert.equal(z.zones[0].pixels,37);assert.equal(z.zones[1].pixels,40);});
 test('62 face/background/transparency remain excluded',async()=>{const z=await get();assert.equal(z.excluded.face,1);assert.equal(z.excluded.background,1);assert.equal(z.excluded.alpha,1);});
 test('62 no semantic painting',async()=>{const z=await get();assert.equal(z.independentAnatomicalPixels,0);assert.equal(z.productPaintAuthorized,false);});
 test('62 original pixels mutated without SHA rejected',async()=>{const f=fixture();f.originalRgba[0]^=1;await assert.rejects(()=>observeSourceColorOwners(f),/SOURCE_PIN_MISMATCH/);});
 test('62 frozen baseline SHA mutation rejected',async()=>{const f=fixture();f.baselineRgba[5]^=1;await assert.rejects(()=>observeSourceColorOwners(f),/BASELINE_SHA_MISMATCH/);});
 test('62 historic owner collision rejected',async()=>{const f=fixture();f.arms.right_arm.mask[2*12+2]=255;f.arms.right_arm.sha256=sha(f.arms.right_arm.mask);await assert.rejects(()=>observeSourceColorOwners(f),/HISTORICAL_OWNER_COLLISION/);});
 test('62 source masks pass SHA pin for excluded source subset',async()=>{const z=await get();assert.equal(sha(z.zones[0].sourceMask),z.zones[0].sourceMaskSha256);});
// Stage63
 test('63 observed medoids originate in original RGB array',()=>{const a=rgb(),r=partitionObservedSourceColors({rgb:a,pixels:6,maxColors:3,minClusterPixels:1});for(const p of r.palette)assert([...Array(6).keys()].some(i=>a[3*i]===p[0]&&a[3*i+1]===p[1]&&a[3*i+2]===p[2]));});
 test('63 medoids reduce input L1 versus one medoid',()=>{const r=partitionObservedSourceColors({rgb:rgb(),pixels:6,maxColors:3,minClusterPixels:1});assert(r.colorL1<=r.singleColorL1);});
 test('63 reproducible deterministic partitions',()=>{const a=partitionObservedSourceColors({rgb:rgb(),pixels:6,maxColors:3,minClusterPixels:1});assert.deepEqual(a,partitionObservedSourceColors({rgb:rgb(),pixels:6,maxColors:3,minClusterPixels:1}));});
 test('63 no additional color sampling or guessed anatomy',()=>{const r=partitionObservedSourceColors({rgb:rgb(),pixels:6,maxColors:2,minClusterPixels:1});assert.equal(r.productPaintAuthorized,false);assert.equal(r.sourceAnatomyCertified,false);});
 test('63 one-color case honest baseline',()=>{const r=partitionObservedSourceColors({rgb:rgb(),pixels:6,maxColors:1});assert.equal(r.colorL1,r.singleColorL1);});
 test('63 reject wrong RGB bytes',()=>{assert.throws(()=>partitionObservedSourceColors({rgb:rgb(),pixels:9}),/INVALID_SOURCE_COLOR_PARTITION/);});
 test('63 reject invalid palette budget',()=>{assert.throws(()=>partitionObservedSourceColors({rgb:rgb(),pixels:6,maxColors:17}),/INVALID_SOURCE_COLOR_PARTITION/);});
 test('63 small inputs abstain from splitting',()=>{const r=partitionObservedSourceColors({rgb:rgb(),pixels:6,maxColors:6,minClusterPixels:6});assert.equal(r.palette.length,1);});
// Stage64
 test('64 source contrast edges are inventoried',async()=>{const a=await get();assert(a.zones.some(x=>x.sourceContrastEdges>0));});
 test('64 computed edge retention never implies approval',async()=>{const o=await get(),z=o.zones[0],p=partitionObservedSourceColors({rgb:z.rgb,pixels:z.pixels,maxColors:4,minClusterPixels:1}),r=evaluateObservedColorBoundaries({width:o.width,height:o.height,originalRgba:o.originalRgba,ownerMask:z.sourceMask,partition:p});assert.equal(r.reviewerApprovedPixels,0);assert.equal(r.productionReleaseAuthorized,false);});
 test('64 mismatched mask size rejects',async()=>{const o=await get(),z=o.zones[0],p=partitionObservedSourceColors({rgb:z.rgb,pixels:z.pixels,maxColors:4,minClusterPixels:1});assert.throws(()=>evaluateObservedColorBoundaries({width:3,height:4,originalRgba:o.originalRgba,ownerMask:z.sourceMask,partition:p}),/INVALID_EDGE_DIAGNOSTIC/);});
 test('64 nonbinary mask rejects',async()=>{const o=await get(),z=o.zones[0],p=partitionObservedSourceColors({rgb:z.rgb,pixels:z.pixels,maxColors:4,minClusterPixels:1}),m=z.sourceMask.slice();m[0]=3;assert.throws(()=>evaluateObservedColorBoundaries({width:o.width,height:o.height,originalRgba:o.originalRgba,ownerMask:m,partition:p}),/NONBINARY_OWNER/);});
 test('64 forged palette index rejects',async()=>{const o=await get(),z=o.zones[0],p=partitionObservedSourceColors({rgb:z.rgb,pixels:z.pixels,maxColors:4,minClusterPixels:1});p.assignments[0]=255;assert.throws(()=>evaluateObservedColorBoundaries({width:o.width,height:o.height,originalRgba:o.originalRgba,ownerMask:z.sourceMask,partition:p}),/PALETTE_INDEX_OUTSIDE_SOURCE/);});
// Stage65
 test('65 complete owner source coverage',async()=>{const o=await get(),r=await runSourceColorDiagnostic({observation:o,maxColors:4,minClusterPixels:1});assert.equal(r.sourcePixels,o.eligiblePixels);});
 test('65 original-only palette no release',async()=>{const o=await get(),r=await runSourceColorDiagnostic({observation:o,maxColors:4,minClusterPixels:1});assert.equal(r.releaseVerdict,'HOLD_NO_INDEPENDENT_ANATOMY');assert.equal(r.paintAuthorized,false);});
 test('65 wrong observation status rejected',async()=>{const o=await get();o.productionReleaseAuthorized=true;await assert.rejects(()=>runSourceColorDiagnostic({observation:o}),/INVALID_OBSERVATION/);});
 test('65 stage65 record does not expose raw original image bytes',async()=>{const r=await runSourceColorDiagnostic({observation:await get(),maxColors:4,minClusterPixels:1});assert(!JSON.stringify(r).includes('originalRgba'));assert(!JSON.stringify(r).includes('sourceMask'));});
 test('65 source contrast measure is nonnegative',async()=>{const r=await runSourceColorDiagnostic({observation:await get(),maxColors:4,minClusterPixels:1});for(const row of r.rows){assert(row.sourceColorL1>=0);assert(row.edge.highContrastEdges>=row.edge.retainedHighContrastEdges);}});
