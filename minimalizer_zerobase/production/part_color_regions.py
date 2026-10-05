from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class PartColorRegion:
 mask: np.ndarray
 rgb: tuple[int,int,int]
 area: int
 score: float

def _quant(rgb):
 return (np.asarray(rgb,dtype=np.uint16)//32).astype(np.int16)

def extract_part_color_regions(rgb:np.ndarray, part_mask:np.ndarray, *, max_regions:int=3, min_area_ratio:float=.018)->tuple[PartColorRegion,...]:
 """Deterministic connected color regions inside one authorized semantic part."""
 image=np.asarray(rgb,dtype=np.uint8); pm=np.asarray(part_mask,bool)
 total=int(pm.sum())
 if total==0:return ()
 q=_quant(image); keys=q[:,:,0]*64+q[:,:,1]*8+q[:,:,2]
 seen=np.zeros(pm.shape,bool);h,w=pm.shape;rows=[]
 for y in range(h):
  for x in range(w):
   if not pm[y,x] or seen[y,x]:continue
   key=keys[y,x]; stack=[(y,x)];seen[y,x]=1;pts=[]
   while stack:
    cy,cx=stack.pop();pts.append((cy,cx))
    for ny,nx in ((cy-1,cx),(cy,cx-1),(cy,cx+1),(cy+1,cx)):
     if 0<=ny<h and 0<=nx<w and pm[ny,nx] and not seen[ny,nx] and keys[ny,nx]==key:
      seen[ny,nx]=1;stack.append((ny,nx))
   area=len(pts)
   if area < max(2,int(total*min_area_ratio)):continue
   m=np.zeros(pm.shape,bool); yy,xx=zip(*pts);m[yy,xx]=1
   pix=image[m]; col=tuple(int(v) for v in np.median(pix,axis=0))
   chroma=max(col)-min(col); score=area*(1.0+chroma/255.0)
   rows.append(PartColorRegion(m,col,area,score))
 rows.sort(key=lambda r:(-r.score,-r.area,r.rgb))
 return tuple(rows[:max_regions])
