/**
 * MinimalizerPublic R3: mathematically exact lattice-edge simplification research.
 * Only removes strictly BETWEEN collinear original vertices. Never invents points.
 * Whole-owner 2x raster and unit-lattice directed edge-multiset remain authoritative.
 * Candidates do not enter the Public production path.
 */
"use strict";
const fs=require("node:fs");
const path=require("node:path");
const crypto=require("node:crypto");
const {parse,shapeXml,sameMask}=require("./public_r2_owner_geometry.cjs");
const raster=require("../web/static/opencv-fill-raster.js");
const W=340,H=340;
const sha256=b=>crypto.createHash("sha256").update(b).digest("hex");
const cap=200000;
function gcd(a,b){a=Math.abs(a);b=Math.abs(b);while(b){const t=a%b;a=b;b=t;}return a;}
function exactCollinear(a,b,c){
  const ux=b[0]-a[0],uy=b[1]-a[1],vx=c[0]-b[0],vy=c[1]-b[1];
  // A--B--C in order: parallel and non-reversing, no hidden spike deletion.
  return (ux*vy-uy*vx===0) && (ux*vx+uy*vy>0);
}
function removeStrictCollinear(ring) {
  if(!Array.isArray(ring)||ring.length<3)return null;
  const current=ring.map(p=>p.slice());
  let removed=0;
  // Deterministic topology-preserving cyclic fixed point.
  for(let pass=0;pass<ring.length;pass++){
    let any=false;
    for(let i=0;i<current.length && current.length>3;){
      const n=current.length;
      if(exactCollinear(current[(i+n-1)%n],current[i],current[(i+1)%n])){
        current.splice(i,1);removed++;any=true;
      }else i++;
    }
    if(!any)break;
  }
  return {ring:current,removed};
}
function edgeMultiset(loops) {
  const multiset=new Map();
  let unitCount=0;
  for(const ring of loops)for(let i=0;i<ring.length;i++){
    const [x1,y1]=ring[i], [x2,y2]=ring[(i+1)%ring.length];
    const dx=x2-x1,dy=y2-y1,steps=gcd(dx,dy);
    if(steps===0 || steps>cap || unitCount+steps>cap)
      throw Error("invalid or over-budget lattice segment");
    const sx=dx/steps,sy=dy/steps;
    if(!Number.isSafeInteger(sx)||!Number.isSafeInteger(sy))
      throw Error("non-exact lattice step");
    for(let n=0;n<steps;n++){
      const ax=x1+sx*n,ay=y1+sy*n;
      const bx=ax+sx,by=ay+sy;
      const key=ax+","+ay+":"+bx+","+by;
      multiset.set(key,(multiset.get(key)||0)+1);
    }
    unitCount+=steps;
  }
  return multiset;
}
function sameMultiset(a,b){
  if(a.size!==b.size)return false;
  for(const [key,num]of a)if(b.get(key)!==num)return false;
  return true;
}
function analyzeSvg(svg) {
  const parsed=parse(svg);
  let checked=0,positive=0,removed=0,failedEdges=0,failedMask=0;
  let directedLatticeEdges=0;
  const groups=[],candidates=[];
  for(let gi=0;gi<parsed.groups.length;gi++){
    const g=parsed.groups[gi];
    checked++;
    const next=g.loops.map(removeStrictCollinear);
    if(next.some(c=>!c||!c.ring||c.ring.length<3))
      throw Error("invalid contour proposal");
    const savings=next.reduce((n,c)=>n+c.removed,0);
    const row={groupIndex:gi,color:g.rgb,ringCount:g.loops.length,
      originalVertices:g.loops.reduce((n,r)=>n+r.length,0),
      proposedVerticesRemoved:savings,edgeExact:false,maskExact:false,
      sourceSemanticPartAuthorized:false};
    if(savings>0) {
      positive++;
      const rings=next.map(c=>c.ring);
      const edges=edgeMultiset(g.loops),after=edgeMultiset(rings);
      directedLatticeEdges+=Array.from(edges.values()).reduce((a,b)=>a+b,0);
      if(!sameMultiset(edges,after)){
        failedEdges++;candidates.push(g.original);
      }else {
        row.edgeExact=true;
        const sourceMask=raster.rasterizeLoops(g.loops,W,H,2);
        const proposedMask=raster.rasterizeLoops(rings,W,H,2);
        if(!sameMask(sourceMask,proposedMask)){
          failedMask++;candidates.push(g.original);
        }else {
          row.maskExact=true;removed+=savings;
          candidates.push(shapeXml(g.rgb,rings));
        }
      }
    }else candidates.push(g.original);
    groups.push(row);
  }
  const candidate=parsed.prefix+candidates.join("")+parsed.suffix;
  const summary={
    version:"r3-exact-collinear-lattice-bridge-v1",
    sourceSHA256:sha256(Buffer.from(svg)),
    candidateSHA256:sha256(Buffer.from(candidate)),
    sourceColorGroups:parsed.groups.length,checkedColorGroups:checked,
    sourceVertices:parsed.count,groupsWithCollinearProposals:positive,
    provenEdgeAndMaskGroups:groups.filter(g=>g.edgeExact&&g.maskExact).length,
    mathematicallyProposedVertexSavings:removed,
    failedEdgeProofGroups:failedEdges,failedWholeMaskGroups:failedMask,
    unitLatticeSegmentsProved:directedLatticeEdges,
    candidateCoverageComplete:checked===parsed.groups.length,
    sourceRgbUnchanged:true,faceFeaturesAdded:false,
    appliedToPublic:false,semanticPartAuthorized:false,
    chromeNativeAnd2xPending:true,groups
  };
  return {candidate,summary};
}
function cli(){
 const [source,candidate,metrics]=process.argv.slice(2);
 if(!source||!candidate||!metrics||path.resolve(source)===path.resolve(candidate))
    throw Error("usage: node public_r3_exact_collinear.cjs SOURCE.svg OUT.svg OUT.json");
 const data=fs.readFileSync(source,"utf8");
 const res=analyzeSvg(data);
 fs.writeFileSync(candidate,res.candidate,{flag:"wx"});
 fs.writeFileSync(metrics,JSON.stringify(res.summary,null,2)+"\n",{flag:"wx"});
 console.log(JSON.stringify({checked:res.summary.checkedColorGroups,
  proposedGroups:res.summary.groupsWithCollinearProposals,
  provedGroups:res.summary.provenEdgeAndMaskGroups,
  removed:res.summary.mathematicallyProposedVertexSavings}));
}
if(require.main===module)cli();
module.exports={exactCollinear,removeStrictCollinear,edgeMultiset,sameMultiset,analyzeSvg};
