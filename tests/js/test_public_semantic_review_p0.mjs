import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {buildSemanticReviewPacket} from '../../web/static/public-semantic-review-packet-p0.mjs';
import {auditProposedSemanticReview,gateSourceOwnerPaint} from '../../web/static/public-semantic-review-admission-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
function fixture(caseId='GC001'){
 const width=24,height=24,n=width*height,source=new Uint8Array(n*4),face=new Uint8Array(n),background=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n),p1=new Uint8Array(n),p2=new Uint8Array(n);
 for(let i=0;i<n;i++)source.set([80,90,100,255],4*i);
 for(let y=3;y<20;y++)for(let x=1;x<10;x++)left[y*width+x]=255;
 for(let y=3;y<20;y++)for(let x=14;x<22;x++)right[y*width+x]=255;
 for(let y=4;y<12;y++)for(let x=2;x<7;x++)p1[y*width+x]=255;
 for(let y=13;y<17;y++)for(let x=7;x<9;x++)p2[y*width+x]=255;
 for(let y=18;y<20;y++)for(let x=7;x<9;x++)p2[y*width+x]=255;
 face[8*width+11]=255;background[5*width+9]=255;
 return {caseId,width,height,sourceRgba:source,sourceSha256:sha(source),faceMask:face,faceSha256:sha(face),backgroundMask:background,backgroundSha256:sha(background),
  owners:[{role:'left_arm',mask:left,maskSha256:sha(left),evidenceLevel:'historical_stage04_signed'},
  {role:'right_arm',mask:right,maskSha256:sha(right),evidenceLevel:'historical_stage04_signed'}],
  partitions:[{id:'left_top',parentRole:'left_arm',mask:p1,maskSha256:sha(p1),evidenceLevel:'source_color_observation'},
  {id:'left_split',parentRole:'left_arm',mask:p2,maskSha256:sha(p2),evidenceLevel:'source_color_observation'}]};
}
const run=(caseId)=>buildSemanticReviewPacket(fixture(caseId));
test('S21 detached color mass produces two components but no semantic claim',async()=>{const p=await run('GC001');const f=p.observations.find(x=>x.id==='left_split');assert.equal(f.componentCount,2);assert.equal(f.observedPixels,12);assert.equal(f.semanticLabel,'unknown');assert.equal(p.productPromotionAuthorized,false);});
test('S21 deterministic packet',async()=>assert.deepEqual(await run('GC001'),await run('GC001')));
test('S21 distinct cases independently verified',async()=>{const a=await run('GC001'),b=await run('Raden');assert.equal(a.sourceSha256,b.sourceSha256);assert.notEqual(a.caseId,b.caseId);});
test('S21 cover counts never pretend full semantic owner coverage',async()=>{const p=await run();assert(p.owners[0].unclassifiedPixels>0);assert(p.owners[1].unclassifiedPixels>0);});
test('S21 source SHA mismatches throw',async()=>{const f=fixture();f.sourceRgba[0]=22;await assert.rejects(()=>buildSemanticReviewPacket(f),/SOURCE_SHA_MISMATCH/);});
test('S21 historic owner SHA mismatches throw',async()=>{const f=fixture();f.owners[0].mask[1]=255;await assert.rejects(()=>buildSemanticReviewPacket(f),/OWNER_SHA_MISMATCH/);});
test('S21 observed color SHA mismatches throw',async()=>{const f=fixture();f.partitions[0].mask[0]=255;await assert.rejects(()=>buildSemanticReviewPacket(f),/OBSERVATION_SHA_MISMATCH/);});
test('S21 background evidence SHA mismatches throw',async()=>{const f=fixture();f.backgroundMask[0]=255;await assert.rejects(()=>buildSemanticReviewPacket(f),/BACKGROUND_SHA_MISMATCH/);});
test('S21 nonbinary source observation is rejected',async()=>{const f=fixture();f.partitions[0].mask[0]=128;f.partitions[0].maskSha256=sha(f.partitions[0].mask);await assert.rejects(()=>buildSemanticReviewPacket(f),/OBSERVATION_NONBINARY/);});
test('S21 evidence outside signed owner rejects',async()=>{const f=fixture();f.partitions[0].mask[1]=255;f.partitions[0].maskSha256=sha(f.partitions[0].mask);await assert.rejects(()=>buildSemanticReviewPacket(f),/UNAUTHORIZED_OR_DUPLICATE_OBSERVATION/);});
test('S21 duplicate observation pixels reject',async()=>{const f=fixture();f.partitions.push({...f.partitions[0],id:'duplicate'});await assert.rejects(()=>buildSemanticReviewPacket(f),/UNAUTHORIZED_OR_DUPLICATE_OBSERVATION/);});
test('S21 background owner exclusion blocks proposal',async()=>{const f=fixture();f.backgroundMask[5*24+3]=255;f.backgroundSha256=sha(f.backgroundMask);await assert.rejects(()=>buildSemanticReviewPacket(f),/UNAUTHORIZED_OR_DUPLICATE_OBSERVATION/);});
test('S21 signed owner overlap rejects',async()=>{const f=fixture();f.owners[1].mask[6*24+3]=255;f.owners[1].maskSha256=sha(f.owners[1].mask);await assert.rejects(()=>buildSemanticReviewPacket(f),/SIGNED_OWNER_OVERLAP/);});
test('S21 research mask cannot claim historic signoff',async()=>{const f=fixture();f.owners[0].evidenceLevel='research_observation';await assert.rejects(()=>buildSemanticReviewPacket(f),/MISSING_OWNER_PROVENANCE/);});
test('S21 source color observation cannot claim signoff',async()=>{const f=fixture();f.partitions[0].evidenceLevel='independent_signed';await assert.rejects(()=>buildSemanticReviewPacket(f),/INVALID_OBSERVATION_PROVENANCE/);});
test('S22 proposed class is untrusted, even if human-like label',async()=>{const p=await run();const e=p.observations[0];const r=auditProposedSemanticReview({packet:p,annotations:[{observationId:e.id,proposedClass:'sleeve',observationSha256:e.sourceObservationSha256,approved:true}]});assert.equal(r.productPromotionAuthorized,false);assert.equal(r.originalSourceSemanticBoundaryAttested,false);assert.equal(r.reviewedCount,1);});
test('S22 rejects unknown observation ID',async()=>{const p=await run();assert.throws(()=>auditProposedSemanticReview({packet:p,annotations:[{observationId:'fake',proposedClass:'hair'}]}),/INVALID_REVIEW_ANNOTATION/);});
test('S22 rejects source SHA switch',async()=>{const p=await run(),e=p.observations[0];assert.throws(()=>auditProposedSemanticReview({packet:p,annotations:[{observationId:e.id,proposedClass:'hair',observationSha256:'0'.repeat(64)}]}),/REVIEW_SOURCE_SHA_CONFLICT/);});
test('S22 rejects duplicate annotations',async()=>{const p=await run(),e=p.observations[0],a={observationId:e.id,proposedClass:'hair',observationSha256:e.sourceObservationSha256};assert.throws(()=>auditProposedSemanticReview({packet:p,annotations:[a,a]}),/INVALID_REVIEW_ANNOTATION/);});
test('S22 unknown semantic review remains pending',async()=>{const p=await run();const r=auditProposedSemanticReview({packet:p});assert.equal(r.pendingCount,p.observations.length);});
test('S23 real two-case preflight prevents Stage18 recolor',async()=>{const r=gateSourceOwnerPaint({packets:[await run('GC001'),await run('Raden')]});assert.equal(r.stage18PaintAllowed,false);assert.equal(r.status,'DRAFT_HOLD');assert(r.blockers.some(x=>x.includes('SEMANTICS')));});
test('S23 attacker may forge receipt flags but still cannot promote',async()=>{const a=await run('GC001'),b=await run('Raden');const r=gateSourceOwnerPaint({packets:[a,b],reviewReceipts:[{caseId:'GC001',originalSourceSemanticBoundaryAttested:true,signature:'forged',productPromotionAuthorized:true}]});assert.equal(r.productPromotionAuthorized,false);assert(r.blockers.some(x=>x.includes('SELF_DECLARED')));});
test('S23 partial single-case review refuses',async()=>{const p=await run();assert.throws(()=>gateSourceOwnerPaint({packets:[p]}),/REQUIRE_TWO_CASES/);});
test('S23 duplicate case refuses',async()=>{const p=await run();assert.throws(()=>gateSourceOwnerPaint({packets:[p,p]}),/REQUIRE_TWO_CASES/);});
test('S23 source only JSON bytes never contain raw pixel mask',async()=>{const p=await run();const dump=JSON.stringify(p);assert(!dump.includes('sourceRgba'));assert(!dump.includes('faceMask'));assert(!dump.includes('backgroundMask'));});
