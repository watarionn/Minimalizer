"use strict";
const assert=require("node:assert/strict");
const {analyzeSvg,decode,parse}=require("../../scripts/public_r2_owner_geometry.cjs");
const raster=require("../../web/static/opencv-fill-raster.js");
const banner='<svg xmlns="http://www.w3.org/2000/svg" width="340" height="340"><image href="data:image/png;base64,eA=="/>';
const shape=(rgb,paths)=>'<path fill="#'+rgb+'" fill-rule="evenodd" d="'+paths+'"/>';
const full=(...groups)=>banner+groups.join("")+'</svg>';
// Genuine pinned SVGPathCommander understands the relative v34 h/v/l path.
assert.deepEqual(decode("M2 2h10v10h-10Z"),[[[2,2],[12,2],[12,12],[2,12]]]);
assert.throws(()=>decode("M1 1Q2 2 3 3Z"),/unsupported/);
assert.throws(()=>decode("M2 2L20 2"),/unclosed/);
// Safe positive: simplify-js deletes redundant collinear vertices and the
// exact complete owner mask (2x supersampled raster) matches the source.
const positive=full(shape("ff0000","M2 2L5 2L8 2L12 2L12 12L2 12Z"));
const original=parse(positive);
const before=JSON.stringify(original.groups[0].loops);
const a=analyzeSvg(positive);
assert.equal(a.audit.totalColorGroups,1);
assert.equal(a.audit.visitedGroups,1);
assert.equal(a.audit.fullOwnerMasksBuilt,1);
assert.ok(a.audit.acceptedGroups>=1,JSON.stringify(a.audit));
assert.ok(a.audit.proposedSavedVertices>=1,JSON.stringify(a.audit));
assert.equal(a.audit.groups[0].candidateMaskExact,true);
assert.equal(a.audit.outputApplied,false);
assert.equal(JSON.stringify(original.groups[0].loops),before);
const reduced=parse(a.candidate).groups[0].loops;
assert.deepEqual(raster.rasterizeLoops(original.groups[0].loops,340,340,2),
                 raster.rasterizeLoops(reduced,340,340,2));
// Unsafe notch geometry: reduction that paints over original notch fails.
const notch=full(shape("123abc",
 "M2 2L21 2L21 21L14 21L14 20L9 20L9 21L2 21Z"));
const n=analyzeSvg(notch);
assert.equal(n.audit.totalColorGroups,1);
assert.ok(n.audit.proposalsTested>0,JSON.stringify(n.audit));
assert.ok(n.audit.proposalsRejected>0,JSON.stringify(n.audit));
assert.equal(n.audit.outputApplied,false);
// Whole color group keeps all disconnected components. Do NOT send disconnected
// rings into Earcut under a guessed 'outer plus hole' convention.
const detached=full(shape("ffe000",
 "M2 2h8v8h-8Z M30 30h8v8h-8Z"));
const d=analyzeSvg(detached);
assert.equal(d.audit.totalColorGroups,1);
assert.equal(d.audit.groups[0].rings,2);
assert.equal(d.audit.earcutUnambiguousSingleRingGroups,0);
assert.equal(d.audit.fullOwnerMasksBuilt,1);
// Source group coverage is independent of the 8-shape caps in default library adapters.
const twelve=full(...Array.from({length:12},(_,i)=>
 shape("aaaaaa","M"+(i*20)+" 10h5v5h-5Z")));
const t=analyzeSvg(twelve);
assert.equal(t.audit.totalColorGroups,12);
assert.equal(t.audit.visitedGroups,12);
assert.equal(t.audit.fullOwnerMasksBuilt,12);
assert.equal(t.audit.clippingRingsVisited,12);
assert.equal(t.audit.earcutUnambiguousSingleRingGroups,12);
// Source exactness and safe failure behavior.
assert.throws(()=>parse("<svg><path d='M1 2Z'/></svg>"),/not frozen/);
assert.throws(()=>analyzeSvg(positive,{maxCandidates:0}),/invalid cap/);
console.log("R2 full-color-group Simplify/SVGPath/clipping/Earcut: 6 scenarios PASS");
