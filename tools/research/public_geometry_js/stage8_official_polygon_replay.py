"""Research-only independent mirror of the official SA10.34 polygon raster contract.
Source: minimalizer_zerobase/composition/semantic.py::rasterize_primitive_candidate
Never changes source rings and never authorizes budget/production gate.
"""
import argparse,hashlib,json
from pathlib import Path
import cv2,numpy as np

def official_mirror(part):
 rings=part["parameters"]["rings"]
 normalized=[]
 for index,ring in enumerate(rings):
  depth=ring.get("depth",-1)
  if not isinstance(depth,int) or depth<0 or ring.get("role")!=("fill" if depth%2==0 else "hole"):
   raise ValueError("unsigned ring hierarchy")
  points=np.asarray(ring.get("points"),dtype=np.float64)
  if points.ndim!=2 or points.shape[1]!=2 or not len(points) or not np.isfinite(points).all():
   raise ValueError("invalid signed ring")
  normalized.append((depth,index,np.rint(points).astype(np.int32).reshape(-1,1,2)))
 ordered=[v[2] for v in sorted(normalized,key=lambda x:(x[0],x[1]))]
 canvas=np.zeros((340,340),np.uint8)
 cv2.drawContours(canvas,ordered,-1,255,thickness=cv2.FILLED,lineType=cv2.LINE_8)
 return canvas>0

def evaluate(scene_dir,mask_dir,manifest):
 source=json.loads(Path(manifest).read_text())
 output={"schema":"stage8-official-single-draw-owner-parity-v1","production":"UNCHANGED","golden":"HOLD","cases":{}}
 for case in ("GC001","Raden"):
  scene_file=Path(scene_dir)/f"{case}_stage8_signed.json"
  scene=json.loads(scene_file.read_text())
  if scene.get("original_source_sha256")!=source[case]["signedSourceSha"]:
   raise ValueError("source provenance mismatch")
  if len(scene["primitives_back_to_front"])!=11:raise ValueError("missing source owner")
  results={}
  for part in scene["primitives_back_to_front"]:
   raw=part["composition_part"]
   role="unknown" if raw=="__unbound__" else raw
   maskfile=Path(mask_dir)/f"{case}_{role}_visible.bin"
   b=maskfile.read_bytes()
   if hashlib.sha256(b).hexdigest()!=source[case]["ownerMasksSha"][role] or len(b)!=340*340:
    raise ValueError("unsigned source mask")
   signed=np.frombuffer(b,np.uint8).reshape(340,340)
   if not np.isin(signed,[0,1]).all():raise ValueError("invalid mask values")
   observed=official_mirror(part)
   outside=int(np.count_nonzero(observed & ~signed.astype(bool)))
   missing=int(np.count_nonzero((~observed)& signed.astype(bool)))
   results[role]={"outside":outside,"missing":missing,"exact":outside+missing==0,
      "signedMaskSha256":hashlib.sha256(b).hexdigest(),"rings":len(part["parameters"]["rings"])}
  output["cases"][case]={"owners":results,"exactOwnerCount":sum(v["exact"] for v in results.values()),
    "allOwnersExact":all(v["exact"] for v in results.values()),
    "signedStage8Sha256":hashlib.sha256(scene_file.read_bytes()).hexdigest(),
    "sourceRingBudget":"HOLD","microDeletionAuthorized":False}
 return output
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--stage",type=Path,required=True);p.add_argument("--masks",type=Path,required=True)
 p.add_argument("--manifest",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();v=evaluate(a.stage,a.masks,a.manifest)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(v,indent=2)+"\n")
 print(json.dumps({case:{"exactOwners":x["exactOwnerCount"],"allExact":x["allOwnersExact"],
    "mismatches":{k:v["outside"]+v["missing"] for k,v in x["owners"].items() if not v["exact"]}}
    for case,x in v["cases"].items()}))
