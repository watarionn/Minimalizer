"""Research-only, owner-preserving shape cleanup for class32 sleeve candidates.

This is a source-only postfilter of the existing contact-density/palette shadow.
It never erases an immutable owner pixel or creates source pixels. A standard
3x3 binary opening of the *complete candidate owner* (not the sparse delta)
rejects thin unsupported additions. The result is still NOT semantic authority.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from local_l02_contact_density_palette_shadow import (
    ContactPaletteHold, propose_contact_density_palette_shadow,
)
from local_l02_hue_extended_owner_shadow import (
    ExtendedOwnerHold, _assert_component_identity,
)
from local_l02_cross_owner_contact_gate import (
    CrossOwnerContactHold, verify_no_new_cross_owner_contacts,
)


class ContactMorphologyHold(ValueError):
    pass


OPENING_FOOTPRINT = np.ones((3, 3), dtype=bool)
CONNECTIVITY_4 = ndimage.generate_binary_structure(2, 1)


def propose_contact_morphology_shadow(*, source_rgba: np.ndarray,
        class_ids: np.ndarray, anime_classes: np.ndarray,
        baseline_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    """Return a nonproduction owner shadow with source-only provenance.

    Human masks/coordinates are not inputs. Opening operates on full owner
    silhouettes; opening only the sparse new-pixel delta would erase sleeves.
    """
    try:
        proposed, previous = propose_contact_density_palette_shadow(
            source_rgba=source_rgba, class_ids=class_ids,
            anime_classes=anime_classes, baseline_owner=baseline_owner)
    except ContactPaletteHold as exc:
        raise ContactMorphologyHold('UPSTREAM_CONTACT_PALETTE_HOLD:' + str(exc)) from exc
    if (type(baseline_owner) is not np.ndarray or
            baseline_owner.dtype != np.uint8 or
            proposed.shape != baseline_owner.shape):
        raise ContactMorphologyHold('INVALID_FROZEN_OWNER')
    new = (baseline_owner == 0) & (proposed > 0)
    out = baseline_owner.copy()
    for owner in (1, 2):
        opened = ndimage.binary_opening(proposed == owner,
                                       structure=OPENING_FOOTPRINT)
        out[new & (proposed == owner) & opened] = owner
    # Opening may disconnect thin additions. Keep only additions reachable
    # through a 4-neighbour chain to an immutable same-owner source pixel.
    for owner in (1, 2):
        reachable = ndimage.binary_propagation(
            baseline_owner == owner, structure=CONNECTIVITY_4,
            mask=out == owner)
        out[(baseline_owner == 0) & (out == owner) & ~reachable] = 0
    added = (baseline_owner == 0) & (out > 0)
    if (np.any((baseline_owner > 0) & (out != baseline_owner)) or
            np.any((out > 0) & (source_rgba[..., 3] == 0)) or
            np.any(added & ~new) or
            np.any(added & (class_ids != 32))):
        raise ContactMorphologyHold('SOURCE_OR_OWNER_INVARIANT')
    try:
        for owner in (1, 2):
            for connectivity in (4, 8):
                _assert_component_identity(baseline_owner, out, owner,
                                           connectivity)
        verify_no_new_cross_owner_contacts(before=baseline_owner, after=out)
    except (ExtendedOwnerHold, CrossOwnerContactHold) as exc:
        raise ContactMorphologyHold('COMPONENT_OR_CONTACT_HOLD') from exc
    return out, {
        'schema': 'minimalizer/local-l02/contact-morphology-shadow/v0',
        'upstream': previous['schema'],
        'source_only_upstream_added_px': int(np.count_nonzero(new)),
        'source_only_retained_added_px': int(np.count_nonzero(added)),
        'source_only_rejected_added_px': int(np.count_nonzero(new & ~added)),
        'frozen_owner_changed_px': 0,
        'opening_footprint': '3x3_full_owner',
        'human_labels_used_for_inference': False,
        'unknown_pixels_not_treated_as_negative': True,
        'known_case_exposed': True,
        'semantic_quality_pass': False,
        'unseen_signed_blind': 'PENDING',
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
