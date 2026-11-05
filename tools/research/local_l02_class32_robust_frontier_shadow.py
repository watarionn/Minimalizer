"""Lane-A-only geodesic two-order class32 shadow; never Phase4 authority.

The geodesic margin is an EXPOSED-KNOWN-CASE research hypothesis, not a
blind-tuned quality threshold. No annotation, mask, coordinate or postscore is
accepted by the inference functions. Unknown regions remain unscored.
"""
from __future__ import annotations

from collections import deque
import numpy as np
from scipy import ndimage as ndi

from tools.research.local_l02_class32_color_positive_shadow import (
    propose_pinned_run30_class32_positive,
)
from tools.research.local_l02_class32_topology_palette_shadow import (
    SourceOnlyAbstentionHold,
)

_CROSS = ndi.generate_binary_structure(2, 1)
_SQUARE = ndi.generate_binary_structure(2, 2)
_MAX_PIXELS = 16_000_000
_MAX_POSITIVE = 100_000
_MAX_PASSES = 32
_MIN_GEODESIC_OWNER_MARGIN = 8  # exposed H08 hypothesis; NOT blind-validated
_INF = np.iinfo(np.int32).max


def _topology(owner: np.ndarray) -> tuple[tuple[int, int], ...]:
    return tuple((int(ndi.label(owner == oid, structure=s)[1]),
                  int(ndi.label(ndi.binary_fill_holes(owner == oid, structure=s)
                                & (owner != oid), structure=s)[1]))
                 for oid in (1, 2) for s in (_CROSS, _SQUARE))


def _geodesic_distance(eligible: np.ndarray, owner: np.ndarray,
                       owner_id: int) -> np.ndarray:
    """Exact 4-neighbour path distance through eligible positive pixels only."""
    h, w = eligible.shape
    distance = np.full((h, w), _INF, dtype=np.int32)
    seed = ndi.binary_dilation(owner == owner_id, structure=_CROSS) & eligible
    ys, xs = np.nonzero(seed)
    distance[ys, xs] = 1
    queue = deque(zip(ys.tolist(), xs.tolist()))
    while queue:
        y, x = queue.popleft()
        next_distance = int(distance[y, x]) + 1
        for ny, nx in ((y - 1, x), (y + 1, x),
                       (y, x - 1), (y, x + 1)):
            if (0 <= ny < h and 0 <= nx < w and eligible[ny, nx]
                    and next_distance < distance[ny, nx]):
                distance[ny, nx] = next_distance
                queue.append((ny, nx))
    return distance


def _local_safe(patch: np.ndarray, owner_id: int) -> bool:
    same = patch == owner_id
    if (ndi.label(same, structure=_CROSS)[1] != 1 or
            ndi.label(same, structure=_SQUARE)[1] != 1):
        return False
    background = ~same
    after = background.copy()
    after[1, 1] = False
    return all(ndi.label(background, structure=s)[1] ==
               ndi.label(after, structure=s)[1] for s in (_CROSS, _SQUARE))


