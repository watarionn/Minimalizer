from __future__ import annotations
from dataclasses import dataclass
import numpy as np

FEATURE_LOCAL_VERSION="sa7.10-v1"
GRID_SIZE=16
MIN_COMPONENT_CELLS=2
MAX_COMPONENT_RATIO=.30
SIMILARITY_THRESHOLD=.72

@dataclass(frozen=True)
class FeatureLocalEvidence:
    evidence_id:str
    mask:np.ndarray
    confidence:float
    observer_role:str="feature_local"

def _cosine(a:np.ndarray,b:np.ndarray)->np.ndarray:
    an=np.linalg.norm(a,axis=-1,keepdims=True);bn=np.linalg.norm(b)
    return (a@b)/(np.maximum(an[...,0],1e-8)*max(float(bn),1e-8))

def feature_local_regions(
    patch_features:np.ndarray,
    *,
    authority_grid:np.ndarray,
    prototype:np.ndarray,
    output_shape:tuple[int,int],
)->tuple[FeatureLocalEvidence,...]:
    """Turn frozen local feature embeddings into bounded spatial evidence.

    The prototype is supplied by a non-target reference/fixture. This function
    has no semantic label and cannot grant semantic authority.
    """
    f=np.asarray(patch_features,dtype=np.float32);a=np.asarray(authority_grid).astype(bool);p=np.asarray(prototype,dtype=np.float32)
    if f.ndim!=3 or f.shape[:2]!=a.shape or f.shape[2]!=p.shape[0]:raise ValueError("feature grid shape mismatch")
    sim=_cosine(f,p)
    active=(sim>=SIMILARITY_THRESHOLD)&a
    h,w=a.shape
    seen=np.zeros_like(active);items=[]
    for yy in range(h):
      for xx in range(w):
        if not active[yy,xx] or seen[yy,xx]:continue
        stack=[(yy,xx)];seen[yy,xx]=1;cells=[]
        while stack:
          y,x=stack.pop();cells.append((y,x))
          for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
            ny,nx=y+dy,x+dx
            if 0<=ny<h and 0<=nx<w and active[ny,nx] and not seen[ny,nx]:
              seen[ny,nx]=1;stack.append((ny,nx))
        ratio=len(cells)/max(1,int(a.sum()))
        if len(cells)<MIN_COMPONENT_CELLS or ratio>MAX_COMPONENT_RATIO:continue
        mask=np.zeros(output_shape,bool)
        for y,x in cells:
          y0=round(y*output_shape[0]/h);y1=round((y+1)*output_shape[0]/h)
          x0=round(x*output_shape[1]/w);x1=round((x+1)*output_shape[1]/w)
          mask[y0:y1,x0:x1]=1
        conf=float(np.mean([sim[y,x] for y,x in cells]))
        items.append(FeatureLocalEvidence(f"dino-local-{len(items)}",mask,conf))
    return tuple(items)
