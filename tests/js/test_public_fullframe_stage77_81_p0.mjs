import {test} from 'node:test';import assert from 'node:assert/strict';
import {webcrypto,createHash} from 'node:crypto';
import {buildFullFrameReviewWorklist,encodeFullFrameDraftRle,validateUntrustedFullFrameDraft,compareUntrustedFullFrameDrafts,fullFrameGoldenGate} from '../../web/static/public-fullframe-review-p0.mjs';
import {buildSourceCompactHybridSvg,verifySourceCompactHybridSvg} from '../../web/static/public-source-compact-hybrid-p0.mjs';
globalThis.crypto||=webcrypto;const hash=b=>createHash('sha256').update(b).digest('hex');
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
function full(caseId='GC001'){
 const width=12,height=12,n=width*height,sourceRgba=new Uint8Array(n*4),faceMask=new Uint8Array(n),
 backgroundMask=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n);
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const i=y*width+x;sourceRgba.set(x<6?[22,34,55,255]:[177,151,121,255],4*i);
  if(y>=2&&y<9&&x>=1&&x<4)left[i]=255;
  if(y>=3&&y<10&&x>=8&&x<11)right[i]=255;
 }
 faceMask[5*width+5]=255;backgroundMask[0]=255;sourceRgba[4*(height*width-1)+3]=0;
 const owners={left_arm:{mask:left,sha256:hash(left)},right_arm:{mask:right,sha256:hash(right)}};
 return {caseId,width,height,sourceRgba,sourceRgbaSha256:hash(sourceRgba),sourcePngSha256:'a'.repeat(64),
  faceMask,faceSha256:hash(faceMask),backgroundMask,backgroundSha256:hash(backgroundMask),owners};
}
async function draftFixture(){
 const f=full(),w=await buildFullFrameReviewWorklist({...f,tileSize:8});
 const labels=new Uint8Array(f.width*f.height);labels[10]=2;labels[11]=7;labels[12]=8;
 const draft={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId:f.caseId,
  dimensions:[f.width,f.height],sourceRgbaSha256:f.sourceRgbaSha256,sourcePngSha256:f.sourcePngSha256,
  sourceEligibilitySha256:w.sourceEligibilitySha256,status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',
  approved:false,paintAuthorized:false,reviewerAuthenticated:false,roles,rle:encodeFullFrameDraftRle(labels)};
 return {f,draft,w,labels};
}
function colors(w=14,h=11){
 const n=w*h,sourceRgba=new Uint8Array(n*4),ownerMask=new Uint8Array(n),palette=[[25,35,50],[190,145,105]],ls=[];
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  const i=y*w+x,c=x<7?0:1;sourceRgba.set([...palette[c],255],4*i);
  if(x>=1&&x<=12&&y>=1&&y<=9){ownerMask[i]=255;ls.push(c);}
 }
 return {width:w,height:h,sourceRgba,sourceSha256:hash(sourceRgba),ownerMask,ownerSha256:hash(ownerMask),
  palette,assignments:Uint8Array.from(ls)};
}
test('S77 fullframe covers EVERY original pixel, including untrusted backdrop',async()=>{
 const f=full(),q=await buildFullFrameReviewWorklist({...f,tileSize:8});
 assert.equal(q.totalPixels,144);assert.equal(q.tiles.length,4);assert.equal(q.tiles.reduce((a,t)=>a+t.pixels,0),144);
 assert.equal(q.allOriginalPixelsQueued,true);assert.equal(q.backgroundSemanticsCertified,false);
});
test('S77 original alpha counted, never promoted to character segmentation',async()=>{
 const q=await buildFullFrameReviewWorklist({...full(),tileSize:8});assert.equal(q.nonOpaquePixels,1);assert.equal(q.bodySilhouetteCertified,false);assert.equal(q.independentlyHumanVerifiedPixels,0);
});
test('S77 historical owners included but not equated to full body',async()=>{
 const q=await buildFullFrameReviewWorklist({...full(),tileSize:8});assert.equal(q.historicalOwnerCandidatePixels,42);assert(q.opaquePixels>q.historicalOwnerCandidatePixels);
});
test('S77 full image strong source RGB edges measured without human class',async()=>{
 const q=await buildFullFrameReviewWorklist({...full(),tileSize:8});assert(q.sourceHighContrastEdges>0);assert.equal(q.paintAuthorized,false);
});
test('S77 SHA-altered original forbidden',async()=>{const f=full();f.sourceRgba[0]^=1;await assert.rejects(()=>buildFullFrameReviewWorklist({...f,tileSize:8}),/SOURCE_PIN_MISMATCH/);});
test('S77 corrupted face pin forbidden',async()=>{const f=full();f.faceMask[0]=255;await assert.rejects(()=>buildFullFrameReviewWorklist({...f,tileSize:8}),/FACE_PIN_MISMATCH/);});
test('S77 corrupted historical owner denied',async()=>{const f=full();f.owners.left_arm.mask[0]=255;await assert.rejects(()=>buildFullFrameReviewWorklist({...f,tileSize:8}),/left_arm_PIN_MISMATCH/);});
test('S77 invalid worklist tile refused',async()=>{await assert.rejects(()=>buildFullFrameReviewWorklist({...full(),tileSize:2}),/INVALID_FULLFRAME_TILE/);});
test('S78 fullframe proposal covers entire canvas but remains unverified',async()=>{
 const {f,draft}=await draftFixture(),v=await validateUntrustedFullFrameDraft({...f,draft});
 assert.equal(v.counts[2],1);assert.equal(v.proposedPixels,3);assert.equal(v.authenticReviewApproved,false);
});
test('S78 RLE encoding preserves zero and classified counts',()=>{const b=Uint8Array.from([0,0,1,1,0,7,7]);assert.deepEqual(encodeFullFrameDraftRle(b),[[0,2],[1,2],[0,1],[7,2]]);});
test('S78 invalid label code rejected',()=>assert.throws(()=>encodeFullFrameDraftRle(Uint8Array.from([0,10])),/INVALID_FULLFRAME_LABEL/));
test('S78 wrong declared case blocked',async()=>{const {f,draft}=await draftFixture();draft.caseId='Raden';await assert.rejects(()=>validateUntrustedFullFrameDraft({...f,draft}),/UNTRUSTED_FULLFRAME_DRAFT_IDENTITY/);});
test('S78 forged independent approval blocked',async()=>{const {f,draft}=await draftFixture();draft.approved=true;await assert.rejects(()=>validateUntrustedFullFrameDraft({...f,draft}),/UNTRUSTED_FULLFRAME_DRAFT_IDENTITY/);});
test('S78 forged reviewer authentication blocked',async()=>{const {f,draft}=await draftFixture();draft.reviewerAuthenticated=true;await assert.rejects(()=>validateUntrustedFullFrameDraft({...f,draft}),/UNTRUSTED_FULLFRAME_DRAFT_IDENTITY/);});
test('S78 changed original eligibility pin blocked',async()=>{const {f,draft}=await draftFixture();draft.sourceEligibilitySha256='e'.repeat(64);await assert.rejects(()=>validateUntrustedFullFrameDraft({...f,draft}),/UNTRUSTED_FULLFRAME_DRAFT_IDENTITY/);});
test('S78 labels over source nonopaque pixel blocked',async()=>{
 const {f,draft,labels}=await draftFixture();labels[143]=3;draft.rle=encodeFullFrameDraftRle(labels);
 await assert.rejects(()=>validateUntrustedFullFrameDraft({...f,draft}),/FULLFRAME_NONOPAQUE_PROPOSAL/);
});
test('S78 fake length of RLE rejected',async()=>{const {f,draft}=await draftFixture();draft.rle=[[0,1]];await assert.rejects(()=>validateUntrustedFullFrameDraft({...f,draft}),/FULLFRAME_RLE_LENGTH/);});
test('S78 original alpha not painted by unreviewed annotation',async()=>{const {f,draft}=await draftFixture(),r=await validateUntrustedFullFrameDraft({...f,draft});assert.equal(r.productPaintAuthorized,false);});
test('S79 two distinct untrusted drafts produce an uncertainty-only report',async()=>{
 const {f,draft,labels}=await draftFixture(),second={...draft};const labels2=labels.slice();labels2[11]=6;second.rle=encodeFullFrameDraftRle(labels2);
 const r=await compareUntrustedFullFrameDrafts({...f,drafts:[draft,second]});assert.equal(r.untrustedMatchingPixels,2);assert.equal(r.untrustedDisagreedPixels,1);
 assert.equal(r.semanticPixelsAuthenticated,0);assert.equal(r.releaseAuthorized,false);
});
test('S79 exact duplicate draft cannot claim 2 independent reviewers',async()=>{
 const {f,draft}=await draftFixture();await assert.rejects(()=>compareUntrustedFullFrameDrafts({...f,drafts:[draft,{...draft}]}),/FULLFRAME_DUPLICATE_DRAFTS_NOT_INDEPENDENT/);
});
test('S79 cross-case draft rejected',async()=>{
 const {f,draft,labels}=await draftFixture(),other={...draft,caseId:'Raden',rle:encodeFullFrameDraftRle(labels)};
 await assert.rejects(()=>compareUntrustedFullFrameDrafts({...f,drafts:[draft,other]}),/UNTRUSTED_FULLFRAME_DRAFT_IDENTITY/);
});
test('S79 release gate stays HOLD even when both case IDs supplied',()=>{
 const x=fullFrameGoldenGate({cases:[{caseId:'GC001',approved:true},{caseId:'Raden',approved:true}]});
 assert.equal(x.independentlyAuthenticatedSemanticPixels,0);assert.equal(x.releaseAuthorized,false);
});
test('S80 exact hybrid geometry source-only and no release claim',async()=>{
 const c=await buildSourceCompactHybridSvg(colors());assert.equal(c.sourcePixels,108);assert.equal(c.hybridSvgBytes<=c.exactRectSvgBytes,true);
 assert.equal(c.productionReleaseAuthorized,false);assert.equal(c.actualChromeDprVerified,false);
});
test('S80 deterministic geometry choice',async()=>{
 const z=colors(),a=await buildSourceCompactHybridSvg(z),b=await buildSourceCompactHybridSvg(z);assert.equal(a.hybridSvg,b.hybridSvg);assert.deepEqual(a.chosenLayers,b.chosenLayers);
});
test('S80 exact replay verifies without semantically approving',async()=>{
 const input=colors(),candidate=await buildSourceCompactHybridSvg(input),r=await verifySourceCompactHybridSvg({...input,candidate});
 assert.equal(r.sourceMembershipVerified,true);assert.equal(r.humanGoldenApproved,false);
});
test('S80 forged contour markup blocked',async()=>{
 const input=colors(),candidate=await buildSourceCompactHybridSvg(input);candidate.hybridSvg+='<image href="x"/>';
 await assert.rejects(()=>verifySourceCompactHybridSvg({...input,candidate}),/HYBRID_REPLAY_TAMPERED/);
});
test('S80 invented source color cannot make hybrid',async()=>{
 const input=colors();input.palette[1]=[3,4,5];await assert.rejects(()=>buildSourceCompactHybridSvg(input),/UNOBSERVED_SOURCE_COLOR/);
});
test('S80 source mask hash corruption fails closed',async()=>{
 const input=colors();input.ownerMask[0]=255;await assert.rejects(()=>buildSourceCompactHybridSvg(input),/COLOR_SVG_SHA_MISMATCH/);
});
test('S81 no Golden, no Safari, no rollback claim',()=>{
 const r=fullFrameGoldenGate();assert.equal(r.fullBodySilhouetteGolden,false);assert.equal(r.fullSceneSvgBudgetPassed,false);
 assert.equal(r.realIphoneSafariPassed,false);assert.equal(r.rollbackPassed,false);assert.equal(r.status,'DRAFT_HOLD');
});