def _ordered_growth(eligible: np.ndarray, frozen: np.ndarray,
                    distance1: np.ndarray, distance2: np.ndarray,
                    reverse_equal_distance: bool) -> np.ndarray:
    # Int32 distances are finite only when a source-only path exists.
    # Subtraction is safe because 2000x2000 source dimensions and the positive
    # budget bound any finite geodesic distance below _MAX_POSITIVE.
    winner = np.zeros(frozen.shape, dtype=np.uint8)
    winner[eligible & (distance1 < _INF) &
           ((distance2.astype(np.int64) - distance1) >=
            _MIN_GEODESIC_OWNER_MARGIN)] = 1
    winner[eligible & (distance2 < _INF) &
           ((distance1.astype(np.int64) - distance2) >=
            _MIN_GEODESIC_OWNER_MARGIN)] = 2
    ys, xs = np.nonzero(winner)
    depths = np.minimum(distance1[ys, xs], distance2[ys, xs])
    order = np.lexsort((-xs, -ys, depths) if reverse_equal_distance
                       else (xs, ys, depths))
    pending = [(int(ys[i]), int(xs[i]), int(winner[ys[i], xs[i]]))
               for i in order]
    result = frozen.copy()
    h, w = result.shape
    for _ in range(_MAX_PASSES):
        if not pending:
            break
        deferred = []
        added = 0
        for y, x, owner_id in pending:
            if y == 0 or x == 0 or y == h - 1 or x == w - 1:
                deferred.append((y, x, owner_id))
                continue
            patch = result[y - 1:y + 2, x - 1:x + 2]
            near4 = {int(v) for v in (patch[0, 1], patch[1, 0],
                                      patch[1, 2], patch[2, 1]) if v}
            near8 = set(np.unique(patch).tolist()) - {0}
            if near4 != {owner_id} or near8 != {owner_id} or not _local_safe(patch, owner_id):
                deferred.append((y, x, owner_id))
                continue
            result[y, x] = owner_id
            added += 1
        pending = deferred
        if not added:
            break
    return result


