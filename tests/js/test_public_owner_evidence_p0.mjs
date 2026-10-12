import {test} from 'node:test';import assert from 'node:assert/strict';
import {createHash,webcrypto} from 'node:crypto';
import {prepareVisibleSourceOwners} from '../../web/static/public-owner-evidence-guard-p0.mjs';
import {replaySourceOwnedColorMasses} from '../../web/static/public-owner-color-mass-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=x=>createHash('sha256').update(x).digest('hex');
function fixture(){
 const width=12,height=12,n=144,source=new Uint8Array(4*n),baseline=new Uint8Array(4*n),face=new Uint8Array(n),background=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n),color=new Uint8Array(n);
 for(let i=0;i<n;i++){source.set([20,30,70,255],4*i);baseline.set([220,200,180,255],4*i);}
 for(let y=2;y<10;y++)for(let x=1;x<5;x++){let i=y*width+x;left[i]=255;source.set([25,45,72,255],4*i);color[i]=255;}
 for(let y=2;y<10;y++)for(let x=6;x<10;x++){let i=y*width+x;right[i]=255;source.set([100,110,125,255],4*i);}
 background[3*width+2]=255;color[3*width+2]=0;
 face[4*width+4]=255;color[4*width+4]=0;
 source[5*width*4+3*4+3]=0;color[5*width+3]=0;
 const owners=[{role:'left_arm',mask:left,maskSha256:sha(left),evidenceLevel:'historical_stage04_signed',evidenceRef:'fixture-historical-stage04'},
  {role:'right_arm',mask:right,maskSha256:sha(right),evidenceLevel:'historical_stage04_signed',evidenceRef:'fixture-historical-stage04'}];
 return {width,height,n,source,baseline,face,background,left,right,color,owners};
}
const guardInput=x=>({width:x.width,height:x.height,sourceRgba:x.source,sourceSha256:sha(x.source),faceMask:x.face,faceSha256:sha(x.face),backgroundMask:x.background,backgroundSha256:sha(x.background),owners:x.owners});
const massesInput=(x,o,p)=>({width:x.width,height:x.height,originalRgba:x.source,originalSha256:sha(x.source),frozenRgba:x.baseline,frozenSha256:sha(x.baseline),visibleOwners:o.owners,partitions:p,minPartitionPixels:20,maxChangedPixels:x.n});
test('S17 historical owners clipped to signed source, face, alpha, observed background',async()=>{const x=fixture(),r=await prepareVisibleSourceOwners(guardInput(x));assert.equal(r.owners.length,2);assert.equal(r.owners[0].visiblePixels,29);assert.equal(r.owners[0].excludedFace,1);assert.equal(r.owners[0].excludedBackground,1);assert.equal(r.owners[0].excludedAlpha,1);assert.equal(r.totalVisiblePixels,61);assert.equal(r.productPromotionAuthorized,false);});
test('S17 deterministic bitwise source authority',async()=>{const x=fixture();assert.deepEqual(await prepareVisibleSourceOwners(guardInput(x)),await prepareVisibleSourceOwners(guardInput(x)));});
test('S17 reject unsigned owner evidence',async()=>{const x=fixture();x.owners[0].evidenceLevel='research_observation';await assert.rejects(()=>prepareVisibleSourceOwners(guardInput(x)),/OWNER_PROVENANCE/);});
test('S17 reject forged signed arm mask SHA',async()=>{const x=fixture();x.owners[0].mask[0]=255;await assert.rejects(()=>prepareVisibleSourceOwners(guardInput(x)),/left_arm_SHA_MISMATCH/);});
test('S17 reject forged source SHA',async()=>{const x=fixture(),z=guardInput(x);z.sourceRgba[0]=1;await assert.rejects(()=>prepareVisibleSourceOwners(z),/SOURCE_SHA_MISMATCH/);});
test('S17 reject nonbinary owner',async()=>{const x=fixture();x.left[0]=128;await assert.rejects(()=>prepareVisibleSourceOwners(guardInput(x)),/NONBINARY/);});
test('S17 reject duplicate arm role',async()=>{const x=fixture();x.owners.push({...x.owners[0]});await assert.rejects(()=>prepareVisibleSourceOwners(guardInput(x)),/OWNER_PROVENANCE/);});
test('S17 reject owner overlap',async()=>{const x=fixture();x.right[2*12+2]=255;x.owners[1].maskSha256=sha(x.right);await assert.rejects(()=>prepareVisibleSourceOwners(guardInput(x)),/UNRESOLVED_VISIBLE_OWNER_OVERLAP/);});
test('S17 reject without visible source',async()=>{const x=fixture();x.background.set(x.left);const z=guardInput(x);await assert.rejects(()=>prepareVisibleSourceOwners(z),/OWNER_WITHOUT_VISIBLE_SOURCE/);});
test('S18 medoid is literal original RGB, excludes every protected pixel',async()=>{const x=fixture(),g=await prepareVisibleSourceOwners(guardInput(x));const partition={id:'color_mass',parentRole:'left_arm',mask:g.owners[0].visibleMask.slice(),evidenceLevel:'source_color_observation',evidenceRef:'fixture-source-class'};partition.maskSha256=sha(partition.mask);
 const r=await replaySourceOwnedColorMasses(massesInput(x,g,[partition]));assert.equal(r.audit.changedPixels,29);assert.deepEqual(r.audit.partitions[0].sourcePixelMedoid,[25,45,72]);assert.equal(r.audit.sourceAbsentChangedPixels,0);assert.equal(r.audit.productPromotionAuthorized,false);for(let i=0;i<x.n;i++)if(!partition.mask[i])assert.deepEqual([...r.rgba.slice(i*4,i*4+4)],[...x.baseline.slice(i*4,i*4+4)]);});
