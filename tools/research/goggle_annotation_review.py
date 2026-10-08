"""Source-viewable goggles annotation evidence sheet, deliberately unverified.

Uses original pixels, and records distinct left/right/frame review zones.
No generated goggle mask, no polygon filled from guesswork, no paint into SVG.
"""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw
from semantic_art_mixer_v1 import sha256
# Review-only boxes, not polygon segmentation.
ZONES={"left_lens":(106,45,150,90),"right_lens":(143,31,197,77),
       "frame":(102,32,201,98)}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 src=Image.open(a.source).convert("RGB")
 if src.size!=(340,340):raise ValueError("Canonical size mismatch")
 board=Image.new("RGB",(1360,399),"#f3f1ee")
 board.paste(src,(0,0))
 d=ImageDraw.Draw(board)
 d.text((8,357),"ORIGINAL",fill="#222")
 for i,(name,box) in enumerate(ZONES.items(),1):
  panel=src.copy();draw=ImageDraw.Draw(panel)
  draw.rectangle(box,outline="#05efae",width=2)
  # Enlarged crop is for visual human boundary review; no replacement image.
  crop=src.crop(box).resize(((box[2]-box[0])*3,(box[3]-box[1])*3),Image.Resampling.NEAREST)
  panel.paste(crop,(340-crop.width-4,340-crop.height-4))
  board.paste(panel,(i*340,0))
  d.text((i*340+8,357),name.upper()+" REVIEW / NOT ANNOTATED",fill="#222")
 board.save(a.out/"goggle_source_annotation_review.png",optimize=True)
 report={"source_sha256":sha256(a.source),"status":"REVIEW_REGIONS_ONLY",
   "review_zones_xyxy":ZONES,"actual_visible_boundaries_annotated":False,
   "source_verified_lens_frame_mask":False,"goggles_svg_generated":False,
   "hold_reason":"rectangular review windows are not source-following semantic polygons",
   "files":[{"name":"goggle_source_annotation_review.png","sha256":sha256(a.out/"goggle_source_annotation_review.png")}]}
 (a.out/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"source_sha256":report["source_sha256"],"zones":report["review_zones_xyxy"]}))
if __name__=="__main__":main()
