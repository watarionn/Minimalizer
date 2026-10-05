from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np


@dataclass(frozen=True)
class IdentityStructureEvidence:
    evidence_id: str
    mask: np.ndarray
    bbox: tuple[int, int, int, int]
    edge_density: float
    area_ratio: float
    confidence: float


def observe_identity_structures(
    rgb: np.ndarray,
    authority_mask: np.ndarray,
    *,
    max_structures: int = 3,
    min_area_ratio: float = .008,
    max_area_ratio: float = .35,
) -> tuple[IdentityStructureEvidence, ...]:
    """Observe coherent internal structures without assigning semantic authority."""
    image=np.asarray(rgb,dtype=np.uint8)
    authority=np.asarray(authority_mask).astype(bool)
    if image.ndim != 3 or image.shape[2] != 3 or authority.shape != image.shape[:2]:
        raise ValueError("image/mask shape mismatch")
    total=max(1,int(authority.sum()))
    gray=cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
    edges=cv2.Canny(gray,55,135)>0
    edges &= authority
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
    joined=cv2.morphologyEx(edges.astype(np.uint8),cv2.MORPH_CLOSE,kernel,iterations=2)
    joined=cv2.dilate(joined,kernel,iterations=1)
    count,labels,stats,_=cv2.connectedComponentsWithStats(joined,8)
    rows=[]
    for label in range(1,count):
        x,y,w,h,area=(int(v) for v in stats[label])
        component=(labels==label)&authority
        pixel_area=int(component.sum())
        ratio=pixel_area/total
        if not (min_area_ratio <= ratio <= max_area_ratio):
            continue
        if w < 4 or h < 3:
            continue
        density=float(edges[component].sum()/max(1,pixel_area))
        if density < .025:
            continue
        confidence=min(1.0,.45+density*.55+min(ratio,.12)*2.5)
        rows.append((confidence,pixel_area,x,y,w,h,component,density,ratio))
    # Add medium-scale coherent color regions as observer evidence. Color alone is
    # never authority; promotion still requires an authorized SemanticPart parent.
    parent_median=np.median(image[authority],axis=0).astype(float)
    quant=(image//48).astype(np.int32)
    packed=(quant[:,:,0]<<16)|(quant[:,:,1]<<8)|quant[:,:,2]
    for key in np.unique(packed[authority]):
        color_mask=((packed==key)&authority).astype(np.uint8)
        ccount,clabels,cstats,_=cv2.connectedComponentsWithStats(color_mask,8)
        for label in range(1,ccount):
            x,y,w,h,area=(int(v) for v in cstats[label])
            ratio=area/total
            if not (.002 <= ratio <= .14) or w < 4 or h < 3:
                continue
            component=clabels==label
            color=np.median(image[component],axis=0).astype(float)
            contrast=float(np.linalg.norm(color-parent_median))
            if contrast < 42.0:
                continue
            boundary=cv2.morphologyEx(component.astype(np.uint8),cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0
            density=float(edges[component].sum()/max(1,area))
            confidence=min(1.0,.48+min(contrast/255.0,.35)+min(ratio,.08)+min(float(boundary.sum())/max(1,area)*.04,.08))
            rows.append((confidence,area,x,y,w,h,component,density,ratio))
    rows.sort(key=lambda r:(-r[0],-r[1],r[3],r[2]))
    return tuple(
        IdentityStructureEvidence(
            evidence_id=f"identity-structure:{i}",
            mask=row[6],
            bbox=(row[2],row[3],row[4],row[5]),
            edge_density=round(row[7],6),
            area_ratio=round(row[8],9),
            confidence=round(row[0],6),
        )
        for i,row in enumerate(rows[:max_structures])
    )
