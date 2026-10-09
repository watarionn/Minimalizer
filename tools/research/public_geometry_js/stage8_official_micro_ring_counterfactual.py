"""Research-only exact Stage8 tiny-ring deletion counterfactual.
Official OpenCV even-odd contour replay; strict source SHA, signed mask and alpha.
Saves only count/index evidence; does not mutate the original Stage8 file.
"""
from pathlib import Path
import argparse, hashlib, json
import cv2, numpy as np
from PIL import Image
from stage8_official_polygon_replay import official_mirror

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(stage,sources,masks,manifest):
 out={"schema":"stage8-tiny-ring-official-parity-v1","golden":"HOLD","production":"UNCHANGED","cases":{}}
 info=json.loads(manifest.read_text())
 for case in ("GC001","Raden"):
  scene_file=stage/f"{case}_stage8_signed.json"; source=sources/f"{case}_source.png"
  obj=json.loads(scene_file.read_text()); signed=info[case]["signedSourceSha"]
  if sha(source)!=signed or obj["original_source_sha256"]!=signed:raise ValueError("original authority mismatch")
  alpha=np.asarray(Image.open(source).convert("RGBA"))[:,:,3]>0
  if alpha.shape!=(340,340) or len(obj["primitives_back_to_front"])!=11:raise ValueError("wrong scene")
  totals={"candidates":0,"individuallyExact":0,"combinedExactOwners":0,
          "combinedChangedPixels":0,"removedVertices":0}
  evidence={}
  for owner in obj["primitives_back_to_front"]:
   name=owner["composition_part"].replace("__unbound__","unknown")
   signed_mask_file=masks/f"{case}_{name}_visible.bin"
   if name not in info[case]["ownerMasksSha"] or sha(signed_mask_file)!=info[case]["ownerMasksSha"][name]:
    raise ValueError("signed visible owner mask checksum")
   expected=np.frombuffer(signed_mask_file.read_bytes(),np.uint8).reshape(340,340)>0
   original=official_mirror(owner)&alpha
   if not np.array_equal(original,expected):raise ValueError("baseline original must be pixel exact")
   rings=owner["parameters"]["rings"];chosen=[]
   for i,ring in enumerate(rings):
    if len(ring["points"])>2:continue
    totals["candidates"]+=1
    candidate=dict(owner,parameters=dict(owner["parameters"],
                        rings=rings[:i]+rings[i+1:]))
    if np.array_equal(official_mirror(candidate)&alpha,expected):
     chosen.append(i);totals["individuallyExact"]+=1
   all_candidate=dict(owner,parameters=dict(owner["parameters"],
                        rings=[ring for i,ring in enumerate(rings) if i not in set(chosen)]))
   after=official_mirror(all_candidate)&alpha
   difference=int(np.count_nonzero(after!=expected))
   totals["combinedChangedPixels"]+=difference
   totals["combinedExactOwners"]+=int(difference==0)
   removed=sum(len(rings[i]["points"]) for i in chosen)
   if difference==0:totals["removedVertices"]+=removed
   evidence[name]={"individualSafeRingIndices":chosen,"individuallyRemovableVertices":removed,
                   "combinedPixelDelta":difference,"remainingRingCount":len(rings)-len(chosen)}
  out["cases"][case]={"summary":totals,"ownerEvidence":evidence,
    "sourceRingBudget":"HOLD","sourceSceneModified":False,
    "humanGolden":"PENDING","safeForProduction":False}
 return out

if __name__=="__main__":
 p=argparse.ArgumentParser()
 for k in ("stage","sources","masks","manifest","out"):p.add_argument("--"+k,required=True,type=Path)
 a=p.parse_args(); result=verify(a.stage,a.sources,a.masks,a.manifest)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({k:v["summary"] for k,v in result["cases"].items()}))
