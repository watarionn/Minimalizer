"""Research-only Stage8 exact-source owner replay diagnostic.
Compare fill strategies against independently signed binary owner masks.
No deletion is authorized by matching a subset or by best-effort similarity.
"""
import json,hashlib,argparse
from pathlib import Path
import numpy as np, cv2

def raster(rings, mode, size=340):
 out=np.zeros((size,size),np.uint8)
 ordered=sorted(enumerate(rings),key=lambda v:(v[1].get("depth",0),v[0]))
 if mode.endswith("reverse"):ordered=list(reversed(ordered))
 for _,ring in ordered:
  points=ring.get("points",[])
  if not points:continue
  pts=np.array(points,np.int32).reshape(-1,1,2)
  hole=ring.get("role")=="hole" if mode.startswith("role") else ring.get("depth",0)%2==1
  if len(points)==1:
   x,y=map(int,points[0])
   if 0<=x<size and 0<=y<size:out[y,x]=int(not hole)
  else:cv2.drawContours(out,[pts],-1,int(not hole),-1,cv2.LINE_8)
 return out

def analyze(input_dir):
 results={}
 for case in ("GC001","Raden"):
  cfg=json.loads((input_dir/case/"phase8_adaptive_source_contour_research.json").read_text())
  owner={}
  for p in cfg["primitives_back_to_front"]:
   rings=p["parameters"]["rings"]
   modes=("depth_order","role_order","depth_reverse","role_reverse")
   owner[p["composition_part"]]={"rings":len(rings),
     "modes":{mode:{"pixels":int(raster(rings,mode).sum()),
                    "sha256":hashlib.sha256(raster(rings,mode).tobytes()).hexdigest()} for mode in modes}}
  results[case]=owner
 return results

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();res=analyze(a.source);a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps({"schema":"stage8-owner-renderer-mode-matrix-v1","researchOnly":True,
    "sourceOwnerMatch":"UNVERIFIED_UNTIL_SIGNED_BASELINE_COMPARISON","cases":res},indent=2)+"\n")
 print(json.dumps({k:len(v) for k,v in res.items()}))
