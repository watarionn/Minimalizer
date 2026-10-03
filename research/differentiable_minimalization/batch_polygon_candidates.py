from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path

def main():
    a=argparse.ArgumentParser();a.add_argument("--simplification",type=Path,required=True);a.add_argument("--part",required=True);a.add_argument("--target-mask",type=Path,required=True);a.add_argument("--baseline",type=Path,required=True);a.add_argument("--out-dir",type=Path,required=True);x=a.parse_args()
    d=json.loads(x.simplification.read_text(encoding="utf8")); c=next(v for v in d["candidates"] if v["name"]==d["selected_name"])
    x.out_dir.mkdir(parents=True,exist_ok=True); results=[]
    for i,p in enumerate(c["primitives"]):
        if p["composition_part"]!=x.part: continue
        out=x.out_dir/f"{i:03d}.png"; pts=x.out_dir/f"{i:03d}.json"
        cmd=[sys.executable,str(Path(__file__).with_name("refine_phase12_polygon.py")),"--simplification",str(x.simplification),"--target-mask",str(x.target_mask),"--baseline",str(x.baseline),"--output",str(out),"--points-output",str(pts),"--primitive-index",str(i)]
        q=subprocess.run(cmd,text=True,capture_output=True)
        results.append({"index":i,"primitive_id":p["primitive_id"],"feasible":q.returncode==0,"stdout":q.stdout.strip(),"stderr":q.stderr.strip()})
    (x.out_dir/"batch.json").write_text(json.dumps(results,indent=2),encoding="utf8")
    print(json.dumps(results,indent=2))
if __name__=="__main__":main()
