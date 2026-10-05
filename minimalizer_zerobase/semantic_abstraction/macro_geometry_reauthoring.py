from __future__ import annotations
from dataclasses import dataclass
import cv2,numpy as np

MACRO_GEOMETRY_VERSION="sa7.24-v1"
MAX_EXPANSION_RATIO=1.12
MIN_SOURCE_COVERAGE=.65

@dataclass(frozen=True)
class MacroGeometryPrimitive:
 semantic_part:str
 polygon:np.ndarray
 source_area:int
 retained_area:int

def _masses(mask:np.ndarray,limit:int)->tuple[np.ndarray,...]:
 m=np.asarray(mask).astype(np.uint8)
 k=max(3,int(round(min(m.shape)*.008))|1)
 clean=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((k,k),np.uint8))
 n,lab,stats,_=cv2.connectedComponentsWithStats(clean,8)
 rows=[(int(stats[i,cv2.CC_STAT_AREA]),i) for i in range(1,n) if int(stats[i,cv2.CC_STAT_AREA])>=max(12,int(m.sum()*.02))]
 rows.sort(key=lambda x:(-x[0],x[1]))
 return tuple(lab==i for _,i in rows[:limit])

def _coarse_polygon(mask:np.ndarray)->np.ndarray|None:
 ys,xs=np.where(mask)
 if not xs.size:return None
 pts=np.column_stack((xs,ys)).astype(np.int32)
 hull=cv2.convexHull(pts.reshape(-1,1,2))
 peri=cv2.arcLength(hull,True)
 poly=cv2.approxPolyDP(hull,max(2.0,.035*peri),True).reshape(-1,2)
 return poly if len(poly)>=3 else hull.reshape(-1,2)

def reauthor_macro_geometry(*,hair_mask:np.ndarray,clothing_mask:np.ndarray)->tuple[MacroGeometryPrimitive,...]:
 out=[]
 for name,mask,limit in (("hair",hair_mask,3),("major_clothing",clothing_mask,2)):
  src=np.asarray(mask).astype(bool)
  for mass in _masses(src,limit):
   poly=_coarse_polygon(mass)
   if poly is None:continue
   canvas=np.zeros(src.shape,np.uint8);cv2.fillPoly(canvas,[poly.astype(np.int32)],1)
   # Geometry may bridge tiny source gaps but must remain near source support.
   dil=cv2.dilate(src.astype(np.uint8),np.ones((5,5),np.uint8))>0
   clipped=(canvas>0)&dil
   poly2=_coarse_polygon(clipped)
   if poly2 is None:continue
   final=np.zeros(src.shape,np.uint8);cv2.fillPoly(final,[poly2.astype(np.int32)],1)
   source_n=max(1,int(mass.sum())); final_n=int(final.sum()); covered=int(((final>0)&mass).sum())
   expansion=final_n/source_n; coverage=covered/source_n
   if expansion>MAX_EXPANSION_RATIO or coverage<MIN_SOURCE_COVERAGE:
    contours,_=cv2.findContours(mass.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not contours:continue
    q=max(contours,key=cv2.contourArea);peri=cv2.arcLength(q,True)
    poly2=cv2.approxPolyDP(q,max(1.5,.02*peri),True).reshape(-1,2)
    if len(poly2)<3:continue
    final=np.zeros(src.shape,np.uint8);cv2.fillPoly(final,[poly2.astype(np.int32)],1)
    final_n=int(final.sum());covered=int(((final>0)&mass).sum())
    if final_n/source_n>MAX_EXPANSION_RATIO or covered/source_n<MIN_SOURCE_COVERAGE:continue
   out.append(MacroGeometryPrimitive(name,poly2,int(source_n),int(final_n)))
 return tuple(out)
