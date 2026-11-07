"""Dormant source-only class32 reach after a SHA-pinned strict owner.

EXPOSED known-case hypothesis only. This does not approve semantic owner,
Phase4, L03, Golden or production. No labels or annotations are inputs.
"""
from __future__ import annotations
import hashlib
import cv2
import numpy as np
from scipy import ndimage
from local_l02_sleeve_no_merge_shadow import _cut_collisions

class StrictLabReachHold(ValueError):
    pass

# Inherited from the exposed PR#445 LAB reach experiment, NOT blind tuned.
MAX_REACH = 20
MAX_LAB = 20
OTHER_MARGIN = 5

def propose_strict_lab_reach_shadow(*, source_rgba, class_ids, strict_owner,
                                    expected_strict_owner_sha256):
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8 or
            source_rgba.ndim != 3 or source_rgba.shape[-1] != 4 or
            type(class_ids) is not np.ndarray or class_ids.dtype != np.uint8 or
            type(strict_owner) is not np.ndarray or strict_owner.dtype != np.uint8 or
            strict_owner.ndim != 2 or not strict_owner.size or
            class_ids.shape != strict_owner.shape or
            source_rgba.shape[:2] != strict_owner.shape or
            source_rgba.shape[0] * source_rgba.shape[1] > 16_000_000):
        raise StrictLabReachHold('INVALID_SIGNED_SOURCE_OR_OWNER')
    if (not isinstance(expected_strict_owner_sha256, str) or
            len(expected_strict_owner_sha256) != 64 or
            any(c not in '0123456789abcdef' for c in expected_strict_owner_sha256) or
            hashlib.sha256(strict_owner.tobytes(order='C')).hexdigest()
            != expected_strict_owner_sha256):
        raise StrictLabReachHold('STRICT_OWNER_EXTERNAL_PIN_MISMATCH')
    alpha = source_rgba[..., 3]
    if (np.any(strict_owner > 2) or np.any(class_ids >= 47) or
            np.any((strict_owner > 0) & (alpha == 0)) or
            np.any((strict_owner == 1) & ~np.isin(class_ids, (5, 29, 30, 31, 32))) or
            np.any((strict_owner == 2) & ~np.isin(class_ids, (10, 29, 30, 31, 32)))):
        raise StrictLabReachHold('INVALID_STRICT_OWNER_PROVENANCE')
    before = strict_owner
    out = before.copy()
    if np.any(before == 1) and np.any(before == 2):
        eligible = (before == 0) & (class_ids == 32) & (alpha == 255)
        lab = cv2.cvtColor(source_rgba[..., :3], cv2.COLOR_RGB2LAB).astype(np.float32)
        options = []
        for owner_id in (1, 2):
            dist, indices = ndimage.distance_transform_edt(
                before != owner_id, return_indices=True)
            nearest = lab[indices[0], indices[1]]
            delta = np.linalg.norm(lab - nearest, axis=2)
            options.append((dist, delta))
        for i, owner_id in enumerate((1, 2)):
            dist, delta = options[i]
            other = options[1-i][0]
            admit = (eligible & (dist <= MAX_REACH) & (delta <= MAX_LAB) &
                     (other > dist + OTHER_MARGIN))
            out[admit] = owner_id
        st8 = np.ones((3, 3), dtype=bool)
        for _ in range(3):
            new1 = (out == 1) & (before == 0)
            new2 = (out == 2) & (before == 0)
            bad = ((new1 & ndimage.binary_dilation(out == 2, structure=st8)) |
                   (new2 & ndimage.binary_dilation(out == 1, structure=st8)))
            if not np.any(bad):
                break
            out[bad] = 0
        for connectivity in (4, 8):
            for owner_id in (1, 2):
                _cut_collisions(before, out, owner_id, connectivity)
    added = (before == 0) & (out > 0)
    if (np.any((before > 0) & (out != before)) or
            np.any(added & ((class_ids != 32) | (alpha != 255))) or
            np.any((out > 0) & (alpha == 0))):
        raise StrictLabReachHold('FROZEN_OWNER_OR_SOURCE_REGRESSION')
    for owner_id, other_id in ((1, 2), (2, 1)):
        if np.any(added & (out == owner_id) & ndimage.binary_dilation(
                out == other_id, structure=np.ones((3, 3), dtype=bool))):
            raise StrictLabReachHold('NEW_CROSS_OWNER_CONTACT')
        for conn in (1, 2):
            st = ndimage.generate_binary_structure(2, conn)
            old, n_old = ndimage.label(before == owner_id, structure=st)
            new, n_new = ndimage.label(out == owner_id, structure=st)
            if n_old != n_new:
                raise StrictLabReachHold('FROZEN_COMPONENT_COUNT_CHANGED')
            if n_old:
                frozen = before == owner_id
                pairs = np.unique(np.stack((old[frozen], new[frozen]), axis=1), axis=0)
                if (len(pairs) != n_old or len(np.unique(pairs[:, 0])) != n_old or
                        len(np.unique(pairs[:, 1])) != n_old or np.any(pairs == 0)):
                    raise StrictLabReachHold('FROZEN_COMPONENT_IDENTITY_CHANGED')
    return out, {
        'schema': 'minimalizer/local-l02/strict-lab-reach-shadow/v0',
        'strict_owner_sha256': expected_strict_owner_sha256,
        'proposed_owner_sha256': hashlib.sha256(out.tobytes(order='C')).hexdigest(),
        'new_source_pixels': int(np.count_nonzero(added)),
        'frozen_owner_modified_pixels': 0, 'source_pixels_generated': 0,
        'known_cases_exposed': True, 'human_labels_used_for_inference': False,
        'unknown_treated_as_negative': False, 'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
