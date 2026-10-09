"""Independently revalidate proposed multi-point reduction against ORIGINAL signed Stage8.
Fail closed for all 11 owners, raw raster, 8-connected components, hole tree,
identity/provenance, unchanged source PNG SHA, and never authorize production.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np, cv2
from stage8_official_polygon_replay import official_mirror

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(original_root,candidate_root):
 out={"schema":"stage8-multipoint-original-parity-v1","cases":{},"production":"UNCHANGED","golden":"HOLD"}
 for case,cap,expected in (("GC001",1887,3604),("Raden",1412,2370)):
  original_path=original_root/case/"phase8_adaptive_source_contour_research.json"
  candidate_path=candidate_root/f"{case}_multi_point_candidate_PRIVATE.json"
  orig=json.loads(original_path.read_text(encoding="utf-8"))
  cand=json.loads(candidate_path.read_text(encoding="utf-8"))
  if orig.get("original_source_sha256")!=cand.get("original_source_sha256"):raise ValueError("source SHA drift")
  a=orig["primitives_back_to_front"];b=cand["primitives_back_to_front"]
  if len(a)!=11 or len(b)!=11:raise ValueError("11 owner count")
  reports={};src_total=dst_total=0
  for x,y in zip(a,b):
   for k in ("primitive_id","composition_part","source_mask_owner","palette_color_rgb","raster_index","structural_support_only"):
    if x.get(k)!=y.get(k):raise ValueError("source provenance changed: "+k)
   left=official_mirror(x);right=official_mirror(y)
   if not np.array_equal(left,right):raise ValueError("whole owner raw pixels changed")
   n1,_=cv2.connectedComponents(left.astype(np.uint8),connectivity=8)
   n2,_=cv2.connectedComponents(right.astype(np.uint8),connectivity=8)
   if n1!=n2:raise ValueError("components changed")
   _,h1=cv2.findContours(left.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
   _,h2=cv2.findContours(right.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
   if not np.array_equal(h1,h2):raise ValueError("hole hierarchy changed")
   role=x["composition_part"]
   old=sum(len(r["points"]) for r in x["parameters"]["rings"])
   new=sum(len(r["points"]) for r in y["parameters"]["rings"])
   if new>old:raise ValueError("vertex count increased")
   src_total+=old;dst_total+=new
   reports[role]={"old":old,"new":new,"saved":old-new,"rawPixelDifference":0,"topologyExact":True}
  if src_total!=expected:raise ValueError("original historical ring count mismatch")
  out["cases"][case]={"originalStage8Sha256":sha(original_path),"candidateSha256":sha(candidate_path),
   "oldVertices":src_total,"candidateVertices":dst_total,"savedVertices":src_total-dst_total,
   "historicCap":cap,"remainingGap":max(0,dst_total-cap),"historicCapPass":dst_total<=cap,
   "allOwnersExact":True,"owners":reports}
 return out

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--original",type=Path,required=True);p.add_argument("--candidate",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True);args=p.parse_args()
 result=audit(args.original,args.candidate);args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({k:{m:v[m] for m in ("oldVertices","candidateVertices","savedVertices","remainingGap","allOwnersExact")} for k,v in result["cases"].items()}))
