import cv2,numpy as np
from ..models import Region,Shape
from .regularize import fit_boat_polygon
def _dark(rgb,f=.78):return tuple(int(np.clip(round(v*f),0,255)) for v in rgb)
def _blob(r,maxv=9,concave=False):
    cs,_=cv2.findContours(r.mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not cs:return []
    c=max(cs,key=cv2.contourArea); base=c if concave else cv2.convexHull(c); per=max(float(cv2.arcLength(base,True)),1)
    eps=per*(.008 if concave else .025); poly=cv2.approxPolyDP(base,eps,True);f=1
    while len(poly)>maxv and f<7:f*=1.22;poly=cv2.approxPolyDP(base,eps*f,True)
    return [(float(p[0][0]),float(p[0][1])) for p in poly]
def design_primitive_for_region(r,start_id):
    if r.semantic_confidence<.62:return None
    x,y,w,h=r.bbox;fill=r.color_rgb;sem=r.semantic_type
    common=dict(source_region_id=r.id,importance=r.importance_score,source_role=r.role,layer_name=r.composition_layer,semantic_type=sem,pattern_group=r.pattern_group)
    if sem=="accent" and min(w,h)/max(w,h)>=.55:
        rad=max(1,.26*(w+h));return [Shape(start_id,"circle",fill,cx=r.centroid[0],cy=r.centroid[1],rx=rad,ry=rad,**common)]
    if sem=="elongated" and r.area_ratio<=.025 and r.area/max(1,w*h)>=.52:
        return [Shape(start_id,"rectangle",fill,x=float(x),y=float(y),width=float(w),height=float(h),**common)]
    if sem=="roof" and w>=8 and h>=4:
        ins=min(w*.22,h*.9);pts=[(x,y+h),(x+ins,y),(x+w-ins,y),(x+w,y+h)]
        return [Shape(start_id,"polygon",fill,points=[(float(a),float(b)) for a,b in pts],**common)]
    if sem=="building" and r.area_ratio>=.006 and w>=12 and h>=12:
        by=y+h*.22;body=Shape(start_id,"rectangle",fill,x=float(x),y=float(by),width=float(w),height=float(h*.78),**common)
        pts=[(x-w*.03,by),(x+w*.16,y),(x+w*.84,y),(x+w*1.03,by)]
        return [body,Shape(start_id+1,"polygon",_dark(fill,.72),points=[(float(a),float(b)) for a,b in pts],**common)]
    if sem in {"subject_mass","subject_organic"}:
        pts=_blob(r,20 if sem=="subject_mass" else 16,True)
        return [Shape(start_id,"polygon",fill,points=pts,**common)] if len(pts)>=3 else None
    if sem in {"tree","organic"}:
        pts=_blob(r,8,False);return [Shape(start_id,"polygon",fill,points=pts,**common)] if len(pts)>=3 else None
    if sem=="boat":
        hull=Shape(start_id,"polygon",fill,points=fit_boat_polygon(r.bbox),**common)
        return [hull,Shape(start_id+1,"rectangle",_dark(fill,.78),x=x+w*.25,y=y+h*.18,width=w*.5,height=max(2,h*.22),**common)] if w>=24 and h>=10 and r.area_ratio>=.002 else [hull]
    if sem=="bridge" and w/max(h,1)>=1.7:return [Shape(start_id,"rectangle",fill,x=float(x),y=float(y+h*.42),width=float(w),height=float(max(2,h*.38)),**common)]
    return None
