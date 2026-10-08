"""GC001 goggles: local feature proposal with independent source evidence gates.

Produces lens/frame *candidate masks* using GrabCut seeds in observed head ROI,
NOT verified part labels; never exports inferred goggle SVG or alters hair.
"""
import argparse,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import load_assets,sha256
from semantic_art_mixer_v3_source_masks import load_observed_masks

# Separate conservative windows around visibly plausible left lens,
# right lens and frame. Spatial prompts are only investigation cues.
WINDOWS={"left_lens":(108,48,150,89),"right_lens":(145,36,196,70),
         "frame":(104,37,197,98)}
def proposals(image):
 rgb=np.asarray(image.convert("RGB"))
 output={}
 for name,(x0,y0,x1,y1) in WINDOWS.items():
  # 4 class GrabCut initialization: outer pixels definite background,
  # center probable foreground. No semantic certainty from rectangle.
  region=np.zeros(rgb.shape[:2],dtype=np.uint8)
  region[y0:y1,x0:x1]=cv2.GC_PR_FGD
  region[max(0,y0-4):min(340,y1+4),max(0,x0-4):min(340,x1+4)]=cv2.GC_PR_BGD
  region[y0:y1,x0:x1]=cv2.GC_PR_FGD
  region[y0+3:y1-3,x0+3:x1-3]=cv2.GC_FGD
  bg=np.zeros((1,65),np.float64);fg=np.zeros((1,65),np.float64)
  cv2.setRNGSeed(419)
  cv2.grabCut(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),region,None,bg,fg,3,cv2.GC_INIT_WITH_MASK)
  mask=np.isin(region,[cv2.GC_FGD,cv2.GC_PR_FGD])
  output[name]=mask
 return output
def main():
 p=argparse.ArgumentParser()
 for k in ("root","out"):p.add_argument("--"+k,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 src,_,_=load_assets(a.root);masks,_=load_observed_masks()
 proposals_by_name=proposals(src)
 rgb=np.asarray(src.convert("RGB"))
 board=Image.new("RGB",(1360,399),"#eee")
 board.paste(src.convert("RGB"),(0,0))
 draw=ImageDraw.Draw(board)
 draw.text((8,360),"SOURCE",fill="#223322")
 records=[]
 for i,(name,mask) in enumerate(proposals_by_name.items(),1):
  out=rgb.copy()
  out[~mask]=(out[~mask]*0.35).astype(np.uint8)
  board.paste(Image.fromarray(out),(i*340,0))
  draw.text((i*340+8,360),name.upper()+" / UNVERIFIED",fill="#223322")
  Image.fromarray(mask.astype(np.uint8)*255).save(a.out/(name+"_proposal.png"))
  n,label,stats,_=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
  overlaps={part:int((mask&masks[part]).sum()) for part in ("hair","face","accessory_or_held_object")}
  records.append({"name":name,"proposed_pixels":int(mask.sum()),
    "existing_part_overlaps":overlaps,
    "connected_components":int(n-1),
    "source_window_xyxy":list(WINDOWS[name])})
 board.save(a.out/"goggle_component_proposals.png",optimize=True)
 report={"status":"CANDIDATES_NOT_VERIFIED","proposals":records,
    "semantic_goggle_labels_verified":False,"goggle_svg_produced":False,
    "hair_mask_modified":False,"golden_pass":False,
    "files":[{"name":x.name,"sha256":sha256(x)} for x in sorted(a.out.iterdir()) if x.is_file()]}
 (a.out/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"proposals":records}))
if __name__=="__main__":main()
