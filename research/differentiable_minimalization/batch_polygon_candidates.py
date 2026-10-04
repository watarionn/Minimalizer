from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

def _preflight(primitive,target,max_vertices,min_mismatch):
    components=primitive.get("parameters",{}).get("components",[])
    if len(components)!=1 or len(components[0])<3:
        return False,"unsupported_component_topology",0,0.0
    vertices=len(components[0])
    points=np.asarray(components[0],dtype=np.float32)
    if vertices>max_vertices:
        return False,"vertex_budget",vertices,0.0
    if len(np.unique(points,axis=0))<3:
        return False,"degenerate_polygon",vertices,0.0
    closed=np.vstack([points,points[:1]])
    if float(np.linalg.norm(np.diff(closed,axis=0),axis=1).sum())<=1e-4:
        return False,"zero_boundary_length",vertices,0.0
    h,w=target.shape
    canvas=Image.new("L",(w,h),0)
    ImageDraw.Draw(canvas).polygon(
        [tuple(map(float,point)) for point in components[0]],fill=255
    )
    mask=np.asarray(canvas,dtype=np.float32)/255.0
    mismatch=float(np.mean((mask-target)**2))
    if mismatch<min_mismatch:
        return False,"low_improvement_headroom",vertices,mismatch
    return True,"scheduled",vertices,mismatch

def main():
    a=argparse.ArgumentParser();a.add_argument("--simplification",type=Path,required=True);a.add_argument("--part",required=True);a.add_argument("--target-mask",type=Path,required=True);a.add_argument("--baseline",type=Path,required=True);a.add_argument("--out-dir",type=Path,required=True);a.add_argument("--max-vertices",type=int,default=96);a.add_argument("--min-mismatch",type=float,default=0.002);a.add_argument("--preflight-only",action="store_true");x=a.parse_args()
    d=json.loads(x.simplification.read_text(encoding="utf8")); c=next(v for v in d["candidates"] if v["name"]==d["selected_name"])
    target=np.asarray(Image.open(x.target_mask).convert("L"),dtype=np.float32)/255.0
    x.out_dir.mkdir(parents=True,exist_ok=True); results=[]
    queue=[]
    for i,p in enumerate(c["primitives"]):
        if p["composition_part"]!=x.part: continue
        scheduled,reason,vertices,mismatch=_preflight(p,target,x.max_vertices,x.min_mismatch)
        base={"index":i,"primitive_id":p["primitive_id"],"scheduled":scheduled,"preflight_reason":reason,"vertex_count":vertices,"initial_mask_mismatch":mismatch}
        if scheduled:
            queue.append((mismatch/max(vertices,1),base))
        else:
            results.append(base)
    queue.sort(key=lambda item:(-item[0],item[1]["vertex_count"],item[1]["index"]))
    for rank,(_,base) in enumerate(queue,1):
        base["schedule_rank"]=rank
        if x.preflight_only:
            results.append(base); continue
        i=base["index"]; out=x.out_dir/f"{i:03d}.png"; pts=x.out_dir/f"{i:03d}.json"
        cmd=[sys.executable,str(Path(__file__).with_name("refine_phase12_polygon.py")),"--simplification",str(x.simplification),"--target-mask",str(x.target_mask),"--baseline",str(x.baseline),"--output",str(out),"--points-output",str(pts),"--primitive-index",str(i)]
        q=subprocess.run(cmd,text=True,capture_output=True)
        results.append({**base,"feasible":q.returncode==0,"stdout":q.stdout.strip(),"stderr":q.stderr.strip()})
    (x.out_dir/"batch.json").write_text(json.dumps(results,indent=2),encoding="utf8")
    print(json.dumps(results,indent=2))
if __name__=="__main__":main()
