import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {buildPinnedReviewTileManifest} from '../../web/static/public-review-tile-manifest-p0.mjs';
import {summarizeUntrustedReviewProgress} from '../../web/static/public-review-progress-ledger-p0.mjs';
import {compareUntrustedReviewProgress} from '../../web/static/public-review-progress-diff-p0.mjs';
import {evaluateSourceReviewBundleGate} from '../../web/static/public-review-stage40-gate-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=a=>createHash('sha256').update(a).digest('hex');
function source(caseId='GC001'){
 const width=16,height=16,n=256,sourceRgba=new Uint8Array(n*4),faceMask=new Uint8Array(n),backgroundMask=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
 for(let y=0;y<16;y++)for(let x=0;x<16;x++)sourceRgba.set([x<8?20:120,y<8?40:140,70,255],4*(y*16+x));
 for(let y=3;y<13;y++)for(let x=2;x<7;x++)left[y*16+x]=255;
 for(let y=3;y<13;y++)for(let x=10;x<15;x++)right[y*16+x]=255;
 faceMask[6*16+11]=255;backgroundMask[4*16+2]=255;sourceRgba[4*(8*16+4)+3]=0;
 return {caseId,width,height,sourceRgba,sourceRgbaSha256:sha(sourceRgba),sourcePngSha256:'a'.repeat(64),faceMask,faceSha256:sha(faceMask),backgroundMask,backgroundSha256:sha(backgroundMask),owners:{left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}},tileSize:8};
}
const manifest=(x=source())=>buildPinnedReviewTileManifest(x);
const progress=(m,marks=[])=>summarizeUntrustedReviewProgress({manifest:m,expectedManifestSha256:m.manifestSha256,marks});
const cases=()=>['GC001','Raden'].map((caseId,i)=>({caseId,eligiblePixels:i?20177:9160,queuedPixels:i?20177:9160,missingTiles:0,verifiedSemanticPixels:0,trustedIndependentReviewer:false,anatomyGoldenApproved:false}));

test('S37 each tile contributes exactly 1 of all 97 source-eligible pixels',async()=>{const m=await manifest();assert.equal(m.totals.total,97);assert.equal(m.tiles.reduce((a,t)=>a+t.eligiblePixels,0),97);assert(m.tiles.length>1);});
test('S37 SHA256 manifest reproducible',async()=>{assert.deepEqual(await manifest(),await manifest());});
test('S37 case-specific identity even where arrays coincidentally same',async()=>{const a=await manifest(source('GC001')),b=await manifest(source('Raden'));assert.notEqual(a.manifestSha256,b.manifestSha256);});
test('S37 changed original bytes rejected',async()=>{const s=source();s.sourceRgba[0]^=1;await assert.rejects(()=>manifest(s),/SOURCE_PIN_MISMATCH/);});
test('S37 changed face mask rejects',async()=>{const s=source();s.faceMask[0]=255;await assert.rejects(()=>manifest(s),/FACE_PIN_MISMATCH/);});
test('S37 historic owner collision is fatal',async()=>{const s=source();s.owners.right_arm.mask[3*16+3]=255;s.owners.right_arm.sha256=sha(s.owners.right_arm.mask);await assert.rejects(()=>manifest(s),/HISTORICAL_OWNER_COLLISION/);});
test('S37 low task cap refuses rather than truncates',async()=>{await assert.rejects(()=>manifest({...source(),tileSize:4,maxTasks:1}),/COMPLETE_REVIEW_QUEUE_BUDGET_EXCEEDED/);});
test('S37 does not export source image or semantic approval',async()=>{const m=await manifest();assert.equal(m.paintAuthorized,false);assert.equal(m.productPromotionAuthorized,false);assert(!('sourceRgba' in m));assert(!('sourceRgba' in m.tiles[0]));});
test('S37 zero-source-contrast leaves all eligible accounted for',async()=>{const m=await manifest({...source(),minContrast:765});assert.equal(m.totals.total,97);});

