from __future__ import annotations
import argparse,itertools,json,subprocess,sys
from pathlib import Path
from PIL import Image
import numpy as np
def silhouette(base,candidate):
    a=np.asarray(Image.open(base).convert("RGB"));b=np.asarray(Image.open(candidate).convert("RGB"));bg=a[0,0];ma=np.any(a!=bg,axis=2);mb=np.any(b!=bg,axis=2);u=np.logical_or(ma,mb).sum();return 1.0 if u==0 else float(np.logical_and(ma,mb).sum()/u)
def main():
    p=argparse.ArgumentParser();p.add_argument("--simplification",type=Path,required=True);p.add_argument("--baseline",type=Path,required=True);p.add_argument("--points",type=Path,nargs="+",required=True);p.add_argument("--out-dir",type=Path,required=True);x=p.parse_args();x.out_dir.mkdir(parents=True,exist_ok=True);rows=[]
    composer=Path(__file__).with_name("compose_polygon_candidates.py")
    for n in range(1,len(x.points)+1):
        for combo in itertools.combinations(x.points,n):
            name="_".join(q.stem for q in combo);out=x.out_dir/f"{name}.png"
            q=subprocess.run([sys.executable,str(composer),"--simplification",str(x.simplification),"--baseline",str(x.baseline),"--points",*[str(v) for v in combo],"--output",str(out)],capture_output=True,text=True)
            if q.returncode==0:rows.append({"points":[v.name for v in combo],"silhouette_iou":silhouette(x.baseline,out),"output":str(out)})
    rows.sort(key=lambda r:(-r["silhouette_iou"],-len(r["points"])))
    print(json.dumps(rows,indent=2));(x.out_dir/"subsets.json").write_text(json.dumps(rows,indent=2),encoding="utf8")
if __name__=="__main__":main()
