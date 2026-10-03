from __future__ import annotations
import argparse,json
from pathlib import Path
import torch
from PIL import Image
from transformers import AutoImageProcessor,AutoModel
from minimalizer_zerobase.refine.dino_spatial import observation_from_feature_map,compare_dino_spatial
MODEL="facebook/dinov3-convnext-tiny-pretrain-lvd1689m"
def obs(p,m,path):
    z=p(images=Image.open(path).convert("RGB"),return_tensors="pt")["pixel_values"].cuda()
    with torch.inference_mode(): o=m(pixel_values=z,output_hidden_states=True)
    return observation_from_feature_map(o.hidden_states[-1][0].permute(1,2,0).float().cpu().numpy())
def main():
    a=argparse.ArgumentParser();a.add_argument("--source",type=Path,required=True);a.add_argument("--baseline",type=Path,required=True);a.add_argument("--candidate",type=Path,required=True);x=a.parse_args()
    p=AutoImageProcessor.from_pretrained(MODEL,local_files_only=True);m=AutoModel.from_pretrained(MODEL,local_files_only=True).cuda().eval();s=obs(p,m,x.source);b=compare_dino_spatial(s,obs(p,m,x.baseline));c=compare_dino_spatial(s,obs(p,m,x.candidate))
    print(json.dumps({"baseline":{"global":b.global_cosine,"aligned":b.aligned_patch_cosine,"coarse":b.coarse_patch_cosine,"score":b.score},"candidate":{"global":c.global_cosine,"aligned":c.aligned_patch_cosine,"coarse":c.coarse_patch_cosine,"score":c.score},"delta":c.score-b.score},indent=2))
if __name__=="__main__":main()
