"""Signed Stage8 ring conservative collinear replay. Research only."""
import json,argparse,hashlib
from pathlib import Path
import cv2,numpy as np

def linear(a,b,c):
 return (b[0]-a[0])*(c[1]-b[1])==(b[1]-a[1])*(c[0]-b[0])
def candidate(ring):
 if len(ring)<4:return None
 for i in range(len(ring)):
  a,b,c=ring[i-1],ring[i],ring[(i+1)%len(ring)]
  if linear(a,b,c) and ((b[0]-a[0])*(b[0]-c[0])+(b[1]-a[1])*(b[1]-c[1]))<=0:
   out=ring[:i]+ring[i+1:]
   if len(out)>=3:return i,out
 return None
def raster(rings):
 # Diagnostic ring-native outline and winding not a trusted owner fill replay.
 out=np.zeros((340,340),np.uint8)
 for r in rings:
  if len(r)>=2:cv2.polylines(out,[np.asarray(r,np.int32)],True,1,1,cv2.LINE_8)
  elif r:out[int(r[0][1]),int(r[0][0])]=1
 return out
def verify(root):
 result={"schema":"stage8-collinear-replay-v1","production":"UNCHANGED","golden":"HOLD","cases":{}}
 for case in ("GC001","Raden"):
  p=root/case/"phase8_adaptive_source_contour_research.json"
  data=json.loads(p.read_text(encoding="utf-8"))
  parts=data["primitives_back_to_front"]
  records=[];approved=0;total=0
  for part in parts:
   role=part["composition_part"]
   rings=[x["points"] for x in part["parameters"]["rings"]]
   original=raster(rings)
   for idx,ring in enumerate(rings):
    attempt=candidate(ring)
    if attempt is None:continue
    total+=1;i,reduced=attempt
    update=rings.copy();update[idx]=reduced
    proposed=raster(update)
    changed=int(np.count_nonzero(original!=proposed))
    # No trust in line-only checks for owner fill, interior, topology, and DPR4.
    records.append({"owner":role,"ringIndex":idx,"vertexIndex":i,
       "outlinePixelDelta":changed,"lineRasterSame":changed==0,
       "sourceOwnerFillVerified":False,"topologyVerified":False,
       "safeToRemove":False})
  result["cases"][case]={"originalSha256":hashlib.sha256(p.read_bytes()).hexdigest(),
   "triedRingCandidates":total,"outlineCompatible":sum(v["lineRasterSame"] for v in records),
   "outlineIncompatible":sum(not v["lineRasterSame"] for v in records),
   "confirmedSafeRemovals":0,"candidates":records}
 return result
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=Path,required=True);a.add_argument("--out",type=Path,required=True)
 x=a.parse_args();result=verify(x.root);x.out.parent.mkdir(parents=True,exist_ok=True)
 x.out.write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({k:{f:v[f] for f in ("triedRingCandidates","outlineCompatible","outlineIncompatible","confirmedSafeRemovals")} for k,v in result["cases"].items()}))