def _robust_two_order_candidate(positive: np.ndarray,
                                frozen_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    if (type(positive) is not np.ndarray or type(frozen_owner) is not np.ndarray or
            positive.dtype != np.bool_ or frozen_owner.dtype != np.uint8 or
            positive.ndim != 2 or positive.shape != frozen_owner.shape or
            not 0 < positive.size <= _MAX_PIXELS or
            np.any(frozen_owner > 2) or np.any(positive & (frozen_owner != 0))):
        raise SourceOnlyAbstentionHold('INVALID_ROBUST_FRONTIER_INPUT')
    if int(positive.sum()) > _MAX_POSITIVE:
        raise SourceOnlyAbstentionHold('ROBUST_FRONTIER_POSITIVE_BUDGET')
    enclosed = np.zeros(positive.shape, dtype=bool)
    for owner_id in (1, 2):
        for structure in (_CROSS, _SQUARE):
            mask = frozen_owner == owner_id
            enclosed |= ndi.binary_fill_holes(mask, structure=structure) & ~mask
    eligible = positive & ~enclosed
    before = _topology(frozen_owner)
    distance1 = _geodesic_distance(eligible, frozen_owner, 1)
    distance2 = _geodesic_distance(eligible, frozen_owner, 2)
    forward = _ordered_growth(eligible, frozen_owner, distance1, distance2, False)
    reverse = _ordered_growth(eligible, frozen_owner, distance1, distance2, True)
    consensus = ((forward == reverse) & (forward != 0) &
                 (frozen_owner == 0))
    result = frozen_owner.copy()
    result[consensus] = forward[consensus]
    # Intersection may strand fragments. Retain only pixels connected to the
    # original owner via 4-neighbour paths; no artificial bridges.
    for owner_id in (1, 2):
        reached = ndi.binary_propagation(frozen_owner == owner_id,
                                          structure=_CROSS,
                                          mask=result == owner_id)
        result[(result == owner_id) & ~reached] = 0
    after = _topology(result)
    admitted = result != frozen_owner
    integrity = (before == after and
                 not np.any(admitted & ~eligible) and
                 not np.any(admitted & (frozen_owner != 0)) and
                 not np.any((frozen_owner != 0) & (result != frozen_owner)))
    if not integrity:
        # A structural FAIL must never return an unverified owner map.
        result = frozen_owner.copy()
        admitted = np.zeros(frozen_owner.shape, dtype=bool)
    return result, {
        'schema': 'minimalizer/l02/class32-robust-frontier-shadow/v1',
        'positive_evidence_px': int(positive.sum()),
        'two_order_disagreement_px': int(np.count_nonzero(forward != reverse)),
        'two_order_agreed_admission_px': int(consensus.sum()),
        'assigned_positive_px': int(admitted.sum()),
        'abstained_positive_px': int(positive.sum() - admitted.sum()),
        'owner_topology_before': before,
        'owner_topology_after': _topology(result),
        'topology_integrity': 'PASS' if integrity else 'FAIL',
        'returned_frozen_owner_on_integrity_failure': not integrity,
        'geodesic_owner_margin_px': _MIN_GEODESIC_OWNER_MARGIN,
        'margin_known_case_exposed_not_blind': True,
        'uses_human_labels': False,
        'independent_model_evidence': False,
        'quality': 'UNASSESSED' if integrity else 'FAIL',
        'L02': 'HOLD', 'Phase4': 'FAIL', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }


def propose_pinned_run30_class32_robust_frontier_shadow(*, case_id: str,
        source_bytes: bytes, class_ids: np.ndarray,
        frozen_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    """Signed Run30 source-only research; NEVER a Phase4 owner promotion."""
    positive, evidence = propose_pinned_run30_class32_positive(
        case_id=case_id, source_bytes=source_bytes,
        class_ids=class_ids, frozen_owner=frozen_owner)
    result, receipt = _robust_two_order_candidate(positive, frozen_owner)
    return result, {
        **receipt, 'case': case_id,
        'pinned_source_class_owner': evidence['source_class_owner_sha_pinned'],
        'positive_evidence_reason': evidence['reason'],
    }


def propose_semantic_observer_gated_frontier(*, positive: np.ndarray,
        frozen_owner: np.ndarray, observer: np.ndarray,
        expected_observer_sha256: str) -> tuple[np.ndarray, dict]:
    """Conservative research gate for a separately frozen semantic observer.

    Observer 0=unknown, 1=garment, 2=non-garment. Only explicit garment
    evidence may enable positive growth; unknown and non-garment abstain.
    The supplied digest checks byte integrity, NOT independent provenance.
    Human review masks must never be supplied as an observer.
    """
    import hashlib
    import re

    if (type(observer) is not np.ndarray or observer.dtype != np.uint8 or
            observer.ndim != 2 or observer.shape != frozen_owner.shape or
            observer.size > _MAX_PIXELS or np.any(observer > 2)):
        raise SourceOnlyAbstentionHold('INVALID_SEMANTIC_OBSERVER')
    if (type(expected_observer_sha256) is not str or
            re.fullmatch(r'[0-9a-f]{64}', expected_observer_sha256) is None or
            hashlib.sha256(observer.tobytes(order='C')).hexdigest() !=
            expected_observer_sha256):
        raise SourceOnlyAbstentionHold('SEMANTIC_OBSERVER_SHA_MISMATCH')
    if (type(positive) is not np.ndarray or positive.dtype != np.bool_ or
            positive.shape != observer.shape):
        raise SourceOnlyAbstentionHold('INVALID_SEMANTIC_POSITIVE')
    gated = positive & (observer == 1)
    result, receipt = _robust_two_order_candidate(gated, frozen_owner)
    if np.any((result != frozen_owner) & (observer != 1)):
        raise SourceOnlyAbstentionHold('SEMANTIC_OBSERVER_POSTCONDITION_FAIL')
    return result, {
        **receipt,
        'semantic_observer_integrity_sha_verified': True,
        'semantic_observer_independence_verified': False,
        'semantic_observer_unknown_abstained_px': int(
            np.count_nonzero(positive & (observer == 0))),
        'semantic_observer_nongarment_abstained_px': int(
            np.count_nonzero(positive & (observer == 2))),
        'ungated_positive_px': int(positive.sum()),
        'semantic_observer_is_not_human_label': 'CALLER_MUST_VERIFY',
        'quality': 'UNASSESSED' if receipt['topology_integrity'] == 'PASS' else 'FAIL',
        'Phase4': 'FAIL',
        'L02': 'HOLD',
    }
