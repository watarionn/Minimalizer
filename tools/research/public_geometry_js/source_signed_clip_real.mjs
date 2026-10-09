// Signed original GC001/Raden trial runner. No external pixel painting or Public import.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {clippedSignedSvg} from "./source_signed_clip.mjs";
const check=(ok,msg)=>{if(!ok)throw Error(msg);};
const input=process.argv[2], previous=process.argv[3], target=process.argv[4];
check(input&&previous&&target,"usage: node source_signed_clip_real.mjs prepared.json old_triangles_dir output_dir");
const spec=JSON.parse(fs.readFileSync(input,"utf8"));
const verified=JSON.parse(fs.readFileSync(path.join(path.dirname(input),"verified_inputs.json"),"utf8"));
check(spec.schema==="public-real-two-case-part-geometry-v1","missing SA10.41 signed input manifest");
check(Object.keys(spec.cases).sort().join(",")==="GC001,Raden","two sources required");
fs.mkdirSync(target,{recursive:true});
const evidence={stage:"signed-source-clip-two-case-v1",researchOnly:true,face:"HIDDEN",production:"UNCHANGED",
  golden:"HOLD",sourceShape40Budget:"UNRELAXED",cases:{}};
for(const caseId of ["GC001","Raden"]){
 const obj=spec.cases[caseId],rgb=new Uint8Array(fs.readFileSync(obj.rgb));
 check(obj.size[0]===340&&obj.size[1]===340&&rgb.length===340*340*3,"unaligned signed RGB");
 const oldRecord={};
 for(const role of ["left_arm","right_arm"]){
  const part=obj.roles[role],mask=new Uint8Array(fs.readFileSync(part.signedMask));
  check(part.mask_sha256===verified[caseId].masks[role],"unsigned source role");
  check(part.signedPixels===mask.reduce((a,v)=>a+v,0),"original-signed owner pixel count");
  const file=path.join(previous,caseId+"_"+role+"_triangles.svg"),triangles=fs.readFileSync(file,"utf8");
  const sha=crypto.createHash("sha256").update(triangles).digest("hex");
  oldRecord[role]={originalCandidateSha256:sha,sourceMaskSha256:part.mask_sha256,methods:{}};
  for(const [name,undercoat] of [["clip_only",false],["clip_plus_medoid",true]]){
   const proposal=clippedSignedSvg({mask,rgb,w:340,h:340,trianglesSvg:triangles,
      sourceSha:verified[caseId].source_sha256,maskSha:part.mask_sha256,undercoat});
   const output=caseId+"_"+role+"_"+name+".svg";
   fs.writeFileSync(path.join(target,output),proposal.svg,"utf8");
   oldRecord[role].methods[name]={...proposal.metrics,outputSvg:output,
      outputSha256:crypto.createHash("sha256").update(proposal.svg).digest("hex")};
  }
 }
 evidence.cases[caseId]=oldRecord;
}
fs.writeFileSync(path.join(target,"signed_clip_metrics.json"),JSON.stringify(evidence,null,2)+"\n","utf8");
console.log(JSON.stringify({stage:evidence.stage,scope:"research only",
 cases:Object.fromEntries(Object.entries(evidence.cases).map(([k,v])=>[k,
 Object.fromEntries(Object.entries(v).map(([r,p])=>[r,p.methods.clip_only.clipRects]))]))}));
