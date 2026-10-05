from __future__ import annotations

from typing import Any
import numpy as np


def propose_accent_regions(
    image: np.ndarray,
    subject_mask: np.ndarray,
    *,
    grid: tuple[int, int] = (8, 8),
    max_regions: int = 3,
) -> list[dict[str, Any]]:
    """Propose small color-distinct regions inside an existing subject mask.

    This observer is semantic-free: it does not name or authorize features.
    Ranking uses deterministic cell chroma, contrast from the subject median,
    occupancy, and a small-region preference.
    """
    rgb=np.asarray(image)
    mask=np.asarray(subject_mask)>0
    if rgb.ndim!=3 or rgb.shape[2]!=3 or rgb.dtype!=np.uint8:
        raise ValueError("image must be uint8 RGB")
    if mask.shape!=rgb.shape[:2]:
        raise ValueError("subject_mask must match image height/width")
    pixels=rgb[mask]
    if not len(pixels):
        return []
    subject_median=np.median(pixels.astype(float),axis=0)
    H,W=mask.shape; gy,gx=grid
    ys=np.linspace(0,H,gy+1,dtype=int); xs=np.linspace(0,W,gx+1,dtype=int)
    candidates=[]
    for yy in range(gy):
        for xx in range(gx):
            cm=mask[ys[yy]:ys[yy+1],xs[xx]:xs[xx+1]]
            if not np.any(cm):
                continue
            cp=rgb[ys[yy]:ys[yy+1],xs[xx]:xs[xx+1]][cm].astype(float)
            med=np.median(cp,axis=0)
            chroma=float(med.max()-med.min())/255.0
            contrast=float(np.linalg.norm(med-subject_median))/(255.0*np.sqrt(3.0))
            occupancy=float(cm.mean())
            area_fraction=float(cm.sum()/max(1,mask.sum()))
            smallness=max(0.0,1.0-area_fraction)
            score=chroma*contrast*np.sqrt(occupancy)*smallness
            if score<=0:
                continue
            candidates.append({"bbox":[int(xs[xx]),int(ys[yy]),int(xs[xx+1]-xs[xx]),int(ys[yy+1]-ys[yy])],"score":score,"median_rgb":[int(round(v)) for v in med],"semantic_label":None,"authority":False,"source":"subject_color_hypothesis"})
    candidates.sort(key=lambda r:(-r["score"],r["bbox"][1],r["bbox"][0]))
    return candidates[:max_regions]
