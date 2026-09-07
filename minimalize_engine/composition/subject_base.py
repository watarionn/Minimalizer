import cv2,numpy as np
from ..models import Shape
def build_subject_base_shape(mask,palette_colors,start_id=880000):
    if mask is None or not np.any(mask>0):return []
    cs,_=cv2.findContours((mask>0).astype(np.uint8)*255,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not cs:return []
    c=max(cs,key=cv2.contourArea);per=max(float(cv2.arcLength(c,True)),1);eps=per*.004;poly=cv2.approxPolyDP(c,eps,True);f=1
    while len(poly)>48 and f<8:f*=1.25;poly=cv2.approxPolyDP(c,eps*f,True)
    pts=[(float(p[0][0]),float(p[0][1])) for p in poly]
    if len(pts)<3:return []
    if palette_colors:
        arr=np.asarray(palette_colors,dtype=float);lum=arr[:,0]*.299+arr[:,1]*.587+arr[:,2]*.114;order=np.argsort(lum);fill=tuple(int(v) for v in arr[order[min(len(order)-1,max(0,int(len(order)*.35)))]] )
    else:fill=(90,90,96)
    return [Shape(start_id,"polygon",fill,points=pts,z_index=8,source_role="subject_base",layer_name="skyline_base",importance=1,semantic_type="subject_mass")]
