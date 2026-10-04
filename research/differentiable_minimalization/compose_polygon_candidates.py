from __future__ import annotations
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw

def main():
    a=argparse.ArgumentParser();a.add_argument("--simplification",type=Path,required=True);a.add_argument("--baseline",type=Path,required=True);a.add_argument("--points",type=Path,nargs="*",default=[]);a.add_argument("--output",type=Path,required=True);x=a.parse_args()
    d=json.loads(x.simplification.read_text(encoding="utf8")); c=next(v for v in d["candidates"] if v["name"]==d["selected_name"])
    replacements={}
    for path in x.points:
        z=json.loads(path.read_text(encoding="utf8")); replacements[z["primitive_id"]]=z["points"]
    base=Image.open(x.baseline).convert("RGB"); bg=base.getpixel((0,0)); image=Image.new("RGB",base.size,bg); draw=ImageDraw.Draw(image)
    for p in sorted(c["primitives"],key=lambda q:q["raster_index"]):
        fill=tuple(int(v) for v in p["palette_color_rgb"])
        for j,component in enumerate(p.get("parameters",{}).get("components",[])):
            pts=replacements[p["primitive_id"]] if p["primitive_id"] in replacements and j==0 else component
            if len(pts)>=3: draw.polygon([tuple(map(float,q)) for q in pts],fill=fill)
        for hole in p.get("parameters",{}).get("holes",[]):
            if len(hole)>=3: draw.polygon([tuple(map(float,q)) for q in hole],fill=bg)
    x.output.parent.mkdir(parents=True,exist_ok=True);image.save(x.output)
    print(json.dumps({"replacements":list(replacements),"output":str(x.output)},indent=2))
if __name__=="__main__":main()
