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
import{auditOriginalSourceColorEdges,buildSourceColorManualReviewAgenda}from'../../web/static/public-source-edge-fidelity-p0.mjs';
import{buildSourceColorEdgeGuard,verifySourceColorEdgeGuard,guardSourceColorEdgeRelease}from'../../web/static/public-source-edge-guard-p0.mjs';
import{buildSourceColorEdgeFrontier,chooseSourceColorEdgeCandidate}from'../../web/static/public-source-edge-frontier-p0.mjs';
test('156 original full source SHA is retained in edge audit',async()=>{const{source,draft}=await fixture(),b=await buildAdaptiveSourceRgbPreview({source,draft});const a=await auditOriginalSourceColorEdges({source,draft,renderedRgba:b.renderedRgba});assert.equal(a.sourceRgbaSha256,source.sourceRgbaSha256);assert.equal(a.caseId,'GC001');});
test('156 tampered source bytes are rejected',async()=>{const{source,draft}=await fixture(),b=await buildAdaptiveSourceRgbPreview({source,draft});source.sourceRgba[0]^=1;await assert.rejects(()=>auditOriginalSourceColorEdges({source,draft,renderedRgba:b.renderedRgba}),/SOURCE_PIN_MISMATCH/);});
test('157 source alpha selection preserved exactly',async()=>{const{source,draft}=await fixture(),b=await buildAdaptiveSourceRgbPreview({source,draft}),a=await auditOriginalSourceColorEdges({source,draft,renderedRgba:b.renderedRgba});assert.equal(a.untrustedSelectedSourcePixels,b.paintedPixels);assert.equal(a.rgbChangedSourcePixels,b.originalRgbChangedPixels);});
test('157 opacity injected in unreviewed background is rejected',async()=>{const{source,draft}=await fixture(),b=await buildAdaptiveSourceRgbPreview({source,draft});b.renderedRgba[3]=255;await assert.rejects(()=>auditOriginalSourceColorEdges({source,draft,renderedRgba:b.renderedRgba}),/SOURCE_EDGE_PAINT_OUTSIDE_UNTRUSTED_MEMBERSHIP/);});
test('158 selected alpha corruption rejected',async()=>{const{source,draft}=await fixture(),b=await buildAdaptiveSourceRgbPreview({source,draft});b.renderedRgba[(2*source.width+4)*4+3]=128;await assert.rejects(()=>auditOriginalSourceColorEdges({source,draft,renderedRgba:b.renderedRgba}),/SOURCE_EDGE_SELECTED_ALPHA_CHANGED/);});
test('159 entire original RGB error audited independently',async()=>{const{source,draft}=await fixture(),b=await buildAdaptiveSourceRgbPreview({source,draft}),a=await auditOriginalSourceColorEdges({source,draft,renderedRgba:b.renderedRgba});assert.equal(a.totalRgbL1,b.totalRgbAbsoluteError);assert.equal(a.sourceRgbSse,b.sourceRgbSse);assert.equal(a.maxPixelRgbL1,b.worstPixelRgbL1);});
test('160 interior contrast links conserved as lost+retained',async()=>{const{source,draft}=await fixture(),b=await buildAdaptiveSourceRgbPreview({source,draft}),a=await auditOriginalSourceColorEdges({source,draft,renderedRgba:b.renderedRgba});assert.equal(a.strongSourceColorEdgesRetained+a.strongSourceColorEdgesLost,a.sourceHighContrastNeighborPairs);assert.equal(a.strongSourceColorEdgesRetained+a.renderedArtificialStrongColorEdges,a.renderedHighContrastNeighborPairs);});
test('161 error 95th-percentile bounded by maximum error',async()=>{const{source,draft}=await fixture(),b=await buildAdaptiveSourceRgbPreview({source,draft}),a=await auditOriginalSourceColorEdges({source,draft,renderedRgba:b.renderedRgba});assert(a.p95PixelRgbL1<=a.maxPixelRgbL1);assert(a.p95PixelRgbL1>=0);});
test('162 priority tiles never pretend independent human reviews',async()=>{const{source,draft}=await fixture(),b=await buildAdaptiveSourceRgbPreview({source,draft}),a=await auditOriginalSourceColorEdges({source,draft,renderedRgba:b.renderedRgba}),q=buildSourceColorManualReviewAgenda(a);assert.equal(q.independentReviewersVerified,0);assert(q.returnedHighestPriorityTiles.every(x=>!x.humanReviewerAssigned&&x.manuallyCertifiedPixels===0));});
test('162 original tile priority is ordered deterministically',async()=>{const{source,draft}=await fixture(),b=await buildAdaptiveSourceRgbPreview({source,draft}),a=await auditOriginalSourceColorEdges({source,draft,renderedRgba:b.renderedRgba,options:{tileSize:8}}),q=buildSourceColorManualReviewAgenda(a);assert.equal(q.totalOriginalTiles,4);assert(q.returnedHighestPriorityTiles.every((x,i,arr)=>i===0||arr[i-1].priorityScore>=x.priorityScore));});
test('163 guarded candidate reuses the original source SHA',async()=>{const{source,draft}=await fixture(),q=await buildSourceColorEdgeGuard({source,draft});assert.equal(q.sourceRgbaSha256,source.sourceRgbaSha256);assert.equal(q.allColorsObservedInOriginalSource,true);});
test('163 guarded candidate remains untrusted partial art',async()=>{const{source,draft}=await fixture(),q=await buildSourceColorEdgeGuard({source,draft});assert.equal(q.independentHumanSemanticPixels,0);assert.equal(q.trueWholebodySvgBudgetApproved,false);assert.equal(q.releaseAuthorized,false);});
test('164 source-selected membership cannot change under edge locks',async()=>{const{source,draft}=await fixture(),a=await buildAdaptiveSourceRgbPreview({source,draft}),b=await buildSourceColorEdgeGuard({source,draft});assert.equal(b.paintedSourcePixels,a.paintedPixels);});
test('165 every original high contrast interior pair is protected',async()=>{const{source,draft}=await fixture(),g=await buildSourceColorEdgeGuard({source,draft});assert.equal(g.sourceHighContrastEdgesLostAfterGuard,0);assert(g.sourceHighContrastPairs>0);});
test('166 exact endpoint RGB locks cannot increase original error',async()=>{const{source,draft}=await fixture(),g=await buildSourceColorEdgeGuard({source,draft});assert(g.guardedSourceRgbL1<=g.baselineSourceRgbL1);assert(g.guardedRgbChangedPixels<=g.baselineRgbChangedPixels);});
test('167 guarded rendered alpha remains only 0 or 255',async()=>{const{source,draft}=await fixture(),g=await buildSourceColorEdgeGuard({source,draft});assert(g.guardedRenderedRgba.every((v,i)=>i%4!==3||v===0||v===255));});
test('168 SVG selected RGB rendered deterministically',async()=>{const{source,draft}=await fixture(),a=await buildSourceColorEdgeGuard({source,draft}),b=await buildSourceColorEdgeGuard({source,draft});assert.equal(a.svg,b.svg);assert.equal(a.guardedRenderedRgbaSha256,b.guardedRenderedRgbaSha256);assert.equal(a.vertices,4*a.rectangles);});
test('169 guarded source replay accepts genuine candidate',async()=>{const{source,draft}=await fixture(),g=await buildSourceColorEdgeGuard({source,draft}),v=await verifySourceColorEdgeGuard({source,draft,candidate:g});assert.equal(v.sourceRgbEdgeEndpointsProtected,true);assert.equal(v.releaseAuthorized,false);});
test('169 forged approved image review status fails',async()=>{const{source,draft}=await fixture(),g=await buildSourceColorEdgeGuard({source,draft});g.independentHumanSemanticPixels=100;await assert.rejects(()=>verifySourceColorEdgeGuard({source,draft,candidate:g}),/SOURCE_EDGE_GUARD_REPLAY_TAMPERED/);});
test('169 altered source-raster SHA fails verification',async()=>{const{source,draft}=await fixture(),g=await buildSourceColorEdgeGuard({source,draft});g.guardedRenderedRgba[21]^=1;await assert.rejects(()=>verifySourceColorEdgeGuard({source,draft,candidate:g}),/SOURCE_EDGE_GUARD_REPLAY_TAMPERED/);});
test('169 altered SVG geometry fails verification',async()=>{const{source,draft}=await fixture(),g=await buildSourceColorEdgeGuard({source,draft});g.svg=g.svg.replace('fill=', 'stroke=');await assert.rejects(()=>verifySourceColorEdgeGuard({source,draft,candidate:g}),/SOURCE_EDGE_GUARD_REPLAY_TAMPERED/);});
test('170 changing source SHA prevents guarded output',async()=>{const{source,draft}=await fixture();source.sourceRgba[6]^=1;await assert.rejects(()=>buildSourceColorEdgeGuard({source,draft}),/SOURCE_PIN_MISMATCH/);});
test('171 invalid edge threshold is refused',async()=>{const{source,draft}=await fixture();await assert.rejects(()=>buildSourceColorEdgeGuard({source,draft,edgeOptions:{edgeThreshold:91}}),/EDGE_GUARD_THRESHOLD_UNSUPPORTED/);});
test('171 guarded SVG vertex cap strictly enforced',async()=>{const{source,draft}=await fixture();await assert.rejects(()=>buildSourceColorEdgeGuard({source,draft,edgeOptions:{maxRectangles:1}}),/EDGE_GUARD_RECTANGLE_CAP_EXCEEDED/);});
test('172 finite guarded frontier matches same source selection',async()=>{const{source,draft}=await fixture(),f=await buildSourceColorEdgeFrontier({source,draft,grid:[{tileSize:8,colorsPerTile:1,edgeThreshold:90},{tileSize:16,colorsPerTile:2,edgeThreshold:90}]});assert.equal(f.candidates.length,2);assert(f.finiteEdgeColorPareto.length>=1);assert(f.candidates.every(x=>x.selectedOriginalSourcePixels===f.candidates[0].selectedOriginalSourcePixels));});
test('172 no source high contrast edge may be lost in guarded grid',async()=>{const{source,draft}=await fixture(),f=await buildSourceColorEdgeFrontier({source,draft,grid:[{tileSize:8,colorsPerTile:1,edgeThreshold:90}]});assert.equal(f.candidates[0].guardHighContrastSourceLinksLost,0);assert.equal(f.originalSourceEdgesProtectedFromLoss,true);});
test('173 partial numeric selector cannot approve whole scene',async()=>{const{source,draft}=await fixture(),f=await buildSourceColorEdgeFrontier({source,draft,grid:[{tileSize:8,colorsPerTile:1,edgeThreshold:90}]}),r=chooseSourceColorEdgeCandidate(f,{maxVertices:10000,maxRgbL1:100000});assert(r.selected);assert.equal(r.productionAuthorized,false);assert.equal(r.authenticatedWholeBodyHumanCoverage,false);});
test('173 impossible numeric selector returns null, not fake candidate',async()=>{const{source,draft}=await fixture(),f=await buildSourceColorEdgeFrontier({source,draft,grid:[{tileSize:8,colorsPerTile:1,edgeThreshold:90}]}),r=chooseSourceColorEdgeCandidate(f,{maxVertices:1,maxRgbL1:0});assert.equal(r.selected,null);assert.equal(r.productionAuthorized,false);});
test('174 invalid duplicate finite frontier option is rejected',async()=>{const{source,draft}=await fixture();await assert.rejects(()=>buildSourceColorEdgeFrontier({source,draft,grid:[{tileSize:8,colorsPerTile:1,edgeThreshold:90},{tileSize:8,colorsPerTile:1,edgeThreshold:90}]}),/EDGE_FRONTIER_DUPLICATE_OPTION/);});
test('175 forged Golden flags cannot release even both requested cases present',()=>{const r=guardSourceColorEdgeRelease({cases:[{caseId:'GC001',approved:true},{caseId:'Raden',approved:true}]});assert.equal(r.authenticatedFullframeSemanticPixels,0);assert.equal(r.productionConverterAuthorized,false);});
test('175 invalid release case rejected',()=>assert.throws(()=>guardSourceColorEdgeRelease({cases:[{caseId:'bogus'}]}),/SOURCE_EDGE_RELEASE_CASE_INVALID/));
