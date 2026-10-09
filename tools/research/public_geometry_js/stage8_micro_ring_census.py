"""Signed original Stage8 sub-3-point ring census. No source mutation."""
import argparse,json
from pathlib import Path
def census(root):
 report={}
 for case in ("GC001","Raden"):
  x=json.loads((root/case/"phase8_adaptive_source_contour_research.json").read_text())
  record={}
  for part in x["primitives_back_to_front"]:
   groups=part["parameters"]["rings"]
   singles=[r for r in groups if len(r["points"])==1]
   doubles=[r for r in groups if len(r["points"])==2]
   record[part["composition_part"]]={"onePointRings":len(singles),"twoPointRings":len(doubles),
       "onePointRoles":{t:sum(r.get("role")==t for r in singles) for t in ("fill","hole")},
       "twoPointRoles":{t:sum(r.get("role")==t for r in doubles) for t in ("fill","hole")},
       "totalMicroVertices":len(singles)+2*len(doubles)}
  report[case]=record
 return report
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();v=census(a.root);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(v,indent=2)+"\n")
 print(json.dumps({case:sorted([(owner,s["totalMicroVertices"]) for owner,s in parts.items()],key=lambda x:-x[1])[:5] for case,parts in v.items()}))
