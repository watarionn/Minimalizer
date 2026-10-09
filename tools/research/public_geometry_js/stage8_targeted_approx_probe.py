"""Research-only owner-targeted polygon approximation.
Try OpenCV approxPolyDP epsilon candidates; accept only full official original raster equality.
No source original mutation.
"""
import argparse,json,hashlib
from pathlib import Path
import cv2,numpy as np
from stage8_official_polygon_replay import official_mirror
def run(folder,out):
 out.mkdir(parents=True,exist_ok=True)
 summary={}
 for case in ("GC001","Raden"):
  original=folder/f"{case}_multi_point_candidate_PRIVATE.json"
  doc=json.loads(original.read_text())
  saved=0; owners={}
  for p in doc["primitives_back_to_front"]:
   reference=official_mirror(p)
   rings=p["parameters"]["rings"]
   prior=sum(len(r["points"]) for r in rings)
   candidate=[dict(r,points=list(r["points"])) for r in rings]
   accepted=0
   for idx in sorted(range(len(candidate)),key=lambda i:-len(candidate[i]["points"])):
    ring=candidate[idx];points=ring["points"]
    if len(points)<=3:continue
    for eps in (0.25,0.35,0.45,0.55,0.7,0.9,1.2,1.6):
     approx=cv2.approxPolyDP(np.asarray(points,np.float32).reshape(-1,1,2),eps,True).reshape(-1,2).tolist()
     if len(approx)<3 or len(approx)>=len(points):continue
     test=candidate[:idx]+[dict(ring,points=approx)]+candidate[idx+1:]
     scene=dict(p,parameters=dict(p["parameters"],rings=test))
     if np.array_equal(reference,official_mirror(scene)):
      accepted+=len(points)-len(approx);candidate=test;ring=candidate[idx];points=approx
   if not np.array_equal(reference,official_mirror(dict(p,parameters=dict(p["parameters"],rings=candidate)))):
    raise ValueError("mask parity")
   p["parameters"]["rings"]=candidate
   owners[p["composition_part"]]={"before":prior,"after":prior-accepted,"saved":accepted}
   saved+=accepted
  final=sum(len(r["points"]) for p in doc["primitives_back_to_front"] for r in p["parameters"]["rings"])
  target=out/f"{case}_multi_point_candidate_PRIVATE.json"
  target.write_text(json.dumps(doc,ensure_ascii=False,separators=(",",":")))
  summary[case]={"final":final,"saved":saved,"sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"owners":owners}
 (out/"targeted_approx_metrics.json").write_text(json.dumps(summary,indent=2)+"\n")
 print(json.dumps({k:{"final":v["final"],"saved":v["saved"]} for k,v in summary.items()}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--input",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();run(a.input,a.out)
