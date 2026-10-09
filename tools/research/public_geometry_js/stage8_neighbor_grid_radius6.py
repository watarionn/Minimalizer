"""Research-only local 1px grid perturbation plus vertex fusion.
Every accepted edit maintains exact official OpenCV raw owner pixels.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from stage8_official_polygon_replay import official_mirror
def reduce(p,limit=12000):
 rings=[dict(r,points=list(r["points"])) for r in p["parameters"]["rings"]]
 original=official_mirror(p);attempts=saved=0
 for j in sorted(range(len(rings)),key=lambda idx:-len(rings[idx]["points"])):
  k=0
  while k<len(rings[j]["points"])-1 and attempts<limit:
   pts=rings[j]["points"]
   if len(pts)<=4:break
   x=(pts[k][0]+pts[k+1][0])/2;y=(pts[k][1]+pts[k+1][1])/2
   choices=[]
   for cx in (round(x),round(x)-1,round(x)+1,round(x)-2,round(x)+2,round(x)-3,round(x)+3,round(x)-4,round(x)+4,round(x)-5,round(x)+5,round(x)-6,round(x)+6):
    for cy in (round(y),round(y)-1,round(y)+1,round(y)-2,round(y)+2,round(y)-3,round(y)+3,round(y)-4,round(y)+4,round(y)-5,round(y)+5,round(y)-6,round(y)+6):
     choice=[float(cx),float(cy)]
     if choice not in choices:choices.append(choice)
   accepted=False
   for point in choices:
    candidate=pts[:k]+[point]+pts[k+2:]
    proposed=rings[:j]+[dict(rings[j],points=candidate)]+rings[j+1:]
    temp=dict(p,parameters=dict(p["parameters"],rings=proposed))
    attempts+=1
    if np.array_equal(official_mirror(temp),original):
     rings=proposed;saved+=1;accepted=True;break
    if attempts>=limit:break
   if not accepted:k+=1
 return rings,{"trials":attempts,"saved":saved}
def main():
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--trials",type=int,default=12000)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);summary={}
 for case in ("GC001","Raden"):
  file=a.input/f"{case}_multi_point_candidate_PRIVATE.json";scene=json.loads(file.read_text())
  before=sum(len(r["points"]) for own in scene["primitives_back_to_front"] for r in own["parameters"]["rings"])
  role={}
  for own in scene["primitives_back_to_front"]:
   rings,status=reduce(own,a.trials);own["parameters"]["rings"]=rings;role[own["composition_part"]]=status
  after=sum(len(r["points"]) for own in scene["primitives_back_to_front"] for r in own["parameters"]["rings"])
  output=a.out/f"{case}_multi_point_candidate_PRIVATE.json";output.write_text(json.dumps(scene,ensure_ascii=False,separators=(",",":")))
  summary[case]={"before":before,"after":after,"saved":before-after,"owner":role,"candidateSha256":hashlib.sha256(output.read_bytes()).hexdigest()}
 (a.out/"neighbor_grid_metrics.json").write_text(json.dumps(summary,indent=2)+"\n")
 print(json.dumps({k:{"before":v["before"],"after":v["after"],"saved":v["saved"]} for k,v in summary.items()}))
if __name__=="__main__":main()
