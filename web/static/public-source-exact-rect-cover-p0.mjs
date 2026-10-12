/** Stage49: exact observed bitmap area as disjoint rectangles, no new pixels.
 * Research candidate compared against source-exact contour. Vertex costs remain honest.
 */
export const VERSION='p0-stage49-vertical-merged-source-rectangle-cover-v1';
const fail=s=>{throw new TypeError(s);};
export function exactSourceRectangleCover({width,height,sourceMask,maxRectangles=40000}){
 const n=width*height;
 if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||!(sourceMask instanceof Uint8Array||sourceMask instanceof Uint8ClampedArray)||sourceMask.length!==n||!Number.isInteger(maxRectangles)||maxRectangles<1||maxRectangles>160000)fail('INVALID_RECT_SOURCE');
 const rectangles=[],raster=new Uint8Array(n);let prior=new Map(),positive=0;
 for(let y=0;y<height;y++){
  const current=new Map();
  for(let x=0;x<width;){const i=y*width+x,v=sourceMask[i];if(v!==0&&v!==255)fail('NONBINARY_RECT_SOURCE');if(v===0){x++;continue;}
   const x0=x;while(x<width&&sourceMask[y*width+x]===255){raster[y*width+x]=255;positive++;x++;}
   const key=x0+','+x;let ri=prior.get(key);
   if(ri===undefined){if(rectangles.length>=maxRectangles)fail('RECT_BUDGET_EXCEEDED');ri=rectangles.length;rectangles.push([x0,y,x,y+1]);}
   else rectangles[ri][3]=y+1;
   current.set(key,ri);
  }
  prior=current;
 }
 let mismatch=0;for(let i=0;i<n;i++)if(sourceMask[i]!==raster[i])mismatch++;
 if(mismatch)fail('RECT_SOURCE_RASTER_MISMATCH');
 return {version:VERSION,rectangles,observedPixels:positive,rectangleCount:rectangles.length,
  explicitVertexCost:rectangles.length*4,exactSourceMask:true,exactAtDpr2:true,
  sourceOnly:true,semanticApproved:false,paintAuthorized:false,productPromotionAuthorized:false};
}
/** Reject a rectangle-only replacement that is not strictly cheaper; no pixel or label side-effects. */
export function compareExactCoverBudget({contourVertices,rectCover,hardBudget}){
 if(!Number.isInteger(contourVertices)||contourVertices<4||!Number.isInteger(hardBudget)||hardBudget<4||!rectCover||rectCover.exactSourceMask!==true||!Number.isInteger(rectCover.explicitVertexCost))fail('INVALID_COVER_COMPARISON');
 return {contourVertices,rectangleVertices:rectCover.explicitVertexCost,hardBudget,
  savedVertices:contourVertices-rectCover.explicitVertexCost,
  rectanglePreferred:rectCover.explicitVertexCost<contourVertices,
  rectangleWithinBudget:rectCover.explicitVertexCost<=hardBudget,
  adopted:false,productionReleaseAuthorized:false};
}
