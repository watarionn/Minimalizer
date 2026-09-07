from __future__ import annotations
import colorsys, cv2
from ..models import Region

def _sat(rgb): return colorsys.rgb_to_hsv(*(v/255 for v in rgb))[1]
def _lum(rgb):
    r,g,b=(v/255 for v in rgb); return .299*r+.587*g+.114*b
def _rect(r):
    x,y,w,h=r.bbox; return min(1.0,r.area/max(1,w*h))
def _solid(r):
    cs,_=cv2.findContours(r.mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not cs:return 0
    c=max(cs,key=cv2.contourArea); ha=max(float(cv2.contourArea(cv2.convexHull(c))),1)
    return min(1.0,float(cv2.contourArea(c))/ha)

def classify_pseudo_semantics(regions,image_shape,subject_mode=False):
    h,w=image_shape[:2]
    for r in regions:
        x,y,bw,bh=r.bbox; cx,cy=r.centroid; aspect=bw/max(1,bh); inv=bh/max(1,bw)
        sat,lum,rect,solid=_sat(r.color_rgb),_lum(r.color_rgb),_rect(r),_solid(r)
        label,conf="generic",.4
        if r.role=="accent" or (r.is_accent and r.area_ratio<.004): label,conf="accent",.84
        elif subject_mode:
            if r.area_ratio>=.015: label,conf="subject_mass",.82
            elif inv>=2.3 and r.area_ratio>=.002: label,conf="elongated",.72
            elif solid<.62 and bh/h>.10: label,conf="subject_organic",.70
            elif sat<.18 and lum>.72: label,conf="light_surface",.66
            elif lum<.28: label,conf="dark_surface",.64
            else: label,conf="subject_detail",.58
        elif r.role=="boat": label,conf="boat",.91
        elif r.role=="water": label,conf="water",.90
        elif r.role=="vertical": label,conf="elongated",.82
        elif r.role=="reflection": label,conf="reflection",.84
        elif r.role=="structure":
            if rect>=.72 and aspect>=.70: label,conf="building",.78
            elif aspect>=1.7 and bh/h<.14 and .32<cy/h<.72: label,conf="bridge",.68
            elif solid<.70 and cy/h<.58: label,conf="tree",.70
            elif aspect>=1.25 and bh/h<.18: label,conf="roof",.67
            else: label,conf="structure",.58
        elif inv>=2.5 and r.area_ratio<.015: label,conf="elongated",.68
        elif solid<.62 and r.area_ratio>=.003: label,conf="organic",.62
        r.semantic_type=label; r.semantic_confidence=float(conf)
    return regions
