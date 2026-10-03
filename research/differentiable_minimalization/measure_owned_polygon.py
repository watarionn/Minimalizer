from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from minimalizer_zerobase.refine.semantic_ownership import evaluate_ownership_retention

def raster(points,size):
    im=Image.new("1",size,0); ImageDraw.Draw(im).polygon([tuple(map(float,p)) for p in points],fill=1); return np.asarray(im,dtype=bool)

def main():
    p=argparse.ArgumentParser();p.add_argument("--simplification",type=Path,required=True);p.add_argument("--primitive-index",type=int,default=9);p.add_argument("--candidate-points",type=Path,required=True);p.add_argument("--width",type=int,default=340);p.add_argument("--height",type=int,default=340);a=p.parse_args()
    d=json.loads(a.simplification.read_text(encoding="utf8"));c=next(x for x in d["candidates"] if x["name"]==d["selected_name"]);prim=c["primitives"][a.primitive_index];ref=prim["parameters"]["components"][0];cand=json.loads(a.candidate_points.read_text())["points"]
    r=evaluate_ownership_retention({prim["composition_part"]:raster(ref,(a.width,a.height))},{prim["composition_part"]:raster(cand,(a.width,a.height))},critical_parts=(prim["composition_part"],),minimum_iou=.985)
    print(json.dumps({"part":prim["composition_part"],"iou":r.per_part_iou[prim["composition_part"]],"passed":r.passed,"reasons":r.reasons},indent=2))
if __name__=="__main__":main()
