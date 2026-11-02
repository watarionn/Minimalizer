"""Research-only class32 frontier growth, never a Phase4 or production owner.

Use only frozen signed source/class/owner predictions through the pinned
positive observer. Human annotations and postscore do not enter this module.
The bounded growth is exploratory and is NOT unseen-character validation.
"""
from __future__ import annotations

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
_MAX_PASSES = 32  # bounded exploratory budget, not fitted to human labels


def _topology_counts(owner: np.ndarray) -> tuple[list[int], list[int]]:
    components = []
    holes = []
    for owner_id in (1, 2):
        mask = owner == owner_id
        for structure in (_CROSS, _SQUARE):
            components.append(int(ndi.label(mask, structure=structure)[1]))
            interior = ndi.binary_fill_holes(mask, structure=structure) & ~mask
            holes.append(int(ndi.label(interior, structure=structure)[1]))
    return components, holes


def _frontier_safe_exclusive_assign(positive: np.ndarray,
                                    frozen_owner: np.ndarray, *,
                                    _scan_order: str = 'raster') -> tuple[np.ndarray, dict]:
    """Grow only original unowned evidence into one locally unambiguous owner.

    Unlike all-or-nothing component ownership, each pixel must have exactly
    one 4-connected and 8-neighbour semantic owner at admission time. This
    can leave gaps; it never infers garment identity from reviewed labels.
    """
    if _scan_order not in ('raster', 'reverse'):
        raise SourceOnlyAbstentionHold('INVALID_FRONTIER_SCAN_ORDER')
    if (type(positive) is not np.ndarray or type(frozen_owner) is not np.ndarray or
            positive.dtype != np.bool_ or frozen_owner.dtype != np.uint8 or
            positive.ndim != 2 or positive.shape != frozen_owner.shape or
            not 0 < positive.size <= _MAX_PIXELS or
            np.any(frozen_owner > 2) or np.any(positive & (frozen_owner != 0))):
        raise SourceOnlyAbstentionHold('INVALID_FRONTIER_POSITIVE_INPUT')
    if int(np.count_nonzero(positive)) > _MAX_POSITIVE:
        raise SourceOnlyAbstentionHold('FRONTIER_POSITIVE_BUDGET')

    # Preserve all original enclosed 4/8-connected negative-space pixels.
    enclosed = np.zeros(positive.shape, dtype=bool)
    for owner_id in (1, 2):
        mask = frozen_owner == owner_id
        for structure in (_CROSS, _SQUARE):
            enclosed |= ndi.binary_fill_holes(mask, structure=structure) & ~mask
    eligible = positive & ~enclosed
    before_components, before_holes = _topology_counts(frozen_owner)
    result = frozen_owner.copy()
    height, width = result.shape
    pending = [(int(y), int(x)) for y, x in np.argwhere(eligible)]
    if _scan_order == 'reverse':
        pending.reverse()
    passes = 0
    for _ in range(_MAX_PASSES):
        if not pending:
            break
        passes += 1
        deferred = []
        added = 0
        for y, x in pending:
            if y == 0 or x == 0 or y == height - 1 or x == width - 1:
                deferred.append((y, x))
                continue
            patch = result[y - 1:y + 2, x - 1:x + 2]
            near4 = {int(v) for v in (patch[0, 1], patch[1, 0],
                                      patch[1, 2], patch[2, 1]) if v}
            near8 = set(np.unique(patch).tolist()) - {0}
            if len(near4) != 1 or near4 != near8:
                deferred.append((y, x))
                continue
            owner_id = next(iter(near4))
            same = patch == owner_id
            if (ndi.label(same, structure=_CROSS)[1] != 1 or
                    ndi.label(same, structure=_SQUARE)[1] != 1):
                deferred.append((y, x))
                continue
            # A locally connected owner can still create a new void. Preserve
            # both local negative-space component counts before admission.
            background = ~same
            after_background = background.copy()
            after_background[1, 1] = False
            if (ndi.label(background, structure=_CROSS)[1] !=
                    ndi.label(after_background, structure=_CROSS)[1] or
                    ndi.label(background, structure=_SQUARE)[1] !=
                    ndi.label(after_background, structure=_SQUARE)[1]):
                deferred.append((y, x))
                continue
            result[y, x] = owner_id
            added += 1
        pending = deferred
        if not added:
            break

    after_components, after_holes = _topology_counts(result)
    admitted = result != frozen_owner
    if (before_components != after_components or before_holes != after_holes or
            np.any(admitted & ~eligible) or
            np.any(admitted & (frozen_owner != 0)) or
            np.any(admitted & (result == 0)) or
            np.any((frozen_owner != 0) & (result != frozen_owner))):
        raise SourceOnlyAbstentionHold('FRONTIER_TOPOLOGY_POSTCONDITION_FAIL')
    return result, {
        'positive_evidence_px': int(positive.sum()),
        'assigned_positive_px': int(admitted.sum()),
        'assigned_owner1_px': int(np.count_nonzero(admitted & (result == 1))),
        'assigned_owner2_px': int(np.count_nonzero(admitted & (result == 2))),
        'abstained_positive_px': int(positive.sum() - admitted.sum()),
        'abstained_original_enclosed_void_px': int(np.count_nonzero(positive & enclosed)),
        'growth_passes': passes,
        'growth_pass_limit': _MAX_PASSES,
        'owner_components_before': before_components,
        'owner_components_after': after_components,
        'owner_enclosed_holes_before': before_holes,
        'owner_enclosed_holes_after': after_holes,
        'original_owner_unchanged': True,
        'uses_human_labels': False,
        'independent_model_evidence': False,
        'quality': 'UNASSESSED', 'L02': 'HOLD', 'Phase4': 'FAIL',
        'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
    }



