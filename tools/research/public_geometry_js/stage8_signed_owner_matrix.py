"""Research-only 11-owner signed Stage8 renderer strategy matrix.
Independent signed source-visible owner mask MUST be supplied.
No owner deletion, production promotion or semantic inference.
"""
import argparse,json,hashlib
from pathlib import Path
import cv2,numpy as np
MODES=("depthsorted_role","depthsorted_depth","original_role","original_depth",
 "reverse_role","reverse_depth","depthsorted_reverse_role","depthsorted_reverse_depth")

def render(rings,mode):
 canvas=np.zeros((340,340),np.uint8)
 items=list(enumerate(rings))
 if "depthsorted" in mode:items.sort(key=lambda v:(v[1].get("depth",0),v[0]))
 if "reverse" in mode:items.reverse()
 for _,ring in items:
  points=ring.get("points",[])
  if not points:continue
  vertices=np.asarray(points,np.int32).reshape(-1,1,2)
  hole=(ring.get("role")=="hole") if "role" in mode else ring.get("depth",0)%2==1
  fill=0 if hole else 1
  if len(vertices)==1:
   x,y=vertices[0,0]
   if 0<=x<340 and 0<=y<340:canvas[y,x]=fill
  else:cv2.drawContours(canvas,[vertices],-1,fill,-1,cv2.LINE_8)
 return canvas

def compare(root,mask_dir):
 out={"schema":"stage8-signed-11-owner-renderer-matrix-v1","production":"UNCHANGED","golden":"HOLD","cases":{}}
 for case in ("GC001","Raden"):
  doc=root/f"{case}_stage8_signed.json"
  scene=json.loads(doc.read_text())
  if len(scene["primitives_back_to_front"])!=11:raise ValueError("not eleven owners")
  exact={mode:0 for mode in MODES};owners={}
  for part in scene["primitives_back_to_front"]:
   role=part["composition_part"].replace("__unbound__","unknown")
   f=mask_dir/f"{case}_{role}_visible.bin"
   binary=f.read_bytes()
   if len(binary)!=340*340:raise ValueError("source-visible mask dimensions")
   mask=np.frombuffer(binary,np.uint8).reshape(340,340)
   if not np.isin(mask,[0,1]).all():raise ValueError("binary mask required")
   options={}
   for mode in MODES:
    candidate=render(part["parameters"]["rings"],mode)
    outside=int(np.count_nonzero((candidate==1)&(mask==0)))
    missing=int(np.count_nonzero((candidate==0)&(mask==1)))
    options[mode]={"outside":outside,"missing":missing,"difference":outside+missing}
    exact[mode]+=int(outside+missing==0)
   best=min(MODES,key=lambda m:(options[m]["difference"],m))
   owners[role]={"sourceMaskSha256":hashlib.sha256(binary).hexdigest(),
      "bestMode":best,"bestDifference":options[best]["difference"],
      "options":options}
  out["cases"][case]={"signedStage8Sha256":hashlib.sha256(doc.read_bytes()).hexdigest(),
     "exactOwnersByMode":exact,"bestPerOwnerExact":sum(v["bestDifference"]==0 for v in owners.values()),
     "owners":owners,"releaseEligible":False}
 return out

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--stage",type=Path,required=True)
 p.add_argument("--masks",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();result=compare(a.stage,a.masks)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({c:{"bestPerOwnerExact":v["bestPerOwnerExact"],"exactOwnersByMode":v["exactOwnersByMode"]} for c,v in result["cases"].items()}))
