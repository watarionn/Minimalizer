"""Research-only cyclic ring start perturbation followed by exact grid fusion.
Rotate closed ring point order, then run existing source-exact vertex optimizer;
accept ONLY if all original canonical OpenCV owner mask pixels stay identical.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from stage8_official_polygon_replay import official_mirror
from stage8_neighbor_grid_radius2 import reduce as exact_fuse

def reroute(owner,limit=14000):
 original=official_mirror(owner)
 original_rings=owner["parameters"]["rings"]
 best=[dict(r,points=list(r["points"])) for r in original_rings]
 start=sum(len(r["points"]) for r in best)
 checks=0
 # Shift closed contour start to induce a different traversal and greedy solution.
 for shift in (1,2,3,5,8,13):
  candidate=[]
  for r in best:
   pts=list(r["points"])
   candidate.append(dict(r,points=pts[shift%len(pts):]+pts[:shift%len(pts)] if pts else []))
  trial=dict(owner,parameters=dict(owner["parameters"],rings=candidate))
  checks+=1
  if not np.array_equal(official_mirror(trial),original):continue
  new,stats=exact_fuse(trial,limit=limit)
  compressed=dict(owner,parameters=dict(owner["parameters"],rings=new))
  if not np.array_equal(official_mirror(compressed),original):
   raise ValueError("original raster mismatch")
  if sum(len(x["points"]) for x in new)<sum(len(x["points"]) for x in best):best=new
 return best,{"start":start,"final":sum(len(r["points"]) for r in best),"shiftsChecked":checks}

def main():
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 p.add_argument("--trials",type=int,default=14000);a=p.parse_args()
 a.out.mkdir(parents=True,exist_ok=True);summary={}
 for case in ("GC001","Raden"):
  scene=json.loads((a.input/f"{case}_multi_point_candidate_PRIVATE.json").read_text())
  before=sum(len(r["points"]) for p in scene["primitives_back_to_front"] for r in p["parameters"]["rings"])
  detail={}
  for p in scene["primitives_back_to_front"]:
   rings,stats=reroute(p,a.trials);p["parameters"]["rings"]=rings;detail[p["composition_part"]]=stats
  total=sum(len(r["points"]) for p in scene["primitives_back_to_front"] for r in p["parameters"]["rings"])
  file=a.out/f"{case}_multi_point_candidate_PRIVATE.json";file.write_text(json.dumps(scene,ensure_ascii=False,separators=(",",":")))
  summary[case]={"before":before,"after":total,"saved":before-total,"candidateSha256":hashlib.sha256(file.read_bytes()).hexdigest(),"owners":detail}
 (a.out/"cyclic_start_metrics.json").write_text(json.dumps(summary,indent=2)+"\n")
 print(json.dumps({k:{"before":v["before"],"after":v["after"],"saved":v["saved"]} for k,v in summary.items()}))
if __name__=="__main__":main()
