from __future__ import annotations
from html import escape
from typing import Mapping
import numpy as np

def _bbox(mask: np.ndarray):
 y,x=np.where(np.asarray(mask).astype(bool))
 if not len(x): return None
 return float(x.min()),float(y.min()),float(x.max()+1),float(y.max()+1)

def _median(rgb: np.ndarray, mask: np.ndarray) -> str:
 p=np.asarray(rgb)[np.asarray(mask).astype(bool)]
 if not len(p): return "#808080"
 v=np.median(p,axis=0).astype(int)
 return "#%02x%02x%02x"%tuple(v[:3])

def render_macro_parts_svg(rgb: np.ndarray, part_masks: Mapping[str,np.ndarray], allocations: Mapping[str,int]) -> str:
 h,w=np.asarray(rgb).shape[:2]
 order=("lower_body","torso","left_arm","right_arm","head","hair","accessory")
 chunks=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="#ffffff"/>']
 for role in order:
  n=int(allocations.get(role,0)); mask=part_masks.get(role)
  if n<=0 or mask is None: continue
  box=_bbox(mask)
  if box is None: continue
  x0,y0,x1,y1=box; bw=x1-x0;bh=y1-y0;fill=_median(rgb,mask)
  if role=="head":
   chunks.append(f'<ellipse cx="{x0+bw/2:.2f}" cy="{y0+bh/2:.2f}" rx="{bw/2:.2f}" ry="{bh/2:.2f}" fill="{fill}"/>')
  elif role in ("left_arm","right_arm"):
   chunks.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{bw:.2f}" height="{bh:.2f}" rx="{min(bw,bh)*.28:.2f}" fill="{fill}"/>')
  else:
   inset=bw*.12 if n>1 else 0
   pts=f"{x0+inset:.2f},{y0:.2f} {x1-inset:.2f},{y0:.2f} {x1:.2f},{y1:.2f} {x0:.2f},{y1:.2f}"
   chunks.append(f'<polygon points="{pts}" fill="{fill}"/>')
   if n>1:
    # second primitive must add silhouette information rather than duplicate the first
    chunks.append(f'<ellipse cx="{x0+bw/2:.2f}" cy="{y0+bh*.28:.2f}" rx="{bw*.38:.2f}" ry="{bh*.28:.2f}" fill="{fill}"/>')
 chunks.append("</svg>")
 return "".join(chunks)
