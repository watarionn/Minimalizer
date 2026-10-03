from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import torch,pydiffvg
from minimalizer_zerobase.refine.polygon_guard import validate_polygon_candidate\nfrom minimalizer_zerobase.refine.semantic_trust import SemanticTrustPolicy

def render_mask(points,w,h):
    path=pydiffvg.Path(num_control_points=torch.zeros(len(points),dtype=torch.int32),points=points,is_closed=True)
    group=pydiffvg.ShapeGroup(shape_ids=torch.tensor([0]),fill_color=torch.tensor([1.,1.,1.,1.]))
    args=pydiffvg.RenderFunction.serialize_scene(w,h,[path],[group])
    return pydiffvg.RenderFunction.apply(w,h,2,2,0,None,*args)[...,3]

def main():
    a=argparse.ArgumentParser(); a.add_argument("--simplification",type=Path,required=True); a.add_argument("--target-mask",type=Path,required=True); a.add_argument("--baseline",type=Path,required=True); a.add_argument("--output",type=Path,required=True); a.add_argument("--primitive-index",type=int,default=9); a.add_argument("--points-output",type=Path); args=a.parse_args()
    d=json.loads(args.simplification.read_text(encoding="utf8")); c=next(x for x in d["candidates"] if x["name"]==d["selected_name"]); p=c["primitives"][args.primitive_index]
    ref=np.asarray(p["parameters"]["components"][0],dtype=np.float32); h,w=np.asarray(Image.open(args.target_mask)).shape[:2]
    target=torch.from_numpy((np.asarray(Image.open(args.target_mask).convert("L"),dtype=np.float32)/255.)).to(torch.float32)
    pydiffvg.set_use_gpu(False)
    reference=torch.tensor(ref); delta=torch.zeros_like(reference,requires_grad=True); opt=torch.optim.Adam([delta],lr=.15)
    initial=None
    for _ in range(30):
        opt.zero_grad(); points=reference+4.0*torch.tanh(delta); loss=((render_mask(points,w,h)-target)**2).mean()
        if initial is None: initial=float(loss.detach())
        loss.backward(); torch.nn.utils.clip_grad_norm_([delta],1.0); opt.step()
    candidate=(reference+2.75*torch.tanh(delta)).detach().numpy()
    guard=validate_polygon_candidate(ref,candidate,width=w,height=h)
    if not guard.valid: raise SystemExit("GUARD_REJECT: "+str(guard.reason))
    final=float(((render_mask(torch.tensor(candidate),w,h)-target)**2).mean().detach())
    image=Image.open(args.baseline).convert("RGB"); draw=ImageDraw.Draw(image)
    # repaint only the selected polygon with its canonical fill after a tiny guarded geometry move.
    fill=tuple(int(x) for x in p["palette_color_rgb"]); draw.polygon([tuple(map(float,q)) for q in candidate],fill=fill)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    image.save(args.output)
    if args.points_output:
        args.points_output.write_text(
            json.dumps({"primitive_id":p["primitive_id"],"points":candidate.tolist()}),
            encoding="utf8",
        )
    print(json.dumps({"primitive_id":p["primitive_id"],"part":p["composition_part"],"initial_loss":initial,"final_loss":final,"trust_radius":radius,"ownership_weight":policy.ownership_weight,"guard":"PASS","output":str(args.output)},indent=2))
if __name__=="__main__": main()
