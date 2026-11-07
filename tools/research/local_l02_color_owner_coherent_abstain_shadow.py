"""A-only source-only *exploratory* coherent low-support color-owner veto.

Never receives human masks or annotations. The existing color-mode proposal
provides the low-support owner pixels; this variant vetoes only the largest
8-connected removed region if it represents a strict majority of the proposal.
Smaller disconnected regions abstain from the veto (retain frozen owner).
This limits collateral garment deletion but cannot prove semantic correctness.
"""
import numpy as np
from scipy import ndimage
from local_l02_color_owner_conflict_shadow import (
    propose_color_owner_conflict_shadow, ColorOwnerConflictHold,
)
from local_l02_hue_extended_owner_shadow import (
    _assert_component_identity, ExtendedOwnerHold,
)

class CoherentColorOwnerHold(ValueError):
    pass


def _largest_majority_veto(frozen_owner, raw):
    """Retain only the largest 8-connected raw veto if it is a strict majority."""
    removed = (frozen_owner > 0) & (raw == 0)
    n_removed = int(np.count_nonzero(removed))
    out = frozen_owner.copy()
    largest = 0
    if n_removed:
        ids, count = ndimage.label(removed, structure=np.ones((3, 3), dtype=bool))
        sizes = np.bincount(ids.ravel())
        sizes[0] = 0
        largest_id = int(np.argmax(sizes))
        largest = int(sizes[largest_id])
        if largest * 2 > n_removed:
            out[ids == largest_id] = 0
    return out, n_removed, largest


def propose_coherent_color_owner_shadow(*, source_rgba, class_ids,
                                        independent_outerwear, frozen_owner):
    """Return an exclusive owner *research shadow*, never a quality PASS.

    The largest removed 8-component must be a strict majority of removed
    pixels. Otherwise the entire color veto is rejected (unchanged owner).
    """
    try:
        raw, audit = propose_color_owner_conflict_shadow(
            source_rgba=source_rgba, class_ids=class_ids,
            independent_outerwear=independent_outerwear,
            frozen_owner=frozen_owner)
    except ColorOwnerConflictHold as exc:
        raise CoherentColorOwnerHold(str(exc)) from exc
    out, n_removed, largest = _largest_majority_veto(frozen_owner, raw)
    # The result is a subset of the previously topology-verified veto, but
    # independently enforce owner connectivity and original alpha again.
    for owner_id in (1, 2):
        for connectivity in (4, 8):
            try:
                _assert_component_identity(frozen_owner, out, owner_id, connectivity)
            except ExtendedOwnerHold as exc:
                raise CoherentColorOwnerHold('OWNER_COMPONENT_IDENTITY_CHANGED') from exc
    if np.any((out != 0) & (out != frozen_owner)) or np.any((out > 0) & (source_rgba[..., 3] == 0)):
        raise CoherentColorOwnerHold('SOURCE_OWNER_VIOLATION')
    return out, {
        'schema': 'minimalizer/local-l02/color-owner-coherent-abstain-shadow/v0',
        'raw_color_veto_pixels': n_removed,
        'largest_8_connected_veto_pixels': largest,
        'coherent_veto_pixels': int(np.count_nonzero((frozen_owner > 0) & (out == 0))),
        'retained_owner_pixels_vs_raw_veto': int(np.count_nonzero((raw == 0) & (out > 0))),
        'veto_admitted': bool(n_removed and largest * 2 > n_removed),
        'owner_promotions': 0, 'source_pixels_generated': 0,
        'human_annotations_used_for_inference': False,
        'unseen_character_pass': False, 'semantic_quality_pass': False,
        'quality': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
        'upstream_color_veto_reason': audit.get('reason'),
    }
