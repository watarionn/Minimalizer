"""Validate Stage8 official single-draw owner replay against source-alpha-visible signed masks.
Opaque ownership is (canonical contour pixels AND original source alpha>0).
Fail closed on any SHA or pixel discrepancy. Research-only.
"""
import argparse,json,hashlib
from pathlib import Path
from PIL import Image
import cv2,numpy as np
from stage8_official_polygon_replay import official_mirror
def verify(stage_dir,source_dir,owner_dir,manifest_file):
 manifest=json.loads(Path(manifest_file).read_text())
 result={"schema":"stage8-official-alpha-parity-v1","production":"UNCHANGED","golden":"HOLD","cases":{}}
 for case in ("GC001","Raden"):
  sf=Path(source_dir)/f"{case}_source.png"
  payload=sf.read_bytes()
  if hashlib.sha256(payload).hexdigest()!=manifest[case]["signedSourceSha"]:
   raise ValueError("original source SHA mismatch")
  alpha=np.asarray(Image.open(sf).convert("RGBA"))[:,:,3]>0
  stage=Path(stage_dir)/f"{case}_stage8_signed.json"
  obj=json.loads(stage.read_text())
  if obj["original_source_sha256"]!=manifest[case]["signedSourceSha"] or len(obj["primitives_back_to_front"])!=11:
   raise ValueError("Stage8 signed evidence absent")
  owners={}
  for part in obj["primitives_back_to_front"]:
   role=part["composition_part"].replace("__unbound__","unknown")
   signed_file=Path(owner_dir)/f"{case}_{role}_visible.bin"
   b=signed_file.read_bytes()
   if len(b)!=340*340:raise ValueError("signed mask dimensions")
   if role in manifest[case]["ownerMasksSha"] and hashlib.sha256(b).hexdigest()!=manifest[case]["ownerMasksSha"][role]:
    raise ValueError("signed owner checksum")
   mask=np.frombuffer(b,np.uint8).reshape(340,340)>0
   official=official_mirror(part)
   predicted=official & alpha
   discrepancy=int(np.count_nonzero(predicted!=mask))
   owners[role]={"rawOwnerPixels":int(official.sum()),"transparentOwnerPixels":int((official&~alpha).sum()),
      "visiblePixels":int(predicted.sum()),"differingPixels":discrepancy,"exact":discrepancy==0}
  if len(owners)!=11:raise ValueError("duplicate owner")
  result["cases"][case]={"owners":owners,"exactOwners":sum(v["exact"] for v in owners.values()),
    "allOwnerVisibleMasksExact":all(v["exact"] for v in owners.values()),
    "safeVerticesApproved":0,"stage8Budget":"HOLD"}
 return result
if __name__=="__main__":
 p=argparse.ArgumentParser()
 for flag in ("stage","sources","masks","manifest","out"):p.add_argument("--"+flag,required=True,type=Path)
 a=p.parse_args();report=verify(a.stage,a.sources,a.masks,a.manifest)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({k:{"exactOwners":v["exactOwners"],"allExact":v["allOwnerVisibleMasksExact"],
  "transparentRolePixels":{r:o["transparentOwnerPixels"] for r,o in v["owners"].items() if o["transparentOwnerPixels"]}}
  for k,v in report["cases"].items()}))
