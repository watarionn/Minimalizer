from __future__ import annotations
import cv2
import numpy as np
from ..models import PaletteColor
from ..preprocess.color_space import rgb_to_lab, lab_to_rgb

def quantize_colors(image_rgb,n_colors,seed=42,valid_mask=None):
    lab=rgb_to_lab(image_rgb); h,w=lab.shape[:2]
    valid=np.ones((h,w),bool) if valid_mask is None else (cv2.resize(valid_mask,(w,h),interpolation=cv2.INTER_NEAREST)>0 if valid_mask.shape[:2]!=(h,w) else valid_mask>0)
    coords=np.flatnonzero(valid.reshape(-1)); all_pixels=lab.reshape((-1,3)).astype(np.float32)
    if len(coords)==0: coords=np.arange(h*w); valid[:]=True
    pixels=all_pixels[coords]; k=max(1,min(int(n_colors),len(pixels)))
    cv2.setRNGSeed(int(seed))
    criteria=(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,40,0.5)
    _,vl,centers=cv2.kmeans(pixels,k,None,criteria,5,cv2.KMEANS_PP_CENTERS)
    labels_flat=np.zeros(h*w,dtype=np.int32); labels_flat[coords]=vl.reshape(-1); labels=labels_flat.reshape(h,w)
    centers_u8=np.clip(np.round(centers),0,255).astype(np.uint8)
    quant_lab=lab.copy(); quant_lab.reshape((-1,3))[coords]=centers_u8[vl.reshape(-1)]
    quant_rgb=lab_to_rgb(quant_lab)
    palette=[]; total=max(1,len(coords)); flat=vl.reshape(-1)
    for i,c in enumerate(centers_u8):
        count=int(np.count_nonzero(flat==i)); rgb=lab_to_rgb(c.reshape(1,1,3))[0,0]
        palette.append(PaletteColor(i,tuple(int(x) for x in rgb),tuple(float(x) for x in c),count,count/total))
    return quant_rgb,labels,palette
