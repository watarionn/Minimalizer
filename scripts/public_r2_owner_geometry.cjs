/**
 * MinimalizerPublic R2, offline full-color-group ownership audit.
 * All source paths come from immutable SHA-gated v34 SVGs.
 * No raster source modification or conversion-route hook. Shape proposals
 * are never considered production output without an external Chrome gate.
 */
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const crypto = require("node:crypto");
const ROOT = path.resolve(__dirname,"..");
const vendor = name => path.join(ROOT,"web/static/vendor",name);
function umd(file, variable) {
  const context = {};
  vm.runInNewContext(fs.readFileSync(file,"utf8"),context,{timeout:10000});
  if (!context[variable]) throw Error("Missing actual vendor: "+variable);
  return context[variable];
}
const SVGPathCommander = umd(vendor("svg-path-commander/index.min.js"),"SVGPathCommander");
const simplify = require(vendor("simplify-js/simplify.js"));
const clipping = require(vendor("polygon-clipping/polygon-clipping.umd.min.js"));
const earcut = umd(vendor("earcut/earcut.min.js"),"earcut").default;
const raster = require(path.join(ROOT,"web/static/opencv-fill-raster.js"));
const RE = /<path fill="#([0-9a-fA-F]{6})" fill-rule="evenodd" d="([^"]+)"\/>/g;
const W = 340, H = 340, MAX_GROUPS = 1200, MAX_VERTICES = 20000;
const sha256 = data => crypto.createHash("sha256").update(data).digest("hex");
function decode(d) {
  const segments = new SVGPathCommander(d).toAbsolute().segments;
  const loops=[]; let loop=null,x=0,y=0,closed=true;
  for(const seg of segments) {
    const op=seg[0];
    if(op==="M") {
      if(!closed) throw Error("unterminated subpath");
      if(loop && loop.length<3) throw Error("short subpath");
      x=seg[1];y=seg[2];loop=[[x,y]];loops.push(loop);closed=false;
    } else if(op==="Z") {
      if(closed || !loop || loop.length<3) throw Error("invalid close");
      closed=true;
    } else if(!closed && ["L","H","V"].includes(op)) {
      if(op==="L"){x=seg[1];y=seg[2];}
      else if(op==="H"){x=seg[1];}else{y=seg[1];}
      if(loop.some(()=>false)) throw Error("never");
      loop.push([x,y]);
    } else throw Error("unsupported non-lattice path command: "+op);
    if(!Number.isSafeInteger(x)||!Number.isSafeInteger(y) ||
       x < -1 || y < -1 || x > W+1 || y > H+1) {
      throw Error("source path coordinate outside exact lattice bounds");
    }
  }
  if(!closed || !loops.length)throw Error("unclosed/empty path");
  for(const l of loops) {
    if(l.length>3 && l[0][0]===l[l.length-1][0] && l[0][1]===l[l.length-1][1]) l.pop();
    if(l.length<3)throw Error("degenerate ring");
  }
  return loops;
}
function parse(svg) {
  if(typeof svg!=="string" || svg.length>2000000 || !svg.startsWith("<svg ") ||
     !svg.endsWith("</svg>") || !svg.includes("data:image/png;base64,"))throw Error("not frozen v34 hybrid svg");
  const matches=[...svg.matchAll(RE)];
  if(!matches.length || matches.length>MAX_GROUPS ||
     matches.length !== (svg.match(/<path fill=/g)||[]).length) throw Error("unknown path structure or over-budget");
  if(matches[0].index<0)throw Error("invalid prefix");
  const prefix=svg.slice(0,matches[0].index);
  const suffix=svg.slice(matches[matches.length-1].index+matches[matches.length-1][0].length);
  if(suffix!=="</svg>") throw Error("untrusted tail");
  const groups=matches.map(m=>({original:m[0],rgb:m[1],loops:decode(m[2])}));
  const count=groups.reduce((n,g)=>n+g.loops.reduce((v,l)=>v+l.length,0),0);
  if(count>MAX_VERTICES)throw Error("over-budget source vertices");
  return {prefix,suffix,groups,count};
}
function pathData(loops) {
  return loops.map(points=>points.map(([x,y],i)=>(i?"L":"M")+x+" "+y).join("")+"Z").join(" ");
}
function shapeXml(rgb,loops) {
  return '<path fill="#'+rgb+'" fill-rule="evenodd" d="'+pathData(loops)+'"/>';
}
function sameMask(a,b) {
  if(a.length!==b.length) return false;
  for(let i=0;i<a.length;i++)if(a[i]!==b[i])return false;
  return true;
}
function propose(loops,tolerance) {
  let saved=0;
  const result=[];
  for(const ring of loops) {
    const points=ring.map(p=>({x:p[0],y:p[1]}));
    const proposed=simplify(points,tolerance,true);
    const next=proposed.length>=3 && proposed.length<points.length ?
      proposed.map(p=>[p.x,p.y]) : ring.map(p=>p.slice());
    saved+=ring.length-next.length;
    result.push(next);
  }
  return {rings:result,saved};
}
function clipRing(ring) {
  const polygon=[ring.map(p=>[p[0],p[1]])];
  const bbox=[[[0,0],[W,0],[W,H],[0,H]]];
  return clipping.intersection(polygon,bbox);
}
function triangulateOneRing(ring) {
  const flat=ring.flat();
  return earcut(flat,[],2);
}
function analyzeSvg(svg,{maxCandidates=120}={}) {
  const parsed=parse(svg);
  if(!Number.isInteger(maxCandidates)||maxCandidates<1||maxCandidates>1200)throw Error("invalid cap");
  const output=parsed.groups.map(g=>g.original);
  const rows=[];
  let visited=0, masksBuilt=0, maskComparisons=0, proposed=0, rejected=0, safe=0, saved=0;
  let clipRings=0, clipErrors=0, earcutSingle=0, earcutErrors=0;
  for(let gi=0;gi<parsed.groups.length;gi++){
    const g=parsed.groups[gi];
    visited++;
    const originalMask=raster.rasterizeLoops(g.loops,W,H,2);
    if(!originalMask || originalMask.length!==W*H)throw Error("invalid owner mask");
    masksBuilt++;
    // Clipping is observational and NEVER supplies an output polygon.
    // Every source ring, including all paths of multi-ring color groups, is visited.
    for(const ring of g.loops){
      try{clipRing(ring);clipRings++;}catch(_){clipErrors++;}
    }
    // Earcut's single outer ring is not valid for holes/multiple components.
    // Only unambiguous, bounded one-ring groups are triangulated for diagnostics.
    if(g.loops.length===1 && g.loops[0].length<=120){
      try{const tris=triangulateOneRing(g.loops[0]);
          if(tris.length%3!==0)throw Error("incomplete triangle");
          earcutSingle++;
      }catch(_){earcutErrors++;}
    }
    const beforeVertices=g.loops.reduce((v,r)=>v+r.length,0);
    let selected=null;
    if(proposed < maxCandidates) {
      for(const tolerance of [0.35,0.85,1.25]) {
        const candidate=propose(g.loops,tolerance);
        if(candidate.saved<=0)continue;
        proposed++;
        const testMask=raster.rasterizeLoops(candidate.rings,W,H,2);
        maskComparisons++;
        if(sameMask(originalMask,testMask)) {
          selected=candidate;
          break;
        } else rejected++;
        if(proposed>=maxCandidates)break;
      }
    }
    if(selected) {
      output[gi]=shapeXml(g.rgb,selected.rings);
      safe++;saved+=selected.saved;
    }
    rows.push({group:gi,rgb:g.rgb,rings:g.loops.length,
      originalVertices:beforeVertices,removedVertices:selected?selected.saved:0,
      fullOwnerMaskPrepared:true,candidateMaskExact:selected?true:null,\n      sourceVerifiedSemanticOwner:false});
  }
  const candidate=parsed.prefix+output.join("")+parsed.suffix;
  return {candidate, audit:{
    version:"public-r2-whole-color-groups-v1",sourceSHA256:sha256(Buffer.from(svg)),
    candidateSHA256:sha256(Buffer.from(candidate)),totalColorGroups:parsed.groups.length,
    visitedGroups:visited,fullOwnerMasksBuilt:masksBuilt,\n    candidateFullMaskComparisons:maskComparisons,
    totalSourceVertices:parsed.count,acceptedGroups:safe,proposalsTested:proposed,
    proposalsRejected:rejected,proposedSavedVertices:saved,
    clippingRingsVisited:clipRings,clippingErrors:clipErrors,
    earcutUnambiguousSingleRingGroups:earcutSingle,earcutErrors,
    candidateCoverageComplete:proposed<maxCandidates, outputApplied:false,
    semanticOwnerAuthorized:false,originalColorAndOrderPreserved:true,
    chromeParityPending:true,
    groups:rows
  }};
}
function cli() {
  const [input,out,meter]=process.argv.slice(2);
  if(!input||!out||!meter||[input,out,meter].some(s=>typeof s!=="string")||
     path.resolve(input)===path.resolve(out))throw Error("usage: node SCRIPT input.svg output.svg metrics.json");
  const source=fs.readFileSync(input,"utf8");
  const {candidate,audit}=analyzeSvg(source);
  fs.writeFileSync(out,candidate,{flag:"wx"});
  fs.writeFileSync(meter,JSON.stringify(audit,null,2)+"\n",{flag:"wx"});
  process.stdout.write(JSON.stringify({totalColorGroups:audit.totalColorGroups,
    visitedGroups:audit.visitedGroups,acceptedGroups:audit.acceptedGroups,
    proposedSavedVertices:audit.proposedSavedVertices,
    candidateCoverageComplete:audit.candidateCoverageComplete})+"\n");
}
if(require.main===module)cli();
module.exports={decode,parse,propose,analyzeSvg,sameMask,shapeXml};
