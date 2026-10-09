import test from "node:test";
import assert from "node:assert/strict";
import { wholeSignedRoleGate } from "./real_guards.mjs";

const sha = "a".repeat(64);
const valid = {components:1,maskHoleCount:0,signedPixels:100,componentPixels:100,mask_sha256:sha};
const good = {accepted:true,addedPixels:0,missingPixels:0,protectedPreserved:true};
test("complete but only preliminary signed contour",()=>{
 const r=wholeSignedRoleGate(valid,good);
 assert.equal(r.accepted,true);
 assert.equal(r.productionEligible,false);
});
test("all disconnected islands remain required",()=>{
 for(const n of [2,10]){
  const r=wholeSignedRoleGate({...valid,components:n},good);
  assert.equal(r.accepted,false);
  assert.equal(r.reason,"INCOMPLETE_TOPOLOGY");
 }
});
test("holes cannot be silently discarded",()=>{
 assert.equal(wholeSignedRoleGate({...valid,maskHoleCount:1},good).accepted,false);
});
test("partial component masks never represent signed role",()=>{
 assert.equal(wholeSignedRoleGate({...valid,componentPixels:99},good).accepted,false);
});
test("source expansion, loss, landmark drift are forbidden",()=>{
 for(const changed of [{accepted:false},{addedPixels:1},{missingPixels:1},{protectedPreserved:false}])
  assert.equal(wholeSignedRoleGate(valid,{...good,...changed}).accepted,false);
});
test("reject missing source authority",()=>{
 assert.throws(()=>wholeSignedRoleGate({...valid,mask_sha256:"fake"},good),/unsigned/);
 assert.throws(()=>wholeSignedRoleGate({...valid,componentPixels:101},good),/invalid signed pixels/);
});
