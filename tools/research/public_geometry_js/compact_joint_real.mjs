// Isolated two-source joint-arm budget evaluator. Never imported by production.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {optimizeSignedColorPlanes} from "./compact_signed_planes.mjs";
const check=(v,m)=>{if(!v)throw Error(m);};
const input=process.argv[2],destination=process.argv[3];
check(input&&destination,"node compact_joint_real.mjs <prepared.json> <out>");
const cfg=JSON.parse(fs.readFileSync(input,"utf8"));
const verified=JSON.parse(fs.readFileSync(path.join(path.dirname(input),"verified_inputs.json"),"utf8"));
check(cfg.schema==="public-real-two-case-part-geometry-v1","signed source schema");
check(Object.keys(cfg.cases).sort().join(",")==="GC001,Raden","two originals required");
fs.mkdirSync(destination,{recursive:true});
function render(candidate,n){
 const w=candidate.width,h=candidate.height;
 const shape=candidate.planes.slice(0,n).map(p=>`<rect x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}" fill="rgb(${p.fill.join(",")})"/>`).join("");
 return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><defs><clipPath id="signed" clipPathUnits="userSpaceOnUse"><path d="${candidate.clipPath}" clip-rule="evenodd" fill-rule="evenodd"/></clipPath></defs><g clip-path="url(#signed)"><rect x="0" y="0" width="${w}" height="${h}" fill="rgb(${candidate.baseRgb.join(",")})"/>${shape}</g></svg>\n`;
}
const report={schema:"compact-signed-joint-two-arm-v1",scope:"ARMS_ONLY_NOT_WHOLE_SCENE",production:"UNCHANGED",golden:"HOLD",faceDetails:"NOT_RENDERED",cases:{}};
for(const caseId of ["GC001","Raden"]){
 const c=cfg.cases[caseId],rgb=new Uint8Array(fs.readFileSync(c.rgb));
 check(c.size[0]===340&&c.size[1]===340&&rgb.length===340*340*3,"signed RGB alignment");
 const own={};
 for(const role of ["left_arm","right_arm"]){
  const p=c.roles[role],mask=new Uint8Array(fs.readFileSync(p.signedMask));
  check(p.mask_sha256===verified[caseId].masks[role],"mask SHA mismatch");
  check(mask.reduce((a,v)=>a+v,0)===p.signedPixels,"source owner area");
  // Exclude truly transparent original-source pixels before any RGB plane; do not invent missing paint.
  const alphaPath=path.join(path.dirname(input),caseId,role+"_source_alpha.bin");
  check(fs.existsSync(alphaPath),"source alpha evidence is mandatory");
  const alpha=new Uint8Array(fs.readFileSync(alphaPath));
  check(alpha.length===mask.length,"source alpha mismatch");
  const visible=mask.map((v,i)=>Number(v===1&&alpha[i]>0));
  own[role]=optimizeSignedColorPlanes({mask:visible,rgb,w:340,h:340,budget:80,
    sourceSha:verified[caseId].source_sha256,maskSha:p.mask_sha256});
 }
 const stages={};
 for(const budget of [24,40,60,80]){
  const alloc={left_arm:0,right_arm:0};
  while(alloc.left_arm+alloc.right_arm<budget-4){
   let winner=null,gain=0;
   for(const role of ["left_arm","right_arm"]){
    const r=own[role],n=alloc[role];if(n+1>=r.progress.length)continue;
    const g=r.progress[n]-r.progress[n+1];if(g>gain){gain=g;winner=role;}
   }
   if(!winner)break;alloc[winner]++;
  }
  let shapes=0,err=0,px=0;const roles={};
  for(const role of ["left_arm","right_arm"]){
   const r=own[role],n=alloc[role],svg=render(r,n);
   const file=`${caseId}_${role}_budget${budget}.svg`;
   fs.writeFileSync(path.join(destination,file),svg);
   const count=n+2;shapes+=count;err+=r.progress[n];px+=r.metrics.maskPixels;
   roles[role]={file,shapeCount:count,planes:n,sourceMaskVisiblePixels:r.metrics.maskPixels,
    clipVertexOccurrences:r.metrics.clipBoundaryVertexOccurrences,clipLoops:r.metrics.clipSourceLoops,
    svgSha256:crypto.createHash("sha256").update(svg).digest("hex")};
  }
  check(shapes<=budget,"arm pair primitive count exceeded");
  stages[budget]={budget,combinedArmShapes:shapes,combinedArmRGBMAE:err/(3*px),roles,
    fullBodyShapeBudget:"NOT_EVALUATED",vertexBudget:"NOT_PASSED"};
 }
 report.cases[caseId]=stages;
}
fs.writeFileSync(path.join(destination,"compact_joint_metrics.json"),JSON.stringify(report,null,2)+"\n");
console.log("Arms-only compact proposals generated, release HOLD");