test('S18 rejects forged partition mask sha',async()=>{const x=fixture(),g=await prepareVisibleSourceOwners(guardInput(x));const m=g.owners[0].visibleMask.slice();const p={id:'part',parentRole:'left_arm',mask:m,maskSha256:sha(m),evidenceLevel:'source_color_observation',evidenceRef:'fixture'};m[0]=255;await assert.rejects(()=>replaySourceOwnedColorMasses(massesInput(x,g,[p])),/PARTITION_SHA_MISMATCH/);});
test('S18 refuses drawing inside background exclusion',async()=>{const x=fixture(),g=await prepareVisibleSourceOwners(guardInput(x));const m=x.left.slice();const p={id:'part',parentRole:'left_arm',mask:m,maskSha256:sha(m),evidenceLevel:'source_color_observation',evidenceRef:'fixture'};await assert.rejects(()=>replaySourceOwnedColorMasses(massesInput(x,g,[p])),/PARTITION_OUTSIDE_SIGNED_OWNER_OR_OVERLAP/);});
test('S18 rejects unsigned color class observation',async()=>{const x=fixture(),g=await prepareVisibleSourceOwners(guardInput(x));const m=g.owners[0].visibleMask;const p={id:'part',parentRole:'left_arm',mask:m,maskSha256:sha(m),evidenceLevel:'signed',evidenceRef:'fixture'};await assert.rejects(()=>replaySourceOwnedColorMasses(massesInput(x,g,[p])),/INVALID_PARTITION_AUTHORITY/);});
test('S18 rejects overlap of two observed masses',async()=>{const x=fixture(),g=await prepareVisibleSourceOwners(guardInput(x));const m=g.owners[0].visibleMask;const p={id:'p1',parentRole:'left_arm',mask:m,maskSha256:sha(m),evidenceLevel:'source_color_observation',evidenceRef:'fixture'};await assert.rejects(()=>replaySourceOwnedColorMasses(massesInput(x,g,[p,{...p,id:'p2'}])),/PARTITION_OUTSIDE_SIGNED_OWNER_OR_OVERLAP/);});
test('S18 refuses total change budget',async()=>{const x=fixture(),g=await prepareVisibleSourceOwners(guardInput(x));const m=g.owners[0].visibleMask;const p={id:'p1',parentRole:'left_arm',mask:m,maskSha256:sha(m),evidenceLevel:'source_color_observation',evidenceRef:'fixture'};await assert.rejects(()=>replaySourceOwnedColorMasses({...massesInput(x,g,[p]),maxChangedPixels:2}),/CHANGED_PIXEL_BUDGET/);});
test('S18 abstains rather than painting if baseline source medoid already accurate',async()=>{const x=fixture(),g=await prepareVisibleSourceOwners(guardInput(x));const m=g.owners[0].visibleMask;const p={id:'p1',parentRole:'left_arm',mask:m,maskSha256:sha(m),evidenceLevel:'source_color_observation',evidenceRef:'fixture'};for(let i=0;i<x.n;i++)if(m[i])x.baseline.set([25,45,72,255],4*i);const r=await replaySourceOwnedColorMasses(massesInput(x,g,[p]));assert.equal(r.audit.changedPixels,0);assert.equal(r.audit.partitions[0].acceptedAsPreview,false);});
import {evaluateOwnerVisualGate} from '../../web/static/public-owner-review-gate-p0.mjs';
const caseRows=()=>['GC001','Raden'].map((label,i)=>({case:label,signedOwnerPixels:i?20177:9160,candidateChangedPixels:i?16197:6891,
 backgroundProtectedChangedPixels:0,faceProtectedChangedPixels:0,alphaChangedPixels:0,outsideSignedOwnerPixels:0,
 colorErrorGainPercent:i?6.41:3.93,backgroundObserverIndependentlySigned:false,
 sleeveForearmHairSeparatedAndReviewed:false,fullArmSilhouetteRecovered:false,visualReviewRejected:true}));
test('S19 color gain never authorizes semantic anatomy or production',()=>{const gate=evaluateOwnerVisualGate({cases:caseRows()});assert.equal(gate.status,'DRAFT_HOLD');assert.equal(gate.productPromotionAuthorized,false);assert(gate.blockerCount>=11);assert(gate.blockers.some(x=>x.includes('ARM_SLEEVE_HAIR')));});
test('S19 refuses duplicate case',()=>{const rows=caseRows();rows[1].case='GC001';assert.throws(()=>evaluateOwnerVisualGate({cases:rows}),/REQUIRE_TWO_DISTINCT_CASES/);});
test('S19 flags backdrop mutation',()=>{const rows=caseRows();rows[0].backgroundProtectedChangedPixels=1;const r=evaluateOwnerVisualGate({cases:rows});assert(r.blockers.includes('GC001_BACKGROUND_MUTATION'));});
test('S19 refuses missing audit values',()=>{const rows=caseRows();delete rows[0].outsideSignedOwnerPixels;assert.throws(()=>evaluateOwnerVisualGate({cases:rows}),/INVALID_AUDIT/);});
test('S19 even if all flags true, this RESEARCH gate cannot promote',()=>{const rows=caseRows().map(x=>({...x,backgroundObserverIndependentlySigned:true,sleeveForearmHairSeparatedAndReviewed:true,fullArmSilhouetteRecovered:true,visualReviewRejected:false}));const r=evaluateOwnerVisualGate({cases:rows,independentSemanticReviews:true,fullCharacterGolden:true,iphoneSafariPassed:true,realPublicRoutePassed:true,fullSvgBudgetPassed:true});assert.equal(r.blockerCount,0);assert.equal(r.productPromotionAuthorized,false);});
