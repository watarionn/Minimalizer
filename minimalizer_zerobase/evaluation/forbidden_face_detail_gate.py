from __future__ import annotations
import numpy as np

def forbidden_face_detail_ratio(rgb:np.ndarray,head_mask:np.ndarray,*,base_rgb:tuple[int,int,int]|None=None,delta:int=34)->float:
 """Fraction of head pixels that form non-base internal color detail."""
 a=np.asarray(rgb,np.int16);h=np.asarray(head_mask,bool)
 if not np.any(h): return 0.0
 if base_rgb is None:
  base=np.median(a[h],axis=0)
 else: base=np.asarray(base_rgb,dtype=float)
 dist=np.linalg.norm(a-base,axis=2)
 return float(((dist>=delta)&h).sum()/h.sum())

def passes_forbidden_face_gate(rgb:np.ndarray,head_mask:np.ndarray,*,max_ratio:float=.025,base_rgb:tuple[int,int,int]|None=None)->bool:
 return forbidden_face_detail_ratio(rgb,head_mask,base_rgb=base_rgb)<=max_ratio
