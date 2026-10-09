"""Research-only conservative topology and source-ring counterfactual.
Only independently signed original-source masks with SHA matching may be used.
"""
from pathlib import Path
import json,hashlib,argparse
import numpy as np,cv2
from PIL import Image
from stage8_official_polygon_replay import official_mirror

def evaluate(stage,sources,masks,manifest):
 auth=json.loads(manifest.read_text())
 out={"schema":"source-ring-micro-topology-gate-v1","cases":{},"production":"UNCHANGED","golden":"HOLD"}
 for case in ("GC001","Raden"):
  f=sources/f"{case}_source.png"
  if hashlib.sha256(f.read_bytes()).hexdigest()!=auth[case]["signedSourceSha"]:raise ValueError("source SHA")
  rgba=np.asarray(Image.open(f).convert("RGBA"))
  scene=json.loads((stage/f"{case}_stage8_signed.json").read_text())
  if scene["original_source_sha256"]!=auth[case]["signedSourceSha"]:raise ValueError("stage source")
  alpha=rgba[:,:,3]>0
  result={"owners":{},"originalVertices":0,"proposedRemovedVertices":0,"candidateRingCount":0,"pixelParityOwners":0}
  for p in scene["primitives_back_to_front"]:
   role=p["composition_part"].replace("__unbound__","unknown")
   m=masks/f"{case}_{role}_visible.bin"
   payload=m.read_bytes()
   if len(payload)!=340*340 or (role in auth[case]["ownerMasksSha"] and hashlib.sha256(payload).hexdigest()!=auth[case]["ownerMasksSha"][role]):
    raise ValueError("signed mask")
   truth=np.frombuffer(payload,np.uint8).reshape(340,340).astype(bool)
   rings=p["parameters"]["rings"]
   current=official_mirror(p)
   if role in auth[case]["ownerMasksSha"] and not np.array_equal(current&alpha,truth):raise ValueError("baseline mismatch")
   result["originalVertices"]+=sum(len(r["points"]) for r in rings)
   keep=[]
   for index,r in enumerate(rings):
    if len(r["points"])>2:continue
    trial=dict(p,parameters=dict(p["parameters"],rings=rings[:index]+rings[index+1:]))
    if np.array_equal(official_mirror(trial),current):keep.append(index)
   removed=[r for i,r in enumerate(rings) if i not in set(keep)]
   trial=dict(p,parameters=dict(p["parameters"],rings=removed))
   raw=official_mirror(trial)
   unchanged=bool(np.array_equal(raw,current))
   if not unchanged:raise ValueError("combined raw raster mismatch")
   # Topology on a raster follows from exact pixel equality; count explicitly as a witness.
   components, _=cv2.connectedComponents(current.astype(np.uint8),connectivity=8)
   components_new, _=cv2.connectedComponents(raw.astype(np.uint8),connectivity=8)
   if components!=components_new:raise ValueError("components changed")
   original_holes=cv2.findContours(current.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[1]
   after_holes=cv2.findContours(raw.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[1]
   if not np.array_equal(original_holes,after_holes):raise ValueError("hole hierarchy changed")
   count=sum(len(rings[i]["points"]) for i in keep)
   result["proposedRemovedVertices"]+=count
   result["candidateRingCount"]+=len(keep)
   result["pixelParityOwners"]+=1
   result["owners"][role]={"ringIndices":keep,"removedVertices":count,"rawMaskDiff":0,
      "visibleMaskDiff":0,"connectedComponents":int(components-1),"topologyExact":True,
      "safeProduction":False}
  out["cases"][case]=result
 return out

if __name__=="__main__":
 p=argparse.ArgumentParser()
 for key in ("stage","sources","masks","manifest","out"):p.add_argument("--"+key,type=Path,required=True)
 a=p.parse_args();ans=evaluate(a.stage,a.sources,a.masks,a.manifest)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(ans,indent=2)+"\n")
 print(json.dumps({k:{"removedVertices":v["proposedRemovedVertices"],"candidateRings":v["candidateRingCount"],"exactOwners":v["pixelParityOwners"]} for k,v in ans["cases"].items()}))
