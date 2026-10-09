import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {auditResponse,VERSION} from "../../web/static/public-r5-shadow-gate.mjs";
const PNG=Buffer.from(
 "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9WlJQAAAAASUVORK5CYII=",
 "base64");
let cases=0;
function check(x){cases++;console.log("PASS",x);}
assert.equal(PNG.subarray(0,8).toString("hex"),"89504e470d0a1a0a");
const orig=new Response(PNG,{status:200,headers:{"Content-Type":"image/png"}});
const result=await auditResponse(orig);
assert.equal(result.status,"ok",JSON.stringify(result));
assert.equal(result.sha256,createHash("sha256").update(PNG).digest("hex"));
assert.equal(result.bytes,PNG.byteLength);
assert.equal(result.applied,false);assert.equal(result.mutationCount,0);
assert.equal(result.productionPromoted,false);assert.ok(Object.isFrozen(result));
assert.deepEqual(Buffer.from(await orig.arrayBuffer()),PNG,
  "R5 may read clone but never consume or mutate source response");
check("exact read-only SHA with untouched original Response");
const wrong=await auditResponse(new Response(PNG,{headers:{"Content-Type":"text/plain"}}));
assert.equal(wrong.status,"invalid-mime");check("reject mismatched MIME");
const bad=await auditResponse(new Response(Uint8Array.from([0,1,2,3,4,5,6,7]),{
headers:{"Content-Type":"image/png"}}));
assert.equal(bad.status,"invalid-png");check("reject corrupt PNG");
const huge=await auditResponse(new Response(PNG,{headers:{
"Content-Type":"image/png","Content-Length":"9000000"}}));
assert.equal(huge.status,"over-limit");check("fail closed on oversized response");
const thrown=await auditResponse(new Response(PNG,{headers:{"Content-Type":"image/png"}}),{
digest:()=>{throw Error("subtle unavailable");}});
assert.equal(thrown.status,"error");check("observer error does not leak output");
const denied=await auditResponse(new Response(PNG,{headers:{"Content-Type":"image/png"}}),{
maxBytes:1});
assert.equal(denied.status,"invalid-limit");check("reject unsafe cap");
console.log(VERSION+" "+cases+" scenarios PASS");
