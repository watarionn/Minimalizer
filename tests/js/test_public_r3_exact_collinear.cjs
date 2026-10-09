"use strict";
const assert=require("node:assert/strict");
const {exactCollinear,removeStrictCollinear,edgeMultiset,sameMultiset,analyzeSvg}=
  require("../../scripts/public_r3_exact_collinear.cjs");
const raster=require("../../web/static/opencv-fill-raster.js");
const {parse}=require("../../scripts/public_r2_owner_geometry.cjs");
const PREFIX='<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,eA=="/>';
const G=(c,d)=>'<path fill="#'+c+'" fill-rule="evenodd" d="'+d+'"/>';
const doc=(...shapes)=>PREFIX+shapes.join("")+"</svg>";
// Positive: mathematically identical straight line, no fabricated coordinates.
const points=[[2,2],[5,2],[8,2],[12,2],[12,12],[2,12]];
const reduced=removeStrictCollinear(points);
assert.ok(reduced.removed>=1,JSON.stringify(reduced));
assert.ok(sameMultiset(edgeMultiset([points]),edgeMultiset([reduced.ring])));
assert.deepEqual(raster.rasterizeLoops([points],340,340,2),
                 raster.rasterizeLoops([reduced.ring],340,340,2));
assert.equal(exactCollinear([0,0],[3,0],[3,4]),false);
assert.equal(exactCollinear([0,0],[3,0],[1,0]),false);
// Real vendored parsing and source group rendering under the exact R3 writer.
const v=analyzeSvg(doc(G("ffaa11","M2 2L5 2L8 2L12 2L12 12L2 12Z")));
assert.equal(v.summary.groupsWithCollinearProposals,1);
assert.ok(v.summary.mathematicallyProposedVertexSavings>=1);
assert.equal(v.summary.provenEdgeAndMaskGroups,1);
assert.equal(v.summary.appliedToPublic,false);
assert.equal(parse(v.candidate).groups[0].rgb,"ffaa11");
// Counterexample: near-collinear notch must NOT be simplified.
const notch=doc(G("8822aa","M2 2L20 2L20 20L12 20L12 19L8 19L8 20L2 20Z"));
const un=analyzeSvg(notch);
assert.equal(un.summary.groupsWithCollinearProposals,0);
assert.equal(un.candidate,notch);
// Multi-ring / disconnected color groups preserve separate owners, holes, order.
const multi=doc(G("102030","M2 2h10v10h-10Z M40 40h8v8h-8Z"),
                G("ff00ff","M100 100h10v10h-10Z"));
const b=analyzeSvg(multi);
assert.equal(b.summary.checkedColorGroups,2);
assert.equal(b.summary.provenEdgeAndMaskGroups,0);
assert.equal(b.candidate,multi);
assert.equal(parse(b.candidate).groups[0].loops.length,2);
// Adversarial forms: cannot erase a spike/backtracking or zero-length segment.
assert.equal(exactCollinear([0,0],[5,0],[0,0]),false);
assert.equal(exactCollinear([0,0],[0,0],[5,0]),false);
console.log("R3 exact lattice geometry: 5 safety scenarios PASS");
