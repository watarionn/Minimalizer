"""Research-only greedy removal of contour points with exact unguarded Stage8 raster.
Never commits source geometry; requires full official OpenCV parity at EVERY move.
"""
import argparse,json
from pathlib import Path
import numpy as np
from stage8_official_polygon_replay import official_mirror

def reduce_owner(owner,max_trials=100000):
 rings=[dict(r,points=list(r["points"])) for r in owner["parameters"]["rings"]]
 reference=official_mirror(owner)
 original=sum(len(r["points"]) for r in rings)
 checks=accepted=0
 # First remove point duplicates / redundant points from longest source rings.
 while checks<max_trials:
  changed=False
  order=sorted(range(len(rings)),key=lambda j:(-len(rings[j]["points"]),j))
  for j in order:
   r=rings[j]
   if len(r["points"])<=3:continue
   for i in range(len(r["points"])):
    points=r["points"]
    newring=dict(r,points=points[:i]+points[i+1:])
    newrings=rings[:j]+[newring]+rings[j+1:]
    trial=dict(owner,parameters=dict(owner["parameters"],rings=newrings))
    checks+=1
    if np.array_equal(official_mirror(trial),reference):
     rings=newrings;accepted+=1;changed=True;break
    if checks>=max_trials:break
   if changed or checks>=max_trials:break
  if not changed:break
 return {"startVertices":original,"endVertices":sum(len(r["points"]) for r in rings),
  "provenRemovable":accepted,"trials":checks,"sourceRasterExact":True},rings

def main():
 p=argparse.ArgumentParser();p.add_argument("--source-root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True);p.add_argument("--max-trials",type=int,default=8000)
 a=p.parse_args();result={"schema":"stage8-large-ring-exact-reducer-v1","cases":{},
  "production":"UNCHANGED","golden":"HOLD","safeForProduction":False}
 for case in ("GC001","Raden"):
  original=a.source_root/case/"phase8_adaptive_source_contour_research.json"
  scene=json.loads(original.read_text())
  info={}
  for owner in scene["primitives_back_to_front"]:
   role=owner["composition_part"]
   stat,_=reduce_owner(owner,max_trials=a.max_trials)
   info[role]=stat
  result["cases"][case]={"ownerResults":info,
   "originalVertices":sum(v["startVertices"] for v in info.values()),
   "candidateVertices":sum(v["endVertices"] for v in info.values()),
   "pixelExactRemovals":sum(v["provenRemovable"] for v in info.values())}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({k:{"original":v["originalVertices"],"reduced":v["candidateVertices"],
   "removals":v["pixelExactRemovals"]} for k,v in result["cases"].items()}))
if __name__=="__main__":main()
