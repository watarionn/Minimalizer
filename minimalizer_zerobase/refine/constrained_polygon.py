from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class PolygonCheckpoint:
    step:int
    target_loss:float
    ownership_iou:float
    points:np.ndarray

def hard_mask(points:np.ndarray,width:int,height:int)->np.ndarray:
    from PIL import Image,ImageDraw
    im=Image.new("1",(width,height),0)
    ImageDraw.Draw(im).polygon([tuple(map(float,p)) for p in points],fill=1)
    return np.asarray(im,dtype=bool)

def hard_iou(a:np.ndarray,b:np.ndarray)->float:
    u=np.logical_or(a,b).sum()
    return 1.0 if u==0 else float(np.logical_and(a,b).sum()/u)

def choose_best_feasible(checkpoints:list[PolygonCheckpoint],*,minimum_iou:float=.985,initial_loss:float)->PolygonCheckpoint|None:
    feasible=[c for c in checkpoints if c.ownership_iou>=minimum_iou and c.target_loss<initial_loss]
    return min(feasible,key=lambda c:(c.target_loss,-c.ownership_iou,c.step)) if feasible else None
