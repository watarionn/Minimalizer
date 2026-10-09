/* BrowserFallback v26: READ-ONLY source-backed lost-boundary observer.
 * No part segmentation authority, no visible-output changes, no Local Worker.
 * Foreground U2NetP evidence is a weak filter only, never clothing/arm truth.
 */
(function(root) {
  "use strict";
  const VERSION="browser-structural-evidence-v26";
  const DEFAULTS=Object.freeze({
    minSourceRgbDistance:68, maxFacetRgbDistance:12,
    minimumSegmentPixels:8, maxSegments:150,
    foregroundProbability:0.75, minForegroundConfidence:0.20,
    maxPixels:1000000,
  });
  function rgbDistanceSquared(pixels,one,two) {
    const a=4*one,b=4*two;
    let sum=0;
    for(let c=0;c<3;c++){const x=pixels[a+c]-pixels[b+c];sum+=x*x;}
    return sum;
  }
  function observe(sourceRgba,facetRgba,width,height,subjectEvidence,options) {
    const cfg={...DEFAULTS,...(options||{})};
    const size=width*height;
    if(!Number.isInteger(width)||!Number.isInteger(height)
      ||width<2||height<2||size>cfg.maxPixels
      ||!sourceRgba||!facetRgba
      ||sourceRgba.length!==size*4||facetRgba.length!==size*4
      ||!Number.isFinite(cfg.minSourceRgbDistance)||cfg.minSourceRgbDistance<=0
      ||!Number.isFinite(cfg.maxFacetRgbDistance)||cfg.maxFacetRgbDistance<0
      ||cfg.maxFacetRgbDistance>=cfg.minSourceRgbDistance
      ||!Number.isInteger(cfg.minimumSegmentPixels)||cfg.minimumSegmentPixels<2
      ||!Number.isInteger(cfg.maxSegments)||cfg.maxSegments<1
      ||cfg.maxSegments>500
      ||cfg.foregroundProbability<=0||cfg.foregroundProbability>1
      ||cfg.minForegroundConfidence<0||cfg.minForegroundConfidence>1)
      throw Error("V26 invalid observer input or policy");
    const provenance={
      input:"source-rgba+unchanged-facet-rgba",
      subjectProvider:subjectEvidence?.provider||"none",
      subjectModel:subjectEvidence?.model||"none",
      subjectAuthority:false,
      partProvider:"unavailable",
      partAuthority:false,
      generatedPixels:false,
      visibleOutputAuthority:false,
      coordinateSpace:"source-pixel-top-left",
    };
    const probability=subjectEvidence?.probability;
    const confidence=subjectEvidence?.confidence;
    const withheld=!probability||!confidence;
    if(!withheld&&(probability.length!==size||confidence.length!==size))
      throw Error("V26 subject evidence dimensions do not match the source");
    const empty=(status)=>({version:VERSION,status,width,height,provenance,
      summary:{eligibleSubjectPixels:0,rawLostBoundaryPixels:0,
        componentCount:0,retainedSegmentCount:0,retainedPixels:0,
        unboundSegments:0,knownArmSegments:0,knownGarmentSegments:0},
      segments:[],overlayPixels:[]});
    if(withheld)return empty("withheld_subject_evidence_unavailable");
    if(provenance.subjectProvider!=="browser-u2netp"||provenance.subjectModel!=="u2netp")
      return empty("withheld_unverified_subject_provider");
    const eligible=new Uint8Array(size),edges=new Uint8Array(size);
    const sourceThreshold=cfg.minSourceRgbDistance**2;
    const facetThreshold=cfg.maxFacetRgbDistance**2;
    let eligibleCount=0;
    for(let i=0;i<size;i++) {
      if(sourceRgba[4*i+3]<255)continue; // use original observations only
      if(probability[i]>=cfg.foregroundProbability
        &&confidence[i]>=cfg.minForegroundConfidence) {
        eligible[i]=1;eligibleCount++;
      }
    }
    // Only original-image contrast LOST inside an unchanged Facet color plane.
    // Pure RGB source boundaries are not semantic labels or hallucinated limbs.
    let rawLost=0;
    for(let y=1;y<height-1;y++)for(let x=1;x<width-1;x++) {
      const i=y*width+x;
      if(!eligible[i])continue;
      for(const j of [i+1,i+width]) {
        if(!eligible[j])continue;
        if(rgbDistanceSquared(sourceRgba,i,j)<sourceThreshold)continue;
        if(rgbDistanceSquared(facetRgba,i,j)>facetThreshold)continue;
        if(!edges[i]){edges[i]=1;rawLost++;}
        if(!edges[j]){edges[j]=1;rawLost++;}
      }
    }
    const visited=new Uint8Array(size);
    const segments=[];
    let componentCount=0;
    for(let start=0;start<size;start++) {
      if(!edges[start]||visited[start])continue;
      componentCount++;
      const points=[],queue=[start];
      visited[start]=1;
      let head=0,minX=width,minY=height,maxX=0,maxY=0;
      while(head<queue.length) {
        const i=queue[head++],x=i%width,y=Math.floor(i/width);
        points.push(i);
        if(x<minX)minX=x;if(x>maxX)maxX=x;
        if(y<minY)minY=y;if(y>maxY)maxY=y;
        for(let yy=Math.max(0,y-1);yy<=Math.min(height-1,y+1);yy++)
          for(let xx=Math.max(0,x-1);xx<=Math.min(width-1,x+1);xx++) {
            const j=yy*width+xx;
            if(!edges[j]||visited[j])continue;
            visited[j]=1;queue.push(j);
          }
      }
      if(points.length<cfg.minimumSegmentPixels)continue;
      points.sort((a,b)=>a-b);
      segments.push({
        evidenceId:"source-edge-"+start,
        semanticPart:"unbound",
        semanticConfidence:0,
        reason:"source_contrast_missing_in_flat_facet",
        pixelCount:points.length,
        bbox:[minX,minY,maxX-minX+1,maxY-minY+1],
        pixelIndices:points,
      });
    }
    segments.sort((a,b)=>b.pixelCount-a.pixelCount
      ||a.pixelIndices[0]-b.pixelIndices[0]);
    const retained=segments.slice(0,cfg.maxSegments);
    const overlayPixels=retained.flatMap(s=>s.pixelIndices).sort((a,b)=>a-b);
    return {version:VERSION,status:retained.length?"evidence_only_unbound":
      "no_supported_lost_boundaries",width,height,provenance,
      policy:cfg,
      summary:{eligibleSubjectPixels:eligibleCount,rawLostBoundaryPixels:rawLost,
        componentCount,retainedSegmentCount:retained.length,
        retainedPixels:overlayPixels.length,unboundSegments:retained.length,
        knownArmSegments:0,knownGarmentSegments:0},
      segments:retained,overlayPixels};
  }
  const api=Object.freeze({VERSION,DEFAULTS,observe});
  root.MinimalizerStructuralEvidenceV26=api;
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
}(typeof window!=="undefined"?window:globalThis));
