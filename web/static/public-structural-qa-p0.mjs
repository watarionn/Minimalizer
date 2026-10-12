/** Stage9 independent, fail-closed quantitative QA; not a visual/semantic classifier. */
export const VERSION='structural-p0-stage9-quantitative-qa-v1';
const typed=x=>x instanceof Uint8Array||x instanceof Uint8ClampedArray;
export function auditStructuralCandidate({width,height,sourceRgba,baselineRgba,candidateRgba,
 faceMask,observations,geometry}){
 const n=width*height;
 if(!Number.isInteger(n)||n<1||n>160000||!typed(sourceRgba)||!typed(baselineRgba)||!typed(candidateRgba)||
 sourceRgba.length!==n*4||baselineRgba.length!==n*4||candidateRgba.length!==n*4||
 !typed(faceMask)||faceMask.length!==n||!Array.isArray(observations)||!geometry?.parts)throw Error('INVALID_QA_INPUT');
 let baselineLoss=0,candidateLoss=0,changed=0,offObservation=0,alphaChanges=0,faceChanges=0;
 const support=new Uint8Array(n);
 for(const x of observations){if(!typed(x.mask)||x.mask.length!==n)throw Error('INVALID_SOURCE_OBSERVATION');
  for(let i=0;i<n;i++)if(x.mask[i])support[i]=1;}
 for(let i=0;i<n;i++){
  const o=i*4;
  if(candidateRgba[o+3]!==baselineRgba[o+3])alphaChanges++;
  const changedRgb=candidateRgba[o]!==baselineRgba[o]||candidateRgba[o+1]!==baselineRgba[o+1]||candidateRgba[o+2]!==baselineRgba[o+2];
  if(changedRgb){changed++;if(faceMask[i])faceChanges++;else if(!support[i])offObservation++;}
  if(faceMask[i])continue;
  for(let k=0;k<3;k++){
   const a=sourceRgba[o+k]-baselineRgba[o+k];
   const b=sourceRgba[o+k]-candidateRgba[o+k];
   baselineLoss+=a*a;candidateLoss+=b*b;
  }
 }
 const originalCovered=geometry.parts.reduce((s,p)=>s+p.observedPixels,0);
 const candidateCovered=geometry.parts.reduce((s,p)=>s+p.containedPixels,0);
 return {version:VERSION,baselineLoss,candidateLoss,
  percentGain:baselineLoss?((baselineLoss-candidateLoss)/baselineLoss)*100:0,
  changed,alphaChanges,faceChanges,offObservation,
  sourceEvidenceCoverage:originalCovered?candidateCovered/originalCovered:0,
  originalObservedPixels:originalCovered,candidateCoveredPixels:candidateCovered,
  geometryVertices:geometry.totalVertices,
  sourceOnlyPass:alphaChanges===0&&offObservation===0,
  improvesOriginalRGB:baselineLoss>candidateLoss,
  semanticShapeQualityApproved:false,faceOutsideOriginalGuardVerified:false,
  productPromotionAuthorized:false};
}
/** Explicit research-preview admission: never trade away previous readable masks for
 * sparse rectangles when the old source-observed preview is quantitatively better.
 * Quality is still independently reviewed; admission is a one-way veto only. */
export function vetoRegressingGeometry({candidate,prior,minimumSourceCoverage=.60}){
 if(!candidate||!prior||typeof candidate.percentGain!=='number'||typeof prior.percentGain!=='number'||
 !Number.isFinite(minimumSourceCoverage)||minimumSourceCoverage<0||minimumSourceCoverage>1)throw Error('INVALID_GEOMETRY_COMPARISON');
 const reasons=[];
 if(!candidate.sourceOnlyPass)reasons.push('SOURCE_BOUNDARY_CHANGED');
 if(candidate.sourceEvidenceCoverage<minimumSourceCoverage)reasons.push('SOURCE_STRUCTURE_LOST');
 if(candidate.percentGain+1e-9<prior.percentGain)reasons.push('REGRESSION_AGAINST_PREVIOUS_CANDIDATE');
 return {adoptNewCandidate:reasons.length===0,reasonCodes:reasons,
  humanGoldenApproved:false,productPromotionAuthorized:false};
}
