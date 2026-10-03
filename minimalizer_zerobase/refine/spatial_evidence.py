from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np

from .regions import RegionObservation, regional_spatial_iou

@dataclass(frozen=True)
class SpatialEvidencePolicy:
    active_threshold: float = 0.20
    min_confidence: float = 0.5

def observations_from_confidence_npz(
    path: str | Path,
    *,
    policy: SpatialEvidencePolicy = SpatialEvidencePolicy(),
) -> tuple[RegionObservation, ...]:
    """Convert observation-only Grounded-SAM confidence evidence into immutable masks."""
    with np.load(Path(path), allow_pickle=False) as data:
        labels=tuple(str(v) for v in data["labels"].tolist())
        confidence=np.asarray(data["confidence"],dtype=np.float32)
    if confidence.ndim != 3 or confidence.shape[0] != len(labels):
        raise ValueError("confidence evidence must be [label,height,width]")
    if len(set(labels)) != len(labels):
        raise ValueError("confidence evidence labels must be unique")
    result=[]
    for index,label in enumerate(labels):
        channel=confidence[index]
        if not np.isfinite(channel).all():
            raise ValueError(f"non-finite confidence evidence for {label}")
        mask=channel >= policy.active_threshold
        result.append(RegionObservation(
            label=label,
            coverage=float(mask.mean()),
            confidence=1.0,
            spatial_mask=tuple(tuple(bool(v) for v in row) for row in mask),
        ))
    return tuple(result)

def spatial_overlap_from_npz(
    reference_path: str | Path,
    candidate_path: str | Path,
    *,
    policy: SpatialEvidencePolicy = SpatialEvidencePolicy(),
) -> Mapping[str,float | None]:
    reference=observations_from_confidence_npz(reference_path,policy=policy)
    candidate=observations_from_confidence_npz(candidate_path,policy=policy)
    return regional_spatial_iou(reference,candidate)
