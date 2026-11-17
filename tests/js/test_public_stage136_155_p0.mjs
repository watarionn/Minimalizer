import {test}from'node:test';import assert from'node:assert/strict';
import{createHash,webcrypto}from'node:crypto';
import{encodeFullFrameDraftRle}from'../../web/static/public-fullframe-review-p0.mjs';
import{buildHumanReviewQueue}from'../../web/static/public-human-review-queue-p0.mjs';
import{buildAdaptiveSourceRgbPreview,verifyAdaptiveSourceRgbPreview,guardAdaptiveReleaseGate}from'../../web/static/public-adaptive-source-rgb-p0.mjs';
import{buildFiniteAdaptiveSourceRgbFrontier,chooseBoundedPartialCandidate}from'../../web/static/public-adaptive-source-rgb-frontier-p0.mjs';
globalThis.crypto||=webcrypto;
const sha=x=>createHash('sha256').update(x).digest('hex');
const roles=['unreviewed','background_proposal','hair_proposal','face_proposal','skin_proposal','sleeve_proposal','garment_proposal','neckwear_proposal','accessory_proposal','uncertain_subject'];
async function fixture({width=16,height=16,caseId='GC001'}={}){
 const n=width*height,rgba=new Uint8Array(n*4),face=new Uint8Array(n),bg=new Uint8Array(n),left=new Uint8Array(n),right=new Uint8Array(n),labels=new Uint8Array(n);
 for(let i=0;i<n;i++){
  const x=i%width,y=Math.floor(i/width);
  rgba.set([Math.round((x%8)*27),Math.round((y%8)*21),Math.round((x+y)%7*32),255],4*i);
  if(x>=2&&x<width-2&&y>=2&&y<height-2)labels[i]=9;
 }
 labels[0]=1;labels[1]=3;labels[2*width+2]=5;labels[2*width+3]=5;
 rgba[4*(n-1)+3]=0;
 face[1]=255;bg[0]=255;left[2*width+4]=255;right[2*width+5]=255;
 const source={caseId,width,height,sourceRgba:rgba,sourceRgbaSha256:sha(rgba),
 sourcePngSha256:'b'.repeat(64),faceMask:face,faceSha256:sha(face),
 backgroundMask:bg,backgroundSha256:sha(bg),
 owners:{left_arm:{mask:left,sha256:sha(left)},right_arm:{mask:right,sha256:sha(right)}}};
 const packet=await buildHumanReviewQueue(source);
 const draft={format:'MinimalizerPublic-P0-fullframe-review-draft-v1',caseId,
 dimensions:[width,height],sourcePngSha256:source.sourcePngSha256,
 sourceRgbaSha256:source.sourceRgbaSha256,sourceEligibilitySha256:packet.eligibilitySha256,
 status:'UNVERIFIED_FULLFRAME_HUMAN_PROPOSAL',approved:false,paintAuthorized:false,
 reviewerAuthenticated:false,roles,rle:encodeFullFrameDraftRle(labels)};
 return{source,packet,draft,labels};
}
test('136 source pin: adaptive output keeps the same source case',async()=>{const{source,draft}=await fixture(),z=await buildAdaptiveSourceRgbPreview({source,draft});assert.equal(z.caseId,'GC001');assert.equal(z.sourceRgbaSha256,source.sourceRgbaSha256);});
test('136 changed original RGBA source must be rejected',async()=>{const{source,draft}=await fixture();source.sourceRgba[2]^=1;await assert.rejects(()=>buildAdaptiveSourceRgbPreview({source,draft}),/SOURCE_PIN_MISMATCH/);});
test('137 original transparent pixels are never painted',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});assert.equal(x.renderedRgba[4*(source.width*source.height-1)+3],0);});
test('137 original source RGBA remains unchanged',async()=>{const{source,draft}=await fixture(),b=source.sourceRgba.slice();await buildAdaptiveSourceRgbPreview({source,draft});assert.deepEqual(source.sourceRgba,b);});
test('138 palettes consist of actual RGB observed inside each source tile',async()=>{const{source,draft,labels}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});for(const p of x.sourceObservedPaletteGroups)for(const hex of p.sourceObservedColors){let seen=false;for(let y=p.y0;y<p.y0+p.height;y++)for(let a=p.x0;a<p.x0+p.width;a++){const i=y*source.width+a;if(labels[i]!==p.role)continue;const sourceHex='#'+[...source.sourceRgba.subarray(4*i,4*i+3)].map(v=>v.toString(16).padStart(2,'0')).join('');if(hex===sourceHex)seen=true;}assert.equal(seen,true);}});
test('139 palette size never exceeds configured colors per tile',async()=>{const{source,draft}=await fixture(),z=await buildAdaptiveSourceRgbPreview({source,draft,options:{colorsPerTile:2}});assert(z.sourceObservedPaletteGroups.every(x=>x.sourceObservedColors.length<=2));});
test('140 one-color tiles must record original RGB error honestly',async()=>{const{source,draft}=await fixture(),z=await buildAdaptiveSourceRgbPreview({source,draft,options:{colorsPerTile:1}});assert(z.originalRgbChangedPixels>0);assert(z.totalRgbAbsoluteError>0);assert(z.worstPixelRgbL1>0);});
test('141 max RGB L1=0 rejects source-incorrect palette',async()=>{const{source,draft}=await fixture();await assert.rejects(()=>buildAdaptiveSourceRgbPreview({source,draft,options:{maxPixelL1:0,colorsPerTile:1}}),/ADAPTIVE_SOURCE_RGB_ERROR_BOUND_EXCEEDED/);});
test('141 admissible 765 RGB difference bound cannot exceed itself',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft,options:{maxPixelL1:765}});assert(x.worstPixelRgbL1<=765);});
test('142 rectangle geometry tracks counted explicit vertices',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});assert.equal(x.explicitVertices,4*x.rectangleCount);});
test('142 exact selected alpha membership conservation',async()=>{const{source,draft,labels}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});assert.equal(x.paintedPixels,labels.filter(v=>[2,4,5,6,7,8,9].includes(v)).length);assert.equal(x.excludedOriginalPixels,source.width*source.height-x.paintedPixels);});
test('143 source-observed color is grouped but distinct roles remain distinct',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});assert(x.outputLayers.some(z=>z.role===5));assert(x.outputLayers.some(z=>z.role===9));});
test('143 source original background and face proposal classes are not painted',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});assert.equal(x.renderedRgba[3],0);assert.equal(x.renderedRgba[7],0);});
test('144 output rgba alpha exclusively 0/255',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});assert(x.renderedRgba.every((v,i)=>i%4!==3||v===0||v===255));});
test('145 unauthorized paint always false',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});assert.equal(x.paintAuthorized,false);assert.equal(x.releaseAuthorized,false);assert.equal(x.realHumanReviewedSemanticPixels,0);});
test('146 8px tile and 16px tile both source bound',async()=>{const{source,draft}=await fixture(),a=await buildAdaptiveSourceRgbPreview({source,draft,options:{tileSize:8}}),b=await buildAdaptiveSourceRgbPreview({source,draft,options:{tileSize:16}});assert.equal(a.labelsSha256,b.labelsSha256);assert.equal(a.paintedSourceMaskSha256,b.paintedSourceMaskSha256);});
test('147 parametric frontier has all expected rows',async()=>{const{source,draft}=await fixture(),f=await buildFiniteAdaptiveSourceRgbFrontier({source,draft,grid:[{tileSize:8,colorsPerTile:1},{tileSize:8,colorsPerTile:4},{tileSize:16,colorsPerTile:1}]});assert.equal(f.candidates.length,3);assert(f.finitePareto.length>0);assert.equal(f.globalParetoOrOptimalityEstablished,false);});
test('148 dual budget selector cannot grant production permission',async()=>{const{source,draft}=await fixture(),f=await buildFiniteAdaptiveSourceRgbFrontier({source,draft,grid:[{tileSize:8,colorsPerTile:1},{tileSize:8,colorsPerTile:4}]});const r=chooseBoundedPartialCandidate(f,{maxMeanL1:765,maxVertices:100000});assert.equal(r.anyFiniteCandidateUnderRequestedNumericBudgets,true);assert.equal(r.releaseAuthorized,false);assert.equal(r.fullCharacterShapeGolden,false);});
test('148 numerical impossible bound yields no fabricated candidate',async()=>{const{source,draft}=await fixture(),f=await buildFiniteAdaptiveSourceRgbFrontier({source,draft,grid:[{tileSize:8,colorsPerTile:1}]});const r=chooseBoundedPartialCandidate(f,{maxVertices:1,maxMeanL1:0});assert.equal(r.selected,null);assert.equal(r.releaseAuthorized,false);});
test('149 test finite Pareto is only evaluated among supplied candidates',async()=>{const{source,draft}=await fixture(),f=await buildFiniteAdaptiveSourceRgbFrontier({source,draft,grid:[{tileSize:8,colorsPerTile:1},{tileSize:8,colorsPerTile:2}]});assert(f.finitePareto.length>=1);assert(f.finitePareto.length<=2);assert.equal(f.wholeCharacterSceneStudied,false);});
test('149 identical grid entry rejected',async()=>{const{source,draft}=await fixture();await assert.rejects(()=>buildFiniteAdaptiveSourceRgbFrontier({source,draft,grid:[{tileSize:8,colorsPerTile:2},{tileSize:8,colorsPerTile:2}]}),/FINITE_FRONTIER_DUPLICATE_OPTIONS/);});
test('150 original human Golden remains HOLD even when all flags claimed',()=>{const x=guardAdaptiveReleaseGate({cases:[{caseId:'GC001',approved:true},{caseId:'Raden',approved:true}]});assert.equal(x.approvedBodySemanticPixels,0);assert.equal(x.productionReleaseAuthorized,false);assert.equal(x.realIphoneSafariHttpsVerified,false);});
test('150 unsupported case release payload rejected',()=>assert.throws(()=>guardAdaptiveReleaseGate({cases:[{caseId:'fake'}]}),/ADAPTIVE_INVALID_RELEASE_CASES/));
test('151 reproducible adaptive SVG, hashes and numeric metrics',async()=>{const{source,draft}=await fixture(),a=await buildAdaptiveSourceRgbPreview({source,draft}),b=await buildAdaptiveSourceRgbPreview({source,draft});assert.equal(a.svg,b.svg);assert.equal(a.renderedRgbaSha256,b.renderedRgbaSha256);assert.equal(a.totalRgbAbsoluteError,b.totalRgbAbsoluteError);});
test('152 source replay validation accepts exact unchanged candidate',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});const v=await verifyAdaptiveSourceRgbPreview({source,draft,candidate:x});assert.equal(v.replaySourceAndSvgMatches,true);assert.equal(v.releaseAuthorized,false);});
test('153 SVG payload adulteration rejected',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});x.svg=x.svg.replace('fill=','stroke=');await assert.rejects(()=>verifyAdaptiveSourceRgbPreview({source,draft,candidate:x}),/ADAPTIVE_SOURCE_OR_OUTPUT_TAMPERED/);});
test('153 rendered private RGBA byte adulteration rejected',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});x.renderedRgba[0]^=1;await assert.rejects(()=>verifyAdaptiveSourceRgbPreview({source,draft,candidate:x}),/ADAPTIVE_SOURCE_OR_OUTPUT_TAMPERED/);});
test('154 renderer cannot label itself human approved',async()=>{const{source,draft}=await fixture(),x=await buildAdaptiveSourceRgbPreview({source,draft});x.realHumanReviewedSemanticPixels=42;await assert.rejects(()=>verifyAdaptiveSourceRgbPreview({source,draft,candidate:x}),/ADAPTIVE_SOURCE_OR_OUTPUT_TAMPERED/);});
test('155 unsupported sampling geometry fails closed',async()=>{const{source,draft}=await fixture();await assert.rejects(()=>buildAdaptiveSourceRgbPreview({source,draft,options:{tileSize:9}}),/ADAPTIVE_TILE_SIZE_UNSUPPORTED/);});
test('155 negative error budget rejected',async()=>{const{source,draft}=await fixture();await assert.rejects(()=>buildAdaptiveSourceRgbPreview({source,draft,options:{maxPixelL1:-1}}),/ADAPTIVE_PIXEL_ERROR_BOUND_INVALID/);});
test('155 rectangle cap below needed geometry rejects output',async()=>{const{source,draft}=await fixture();await assert.rejects(()=>buildAdaptiveSourceRgbPreview({source,draft,options:{maxRectangles:1}}),/ADAPTIVE_RECT_COUNT_CAP_EXCEEDED/);});
