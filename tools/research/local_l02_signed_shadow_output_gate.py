"""Independent source-only postcondition gate for dormant L02 owner shadows.

The caller must authenticate source/class/owner bytes before invocation. This
is a defensive output check, not a semantic label, Phase4 pass or release gate.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage


class SignedShadowOutputHold(ValueError):
    """Shadow output breaks a frozen-source or owner invariant."""


def verify_signed_shadow_output(*, source_rgba: np.ndarray,
                                class_ids: np.ndarray, before: np.ndarray,
                                after: np.ndarray, receipt: dict) -> dict:
    """Reject frozen-owner erasure, unsupported additions, contact or merges."""
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8 or
            source_rgba.ndim != 3 or source_rgba.shape[-1] != 4 or
            type(class_ids) is not np.ndarray or class_ids.dtype != np.uint8 or
            type(before) is not np.ndarray or before.dtype != np.uint8 or
            type(after) is not np.ndarray or after.dtype != np.uint8 or
            type(receipt) is not dict or before.ndim != 2 or
            not before.size or class_ids.shape != before.shape or
            after.shape != before.shape or source_rgba.shape[:2] != before.shape or
            np.any(before > 2) or np.any(after > 2)):
        raise SignedShadowOutputHold('INVALID_SHADOW_OUTPUT_CONTRACT')
    if np.any((before > 0) & (after != before)):
        raise SignedShadowOutputHold('FROZEN_OWNER_MODIFIED')
    added = (before == 0) & (after > 0)
    if np.any(added & ((class_ids != 32) | (source_rgba[..., 3] != 255))):
        raise SignedShadowOutputHold('UNSUPPORTED_OR_NONOPAQUE_ADDITION')
    n_added = int(np.count_nonzero(added))
    if ('new_source_pixels' not in receipt or
            type(receipt['new_source_pixels']) is not int or
            receipt['new_source_pixels'] != n_added):
        raise SignedShadowOutputHold('SHADOW_RECEIPT_PIXEL_COUNT_MISMATCH')
    if n_added:
        eight = np.ones((3, 3), dtype=bool)
        for owner_id, other_id in ((1, 2), (2, 1)):
            if np.any(added & (after == owner_id) &
                      ndimage.binary_dilation(after == other_id, structure=eight)):
                raise SignedShadowOutputHold('NEW_CROSS_OWNER_CONTACT')
        for owner_id in (1, 2):
            for connectivity in (1, 2):
                st = ndimage.generate_binary_structure(2, connectivity)
                old, n_old = ndimage.label(before == owner_id, structure=st)
                new, n_new = ndimage.label(after == owner_id, structure=st)
                if n_old != n_new:
                    raise SignedShadowOutputHold('FROZEN_COMPONENT_COUNT_CHANGED')
                if n_old:
                    frozen = before == owner_id
                    pairs = np.unique(np.stack((old[frozen], new[frozen]), axis=1), axis=0)
                    if (len(pairs) != n_old or
                            len(np.unique(pairs[:, 0])) != n_old or
                            len(np.unique(pairs[:, 1])) != n_old or
                            np.any(pairs == 0)):
                        raise SignedShadowOutputHold('FROZEN_COMPONENT_IDENTITY_CHANGED')
    return {
        'schema': 'minimalizer/local-l02/signed-shadow-postcondition/v1',
        'new_source_pixels_verified': n_added,
        'frozen_owner_pixels_modified': 0,
        'unsupported_source_pixels_added': 0,
        'new_cross_owner_contacts': 0,
        'frozen_component_identity_preserved_4_and_8': True,
        'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
    }
