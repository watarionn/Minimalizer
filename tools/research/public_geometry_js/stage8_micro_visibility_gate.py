"""Private signed Stage8 micro-ring visibility audit. Coordinates stay private.
Output only aggregate counts. NEVER promotes source vertex deletions.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np

ALIASES={"__unbound__":"unknown"}
def analyze(stage_dir,mask_dir,manifest_path):
 manifest=json.loads(manifest_path.read_text())
 report={"schema":"stage8-micro-owner-visibility-v1","production":"UNCHANGED","golden":"HOLD","cases":{}}
 for case in ("GC001","Raden"):
  original=stage_dir/f"{case}_stage8_signed.json"
  scene=json.loads(original.read_text())
  if scene.get("original_source_sha256")!=manifest[case]["signedSourceSha"]:raise ValueError("original source mismatch")
  parts=scene["primitives_back_to_front"]
  if len(parts)!=11:raise ValueError("missing signed 11 owner layers")
  masks={}
  for role,sha in manifest[case]["ownerMasksSha"].items():
   f=mask_dir/f"{case}_{role}_visible.bin"
   payload=f.read_bytes()
   if hashlib.sha256(payload).hexdigest()!=sha or len(payload)!=340*340:raise ValueError("signed owner mask mismatch")
   masks[role]=np.frombuffer(payload,dtype=np.uint8).reshape((340,340))
   if not np.isin(masks[role],[0,1]).all():raise ValueError("nonbinary signed mask")
  seen=set();count=visible=covered=foreign=0;owners={}
  for layer,p in enumerate(parts):
   role=ALIASES.get(p["composition_part"],p["composition_part"])
   if role in seen or role not in masks and role!="head":raise ValueError("duplicate or unmapped source owner")
   seen.add(role)
   for ring in p["parameters"]["rings"]:
    pts=ring["points"]
    if len(pts)>2:continue
    count+=1
    for x,y in pts:
     x=int(x);y=int(y)
     if not (0<=x<340 and 0<=y<340):raise ValueError("point outside signed image")
     if role not in masks:raise ValueError("unexpected micro point from hidden structural head")
     visible+=int(masks[role][y,x]==1)
     foreign+=int(masks[role][y,x]!=1)
     covered+=int(any(masks[ALIASES.get(q["composition_part"],q["composition_part"])][y,x]==1 for q in parts[layer+1:] if ALIASES.get(q["composition_part"],q["composition_part"]) in masks))
     owners[role]=owners.get(role,0)+1
  report["cases"][case]={"microRings":count,"microVertices":sum(owners.values()),"inOwnSignedMask":visible,
       "outsideOwnSignedMask":foreign,"coveredByLaterOwnerMask":covered,"byOwner":owners,
       "confirmedSafeRemovals":0,"pixelDeletionReplayVerified":False}
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--stage",type=Path,required=True);p.add_argument("--masks",type=Path,required=True)
 p.add_argument("--manifest",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 data=analyze(a.stage,a.masks,a.manifest)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(data,indent=2)+"\n")
 print(json.dumps({k:{"microVertices":v["microVertices"],"outsideOwnSignedMask":v["outsideOwnSignedMask"],"coveredByLaterOwnerMask":v["coveredByLaterOwnerMask"]} for k,v in data["cases"].items()}))
