from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class EdgeRegion:
 mask: np.ndarray
 rgb: tuple[int,int,int]
 area: int
 edge_boundary: float

def edge_map(rgb:np.ndarray)->np.ndarray:
 a=np.asarray(rgb,dtype=np.float32)
 lum=.2126*a[:,:,0]+.7152*a[:,:,1]+.0722*a[:,:,2]
 p=np.pad(lum,1,mode="reflect")
 gx=(-p[:-2,:-2]+p[:-2,2:]-2*p[1:-1,:-2]+2*p[1:-1,2:]-p[2:,:-2]+p[2:,2:])
 gy=(-p[:-2,:-2]-2*p[:-2,1:-1]-p[:-2,2:]+p[2:,:-2]+2*p[2:,1:-1]+p[2:,2:])
 e=np.hypot(gx,gy);scale=float(np.percentile(e,99))
 return np.zeros_like(e) if scale<=1e-9 else np.clip(e/scale,0,1)

def propose_edge_regions(rgb:np.ndarray,part_mask:np.ndarray,*,cell_size:int=8,max_regions:int=6)->tuple[EdgeRegion,...]:
 """Edge-aware deterministic region proposals restricted to one semantic part."""
 a=np.asarray(rgb,np.uint8);pm=np.asarray(part_mask,bool);h,w=pm.shape
 if not pm.any():return ()
 e=edge_map(a); labels=np.full((h,w),-1,np.int32);centers=[]
 # low-edge grid seeds, analogous to v12 SLICO center relocation.
 for y in range(cell_size//2,h,cell_size):
  for x in range(cell_size//2,w,cell_size):
   best=None
   for yy in range(max(0,y-1),min(h,y+2)):
    for xx in range(max(0,x-1),min(w,x+2)):
     if pm[yy,xx] and (best is None or (e[yy,xx],yy,xx)<best):best=(float(e[yy,xx]),yy,xx)
   if best is not None:centers.append((best[1],best[2],a[best[1],best[2]].astype(float)))
 if not centers:return ()
 yy,xx=np.where(pm)
 for y,x in zip(yy,xx):
  cand=[]
  for i,(cy,cx,col) in enumerate(centers):
   if abs(cy-y)>cell_size*2 or abs(cx-x)>cell_size*2:continue
   dc=float(np.sum((a[y,x].astype(float)-col)**2))/65025.0
   ds=((y-cy)**2+(x-cx)**2)/max(1.0,cell_size*cell_size)
   cand.append((dc+ds*.35+float(e[y,x])*.12,i))
  if cand:labels[y,x]=min(cand)[1]
 # Split every label into 4-connected components.
 rows=[]
 for lab in range(len(centers)):
  src=(labels==lab);seen=np.zeros((h,w),bool)
  for sy,sx in zip(*np.where(src)):
   if seen[sy,sx]:continue
   stack=[(sy,sx)];seen[sy,sx]=1;pts=[]
   while stack:
    cy,cx=stack.pop();pts.append((cy,cx))
    for ny,nx in ((cy-1,cx),(cy,cx-1),(cy,cx+1),(cy+1,cx)):
     if 0<=ny<h and 0<=nx<w and src[ny,nx] and not seen[ny,nx]:seen[ny,nx]=1;stack.append((ny,nx))
   if len(pts)<max(3,int(pm.sum()*.012)):continue
   m=np.zeros((h,w),bool);py,px=zip(*pts);m[py,px]=1
   col=tuple(int(v) for v in np.median(a[m],axis=0))
   boundary=float(e[m].mean());rows.append(EdgeRegion(m,col,len(pts),boundary))
 rows.sort(key=lambda r:(-r.area,-r.edge_boundary,r.rgb))
 return tuple(rows[:max_regions])

def propose_contrast_subregions(rgb:np.ndarray,part_mask:np.ndarray,*,max_regions:int=4,min_area_ratio:float=.004,max_area_ratio:float=.12)->tuple[EdgeRegion,...]:
 """Preserve compact minority-color islands before superpixel representative-color collapse."""
 a=np.asarray(rgb,np.uint8);pm=np.asarray(part_mask,bool);total=int(pm.sum())
 if total==0:return ()
 # Coarse color bins estimate local rarity without naming any hue.
 q=(a//32).astype(np.int16)
 vals=q[pm];keys,counts=np.unique(vals,axis=0,return_counts=True)
 freq={tuple(k):int(n) for k,n in zip(keys,counts)}
 cand=np.zeros(pm.shape,bool)
 for y,x in zip(*np.where(pm)):
  ratio=freq[tuple(q[y,x])]/total
  if ratio<=.14:cand[y,x]=1
 h,w=pm.shape;seen=np.zeros((h,w),bool);edge=edge_map(a);out=[]
 for sy,sx in zip(*np.where(cand)):
  if seen[sy,sx]:continue
  stack=[(sy,sx)];seen[sy,sx]=1;pts=[]
  while stack:
   y,x=stack.pop();pts.append((y,x))
   for ny,nx in ((y-1,x),(y,x-1),(y,x+1),(y+1,x)):
    if 0<=ny<h and 0<=nx<w and cand[ny,nx] and not seen[ny,nx]:
     if np.linalg.norm(a[ny,nx].astype(float)-a[y,x].astype(float))<=72:
      seen[ny,nx]=1;stack.append((ny,nx))
  ratio=len(pts)/total
  if not(min_area_ratio<=ratio<=max_area_ratio):continue
  m=np.zeros((h,w),bool);yy,xx=zip(*pts);m[yy,xx]=1
  col=tuple(int(v) for v in np.median(a[m],axis=0))
  chroma=float(max(col)-min(col))/255.0
  rarity=1.0-freq.get(tuple((np.asarray(col)//32).astype(int)),total)/total
  out.append((rarity+.35*chroma,EdgeRegion(m,col,len(pts),float(edge[m].mean()))))
 out.sort(key=lambda x:(-x[0],-x[1].area,x[1].rgb))
 return tuple(x[1] for x in out[:max_regions])
