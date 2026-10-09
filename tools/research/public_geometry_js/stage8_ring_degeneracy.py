"""Classify collinear evidence without proposing unsafe changes."""
from pathlib import Path
import json,argparse
def classify(points):
 n=len(points)
 if n<3:return "undersized"
 categories=[]
 for i in range(n):
  a,b,c=points[i-1],points[i],points[(i+1)%n]
  cross=(b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
  if cross!=0:continue
  ab=(b[0]-a[0],b[1]-a[1]);bc=(c[0]-b[0],c[1]-b[1])
  dot=ab[0]*bc[0]+ab[1]*bc[1]
  categories.append("straight" if dot>0 else "zero_or_reverse")
 return categories
def audit(base):
 out={}
 for case in ("GC001","Raden"):
  data=json.loads((base/case/"phase8_adaptive_source_contour_research.json").read_text())
  rings=[(p["composition_part"],r["points"]) for p in data["primitives_back_to_front"] for r in p["parameters"]["rings"]]
  tallies={"tiny_ring_count":0,"tiny_ring_point_count":0,"straight":0,"zero_or_reverse":0,
           "straight_in_ring_ge4":0}
  for role,pts in rings:
   if len(pts)<3:
    tallies["tiny_ring_count"]+=1;tallies["tiny_ring_point_count"]+=len(pts)
   else:
    for t in classify(pts):
     tallies[t]+=1
     if t=="straight" and len(pts)>=4:tallies["straight_in_ring_ge4"]+=1
  out[case]=tallies
 return out
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True)
 a=p.parse_args();print(json.dumps(audit(a.root),indent=2))
