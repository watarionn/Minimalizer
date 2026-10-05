from __future__ import annotations
import numpy as np

def principal_axis(mask:np.ndarray)->tuple[np.ndarray,np.ndarray]:
 m=np.asarray(mask,bool);y,x=np.where(m)
 if len(x)<2:return np.array([0.,0.]),np.array([0.,1.])
 pts=np.column_stack([x,y]).astype(float);c=pts.mean(0);z=pts-c
 _,_,vh=np.linalg.svd(z,full_matrices=False);v=vh[0]
 if v[1]<0:v=-v
 return c,v

def arm_axis_band(mask:np.ndarray,*,width_ratio:float=.42)->np.ndarray:
 """Keep a connected arm-readable band along the mask's dominant axis, clipped to authority."""
 m=np.asarray(mask,bool)
 if not np.any(m):return m.copy()
 c,v=principal_axis(m);y,x=np.indices(m.shape);dx=x-c[0];dy=y-c[1]
 perp=np.abs(-v[1]*dx+v[0]*dy);proj=v[0]*dx+v[1]*dy
 ys,xs=np.where(m);span=max(xs.max()-xs.min()+1,ys.max()-ys.min()+1)
 band=(perp<=max(2.,span*width_ratio*.5))&m
 # Never erase most of a narrow/curved arm.
 return band if band.sum()>=m.sum()*.38 else m.copy()

def clothing_major_regions(rgb:np.ndarray,mask:np.ndarray,*,max_regions:int=4)->tuple[tuple[np.ndarray,tuple[int,int,int]],...]:
 """Large connected color masses for readable garment construction."""
 a=np.asarray(rgb,np.uint8);m=np.asarray(mask,bool);total=max(1,int(m.sum()))
 q=(a//48).astype(np.int16);keys=q[:,:,0]*36+q[:,:,1]*6+q[:,:,2]
 seen=np.zeros(m.shape,bool);rows=[];h,w=m.shape
 for sy,sx in zip(*np.where(m)):
  if seen[sy,sx]:continue
  key=keys[sy,sx];st=[(sy,sx)];seen[sy,sx]=1;pts=[]
  while st:
   y,x=st.pop();pts.append((y,x))
   for ny,nx in ((y-1,x),(y,x-1),(y,x+1),(y+1,x)):
    if 0<=ny<h and 0<=nx<w and m[ny,nx] and not seen[ny,nx] and keys[ny,nx]==key:
     seen[ny,nx]=1;st.append((ny,nx))
  if len(pts)<max(8,int(total*.045)):continue
  mm=np.zeros_like(m);yy,xx=zip(*pts);mm[yy,xx]=1
  col=tuple(int(v) for v in np.median(a[mm],axis=0));rows.append((len(pts),mm,col))
 rows.sort(key=lambda z:(-z[0],z[2]))
 return tuple((mm,col) for _,mm,col in rows[:max_regions])
