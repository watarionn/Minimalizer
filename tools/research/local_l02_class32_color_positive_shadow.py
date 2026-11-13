"""Source-only class32 positive-evidence shadow; NEVER an exclusive owner map.

This known-case observer makes no owner assignments and accepts no human masks.
H04/H06/H08 source/class/owner provenance is pinned to Run30 4-neighbour.
It is not independent model evidence, blind generalization, or Phase4 PASS.
"""
from __future__ import annotations

import hashlib
import io

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from tools.research.local_l02_class32_topology_palette_shadow import (
    PINNED_RUN30_4_TRIPLES, SourceOnlyAbstentionHold,
)

MIN_SEED = 500
MAX_PIXELS = 16_000_000
G_COLOR_QUANTILE = 0.95
G_VS_COMPETITOR_RATIO = 0.60


def propose_pinned_run30_class32_positive(*, case_id: str, source_bytes: bytes,
        class_ids: np.ndarray, frozen_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    """Return unassigned-class32 *evidence only*, never a changed owner map.

    Garment seed: frozen owner on class5/10. Competitor seeds: class2 and
    class7. CIELAB median distances use only signed source RGB and frozen
    source-only predictions. Radius is the garment-seed 95th percentile;
    a candidate must be strictly closer to garment than to BOTH competitors.
    No human annotation, coordinates, masks, or postscore enter inference.
    """
    if type(case_id) is not str or case_id not in PINNED_RUN30_4_TRIPLES:
        raise SourceOnlyAbstentionHold('UNPINNED_RUN30_CASE')
    if (type(source_bytes) is not bytes or not source_bytes or
            type(class_ids) is not np.ndarray or
            type(frozen_owner) is not np.ndarray or
            class_ids.dtype != np.uint8 or frozen_owner.dtype != np.uint8 or
            class_ids.ndim != 2 or frozen_owner.shape != class_ids.shape or
            not 0 < class_ids.size <= MAX_PIXELS or
            np.any(class_ids >= 47) or np.any(frozen_owner > 2)):
        raise SourceOnlyAbstentionHold('INVALID_SIGNED_REPLAY_INPUT')
    expected = PINNED_RUN30_4_TRIPLES[case_id]
    actual = (hashlib.sha256(source_bytes).hexdigest(),
              hashlib.sha256(class_ids.tobytes(order='C')).hexdigest(),
              hashlib.sha256(frozen_owner.tobytes(order='C')).hexdigest())
    if actual != expected:
        raise SourceOnlyAbstentionHold('RUN30_PROVENANCE_TRIPLE_MISMATCH')
    try:
        with Image.open(io.BytesIO(source_bytes)) as image:
            if image.width * image.height > MAX_PIXELS:
                raise SourceOnlyAbstentionHold('SOURCE_TOO_LARGE')
            rgba = np.asarray(image.convert('RGBA'))
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise SourceOnlyAbstentionHold('INVALID_SOURCE_IMAGE') from exc
    if rgba.shape[:2] != class_ids.shape:
        raise SourceOnlyAbstentionHold('SOURCE_PREDICTION_SHAPE_MISMATCH')
    opaque = rgba[:, :, 3] != 0
    if np.any((frozen_owner != 0) & ~opaque):
        raise SourceOnlyAbstentionHold('OWNER_OUTSIDE_SIGNED_ALPHA')
    garment = np.isin(class_ids, (5, 10)) & (frozen_owner != 0) & opaque
    comp2 = (class_ids == 2) & opaque
    comp7 = (class_ids == 7) & opaque
    target = (class_ids == 32) & (frozen_owner == 0) & opaque
    evidence = np.zeros(class_ids.shape, dtype=bool)
    reason = 'INSUFFICIENT_SOURCE_ONLY_SEEDS'
    radius = None
    if min(int(garment.sum()), int(comp2.sum()), int(comp7.sum())) >= MIN_SEED:
        lab = cv2.cvtColor(rgba[:, :, :3].astype(np.float32) / 255.0,
                           cv2.COLOR_RGB2LAB)
        g = np.median(lab[garment], axis=0)
        c2 = np.median(lab[comp2], axis=0)
        c7 = np.median(lab[comp7], axis=0)
        radius = float(np.quantile(np.linalg.norm(lab[garment] - g, axis=1),
                                   G_COLOR_QUANTILE))
        px = lab[target]
        dg = np.linalg.norm(px - g, axis=1)
        dc = np.minimum(np.linalg.norm(px - c2, axis=1),
                        np.linalg.norm(px - c7, axis=1))
        evidence[target] = ((dg <= radius) &
                            (dg < G_VS_COMPETITOR_RATIO * dc))
        reason = 'SOURCE_COLOR_POSITIVE_SHADOW'
    if np.any(evidence & ((class_ids != 32) | (frozen_owner != 0) | ~opaque)):
        raise SourceOnlyAbstentionHold('POSITIVE_EVIDENCE_POSTCONDITION_FAIL')
    return evidence, {
        'schema': 'minimalizer/l02/class32-source-color-positive/v1',
        'case': case_id, 'reason': reason,
        'target_unassigned_class32_px': int(target.sum()),
        'positive_evidence_px': int(evidence.sum()),
        'garment_seed_px': int(garment.sum()),
        'color_radius_lab': radius,
        'source_class_owner_sha_pinned': True,
        'no_owner_assignment': True, 'uses_human_labels': False,
        'independent_model_evidence': False,
        'quality': 'UNASSESSED', 'L02': 'HOLD', 'Phase4': 'FAIL',
        'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
    }
