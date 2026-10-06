from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
import cv2,numpy as np

ROLE_GAP_VERSION="sa7.31-v1"

@dataclass(frozen=True)
class RoleGap:
 role:str
 pixel_count:int
 area_ratio:float
 lab_mae:float
 edge_disagreement:float
 weighted_gap:float

def attribute_role_gaps(candidate_rgb:np.ndarray,golden_rgb:np.ndarray,role_masks:Mapping[str,np.ndarray])->tuple[RoleGap,...]:
 a=np.asarray(candidate_rgb);g=np.asarray(golden_rgb)
 if a.shape!=g.shape or a.ndim!=3 or a.shape[2]!=3:raise ValueError("image shape mismatch")
 h,w=a.shape[:2]; al=cv2.cvtColor(a.astype(np.uint8),cv2.COLOR_RGB2LAB).astype(np.float32);gl=cv2.cvtColor(g.astype(np.uint8),cv2.COLOR_RGB2LAB).astype(np.float32)
 ae=cv2.Canny(cv2.cvtColor(a.astype(np.uint8),cv2.COLOR_RGB2GRAY),80,160)>0
 ge=cv2.Canny(cv2.cvtColor(g.astype(np.uint8),cv2.COLOR_RGB2GRAY),80,160)>0
 rows=[]
 for role in sorted(role_masks):
  m=np.asarray(role_masks[role]).astype(bool)
  if m.shape!=(h,w):raise ValueError(f"mask shape mismatch: {role}")
  n=int(m.sum())
  if not n:continue
  lab=float(np.abs(al[m]-gl[m]).mean()); edge=float(np.logical_xor(ae,ge)[m].mean()); area=n/(h*w)
  # Attribution only: contribution to whole-image error, not an inference score.
  weighted=area*(lab/255.0+edge)
  rows.append(RoleGap(role,n,area,lab,edge,weighted))
 return tuple(sorted(rows,key=lambda x:(-x.weighted_gap,x.role)))
