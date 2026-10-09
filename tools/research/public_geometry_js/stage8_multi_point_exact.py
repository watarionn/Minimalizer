"""Research-only multi-point exact Stage8 contour reduction.
Runs on private 40k candidates, never edits source originals. Every move must
preserve the full unguarded owner raster, not merely source center samples.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from stage8_official_polygon_replay import official_mirror

def optimize(owner,max_trials=18000,max_span=8):
 rings=[dict(r,points=list(r["points"])) for r in owner["parameters"]["rings"]]
 baseline=official_mirror(owner)
 initial=sum(len(r["points"]) for r in rings)
 accepted=trials=0
 while trials<max_trials:
  success=False
  order=sorted(range(len(rings)),key=lambda j:-len(rings[j]["points"]))
  for j in order:
   pts=rings[j]["points"]
   if len(pts)<=4:continue
   for span in range(min(max_span,len(pts)-3),1,-1):
    for i in range(len(pts)-span+1):
     proposed=pts[:i]+pts[i+span:]
     if len(proposed)<3:continue
     candidate=rings[:j]+[dict(rings[j],points=proposed)]+rings[j+1:]
     tmp=dict(owner,parameters=dict(owner["parameters"],rings=candidate))
     trials+=1
     if np.array_equal(official_mirror(tmp),baseline):
      rings=candidate;accepted+=span;success=True;break
     if trials>=max_trials:break
    if success or trials>=max_trials:break
   if success or trials>=max_trials:break
  if not success:break
 return {"originalVertices":initial,"candidateVertices":sum(len(r["points"]) for r in rings),
   "removedVertices":accepted,"trials":trials,"rawOwnerMaskPixelDifference":0},rings

def run(folder,out,max_trials):
 out.mkdir(parents=True,exist_ok=True)
 result={"schema":"stage8-multi-point-exact-v1","golden":"HOLD","production":"UNCHANGED","cases":{}}
 for case in ("GC001","Raden"):
  candidate=folder/f"{case}_stage8_candidate_PRIVATE.json"
  payload=candidate.read_bytes()
  doc=json.loads(payload)
  info={}
  for part in doc["primitives_back_to_front"]:
   metrics,rings=optimize(part,max_trials=max_trials)
   part["parameters"]["rings"]=rings
   info[part["composition_part"]]=metrics
  target=out/f"{case}_multi_point_candidate_PRIVATE.json"
  target.write_text(json.dumps(doc,separators=(",",":"),ensure_ascii=False))
  result["cases"][case]={"inputSha256":hashlib.sha256(payload).hexdigest(),
   "outputSha256":hashlib.sha256(target.read_bytes()).hexdigest(),
   "owners":info,"startVertices":sum(v["originalVertices"] for v in info.values()),
   "finalVertices":sum(v["candidateVertices"] for v in info.values()),
   "removedVertices":sum(v["removedVertices"] for v in info.values()),
   "signedOriginalPreserved":True}
 (out/"multi_point_exact_metrics.json").write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({k:{"before":v["startVertices"],"after":v["finalVertices"],
   "removed":v["removedVertices"]} for k,v in result["cases"].items()}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True);p.add_argument("--trials",type=int,default=18000)
 a=p.parse_args();run(a.input,a.out,a.trials)
