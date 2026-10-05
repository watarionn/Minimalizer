from __future__ import annotations
from dataclasses import dataclass
import cv2,numpy as np

GEOMETRY_WITNESS_VERSION="sa7.14-v1"
MIN_PAIR_SCORE=.62

@dataclass(frozen=True)
class GeometryWitness:
 mask:np.ndarray
 confidence:float
 paired:bool
 bridge_supported:bool
 pair_score:float

def observe_geometry_witness(rgb:np.ndarray, authority:np.ndarray, face:np.ndarray)->GeometryWitness:
 im=np.asarray(rgb,np.uint8);a=np.asarray(authority).astype(bool);f=np.asarray(face).astype(bool)
 empty=np.zeros(a.shape,bool)
 if im.shape[:2]!=a.shape or f.shape!=a.shape or not f.any():return GeometryWitness(empty,0,False,False,0)
 x,y,w,h=cv2.boundingRect(f.astype(np.uint8));yy,xx=np.indices(a.shape)
 zone=(yy>=max(0,y-int(.65*h)))&(yy<=y+int(.35*h))&(xx>=max(0,x-int(.45*w)))&(xx<=min(a.shape[1]-1,x+int(1.45*w)));a=a&zone
 edge=cv2.Canny(im,50,150);cs,hi=cv2.findContours(edge,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
 cand=[]
 if hi is not None:
  for i,c in enumerate(cs):
   if hi[0][i][2]<0:continue
   bx,by,bw,bh=cv2.boundingRect(c);area=abs(cv2.contourArea(c))
   if area<.003*w*h or area>.20*w*h or bw<.10*w or bh<.06*h or bh>1.2*bw:continue
   cx=bx+bw/2;cy=by+bh/2
   if not (x-.25*w<=cx<=x+1.25*w and y-.55*h<=cy<=y+.30*h):continue
   m=np.zeros(a.shape,np.uint8);cv2.drawContours(m,[c],-1,1,-1);m=m.astype(bool)&a
   if m.sum()<6:continue
   per=max(cv2.arcLength(c,True),1);closure=float(min(1,4*np.pi*max(area,1)/(per*per)))
   cand.append((m,cx,cy,float(m.sum()),closure,bx,by,bw,bh))
 best=None
 mid=x+w/2
 for i,l in enumerate(cand):
  for r in cand[i+1:]:
   l,r=(l,r) if l[1]<r[1] else (r,l)
   sep=(r[1]-l[1])/max(w,1);dy=abs(r[2]-l[2])/max(h,1);sym=min(l[3],r[3])/max(l[3],r[3])
   if not (l[1]<mid<r[1] and .22<=sep<=.95 and dy<=.18 and sym>=.45):continue
   # bridge must have actual source edges between the pair, not a synthesized line.
   lx=l[5]+l[7];rx=r[5];y0=max(l[6],r[6]);y1=min(l[6]+l[8],r[6]+r[8])
   bridge=False
   if rx>lx and y1>y0:
    strip=(edge[y0:y1,lx:rx]>0)&a[y0:y1,lx:rx]
    bridge=bool(strip.sum()>=max(2,(rx-lx)*.08))
   score=.30*sym+.25*(1-min(1,dy/.18))+.25*((l[4]+r[4])/2)+.20*(1 if bridge else 0)
   if best is None or score>best[0]:best=(score,l,r,bridge)
 if best is None or best[0]<MIN_PAIR_SCORE:return GeometryWitness(empty,0,False,False,0 if best is None else float(best[0]))
 score,l,r,bridge=best;mask=(l[0]|r[0])&a
 return GeometryWitness(mask,float(score),True,bool(bridge),float(score))
