/** Stage39: compare two untrusted navigation snapshots. No human reviewer identity inferred. */
export const VERSION='p0-stage39-review-bookmark-diff-v1';
const fail=s=>{throw new TypeError(s);};
export function compareUntrustedReviewProgress({before,after}){
 if(!before||!after||before.manifestSha256!==after.manifestSha256||before.caseId!==after.caseId||
  !Array.isArray(before.tiles)||!Array.isArray(after.tiles)||before.tiles.length!==after.tiles.length)fail('REVIEW_SNAPSHOT_IDENTITY_MISMATCH');
 const prior=new Map(before.tiles.map(x=>[x.tileId,x]));if(prior.size!==before.tiles.length)fail('DUPLICATE_PRIOR_TILES');
 const seen=new Set(),changes=[];let unchanged=0;
 for(const t of after.tiles){if(seen.has(t.tileId)||!prior.has(t.tileId))fail('REVIEW_TILE_SET_CHANGED');seen.add(t.tileId);
   const p=prior.get(t.tileId);if(p.eligiblePixels!==t.eligiblePixels||p.priorityScore!==t.priorityScore||JSON.stringify(p.bbox)!==JSON.stringify(t.bbox))fail('REVIEW_TILE_GEOMETRY_CHANGED');
   if(p.navigationState===t.navigationState)unchanged++;else changes.push({tileId:t.tileId,from:p.navigationState,to:t.navigationState});}
 changes.sort((a,b)=>a.tileId-b.tileId);
 return {version:VERSION,caseId:before.caseId,manifestSha256:before.manifestSha256,
   changedTiles:changes.length,unchangedTiles:unchanged,changes,
   untrustedNavigationOnly:true,reviewerIdentityVerified:false,independentlyReviewedSourcePixels:0,
   productPromotionAuthorized:false,stage18PaintAllowed:false};
}
