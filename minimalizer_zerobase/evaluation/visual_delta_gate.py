from __future__ import annotations
import numpy as np
def visual_delta_ratio(previous:np.ndarray,current:np.ndarray,*,threshold:int=8)->float:
 a=np.asarray(previous,dtype=np.int16);b=np.asarray(current,dtype=np.int16)
 if a.shape!=b.shape: raise ValueError("shape mismatch")
 return float(np.any(np.abs(a-b)>=threshold,axis=2).mean())
def passes_visual_delta(previous:np.ndarray,current:np.ndarray,*,minimum:float=.015,threshold:int=8)->bool:
 return visual_delta_ratio(previous,current,threshold=threshold)>=minimum
