from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
def mask(path,bg):
    a=np.asarray(Image.open(path).convert("RGB"))
    return np.any(a!=np.asarray(bg,dtype=np.uint8),axis=2)
def main():
    p=argparse.ArgumentParser();p.add_argument("--baseline",type=Path,required=True);p.add_argument("--candidate",type=Path,required=True);x=p.parse_args()
    bg=Image.open(x.baseline).convert("RGB").getpixel((0,0));a=mask(x.baseline,bg);b=mask(x.candidate,bg);u=np.logical_or(a,b).sum()
    aa=np.asarray(Image.open(x.baseline).convert("RGB"));bb=np.asarray(Image.open(x.candidate).convert("RGB"))
    print(json.dumps({"silhouette_iou":1.0 if u==0 else float(np.logical_and(a,b).sum()/u),"changed_pixels":int(np.any(aa!=bb,axis=2).sum())},indent=2))
if __name__=="__main__":main()
