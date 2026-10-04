from __future__ import annotations

from typing import Any, Iterable

import numpy as np

from minimalizer_zerobase.analyzers.contracts import Evidence, Provenance
from minimalizer_zerobase.core.coordinates import CoordinateSpace

FROZEN_ACTIVE_THRESHOLD = 0.20
FROZEN_PROVIDER = "phase-e-grounded-sam"
FROZEN_MODEL = "IDEA-Research/grounding-dino-tiny+facebook/sam-vit-base"


def observations_from_semantic_guide(
    labels: Iterable[str],
    confidence_maps: np.ndarray,
    coordinate_space: CoordinateSpace,
    *,
    active_threshold: float = FROZEN_ACTIVE_THRESHOLD,
) -> list[Evidence]:
    if active_threshold != FROZEN_ACTIVE_THRESHOLD:
        raise ValueError("Golden frozen observer threshold is fixed at 0.20")
    names = tuple(str(x) for x in labels)
    maps = np.asarray(confidence_maps)
    if maps.ndim != 3 or maps.shape[0] != len(names):
        raise ValueError("confidence_maps must have shape (labels,H,W)")
    if not np.isfinite(maps).all():
        raise ValueError("confidence_maps must be finite")

    provenance = Provenance(
        producer=FROZEN_PROVIDER,
        producer_version="1.0",
        model_id=FROZEN_MODEL,
        model_version="phase-e-frozen",
    )
    out: list[Evidence] = []
    for index, label in enumerate(names):
        active = maps[index] >= active_threshold
        if not np.any(active):
            continue
        ys, xs = np.where(active)
        bbox = [
            int(xs.min()),
            int(ys.min()),
            int(xs.max() - xs.min() + 1),
            int(ys.max() - ys.min() + 1),
        ]
        confidence = float(np.max(maps[index][active]))
        out.append(
            Evidence(
                evidence_id=f"groundedsam-{label}",
                evidence_type="semantic_mask_bbox",
                coordinate_space=coordinate_space,
                provenance=provenance,
                confidence=confidence,
                semantic_label=label,
                geometry={"bbox": bbox},
                normalization={
                    "active_threshold": active_threshold,
                    "active_pixel_count": int(active.sum()),
                    "geometry_source": "thresholded_semantic_mask_bbox",
                    "observer_role": "hypothesis-only",
                },
            )
        )
    return out
