"""Research-only Stage8 ring-search completion gate and owner Pareto.
Never modifies original assets. Measures all signed owner contours with original raster gate.
"""
from pathlib import Path
import argparse,json,hashlib
from stage8_official_polygon_replay import official_mirror
import numpy as np
def audit(root,out):
 result={}
 for case,cap in (("GC001",1887),("Raden",1412)):
  p=root/f"{case}_multi_point_candidate_PRIVATE.json";data=json.loads(p.read_text())
  owners={}
  for part in data["primitives_back_to_front"]:
   role=part["composition_part"];rings=part["parameters"]["rings"]
   owners[role]={"vertices":sum(len(r["points"]) for r in rings),
    "ringCount":len(rings),"smallRingCount":sum(len(r["points"])<=3 for r in rings),
    "largeRingVertices":sum(len(r["points"]) for r in rings if len(r["points"])>8),
    "rawMaskPixels":int(official_mirror(part).sum())}
  total=sum(x["vertices"] for x in owners.values())
  result[case]={"vertices":total,"hardCap":cap,"capPass":total<=cap,
   "gap":max(0,total-cap),"candidateSHA256":hashlib.sha256(p.read_bytes()).hexdigest(),
   "rankedOwners":dict(sorted(owners.items(),key=lambda x:-x[1]["vertices"]))}
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({k:{"total":v["vertices"],"gap":v["gap"],"leadingOwners":list(v["rankedOwners"].items())[:4]} for k,v in result.items()}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();audit(a.input,a.out)
