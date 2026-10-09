"""GC001 research-only 3-6 source contour vertices -> one observed-grid vertex.
Whole original raw Stage8 owner raster must remain EXACT. Never changes signed originals.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from stage8_official_polygon_replay import official_mirror

def optimize(p,budget=20000):
 rings=[dict(r,points=list(r["points"])) for r in p["parameters"]["rings"]]
 original=official_mirror(p);trials=saved=0
 for j in sorted(range(len(rings)),key=lambda i:-len(rings[i]["points"])):
  i=0
  while i<len(rings[j]["points"])-3 and trials<budget:
   pts=rings[j]["points"]
   best=False
   for span in (6,5,4,3):
    if len(pts)-span+1<3 or i+span>len(pts):continue
    a=pts[i];b=pts[i+span-1]
    midpoint=[round((a[0]+b[0])/2),round((a[1]+b[1])/2)]
    options=[midpoint,[a[0],b[1]],[b[0],a[1]],a,b]
    for choice in options:
     nr=dict(rings[j],points=pts[:i]+[[float(choice[0]),float(choice[1])]]+pts[i+span:])
     new=rings[:j]+[nr]+rings[j+1:]
     trial=dict(p,parameters=dict(p["parameters"],rings=new))
     trials+=1
     if np.array_equal(official_mirror(trial),original):
      rings=new;saved+=span-1;best=True;break
     if trials>=budget:break
    if best or trials>=budget:break
   if not best:i+=1
 return rings,{"trials":trials,"saved":saved}

def run(root,out,limit):
 out.mkdir(parents=True,exist_ok=True);report={}
 for case in ("GC001","Raden"):
  file=root/f"{case}_multi_point_candidate_PRIVATE.json";scene=json.loads(file.read_text())
  prev=sum(len(r["points"]) for p in scene["primitives_back_to_front"] for r in p["parameters"]["rings"])
  ranks={}
  for p in scene["primitives_back_to_front"]:
   rings,stat=optimize(p,limit);p["parameters"]["rings"]=rings;ranks[p["composition_part"]]=stat
  total=sum(len(r["points"]) for p in scene["primitives_back_to_front"] for r in p["parameters"]["rings"])
  target=out/f"{case}_block_replaced_PRIVATE.json";target.write_text(json.dumps(scene,separators=(",",":"),ensure_ascii=False))
  report[case]={"before":prev,"after":total,"saved":prev-total,"cap":{"GC001":1887,"Raden":1412}[case],
   "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"owners":ranks}
 (out/"block_replacement_metrics.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({k:{"before":v["before"],"after":v["after"],"saved":v["saved"],"overage":max(0,v["after"]-v["cap"])} for k,v in report.items()}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 p.add_argument("--trials",type=int,default=20000);a=p.parse_args();run(a.input,a.out,a.trials)
