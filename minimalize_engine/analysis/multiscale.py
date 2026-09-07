from __future__ import annotations
from dataclasses import dataclass
import cv2, numpy as np
from ..models import Region

@dataclass
class MultiScaleAnalysis:
    edge_map: np.ndarray
    saliency_map: np.ndarray
    macro_map: np.ndarray
    detail_map: np.ndarray

def _norm(a):
    a=a.astype(np.float32); mn,mx=float(a.min()),float(a.max())
    return np.zeros_like(a) if mx<=mn+1e-6 else (a-mn)/(mx-mn)

def _spectral(gray):
    small=cv2.resize(gray,(96,96),interpolation=cv2.INTER_AREA).astype(np.float32)/255
    fft=np.fft.fft2(small); amp=np.abs(fft); phase=np.angle(fft)
    log=np.log(amp+1e-6); residual=log-cv2.blur(log.astype(np.float32),(3,3))
    sal=np.abs(np.fft.ifft2(np.exp(residual+1j*phase)))**2
    return _norm(cv2.GaussianBlur(sal.astype(np.float32),(9,9),0))

def analyze_multiscale(image_rgb):
    h,w=image_rgb.shape[:2]; gray=cv2.cvtColor(image_rgb,cv2.COLOR_RGB2GRAY)
    edge=np.zeros((h,w),np.float32); macro=np.zeros_like(edge); detail=np.zeros_like(edge)
    for scale,weight in [(0.35,0.50),(0.60,0.32),(1.0,0.18)]:
        sw,sh=max(32,int(w*scale)),max(32,int(h*scale))
        g=cv2.GaussianBlur(cv2.resize(gray,(sw,sh),interpolation=cv2.INTER_AREA),(5,5),0)
        med=float(np.median(g)); lo=int(max(20,med*.6)); hi=int(min(230,max(lo+20,med*1.35)))
        e=cv2.dilate(cv2.Canny(g,lo,hi),np.ones((3,3),np.uint8),iterations=1)
        up=cv2.resize(e.astype(np.float32)/255,(w,h),interpolation=cv2.INTER_LINEAR)
        edge+=up*weight
        if scale<=.4: macro+=up
        if scale>=.9: detail+=up
    sal=cv2.resize(_spectral(gray),(w,h),interpolation=cv2.INTER_CUBIC)
    return MultiScaleAnalysis(_norm(edge),_norm(sal),_norm(macro),_norm(detail))

def apply_multiscale_scores(regions,analysis,weight=.18):
    weight=float(np.clip(weight,0,.45))
    for r in regions:
        m=r.mask>0
        if not np.any(m): continue
        score=float(np.clip(
            analysis.macro_map[m].mean()*.38+
            analysis.edge_map[m].mean()*.27+
            analysis.saliency_map[m].mean()*.27+
            analysis.detail_map[m].mean()*.08,0,1))
        r.multiscale_score=score
        r.importance_score=float(np.clip(r.importance_score*(1-weight)+score*weight,0,1))
    return regions
