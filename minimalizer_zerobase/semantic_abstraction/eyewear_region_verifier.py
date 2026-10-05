from __future__ import annotations
from dataclasses import dataclass
import cv2,numpy as np

REGION_VERIFIER_VERSION="sa7.15-v1"
MIN_VERIFY_SCORE=.58

@dataclass(frozen=True)
class RegionVerification:
 accepted:bool
 score:float
 pair_found:bool
 bridge_supported:bool
 mask:np.ndarray
 reason:str

def verify_eyewear_region(rgb:np.ndarray,candidate:np.ndarray,authority:np.ndarray)->RegionVerification:
 im=np.asarray(rgb,np.uint8);c=np.asarray(candidate).astype(bool);a=np.asarray(authority).astype(bool);empty=np.zeros(c.shape,bool)
 if im.shape[:2]!=c.shape or a.shape!=c.shape or not c.any():return RegionVerification(False,0,False,False,empty,"invalid_candidate")
 y,x=np.where(c);x0,x1,y0,y1=int(x.min()),int(x.max()+1),int(y.min()),int(y.max()+1)
 bw,bh=x1-x0,y1-y0
 if bw<8 or bh<5:return RegionVerification(False,0,False,False,empty,"too_small")
 if c.sum()/max(1,a.sum())>.72:return RegionVerification(False,0,False,False,empty,"too_large")
 pad=max(4,round(max(bw,bh)*.18));xa=max(0,x0-pad);xb=min(c.shape[1],x1+pad);ya=max(0,y0-pad);yb=min(c.shape[0],y1+pad)
 crop=im[ya:yb,xa:xb];scale=max(1,round(220/max(crop.shape[:2])));up=cv2.resize(crop,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
 edge=cv2.Canny(up,45,135);cs,hi=cv2.findContours(edge,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
 comps=[]
 if hi is not None:
  H,W=edge.shape
  for i,q in enumerate(cs):
   if hi[0][i][2]<0:continue
   bx,by,w,h=cv2.boundingRect(q);area=abs(cv2.contourArea(q))
   if area<.003*W*H or area>.24*W*H or w<.10*W or h<.07*H or h>1.25*w:continue
   per=max(1,cv2.arcLength(q,True));closure=min(1,4*np.pi*max(area,1)/(per*per))
   comps.append((q,bx+w/2,by+h/2,area,closure,bx,by,w,h))
 best=None
 for i,l in enumerate(comps):
  for r in comps[i+1:]:
   l,r=(l,r) if l[1]<r[1] else (r,l);sep=(r[1]-l[1])/max(edge.shape[1],1);dy=abs(r[2]-l[2])/max(edge.shape[0],1);sym=min(l[3],r[3])/max(l[3],r[3])
   if not (.16<=sep<=.72 and dy<=.16 and sym>=.40):continue
   lx=l[5]+l[7];rx=r[5];yy0=max(l[6],r[6]);yy1=min(l[6]+l[8],r[6]+r[8]);bridge=False
   if rx>lx and yy1>yy0:bridge=bool((edge[yy0:yy1,lx:rx]>0).sum()>=max(2,(rx-lx)*.05))
   cm=cv2.resize(c[ya:yb,xa:xb].astype(np.uint8), (edge.shape[1],edge.shape[0]), interpolation=cv2.INTER_NEAREST)>0
   pair=np.zeros_like(edge,np.uint8);cv2.drawContours(pair,[l[0],r[0]],-1,1,-1);overlap=float((pair.astype(bool)&cm).sum())/max(1,int(pair.sum()))
   if overlap<.72:continue
   score=.23*sym+.18*(1-min(1,dy/.16))+.20*((l[4]+r[4])/2)+.22*(1 if bridge else 0)+.17*overlap
   if best is None or score>best[0]:best=(score,l,r,bridge)
 if best is None:return RegionVerification(False,0,False,False,empty,"no_pair")
 score,l,r,bridge=best
 if not bridge or score<MIN_VERIFY_SCORE:return RegionVerification(False,float(score),True,bool(bridge),empty,"weak_structure")
 # Return source candidate, not synthesized lens geometry. Verifier only accepts/rejects.
 return RegionVerification(True,float(score),True,True,c&a,"verified")
