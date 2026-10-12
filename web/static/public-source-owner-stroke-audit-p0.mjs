/** Stage58/60: independently pinned original source/historical owner masks.
 * Names are historical source-mask identifiers, not anatomy or new color ownership.
 */
import {deriveSourceAnnotationAuthority} from './public-annotation-authority-p0.mjs';
import {buildSourceTiledStrokeCandidate} from './public-source-tiled-stroke-p0.mjs';
import {auditTiledStrokeRaster} from './public-source-stroke-raster-audit-p0.mjs';
export const VERSION='p0-stage60-historic-owner-stroke-evaluation-v1';
export async function auditHistoricOwnerStrokeCandidates({width,height,originalRgba,originalSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,arms,tileSizes=[16,32,64]}){
 if(!Array.isArray(tileSizes)||tileSizes.length<1||tileSizes.length>5||tileSizes.some(s=>![8,16,32,64,128].includes(s))||new Set(tileSizes).size!==tileSizes.length)throw new TypeError('INVALID_TILE_SWEEP');
 const authority=await deriveSourceAnnotationAuthority({width,height,originalRgba,originalSha256,faceMask,faceSha256,backgroundMask,backgroundSha256,arms});
 const rows=[];
 for(const role of ['left_arm','right_arm']){
  const sourceMask=role==='left_arm'?authority.left:authority.right;
  // A fully excluded historical owner is a research observation, not a reason to paint.
  if(!sourceMask.some(Boolean)){rows.push({historicRole:role,eligibleSourcePixels:0,candidates:[],winner:null});continue;}
  const candidates=[];
  for(const tileSize of tileSizes){const c=await buildSourceTiledStrokeCandidate({width,height,sourceMask,sourceMaskSha256:await sha(sourceMask),tileSize});const proof=auditTiledStrokeRaster({width,height,sourceMask,candidate:c});if(!proof.mathematicallyExact)throw new TypeError('HISTORIC_OWNER_RASTER_FAIL');candidates.push({tileSize,sourcePixels:proof.sourcePixels,globalSegments:c.globalStrokeCount,tiledSegments:c.tiledStrokeCount,selectedSegments:c.selectedStrokeCount,selectedMode:c.selectedMode,selectedEndpointCount:c.endpointCount,selectedMarkupBytes:new TextEncoder().encode(c.svgPaths).length,parity1x:proof.mismatch340,parity2x:proof.mismatch680});}
  candidates.sort((a,b)=>a.selectedSegments-b.selectedSegments||a.selectedMarkupBytes-b.selectedMarkupBytes||a.tileSize-b.tileSize);
  rows.push({historicRole:role,eligibleSourcePixels:candidates[0].sourcePixels,winner:candidates[0],candidates});
 }
 return {version:VERSION,width,height,authoritySourceSha256:originalSha256,sourceEligibilitySha256:authority.sourceEligibilitySha256,eligiblePixels:authority.eligiblePixels,excludedAlpha:authority.excludedAlpha,excludedBackground:authority.excludedBackground,excludedFace:authority.excludedFace,rows,
 independentAnatomicalPixels:0,sourceColorPaintAuthorized:false,wholeSceneBudgetCertified:false,fullCharacterGoldenVerified:false,productionReleaseAuthorized:false,status:'HOLD_HISTORIC_ROLES_ONLY'};
}
async function sha(x){if(!globalThis.crypto?.subtle)throw new TypeError('WEBCRYPTO_REQUIRED');return [...new Uint8Array(await crypto.subtle.digest('SHA-256',x))].map(x=>x.toString(16).padStart(2,'0')).join('');}
