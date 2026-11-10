"""Research-only source-bound class32 sleeve recovery with independent generic-clothes guard.

No human masks enter inference. No owner promotion, Golden, L03 or production
authorization. Only frozen Run30 candidate pixels may be recovered.
"""
from __future__ import annotations

from collections import deque
import numpy as np
from scipy import ndimage


class SleeveShadowHold(ValueError):
    pass


def _distance_inside(mask: np.ndarray, seed: np.ndarray, connectivity: int) -> np.ndarray:
    """Shortest 4/8-connected steps from an immutable seed into eligible pixels."""
    h, w = mask.shape
    structure = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    frontier = ndimage.binary_dilation(seed, structure=structure) & mask
    flat_mask = mask.ravel()
    dist = np.full(h * w, -1, dtype=np.int32)
    start = np.flatnonzero(frontier)
    dist[start] = 1
    queue = deque(int(x) for x in start)
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if connectivity == 8:
        directions += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    while queue:
        at = queue.popleft()
        y, x = divmod(at, w)
        nxt_dist = dist[at] + 1
        for dy, dx in directions:
            yy, xx = y + dy, x + dx
            if yy < 0 or xx < 0 or yy >= h or xx >= w:
                continue
            neighbor = yy * w + xx
            if flat_mask[neighbor] and dist[neighbor] == -1:
                dist[neighbor] = nxt_dist
                queue.append(neighbor)
    return dist.reshape(mask.shape)


def propose_guarded_sleeve(*, class_ids: np.ndarray, anime_classes: np.ndarray,
                           source_alpha: np.ndarray, frozen_candidate: np.ndarray,
                           frozen_owner: np.ndarray, connectivity: int = 4):
    """Return exclusive owner proposal and non-release metrics.

    Owner IDs: 0 abstain, 1 jacket, 2 coat. Only previously unowned class32
    pixels with independent generic-clothes support may be added. All original
    owner pixels are immutable; geodesic ties and orphan pixels abstain.
    """
    arrays = (class_ids, anime_classes, source_alpha, frozen_owner)
    if any(type(a) is not np.ndarray or a.ndim != 2 or a.dtype != np.uint8
           or not a.size for a in arrays):
        raise SleeveShadowHold('INVALID_UINT8_INPUT')
    if type(frozen_candidate) is not np.ndarray or frozen_candidate.dtype != np.bool_ or frozen_candidate.ndim != 2:
        raise SleeveShadowHold('INVALID_FROZEN_CANDIDATE')
    if any(a.shape != class_ids.shape for a in (*arrays, frozen_candidate)):
        raise SleeveShadowHold('SHAPE_MISMATCH')
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise SleeveShadowHold('INVALID_CONNECTIVITY')
    if np.any(class_ids >= 47) or np.any(anime_classes >= 12):
        raise SleeveShadowHold('UNKNOWN_MODEL_CLASS')
    if np.any(frozen_owner > 2):
        raise SleeveShadowHold('INVALID_FROZEN_OWNER')
    alpha = source_alpha > 0
    if np.any(frozen_candidate & ~alpha) or np.any(frozen_candidate & ~np.isin(class_ids, (5, 10, 32))):
        raise SleeveShadowHold('FROZEN_CANDIDATE_OUTSIDE_SOURCE_OR_CLASSES')
    if np.any((frozen_owner != 0) & ~frozen_candidate):
        raise SleeveShadowHold('FROZEN_OWNER_OUTSIDE_CANDIDATE')
    if np.any((frozen_owner != 0) & ~alpha):
        raise SleeveShadowHold('FROZEN_OWNER_OUTSIDE_SOURCE')
    if np.any((frozen_owner == 1) & ~np.isin(class_ids, (5, 32))) or \
       np.any((frozen_owner == 2) & ~np.isin(class_ids, (10, 32))):
        raise SleeveShadowHold('FROZEN_OWNER_CLASS_CONFLICT')
    jacket = (frozen_owner == 1) & (class_ids == 5)
    coat = (frozen_owner == 2) & (class_ids == 10)
    if not np.any(jacket | coat):
        raise SleeveShadowHold('NO_OUTERWEAR_SEED')
    abstained = frozen_candidate & (class_ids == 32) & (frozen_owner == 0)
    eligible = abstained & (anime_classes == 10)
    out = frozen_owner.copy()
    if np.any(eligible):
        dj = _distance_inside(eligible, jacket, connectivity)
        dc = _distance_inside(eligible, coat, connectivity)
        choose_j = (dj > 0) & ((dc < 0) | (dj < dc))
        choose_c = (dc > 0) & ((dj < 0) | (dc < dj))
        out[choose_j] = 1
        out[choose_c] = 2
    added = out != frozen_owner
    if np.any(added & ~eligible) or np.any((out != 0) & ~alpha):
        raise SleeveShadowHold('SOURCE_OR_FROZEN_OWNER_INVARIANT')
    counts = {
        'schema': 'minimalizer/local-l02/guarded-sleeve-geodesic-shadow/v1',
        'connectivity': connectivity,
        'baseline_owner_pixels': int(np.count_nonzero(frozen_owner)),
        'abstained_class32_pixels': int(np.count_nonzero(abstained)),
        'independent_generic_clothes_support_pixels': int(np.count_nonzero(eligible)),
        'added_sleeve_pixels': int(np.count_nonzero(added)),
        'still_abstained_class32_pixels': int(np.count_nonzero(abstained & (out == 0))),
        'added_jacket_pixels': int(np.count_nonzero(added & (out == 1))),
        'added_coat_pixels': int(np.count_nonzero(added & (out == 2))),
        'source_pixels_generated': 0,
        'frozen_owner_modified_pixels': 0,
        'human_annotations_used_for_inference': False,
        'independent_generic_clothes_is_outerwear_proof': False,
        'independent_unseen_character_pass': False,
        'semantic_quality_pass': False,
        'L02': 'HOLD', 'Golden': 'HOLD', 'L03': 'NO_GO', 'production': 'NO_GO',
    }
    return out, counts
