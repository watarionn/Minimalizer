from __future__ import annotations
from dataclasses import dataclass
import numpy as np
@dataclass(frozen=True)
class FeatureSignature:
 rgb:tuple[int,int,int]; area_ratio:float; cx:float; cy:float
@dataclass(frozen=True)
class SurvivalReport:
 baseline:tuple[FeatureSignature,...]; current:tuple[FeatureSignature,...]; missing:tuple[FeatureSignature,...]; pass_gate:bool
def _q(rgb,step=32):return tuple(int(min(255,(int(v)//step)*step+step//2)) for v in rgb)
def extract_feature_signatures(image,subject_mask=None,*,bins=32,min_area_ratio=.002,max_features=24):
 a=np.asarray(image,dtype=np.uint8)
 if a.ndim!=3 or a.shape[2]!=3:raise ValueError("RGB image required")
 h,w,_=a.shape;m=np.ones((h,w),bool) if subject_mask is None else np.asarray(subject_mask,bool)
 if m.shape!=(h,w):raise ValueError("mask shape mismatch")
 total=max(1,int(m.sum()));groups={}
 ys,xs=np.nonzero(m)
 for y,x in zip(ys.tolist(),xs.tolist()):groups.setdefault(_q(a[y,x],bins),[]).append((y,x))
 out=[]
 for rgb,pts in groups.items():
  ratio=len(pts)/total
  if ratio<min_area_ratio:continue
  py=np.fromiter((p[0] for p in pts),float);px=np.fromiter((p[1] for p in pts),float)
  out.append(FeatureSignature(rgb,ratio,float(px.mean()/max(1,w-1)),float(py.mean()/max(1,h-1))))
 out.sort(key=lambda s:(-s.area_ratio,s.rgb,s.cy,s.cx));return tuple(out[:max_features])
def _dist(a,b):
 cd=np.linalg.norm(np.asarray(a.rgb,float)-np.asarray(b.rgb,float))/441.673
 sd=((a.cx-b.cx)**2+(a.cy-b.cy)**2)**.5/1.414214
 return .72*cd+.28*sd
def feature_survival_report(baseline_image,current_image,baseline_mask=None,current_mask=None,*,match_threshold=.20):
 base=extract_feature_signatures(baseline_image,baseline_mask);cur=extract_feature_signatures(current_image,current_mask)
 missing=tuple(x for x in base if not cur or min(_dist(x,y) for y in cur)>match_threshold)
 return SurvivalReport(base,cur,missing,len(missing)==0)
