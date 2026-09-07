from __future__ import annotations
import cv2
import numpy as np
from ..models import Region, PaletteColor

def extract_regions(labels,palette,valid_mask=None):
    h,w=labels.shape
    valid=np.ones((h,w),np.uint8) if valid_mask is None else ((cv2.resize(valid_mask,(w,h),interpolation=cv2.INTER_NEAREST) if valid_mask.shape[:2]!=(h,w) else valid_mask)>0).astype(np.uint8)
    total=max(1,int(valid.sum())); out=[]; rid=0
    for p in palette:
        mask=((labels==p.id).astype(np.uint8)&valid)
        n,cc,stats,cents=cv2.connectedComponentsWithStats(mask,8)
        for cid in range(1,n):
            area=int(stats[cid,cv2.CC_STAT_AREA])
            if area<=0: continue
            x=int(stats[cid,cv2.CC_STAT_LEFT]); y=int(stats[cid,cv2.CC_STAT_TOP]); bw=int(stats[cid,cv2.CC_STAT_WIDTH]); bh=int(stats[cid,cv2.CC_STAT_HEIGHT])
            comp=(cc==cid).astype(np.uint8)*255
            out.append(Region(rid,p.id,comp,area,area/total,p.rgb,p.lab,(x,y,bw,bh),(float(cents[cid][0]),float(cents[cid][1])),touches_edge=(x==0 or y==0 or x+bw>=w or y+bh>=h)))
            rid+=1
    return out
