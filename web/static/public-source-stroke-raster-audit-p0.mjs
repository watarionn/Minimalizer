/** Stage59: independent exact membership reconstruction at 1x and 2x.
 * Strict source-pixel footprints, no antialiasing; real Chromium is a separate proof.
 */
export const VERSION='p0-stage59-multiscale-source-stroke-membership-v1';
const bad=x=>{throw new TypeError(x);};
export function auditTiledStrokeRaster({width,height,sourceMask,candidate}){
 const n=width*height;if(!Number.isInteger(width)||!Number.isInteger(height)||n<1||n>160000||!(sourceMask instanceof Uint8Array||sourceMask instanceof Uint8ClampedArray)||sourceMask.length!==n||candidate?.width!==width||candidate?.height!==height||!Array.isArray(candidate.strokes)||candidate.strokes.length>100000||candidate.strokes.length===0)bad('INVALID_STROKE_AUDIT');
 const visited=new Uint8Array(n),visited2=new Uint8Array(n*4);let overlap=0;
 for(const s of candidate.strokes){if(!s||!['vertical','horizontal'].includes(s.axis)||![s.x0,s.y0,s.x1,s.y1,s.width].every(Number.isInteger)||s.x0<0||s.y0<0||s.x1>width||s.y1>height||s.x0>=s.x1||s.y0>=s.y1||s.width!==(s.axis==='vertical'?s.x1-s.x0:s.y1-s.y0))bad('INVALID_STROKE_GEOMETRY');
  for(let y=s.y0;y<s.y1;y++)for(let x=s.x0;x<s.x1;x++){const i=y*width+x;if(visited[i])overlap++;visited[i]=255;for(let dy=0;dy<2;dy++)for(let dx=0;dx<2;dx++){const ii=(y*2+dy)*width*2+x*2+dx;if(visited2[ii])overlap++;visited2[ii]=255;}}
 }
 let mismatch340=0,mismatch680=0,sourcePixels=0,spill=0,lost=0;
 for(let i=0;i<n;i++){const s=sourceMask[i];if(s!==0&&s!==255)bad('NONBINARY_AUDIT_MASK');if(s)sourcePixels++;if(visited[i]!==s){mismatch340++;if(visited[i])spill++;else lost++;}const x=i%width,y=Math.floor(i/width);for(let dy=0;dy<2;dy++)for(let dx=0;dx<2;dx++)if(visited2[(2*y+dy)*width*2+2*x+dx]!==s)mismatch680++;}
 const exact=overlap===0&&mismatch340===0&&mismatch680===0;
 return {version:VERSION,sourcePixels,strokeCount:candidate.strokes.length,mismatch340,mismatch680,spill,lost,overlap,mathematicallyExact:exact,realChromeVerified:false,semanticVerified:false,productionReleaseAuthorized:false};
}
