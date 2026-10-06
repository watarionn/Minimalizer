from __future__ import annotations
from dataclasses import dataclass
import cv2,numpy as np
BACKGROUND_COMPOSITION_VERSION="sa7.32-v1"
@dataclass(frozen=True)
class BackgroundComposition:
 background_mask:np.ndarray
 subject_bbox:tuple[int,int,int,int]
 subject_area_ratio:float
 border_background_ratio:float
 negative_space_ratio:float
 dominant_rgb:tuple[int,int,int]
 boundary_ratio:float
def observe_background_composition(rgb:np.ndarray,subject_mask:np.ndarray)->BackgroundComposition:
 im=np.asarray(rgb);s=np.asarray(subject_mask).astype(bool)
 if im.ndim!=3 or im.shape[2]!=3 or s.shape!=im.shape[:2]:raise ValueError("shape mismatch")
 h,w=s.shape;n=int(s.sum())
 if n<16 or n>=h*w:raise ValueError("invalid subject mask")
 ys,xs=np.where(s);bbox=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
 bg=~s
 border=np.zeros_like(s);border[0]=border[-1]=True;border[:,0]=border[:,-1]=True
 border_bg=float((bg&border).sum()/max(1,int(border.sum())))
 area=float(n/(h*w));neg=float(bg.sum()/(h*w))
 # Background palette comes only from source pixels connected to image border.
 nlab,labels,stats,_=cv2.connectedComponentsWithStats(bg.astype(np.uint8),8)
 border_labels=np.unique(np.concatenate((labels[0],labels[-1],labels[:,0],labels[:,-1])))
 valid=[int(i) for i in border_labels if i and stats[int(i),cv2.CC_STAT_AREA]>=16]
 field=np.isin(labels,valid)
 vals=im[field] if field.any() else im[bg]
 color=tuple(int(x) for x in np.median(vals,axis=0))
 # Boundary complexity normalized by subject area.
 edge=cv2.morphologyEx(s.astype(np.uint8),cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0
 boundary=float(edge.sum()/n)
 return BackgroundComposition(bg,bbox,area,border_bg,neg,color,palette,boundary)
