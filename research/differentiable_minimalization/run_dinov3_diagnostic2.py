from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor,AutoModel
from minimalizer_zerobase.refine.dino_spatial import observation_from_feature_map,compare_dino_spatial

MODEL="facebook/dinov3-convnext-tiny-pretrain-lvd1689m"

def extract(processor,model,path:Path):
    image=Image.open(path).convert("RGB")
    pixels=processor(images=image,return_tensors="pt")["pixel_values"].cuda()
    torch.cuda.reset_peak_memory_stats()
    start=time.perf_counter()
    with torch.inference_mode():
        output=model(pixel_values=pixels,output_hidden_states=True)
    torch.cuda.synchronize()
    elapsed=time.perf_counter()-start
    feature=output.hidden_states[-1][0].permute(1,2,0).float().cpu().numpy()
    return observation_from_feature_map(feature),elapsed,torch.cuda.max_memory_allocated()/1024/1024

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kyoko-source",type=Path,required=True); p.add_argument("--kyoko-baseline",type=Path,required=True)
    p.add_argument("--raden-source",type=Path,required=True); p.add_argument("--raden-baseline",type=Path,required=True)
    args=p.parse_args()
    processor=AutoImageProcessor.from_pretrained(MODEL,local_files_only=True)
    model=AutoModel.from_pretrained(MODEL,local_files_only=True).cuda().eval()
    result={}
    for name,source,baseline in (
        ("Hyakuto-Kyoko",args.kyoko_source,args.kyoko_baseline),
        ("Juufuutei-Raden",args.raden_source,args.raden_baseline),
    ):
        a,ta,ma=extract(processor,model,source); b,tb,mb=extract(processor,model,baseline)
        s=compare_dino_spatial(a,b)
        result[name]={"grid_shape":a.grid_shape,"global_cosine":s.global_cosine,"aligned_patch_cosine":s.aligned_patch_cosine,"coarse_patch_cosine":s.coarse_patch_cosine,"score":s.score,"source_seconds":ta,"baseline_seconds":tb,"peak_cuda_mb":max(ma,mb)}
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
