from __future__ import annotations
from dataclasses import dataclass
import cv2,numpy as np

BACKGROUND_FIELD_GEOMETRY_VERSION="sa7.33-v2"
MAX_FIELDS=3
MIN_FIELD_RATIO=.03
MIN_SOURCE_COVERAGE=.60
MAX_EXPANSION_RATIO=1.12
_EPSILON_SCHEDULE=(.01,.0075,.005,.003,.002,.001,0.0)

@dataclass(frozen=True)
class BackgroundFieldPrimitive:
 role_index:int
 polygon:np.ndarray
 rgb:tuple[int,int,int]
 source_area:int
 retained_area:int
 source_coverage:float
 expansion_ratio:float
 subject_overlap:int

def _border_connected_background(subject:np.ndarray)->np.ndarray:
 bg=(~subject).astype(np.uint8)
 _,labels,stats,_=cv2.connectedComponentsWithStats(bg,8)
 border_labels=np.unique(np.concatenate((labels[0],labels[-1],labels[:,0],labels[:,-1])))
 valid=[int(i) for i in border_labels if i and stats[int(i),cv2.CC_STAT_AREA]>=16]
 return np.isin(labels,valid)

def _largest_component(mask:np.ndarray)->np.ndarray:
 n,lab,stats,_=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
 if n<=1:return np.zeros_like(mask,dtype=bool)
 i=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
 return lab==i

def _coarsest_safe_polygon(contour:np.ndarray,component:np.ndarray,subject:np.ndarray):
 source_area=int(component.sum());perimeter=cv2.arcLength(contour,True)
 for frac in _EPSILON_SCHEDULE:
  poly=contour.reshape(-1,2) if frac==0 else cv2.approxPolyDP(contour,max(.25,frac*perimeter),True).reshape(-1,2)
  if len(poly)<3:continue
  raster=np.zeros_like(subject,dtype=np.uint8);cv2.fillPoly(raster,[poly.astype(np.int32)],1);raster=raster.astype(bool)
  retained=int((raster&component).sum());render_area=int(raster.sum())
  coverage=retained/max(1,source_area);expansion=render_area/max(1,source_area);overlap=int((raster&subject).sum())
  if coverage>=MIN_SOURCE_COVERAGE and expansion<=MAX_EXPANSION_RATIO and overlap==0:
   return poly.astype(np.float32),retained,render_area,coverage,expansion,overlap
 return None

def reauthor_background_fields(rgb:np.ndarray,subject_mask:np.ndarray,*,max_fields:int=MAX_FIELDS)->tuple[BackgroundFieldPrimitive,...]:
 im=np.asarray(rgb).astype(np.uint8);subject=np.asarray(subject_mask).astype(bool)
 if im.ndim!=3 or im.shape[2]!=3 or subject.shape!=im.shape[:2]:raise ValueError("shape mismatch")
 field=_border_connected_background(subject);n=int(field.sum())
 if n<64:return ()
 safe=field&(cv2.dilate(subject.astype(np.uint8),np.ones((7,7),np.uint8))==0)
 yy,xx=np.where(safe);data=im[safe].astype(np.float32)
 if len(data)<64:return ()
 k=min(max_fields,max(1,len(data)//64));cv2.setRNGSeed(733)
 _,idx,centers=cv2.kmeans(data,k,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,30,.5),1,cv2.KMEANS_PP_CENTERS)
 labels=idx.reshape(-1);counts=np.bincount(labels,minlength=k)
 order=sorted(range(k),key=lambda i:(-int(counts[i]),tuple(float(x) for x in centers[i])))
 out=[]
 for cluster in order:
  raw=np.zeros_like(subject,dtype=bool);sel=labels==cluster;raw[yy[sel],xx[sel]]=True
  comp=_largest_component(raw);source_area=int(comp.sum())
  if source_area/max(1,n)<MIN_FIELD_RATIO:continue
  cs,_=cv2.findContours(comp.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
  if not cs:continue
  chosen=_coarsest_safe_polygon(max(cs,key=cv2.contourArea),comp,subject)
  if chosen is None:continue
  poly,retained,render_area,coverage,expansion,overlap=chosen
  color=tuple(int(x) for x in np.median(im[comp],axis=0))
  out.append(BackgroundFieldPrimitive(len(out),poly,color,source_area,render_area,coverage,expansion,overlap))
  if len(out)>=max_fields:break
 return tuple(out)
