"""Deterministic sanity checks for rasterized Minimalizer comparison artifacts."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from PIL import Image

@dataclass(frozen=True)
class RenderSanity:
    passed: bool
    nonwhite_ratio: float
    unique_color_count: int
    foreground_bbox_ratio: float
    reason: str

def evaluate_render_sanity(image: Image.Image | np.ndarray, *, white_threshold: int = 250, min_nonwhite_ratio: float = 0.08, min_unique_colors: int = 3) -> RenderSanity:
    rgb=np.asarray(image.convert("RGB") if isinstance(image,Image.Image) else image)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("render sanity requires RGB image")
    fg=np.any(rgb < white_threshold,axis=2)
    nonwhite=float(fg.mean())
    unique=int(len(np.unique(rgb.reshape(-1,3),axis=0)))
    if np.any(fg):
        ys,xs=np.where(fg); bbox_area=(xs.max()-xs.min()+1)*(ys.max()-ys.min()+1)
        bbox_ratio=float(bbox_area/(rgb.shape[0]*rgb.shape[1]))
    else: bbox_ratio=0.0
    reasons=[]
    if nonwhite < min_nonwhite_ratio: reasons.append("foreground_too_sparse")
    if unique < min_unique_colors: reasons.append("insufficient_color_variation")
    return RenderSanity(not reasons,nonwhite,unique,bbox_ratio,"PASS" if not reasons else ",".join(reasons))
