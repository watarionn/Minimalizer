"""Research-only whole-ring redundancy probe on private signed Stage8 candidate.
Pixel-perfect full unguarded owner raster is required for each and combined edit.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from stage8_official_polygon_replay import official_mirror
def inspect(root,out):
 out.mkdir(parents=True,exist_ok=True);record={}
 for case in ("GC001","Raden"):
  path=root/f"{case}_multi_point_candidate_PRIVATE.json"
  data=json.loads(path.read_text())
  details={};removed=0
  for p in data["primitives_back_to_front"]:
   rings=list(p["parameters"]["rings"]);reference=official_mirror(p)
   chosen=[]
   for i in sorted(range(len(rings)),key=lambda j:-len(rings[j]["points"])):
    trial=[r for idx,r in enumerate(rings) if idx!=i]
    if not trial:continue
    candidate=dict(p,parameters=dict(p["parameters"],rings=trial))
    if np.array_equal(reference,official_mirror(candidate)):
     rings=trial;chosen.append(i)
   if not np.array_equal(reference,official_mirror(dict(p,parameters=dict(p["parameters"],rings=rings)))):
    raise ValueError("combined owner mismatch")
   previous=sum(len(r["points"]) for r in p["parameters"]["rings"])
   after=sum(len(r["points"]) for r in rings)
   p["parameters"]["rings"]=rings
   removed+=previous-after
   details[p["composition_part"]]={"before":previous,"after":after,"ringsRemoved":len(chosen)}
  output=out/f"{case}_ring_probe_PRIVATE.json"
  output.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")))
  record[case]={"removedVertices":removed,"endVertices":sum(v["after"] for v in details.values()),
   "ownerDetails":details,"candidateSha256":hashlib.sha256(output.read_bytes()).hexdigest()}
 (out/"ring_probe_metrics.json").write_text(json.dumps(record,indent=2)+"\n")
 print(json.dumps({k:{"endVertices":v["endVertices"],"removedVertices":v["removedVertices"],"changedOwners":[[a,b["ringsRemoved"]] for a,b in v["ownerDetails"].items() if b["ringsRemoved"]]} for k,v in record.items()}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();inspect(a.input,a.out)
