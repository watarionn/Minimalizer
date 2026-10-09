"""Signed Stage8 single micro-ring deletion negative-control.
Only evaluates rings in owners whose baseline OpenCV raster EXACTLY matches original signed owner mask.
Never edits original data or certifies output for production.
"""
import argparse,hashlib,json
from pathlib import Path
import cv2,numpy as np
def raster(rings):
 out=np.zeros((340,340),np.uint8)
 for ring in sorted(rings,key=lambda r:r["depth"]):
  pts=np.asarray(ring["points"],np.int32).reshape(-1,1,2)
  cv2.drawContours(out,[pts],-1,1 if ring["depth"]%2==0 else 0,-1,cv2.LINE_8)
 return out
def audit(stage_dir,masks_dir,manifest_path):
 manifest=json.loads(manifest_path.read_text())
 result={"schema":"signed-stage8-micro-single-delete-v1","production":"UNCHANGED","safeDeletionApproved":0,"cases":{}}
 for case in ("GC001","Raden"):
  stage=stage_dir/f"{case}_stage8_signed.json"
  obj=json.loads(stage.read_text())
  if obj["original_source_sha256"]!=manifest[case]["signedSourceSha"]:raise ValueError("unsigned Stage8")
  summary={"baselineOwnerExact":0,"candidateRingsOnExactOwners":0,
      "singleDeletionMaskExact":0,"rejectedOrUnverified":0,"byOwner":{}}
  for owner in obj["primitives_back_to_front"]:
   role=owner["composition_part"];label="unknown" if role=="__unbound__" else role
   file=masks_dir/f"{case}_{label}_visible.bin"
   if label not in manifest[case]["ownerMasksSha"]:continue
   b=file.read_bytes()
   if hashlib.sha256(b).hexdigest()!=manifest[case]["ownerMasksSha"][label]:
    raise ValueError("signed owner mask changed")
   true=np.frombuffer(b,np.uint8).reshape(340,340)
   rings=owner["parameters"]["rings"]
   baseline=raster(rings)
   exact=bool(np.array_equal(true,baseline))
   micro=[j for j,r in enumerate(rings) if len(r["points"])<=2]
   proven=0
   if exact:
    summary["baselineOwnerExact"]+=1
    summary["candidateRingsOnExactOwners"]+=len(micro)
    for j in micro:
     if np.array_equal(true,raster(rings[:j]+rings[j+1:])):proven+=1
   summary["singleDeletionMaskExact"]+=proven
   summary["rejectedOrUnverified"]+=len(micro)-proven
   summary["byOwner"][role]={"baselineExact":exact,"microCandidates":len(micro),
        "pixelExactAfterSingleDeletion":proven,"baselineDifferentPixels":int(np.count_nonzero(true!=baseline))}
  result["cases"][case]=summary
 return result
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--stage",type=Path,required=True)
 p.add_argument("--masks",type=Path,required=True);p.add_argument("--manifest",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 data=audit(a.stage,a.masks,a.manifest)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(data,indent=2)+"\n")
 print(json.dumps({c:{k:v for k,v in data["cases"][c].items() if k!="byOwner"} for c in data["cases"]}))