test('S38 untouched queue all navigation pending',async()=>{const m=await manifest(),p=await progress(m);assert.equal(p.totalTiles,m.tiles.length);assert.equal(p.counters.unvisited,m.tiles.length);assert.equal(p.independentlyReviewedSourcePixels,0);});
test('S38 visited bookmark changes only navigation and never reviewer certification',async()=>{const m=await manifest(),p=await progress(m,[{tileId:m.tiles[0].tileId,navigationState:'visited'}]);assert.equal(p.counters.visited,1);assert.equal(p.independentlyReviewedSourcePixels,0);assert.equal(p.stage18PaintAllowed,false);});
test('S38 disputed tile can be marked needs revisit',async()=>{const m=await manifest(),p=await progress(m,[{tileId:m.tiles[0].tileId,navigationState:'needs_revisit'}]);assert.equal(p.tiles[0].tileId,m.tiles[0].tileId);});
test('S38 refuse self-declared approved flag',async()=>{const m=await manifest();await assert.rejects(()=>progress(m,[{tileId:m.tiles[0].tileId,navigationState:'visited',approved:true}]),/UNTRUSTED_REVIEW_MARK/);});
test('S38 refuse fake independentReviewer flag',async()=>{const m=await manifest();await assert.rejects(()=>progress(m,[{tileId:m.tiles[0].tileId,navigationState:'visited',reviewerVerified:true}]),/UNTRUSTED_REVIEW_MARK/);});
test('S38 wrong SHA manifest pin rejects',async()=>{const m=await manifest();await assert.rejects(()=>summarizeUntrustedReviewProgress({manifest:m,expectedManifestSha256:'0'.repeat(64)}),/REVIEW_MANIFEST_PIN_MISMATCH/);});
test('S38 refuses invented tile',async()=>{const m=await manifest();await assert.rejects(()=>progress(m,[{tileId:9999,navigationState:'visited'}]),/UNTRUSTED_REVIEW_MARK/);});
test('S38 duplicate tile mark rejects',async()=>{const m=await manifest(),mark={tileId:m.tiles[0].tileId,navigationState:'visited'};await assert.rejects(()=>progress(m,[mark,mark]),/UNTRUSTED_REVIEW_MARK/);});
test('S38 modified upstream manifest but spoofed unchanged digest requires pinned rebuild',async()=>{const m=await manifest();m.tiles.pop();await assert.rejects(()=>progress(m,[{tileId:999,navigationState:'visited'}]),/REVIEW_MANIFEST_CONTENT_CHANGED/);});

test('S39 exact snapshots show zero changes',async()=>{const m=await manifest(),a=await progress(m);assert.equal(compareUntrustedReviewProgress({before:a,after:a}).changedTiles,0);});
test('S39 progress change pinpoints tile and carries no approval',async()=>{const m=await manifest(),a=await progress(m),b=await progress(m,[{tileId:m.tiles[0].tileId,navigationState:'visited'}]);const r=compareUntrustedReviewProgress({before:a,after:b});assert.equal(r.changedTiles,1);assert.equal(r.changes[0].tileId,m.tiles[0].tileId);assert.equal(r.productPromotionAuthorized,false);});
test('S39 different source cases fail',async()=>{const a=await progress(await manifest(source('GC001'))),b=await progress(await manifest(source('Raden')));assert.throws(()=>compareUntrustedReviewProgress({before:a,after:b}),/REVIEW_SNAPSHOT_IDENTITY_MISMATCH/);});
test('S39 changed snapshot priority fails',async()=>{const m=await manifest(),a=await progress(m),b=await progress(m);b.tiles[0].priorityScore+=1;assert.throws(()=>compareUntrustedReviewProgress({before:a,after:b}),/REVIEW_TILE_GEOMETRY_CHANGED/);});
test('S39 tile duplication fails',async()=>{const m=await manifest(),a=await progress(m),b=await progress(m);b.tiles[1].tileId=b.tiles[0].tileId;assert.throws(()=>compareUntrustedReviewProgress({before:a,after:b}),/REVIEW_TILE_SET_CHANGED/);});

test('S40 real two case schema rejects absent Raden',()=>{assert.throws(()=>evaluateSourceReviewBundleGate({cases:[cases()[0]]}),/REQUIRE_TWO_CASES/);});
test('S40 current 2 real cases necessarily HOLD',()=>{const r=evaluateSourceReviewBundleGate({cases:cases()});assert.equal(r.status,'DRAFT_HOLD');assert(r.blockerCount>=11);assert.equal(r.paintAuthorized,false);});
test('S40 missing tile is an explicit blocker',()=>{const c=cases();c[0].missingTiles=1;const r=evaluateSourceReviewBundleGate({cases:c});assert(r.blockers.includes('GC001_TILES_NOT_COVERED'));});
test('S40 even forged all true never promotes',()=>{const c=cases().map(x=>({...x,verifiedSemanticPixels:x.eligiblePixels,trustedIndependentReviewer:true,anatomyGoldenApproved:true}));const r=evaluateSourceReviewBundleGate({cases:c,fullCharacterGolden:true,iphoneSafariVerified:true,realPublicVerified:true,vertexBudgetPassed:true,rollbackVerified:true});assert.equal(r.blockerCount,0);assert.equal(r.productPromotionAuthorized,false);});
test('S40 impossible attested pixel number rejects',()=>{const c=cases();c[0].verifiedSemanticPixels=100000;assert.throws(()=>evaluateSourceReviewBundleGate({cases:c}),/INVALID_COUNTS/);});
