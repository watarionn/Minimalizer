/** Stage38: private review navigation progress. This is a bookmark, NOT a review certificate.
 * Re-pins the upstream manifest through expectedDigest supplied out-of-band.
 */
export const VERSION='p0-stage38-untrusted-offline-review-bookmarks-v1';
const fail=s=>{throw new TypeError(s);};
const hex=/^[0-9a-f]{64}$/;
const key=t=>t.tileId;
export async function summarizeUntrustedReviewProgress({manifest,expectedManifestSha256,marks=[]}){
 if(!manifest||!hex.test(expectedManifestSha256||'')||manifest.manifestSha256!==expectedManifestSha256||
 !Array.isArray(manifest.tiles)||!manifest.tiles.length||!Array.isArray(marks)||marks.length>manifest.tiles.length)fail('REVIEW_MANIFEST_PIN_MISMATCH');
 if(!globalThis.crypto?.subtle)fail('WEBCRYPTO_REQUIRED');
 const core={version:manifest.version,sourceIdentity:manifest.sourceIdentity,tiles:manifest.tiles,totals:manifest.totals};
 const actual=[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(core))))].map(x=>x.toString(16).padStart(2,'0')).join('');
 if(actual!==expectedManifestSha256)fail('REVIEW_MANIFEST_CONTENT_CHANGED');
 const seen=new Set(),states=new Map(),allowed=new Set(manifest.tiles.map(key));
 if(allowed.size!==manifest.tiles.length)fail('DUPLICATE_MANIFEST_TILE');
 for(const m of marks){if(!m||!Number.isSafeInteger(m.tileId)||!allowed.has(m.tileId)||seen.has(m.tileId)||!['visited','needs_revisit','unvisited'].includes(m.navigationState)||Object.keys(m).some(k=>!['tileId','navigationState'].includes(k)))fail('UNTRUSTED_REVIEW_MARK');seen.add(m.tileId);states.set(m.tileId,m.navigationState);}
 const tiles=manifest.tiles.map(t=>({tileId:t.tileId,bbox:t.bbox,eligiblePixels:t.eligiblePixels,priorityScore:t.priorityScore,
   navigationState:states.get(t.tileId)||'unvisited',unverifiedSemanticPixels:t.eligiblePixels}));
 const order={needs_revisit:0,unvisited:1,visited:2};tiles.sort((a,b)=>order[a.navigationState]-order[b.navigationState]||b.priorityScore-a.priorityScore||a.tileId-b.tileId);
 const counters={visited:0,needs_revisit:0,unvisited:0};for(const t of tiles)counters[t.navigationState]++;
 return {version:VERSION,caseId:manifest.sourceIdentity?.caseId,manifestSha256:expectedManifestSha256,
   totalTiles:tiles.length,counters,tiles,remainingNavigationTiles:counters.unvisited+counters.needs_revisit,
   independentlyReviewedSourcePixels:0,semanticApproval:false,stage18PaintAllowed:false,
   productPromotionAuthorized:false,status:'UNTRUSTED_NAVIGATION_ONLY'};
}
