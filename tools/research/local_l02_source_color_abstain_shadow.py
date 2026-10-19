"""Research-only source RGB color disagreement ABSTAIN for frozen class32 owners.

This never paints or promotes an owner. The *independent* AnimeSeg class 11 is
only a disagreement flag, not proof of skin/underlayer. Four seed-derived LAB
clusters and a seed-only 99th-percentile radius define an exploratory color
outlier signal. Human labels are not accepted. This has NOT passed unseen
character or Phase4/Golden quality gates and MUST NOT be used in production.
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy.spatial import cKDTree


class SourceColorAbstainHold(ValueError):
    pass


def propose_source_color_abstain(*, source_rgb: np.ndarray,
                                 source_alpha: np.ndarray,
                                 class_ids: np.ndarray,
                                 anime_classes: np.ndarray,
                                 frozen_owner: np.ndarray,
                                 owner_id: int = 2) -> tuple[np.ndarray, dict]:
    """Abstain on independently disputed class32 pixels far from coat/jacket seed colors.

    Only fully opaque pixels are eligible. Source RGB must be extracted from
    authenticated original bytes by the caller. No human annotations, masks,
    coordinate hints, labels, or learned per-character thresholds are inputs.
    The 4-cluster / 99th-percentile policy is EXPLORATORY, NOT validated.
    """
    if type(source_rgb) is not np.ndarray or source_rgb.dtype != np.uint8 or \
       source_rgb.ndim != 3 or source_rgb.shape[-1] != 3:
        raise SourceColorAbstainHold('INVALID_SOURCE_RGB')
    arrays = (source_alpha, class_ids, anime_classes, frozen_owner)
    if any(type(a) is not np.ndarray or a.dtype != np.uint8 or a.ndim != 2
           or a.shape != source_rgb.shape[:2] for a in arrays):
        raise SourceColorAbstainHold('INVALID_ARRAYS_OR_SHAPE')
    if type(owner_id) is not int or owner_id not in (1, 2):
        raise SourceColorAbstainHold('INVALID_OWNER_ID')
    if np.any(class_ids >= 47) or np.any(anime_classes >= 12) or \
       np.any(frozen_owner > 2):
        raise SourceColorAbstainHold('UNKNOWN_CLASS_OR_OWNER')
    if np.any((frozen_owner != 0) & (source_alpha == 0)):
        raise SourceColorAbstainHold('OWNER_OUTSIDE_SOURCE_ALPHA')
    if np.any((frozen_owner == 1) & ~np.isin(class_ids, (5, 32))) or \
       np.any((frozen_owner == 2) & ~np.isin(class_ids, (10, 32))):
        raise SourceColorAbstainHold('FROZEN_OWNER_CLASS_CONFLICT')
    seed_class = 5 if owner_id == 1 else 10
    seed = (frozen_owner == owner_id) & (class_ids == seed_class) & (source_alpha == 255)
    candidate = (frozen_owner == owner_id) & (class_ids == 32) & \
                (anime_classes == 11) & (source_alpha == 255)
    if np.count_nonzero(seed) < 32:
        raise SourceColorAbstainHold('INSUFFICIENT_AUTHENTIC_GARMENT_SEED')
    if not np.any(candidate):
        return frozen_owner.copy(), {
            'schema': 'minimalizer/local-l02/source-color-abstain-shadow/v1',
            'candidate_pixels': 0, 'abstained_pixels': 0,
            'semantic_quality_pass': False, 'L02': 'HOLD', 'L03': 'NO_GO',
            'Golden': 'HOLD', 'production': 'NO_GO',
        }
    lab = cv2.cvtColor(source_rgb, cv2.COLOR_RGB2LAB)
    seed_lab = lab[seed]
    sample = seed_lab[::max(1, seed_lab.shape[0] // 45000)].astype(np.float32)
    # OpenCV uses a process-wide RNG; this function is research-only and
    # deliberately resets it for replay determinism. Do not call concurrently.
    cv2.setRNGSeed(20261019)
    try:
        _, _, centers = cv2.kmeans(
            sample, 4, None,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.1),
            3, cv2.KMEANS_PP_CENTERS)
    except cv2.error as exc:
        raise SourceColorAbstainHold('GARMENT_COLOR_CLUSTER_FAILURE') from exc
    tree = cKDTree(centers)
    seed_dist = tree.query(seed_lab, workers=1)[0]
    # Radius is calculated ONLY from SegFormer jacket/coat seeds.
    radius = float(np.percentile(seed_dist, 99))
    candidate_dist = tree.query(lab[candidate], workers=1)[0]
    flagged = candidate_dist > radius
    out = frozen_owner.copy()
    out[candidate] = np.where(flagged, 0, owner_id).astype(np.uint8)
    changed = out != frozen_owner
    if np.any(changed & ~candidate) or np.any(out > 2) or \
       np.any((out != 0) & (source_alpha == 0)):
        raise SourceColorAbstainHold('ABSTAIN_ONLY_INVARIANT_FAILURE')
    return out, {
        'schema': 'minimalizer/local-l02/source-color-abstain-shadow/v1',
        'owner_id': owner_id,
        'seed_pixels': int(seed.sum()),
        'candidate_pixels': int(candidate.sum()),
        'seed_only_radius_lab8': radius,
        'abstained_pixels': int(changed.sum()),
        'class32_only': True,
        'independent_class11_is_underlayer_proof': False,
        'human_annotations_used_for_inference': False,
        'unseen_character_pass': False,
        'semantic_quality_pass': False,
        'L02': 'HOLD', 'Golden': 'HOLD', 'L03': 'NO_GO', 'production': 'NO_GO',
    }
