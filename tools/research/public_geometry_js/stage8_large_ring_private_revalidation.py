"""Private output only: SHA-frozen exact raster Stage8 large-ring reduction validation.
Never overwrite original signed Stage8 scene; keep all source owner and face policies.
"""
import argparse,hashlib,json
from pathlib import Path
import cv2,numpy as np
from stage8_large_ring_exact_reducer import reduce_owner
from stage8_official_polygon_replay import official_mirror

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def topology(a):
 n,_=cv2.connectedComponents(a.astype(np.uint8),connectivity=8)
 contours,h=cv2.findContours(a.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
 return (int(n-1),None if h is None else h.tolist())
def run(root,out,per_owner_trials=8000):
 out.mkdir(parents=True,exist_ok=True)
 summary={"schema":"stage8-large-ring-private-revalidation-v1","golden":"HOLD","production":"UNCHANGED","cases":{}}
 for case,cap in (("GC001",1887),("Raden",1412)):
  f=root/case/"phase8_adaptive_source_contour_research.json"
  doc=json.loads(f.read_text(encoding="utf-8"))
  if doc.get("research_only") is not True or doc.get("no_new_material_or_owner") is not True:
   raise ValueError("unsigned source study")
  originals=doc["primitives_back_to_front"]
  if len(originals)!=11:raise ValueError("eleven owners required")
  candidate=json.loads(json.dumps(doc))
  report={"originalSha256":digest(f),"originalVertices":0,"candidateVertices":0,"sourceMaskDiff":0,"topologyMismatch":0,"ownerEvidence":{}}
  for i,owner in enumerate(originals):
   original_mask=official_mirror(owner)
   metrics,rings=reduce_owner(owner,max_trials=per_owner_trials)
   proposed=dict(owner,parameters=dict(owner["parameters"],rings=rings))
   result_mask=official_mirror(proposed)
   delta=int(np.count_nonzero(original_mask!=result_mask))
   if delta or topology(original_mask)!=topology(result_mask):raise ValueError("source owner parity failure")
   if proposed["primitive_id"]!=owner["primitive_id"] or proposed["palette_color_rgb"]!=owner["palette_color_rgb"] or proposed["composition_part"]!=owner["composition_part"]:
    raise ValueError("provenance drift")
   candidate["primitives_back_to_front"][i]=proposed
   report["originalVertices"]+=metrics["startVertices"]
   report["candidateVertices"]+=metrics["endVertices"]
   report["ownerEvidence"][owner["composition_part"]]={"before":metrics["startVertices"],
    "after":metrics["endVertices"],"trials":metrics["trials"],
    "rawMaskSha256":hashlib.sha256(original_mask.astype(np.uint8).tobytes()).hexdigest(),
    "pixelDifference":delta,"topologyExact":True}
  if report["originalVertices"]!={"GC001":3604,"Raden":2370}[case]:raise ValueError("source total mismatch")
  if report["candidateVertices"]>=report["originalVertices"]:raise ValueError("no reduction")
  report["removedVertices"]=report["originalVertices"]-report["candidateVertices"]
  report["historicVertexCap"]=cap
  report["withinHistoricBudget"]=report["candidateVertices"]<=cap
  (out/f"{case}_stage8_candidate_PRIVATE.json").write_text(json.dumps(candidate,ensure_ascii=False,separators=(",",":")))
  report["candidateSha256"]=digest(out/f"{case}_stage8_candidate_PRIVATE.json")
  summary["cases"][case]=report
 (out/"stage8_large_ring_revalidation.json").write_text(json.dumps(summary,indent=2)+"\n")
 print(json.dumps({k:{"original":v["originalVertices"],"candidate":v["candidateVertices"],
   "removed":v["removedVertices"],"budgetPass":v["withinHistoricBudget"]} for k,v in summary["cases"].items()}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 p.add_argument("--trials",type=int,default=8000);a=p.parse_args();run(a.source,a.out,a.trials)
