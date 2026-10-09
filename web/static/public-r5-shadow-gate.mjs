// MinimalizerPublic R5: flag-only, read-only PNG provenance observer.
// No route geometry, palette or render-authority decisions are made here.
// Disabled in normal processing. PNG is inspected by cloning a Response only.
export const VERSION = "public-r5-response-shadow-v1";
const MAX_BYTES = 8 * 1024 * 1024;
const SIGNATURE = [137,80,78,71,13,10,26,10];
export async function auditResponse(response, opts={}) {
  const base={version:VERSION,applied:false,productionPromoted:false,
    sourceSemanticsAuthorized:false,mutationCount:0};
  try {
    if(!response || !response.ok || !response.headers?.get)
      return Object.freeze({...base,status:"invalid-response",bytes:0,sha256:null});
    if(!(response.headers.get("Content-Type")||"").toLowerCase().startsWith("image/png"))
      return Object.freeze({...base,status:"invalid-mime",bytes:0,sha256:null});
    const limit=Number.isInteger(opts.maxBytes)?opts.maxBytes:MAX_BYTES;
    if(limit<8 || limit>MAX_BYTES)return Object.freeze({...base,status:"invalid-limit",bytes:0,sha256:null});
    const length=Number(response.headers.get("Content-Length"));
    if(Number.isFinite(length) && length>limit)
      return Object.freeze({...base,status:"over-limit",bytes:length,sha256:null});
    const clone=response.clone();
    const bytes=new Uint8Array(await clone.arrayBuffer());
    if(bytes.byteLength<24 || bytes.byteLength>limit ||
       !SIGNATURE.every((value,i)=>bytes[i]===value))
      return Object.freeze({...base,status:"invalid-png",bytes:bytes.byteLength,sha256:null});
    const digest=opts.digest || globalThis.crypto?.subtle?.digest;
    if(typeof digest!=="function")
      return Object.freeze({...base,status:"hash-unavailable",bytes:bytes.byteLength,sha256:null});
    const hash=await digest.call(opts.digest ? null : globalThis.crypto.subtle,"SHA-256",bytes);
    const hex=Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,"0")).join("");
    if(hex.length!==64)throw Error("invalid SHA256");
    return Object.freeze({...base,status:"ok",bytes:bytes.byteLength,sha256:hex});
  }catch(_err){
    return Object.freeze({...base,status:"error",bytes:0,sha256:null});
  }
}
