"""Trace tiny signed Stage8 rings against immutable original RGB/alpha and role occlusion.
Diagnostic only. No source pixels/rings are dropped or generated.
"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
import numpy as np

SHAS={"GC001":"75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e",
      "Raden":"d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00"}
def trace(stage8,source_root):
 result={"schema":"stage8-source-micro-ring-rgb-trace-v1","production":"UNCHANGED","golden":"HOLD","cases":{}}
 for case,expected_sha in SHAS.items():
  f=source_root/"original_inputs"/(case+"_source.png")
  if hashlib.sha256(f.read_bytes()).hexdigest()!=expected_sha:raise ValueError("unsigned source")
  rgba=np.asarray(Image.open(f).convert("RGBA"))
  if rgba.shape!=(340,340,4):raise ValueError("wrong image")
  original=stage8/case/"phase8_adaptive_source_contour_research.json"
  obj=json.loads(original.read_text(encoding="utf-8"))
  if obj.get("original_source_sha256")!=expected_sha or obj.get("no_new_material_or_owner") is not True:raise ValueError("unbound Stage8")
  findings=[];seen={}
  for p in obj["primitives_back_to_front"]:
   owner=p["composition_part"]
   for j,r in enumerate(p["parameters"]["rings"]):
    pts=r["points"]
    if len(pts)>2:continue
    samples=[]
    for point in pts:
     x,y=map(int,point)
     if x<0 or y<0 or x>=340 or y>=340:raise ValueError("source coordinate bounds")
     values=list(map(int,rgba[y,x]))
     samples.append({"xy":[x,y],"rgba":values,
        "originalHasPaint":values[3]!=0})
     seen.setdefault((x,y),set()).add(owner)
    findings.append({"owner":owner,"ringIndex":j,"role":r.get("role"),
      "depth":r.get("depth"),"pointCount":len(pts),"samples":samples,
      "releaseEligible":False})
  for record in findings:
   for sample in record["samples"]:
    owners=sorted(seen[tuple(sample["xy"])])
    sample["otherMicroRingOwners"]= [v for v in owners if v!=record["owner"]]
  case_counts={}
  for record in findings:
   case_counts[record["owner"]]=case_counts.get(record["owner"],0)+1
  result["cases"][case]={"sourceSha256":expected_sha,"stage8Sha256":hashlib.sha256(original.read_bytes()).hexdigest(),
   "microRingCount":len(findings),"microRingPoints":sum(r["pointCount"] for r in findings),
   "transparentSampleCount":sum(not s["originalHasPaint"] for r in findings for s in r["samples"]),
   "overlapWithOtherMicroOwnerSamples":sum(bool(s["otherMicroRingOwners"]) for r in findings for s in r["samples"]),
   "byOwner":case_counts,"candidates":findings,"safeRemovals":0,
   "ownerMaskSignedReplay":"NOT_PERFORMED"}
 return result
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--stage8",type=Path,required=True);p.add_argument("--sources",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();v=trace(a.stage8,a.sources);a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({c:{k:v["cases"][c][k] for k in ("microRingCount","microRingPoints","transparentSampleCount","overlapWithOtherMicroOwnerSamples","safeRemovals")} for c in ("GC001","Raden")}))
