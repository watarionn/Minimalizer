"""Private signed Stage8 ring-structure audit: diagnose exact remaining budgets.
No geometry mutated and no source images are exported.
"""
import json,argparse
from pathlib import Path
def run(folder):
 result={}
 for case in ("GC001","Raden"):
  f=folder/f"{case}_multi_point_candidate_PRIVATE.json"
  data=json.loads(f.read_text(encoding="utf-8"))
  details={}
  for p in data["primitives_back_to_front"]:
   rings=p["parameters"]["rings"]
   points=sum(len(r["points"]) for r in rings)
   length=[len(r["points"]) for r in rings]
   details[p["composition_part"]]={"vertices":points,"ringCount":len(rings),
     "ringsUnder3":sum(n<3 for n in length),"ringsExactly3":sum(n==3 for n in length),
     "ringLongerThan8":sum(n>8 for n in length),"largestRing":max(length,default=0),
     "verticesInSmallRings":sum(n for n in length if n<=3),
     "verticesInLargeRings":sum(n for n in length if n>8)}
  result[case]={"totalVertices":sum(x["vertices"] for x in details.values()),
   "ownersByVertexCount":dict(sorted(details.items(),key=lambda kv:-kv[1]["vertices"]))}
 return result
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();v=run(a.input);a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(v,indent=2)+"\n")
 print(json.dumps({k:{"total":v["totalVertices"],
    "topOwners":[[name,d["vertices"],d["ringCount"],d["verticesInSmallRings"]] for name,d in list(v["ownersByVertexCount"].items())[:6]]} for k,v in v.items()}))
