from __future__ import annotations
from dataclasses import dataclass
import cv2,numpy as np

PALETTE_SUBDIVISION_VERSION="sa7.30-v1"
MAX_ROLES_PER_PART=3
MIN_ROLE_RATIO=.10
MIN_COMPONENT_RATIO=.025

@dataclass(frozen=True)
class PaletteRoleMass:
 semantic_part:str
 role_index:int
 mask:np.ndarray
 rgb:tuple[int,int,int]
 source_ratio:float

def _largest_component(mask:np.ndarray)->np.ndarray:
 n,lab,stats,_=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
 if n<=1:return np.zeros_like(mask,dtype=bool)
 i=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
 return lab==i

def observe_palette_role_masses(rgb:np.ndarray,part_mask:np.ndarray,semantic_part:str,*,max_roles:int=MAX_ROLES_PER_PART)->tuple[PaletteRoleMass,...]:
 img=np.asarray(rgb);mask=np.asarray(part_mask).astype(bool)
 if img.ndim!=3 or img.shape[2]!=3 or mask.shape!=img.shape[:2]:raise ValueError("shape mismatch")
 n=int(mask.sum())
 if n<16:return ()
 # Deterministic source-only Lab clustering. Fixed seed and criteria; no Golden/v12 input.
 lab=cv2.cvtColor(img.astype(np.uint8),cv2.COLOR_RGB2LAB)
 vals=lab[mask].astype(np.float32)
 k=min(max_roles,max(1,n//64))
 cv2.setRNGSeed(730)
 criteria=(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,30,.5)
 _,labels,centers=cv2.kmeans(vals,k,None,criteria,1,cv2.KMEANS_PP_CENTERS)
 labels=labels.reshape(-1)
 counts=np.bincount(labels,minlength=k)
 order=sorted(range(k),key=lambda i:(-int(counts[i]),tuple(float(x) for x in centers[i])))
 out=[]
 yy,xx=np.where(mask)
 for cluster in order:
  ratio=float(counts[cluster]/n)
  if ratio<MIN_ROLE_RATIO:continue
  cell=np.zeros_like(mask,dtype=bool); sel=labels==cluster; cell[yy[sel],xx[sel]]=True
  comp=_largest_component(cell)
  if int(comp.sum())/n<MIN_COMPONENT_RATIO:continue
  color=tuple(int(x) for x in np.median(img[comp],axis=0))
  out.append(PaletteRoleMass(semantic_part,len(out),comp,color,ratio))
  if len(out)>=max_roles:break
 return tuple(out)
