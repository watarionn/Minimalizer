"""Research-only exact source-owner contour vertex relocation.
Replace 2 consecutive vertices by one nearby original-grid point. Every accepted
candidate must reproduce entire official unguarded owner mask bit for bit.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from stage8_official_polygon_replay import official_mirror

def optimize(owner,limit=15000):
 rings=[dict(r,points=list(r["points"])) for r in owner["parameters"]["rings"]]
 reference=official_mirror(owner);trials=accepted=0
 for j in sorted(range(len(rings)),key=lambda k:-len(rings[k]["points"])):
  i=0
  while i<len(rings[j]["points"])-1 and trials<limit:
   p=rings[j]["points"]
   if len(p)<=4:break
   a,b=p[i],p[i+1]
   mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
   # Try grid-point alternatives; not a generated image or altered material.
   coords=list(dict.fromkeys([(round(mid[0]),round(mid[1])),(a[0],b[1]),(b[0],a[1]),(a[0],a[1]),(b[0],b[1])]))
   changed=False
   for xy in coords:
    candidate=p[:i]+[[float(xy[0]),float(xy[1])]]+p[i+2:]
    trial=rings[:j]+[dict(rings[j],points=candidate)]+rings[j+1:]
    proposed=dict(owner,parameters=dict(owner["parameters"],rings=trial))
    trials+=1
    if np.array_equal(reference,official_mirror(proposed)):
     rings=trial;accepted+=1;changed=True;break
    if trials>=limit:break
   if not changed:i+=1
 return rings,{"trials":trials,"reduced":accepted,"exact":True}

def run(root,out,limit):
 out.mkdir(parents=True,exist_ok=True)
 report={}
 for case in ("Raden","GC001"):
  f=root/f"{case}_multi_point_candidate_PRIVATE.json"
  original=f.read_bytes();scene=json.loads(original)
  before=sum(len(r["points"]) for p in scene["primitives_back_to_front"] for r in p["parameters"]["rings"])
  detail={}
  for owner in scene["primitives_back_to_front"]:
   role=owner["composition_part"];rings,stats=optimize(owner,limit)
   owner["parameters"]["rings"]=rings;detail[role]=stats
  after=sum(len(r["points"]) for p in scene["primitives_back_to_front"] for r in p["parameters"]["rings"])
  target=out/f"{case}_relocated_PRIVATE.json";target.write_text(json.dumps(scene,separators=(",",":"),ensure_ascii=False))
  report[case]={"from":before,"to":after,"saved":before-after,"cap":{"Raden":1412,"GC001":1887}[case],
    "inputSha256":hashlib.sha256(original).hexdigest(),"candidateSha256":hashlib.sha256(target.read_bytes()).hexdigest(),"owners":detail}
 (out/"relocation_metrics.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({k:{"from":v["from"],"to":v["to"],"saved":v["saved"],"remainingOverage":max(0,v["to"]-v["cap"])} for k,v in report.items()}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--trials",type=int,default=15000)
 a=p.parse_args();run(a.input,a.out,a.trials)