def _scan_order_sensitivity_receipt(positive: np.ndarray,
                                    frozen_owner: np.ndarray,
                                    raster_owner: np.ndarray) -> dict:
    """Independent traversal perturbation; no labels or private coordinates leave.

    Connectivity/hole counts alone do not prove semantic owner identity.
    A reverse traversal must not silently change owner identity or admission.
    This is a fail-closed research gate, not a method for choosing the better
    known-case postscore. Neither candidate is automatically promoted.
    """
    reverse_owner, reverse_receipt = _frontier_safe_exclusive_assign(
        positive, frozen_owner, _scan_order='reverse')
    changed = raster_owner != reverse_owner
    conflicting_owner = ((raster_owner != 0) & (reverse_owner != 0) &
                         (raster_owner != reverse_owner))
    count = int(np.count_nonzero(changed))
    return {
        'scan_order_stability': 'FAIL' if count else 'PASS',
        'scan_order_changed_px': count,
        'scan_order_owner_conflict_px': int(np.count_nonzero(conflicting_owner)),
        'reverse_assigned_positive_px': reverse_receipt['assigned_positive_px'],
        'scan_order_quality_gate': 'HOLD' if count else 'NOT_SUFFICIENT',
        'scan_order_audit_uses_human_labels': False,
    }


def propose_pinned_run30_class32_frontier_positive(*, case_id: str,
        source_bytes: bytes, class_ids: np.ndarray,
        frozen_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    """Pinned Run30 4-neighbour research replay; no unpinned fallback."""
    positive, evidence_receipt = propose_pinned_run30_class32_positive(
        case_id=case_id, source_bytes=source_bytes,
        class_ids=class_ids, frozen_owner=frozen_owner,
    )
    result, receipt = _frontier_safe_exclusive_assign(positive, frozen_owner)
    order_audit = _scan_order_sensitivity_receipt(positive, frozen_owner, result)
    return result, {
        'schema': 'minimalizer/l02/class32-frontier-positive-shadow/v1',
        'case': case_id,
        'pinned_source_class_owner': evidence_receipt['source_class_owner_sha_pinned'],
        'positive_evidence_reason': evidence_receipt['reason'],
        **receipt,
        **order_audit,
    }
