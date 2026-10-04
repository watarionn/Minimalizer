from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class DinoSpatialObservation:
    grid_shape: tuple[int, int]
    features: tuple[tuple[float, ...], ...]
    global_feature: tuple[float, ...]

    def __post_init__(self):
        h,w=self.grid_shape
        if h <= 0 or w <= 0 or len(self.features) != h*w:
            raise ValueError("DINO spatial features must match grid_shape")
        if not self.features or not self.features[0]:
            raise ValueError("DINO spatial features must be non-empty")
        dim=len(self.features[0])
        if any(len(row) != dim for row in self.features):
            raise ValueError("DINO spatial feature dimensions must align")
        if len(self.global_feature) != dim:
            raise ValueError("global and spatial DINO feature dimensions must align")


@dataclass(frozen=True)
class DinoSpatialSimilarity:
    global_cosine: float
    aligned_patch_cosine: float
    coarse_patch_cosine: float
    score: float


def observation_from_feature_map(feature_map: np.ndarray) -> DinoSpatialObservation:
    array=np.asarray(feature_map,dtype=np.float32)
    if array.ndim != 3 or not np.isfinite(array).all():
        raise ValueError("feature_map must be finite [height,width,channels]")
    h,w,c=array.shape
    if min(h,w,c) <= 0:
        raise ValueError("feature_map must be non-empty")
    flat=array.reshape(h*w,c)
    global_feature=flat.mean(axis=0)
    return DinoSpatialObservation(
        grid_shape=(h,w),
        features=tuple(tuple(float(v) for v in row) for row in flat),
        global_feature=tuple(float(v) for v in global_feature),
    )


def _cosine(a: np.ndarray,b: np.ndarray) -> float:
    an=float(np.linalg.norm(a)); bn=float(np.linalg.norm(b))
    if an <= 1e-12 or bn <= 1e-12:
        return 1.0 if an <= 1e-12 and bn <= 1e-12 else 0.0
    return float(np.clip(np.dot(a,b)/(an*bn),-1.0,1.0))


def _coarsen(features: np.ndarray,shape: tuple[int,int],size: int=4) -> np.ndarray:
    h,w=shape
    grid=features.reshape(h,w,-1)
    ys=np.array_split(np.arange(h),min(size,h))
    xs=np.array_split(np.arange(w),min(size,w))
    return np.asarray([grid[np.ix_(y,x)].mean(axis=(0,1)) for y in ys for x in xs],dtype=np.float32)


def compare_dino_spatial(reference: DinoSpatialObservation,candidate: DinoSpatialObservation) -> DinoSpatialSimilarity:
    if reference.grid_shape != candidate.grid_shape:
        raise ValueError("DINO spatial grids must align")
    a=np.asarray(reference.features,dtype=np.float32)
    b=np.asarray(candidate.features,dtype=np.float32)
    global_cosine=_cosine(np.asarray(reference.global_feature),np.asarray(candidate.global_feature))
    aligned=float(np.mean([_cosine(x,y) for x,y in zip(a,b)]))
    ca=_coarsen(a,reference.grid_shape); cb=_coarsen(b,candidate.grid_shape)
    coarse=float(np.mean([_cosine(x,y) for x,y in zip(ca,cb)]))
    score=.20*global_cosine+.45*aligned+.35*coarse
    return DinoSpatialSimilarity(global_cosine,aligned,coarse,score)
