"""Dormant, source-only dual-owner sleeve recovery shadow.

This is an EXPOSED-H08 hypothesis, not a semantic owner authority, Phase4
PASS, blind generalization, Golden or production feature. No labels, private
coordinates, generated pixels or pretrained model calls enter inference.

Input `owner` is an independently authenticated *already composed* exclusive
owner, not an arbitrary SegFormer class map. The caller must verify the signed
source, class observation and composed owner SHA before invoking this function.
"""
from __future__ import annotations

import cv2
import hashlib
import numpy as np
from scipy import ndimage


class DualOwnerLabReachHold(ValueError):
    """The proposed owner violates a source or frozen topology invariant."""


# OpenCV's uint8 RGB->LAB scaling, NOT a perceptual Delta-E 2000 threshold.
# Chosen on exposed known cases. Neither calibrated nor blind validated.
MAX_SPATIAL_REACH_PX = 20
MAX_OPENCV_LAB_DISTANCE = 20
MIN_COMPETING_OWNER_DISTANCE_MARGIN_PX = 5


def _component_identity(before: np.ndarray, after: np.ndarray, owner_id: int,
                        connectivity: int) -> bool:
    structure = ndimage.generate_binary_structure(2, connectivity)
    old, n_old = ndimage.label(before == owner_id, structure=structure)
    new, n_new = ndimage.label(after == owner_id, structure=structure)
    if n_old != n_new:
        return False
    if n_old == 0:
        return True
    immutable = before == owner_id
    pairs = np.unique(np.stack((old[immutable], new[immutable]), axis=1), axis=0)
    return (len(pairs) == n_old and len(np.unique(pairs[:, 0])) == n_old
            and len(np.unique(pairs[:, 1])) == n_old and
            not np.any(pairs == 0))


def propose_dual_owner_lab_reach_shadow(*, source_rgba: np.ndarray,
                                         class_ids: np.ndarray,
                                         composed_owner: np.ndarray,
                                         expected_composed_owner_sha256: str
                                         ) -> tuple[np.ndarray, dict]:
    """Propose only original-source class32 additions to a frozen dual owner.

    Source-only abstention on 8-neighbor cross-owner contacts, 4/8 frozen
    component merges, or disconnected additions. Single-owner domains are
    explicitly unchanged. The result remains an unapproved research shadow.
    """
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8 or
        source_rgba.ndim != 3 or source_rgba.shape[-1] != 4 or
        type(class_ids) is not np.ndarray or class_ids.dtype != np.uint8 or
        type(composed_owner) is not np.ndarray or
        composed_owner.dtype != np.uint8 or composed_owner.ndim != 2 or
        not composed_owner.size or source_rgba.shape[:2] != composed_owner.shape or
        class_ids.shape != composed_owner.shape):
        raise DualOwnerLabReachHold('INVALID_SOURCE_OR_MODEL_CONTRACT')
    if (not isinstance(expected_composed_owner_sha256, str) or
        len(expected_composed_owner_sha256) != 64 or
        any(c not in '0123456789abcdef' for c in expected_composed_owner_sha256)):
        raise DualOwnerLabReachHold('MISSING_OR_INVALID_COMPOSED_OWNER_PIN')
    actual_owner_sha256 = hashlib.sha256(composed_owner.tobytes(order='C')).hexdigest()
    if actual_owner_sha256 != expected_composed_owner_sha256:
        raise DualOwnerLabReachHold('COMPOSED_OWNER_SHA_MISMATCH')
    before = composed_owner
    alpha = source_rgba[..., 3]
    if (np.any(before > 2) or np.any(class_ids >= 47) or
        np.any((before > 0) & (alpha == 0)) or
        np.any((before == 1) & ~np.isin(class_ids, (5, 29, 30, 31, 32))) or
        np.any((before == 2) & ~np.isin(class_ids, (10, 29, 30, 31, 32)))):
        raise DualOwnerLabReachHold('INVALID_FROZEN_OWNER_PROVENANCE')
    receipt = {
        'schema': 'minimalizer/local-l02/dual-owner-lab-reach-shadow/v1',
        'known_cases_exposed': True,
        'verified_composed_owner_sha256': actual_owner_sha256,
        'new_unseen_signed_blind': 'PENDING',
        'human_labels_used_for_inference': False,
        'semantic_owner_authorized': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
    if not np.any(before == 1) or not np.any(before == 2):
        return before.copy(), {**receipt, 'dual_owner_domain': False,
                               'new_source_pixels': 0}

    eligible = (before == 0) & (class_ids == 32) & (alpha == 255)
    # Preserve the exact 8-bit OpenCV-LAB convention in the receipt/code.
    lab = cv2.cvtColor(source_rgba[..., :3], cv2.COLOR_RGB2LAB).astype(np.float32)
    options = []
    for owner_id in (1, 2):
        dist, indices = ndimage.distance_transform_edt(
            before != owner_id, return_indices=True)
        nearest = lab[indices[0], indices[1]]
        delta = np.linalg.norm(lab - nearest, axis=2)
        options.append((dist, delta))

    out = before.copy()
    for i, owner_id in enumerate((1, 2)):
        dist, delta = options[i]
        competing_dist = options[1 - i][0]
        admit = (eligible & (dist <= MAX_SPATIAL_REACH_PX) &
                 (delta <= MAX_OPENCV_LAB_DISTANCE) &
                 (competing_dist > dist + MIN_COMPETING_OWNER_DISTANCE_MARGIN_PX))
        out[admit] = owner_id

    structure8 = np.ones((3, 3), dtype=bool)
    # Remove only newly added endpoints touching the opposite owner.
    for _ in range(2):
        new1 = (out == 1) & (before == 0)
        new2 = (out == 2) & (before == 0)
        bad = ((new1 & ndimage.binary_dilation(out == 2, structure=structure8)) |
               (new2 & ndimage.binary_dilation(out == 1, structure=structure8)))
        out[bad] = 0

    # Do not connect two previously separate immutable garment components.
    for owner_id in (1, 2):
        for conn in (1, 2):
            structure = ndimage.generate_binary_structure(2, conn)
            old_labels, _ = ndimage.label(before == owner_id, structure=structure)
            added_labels, _ = ndimage.label(
                (out == owner_id) & (before == 0), structure=structure)
            for label_id, box in enumerate(ndimage.find_objects(added_labels), 1):
                if box is None:
                    continue
                y0, y1 = max(0, box[0].start - 1), min(out.shape[0], box[0].stop + 1)
                x0, x1 = max(0, box[1].start - 1), min(out.shape[1], box[1].stop + 1)
                added_region = added_labels[y0:y1, x0:x1] == label_id
                contact = (ndimage.binary_dilation(added_region, structure=structure) &
                           (old_labels[y0:y1, x0:x1] > 0))
                distinct = np.unique(old_labels[y0:y1, x0:x1][contact])
                if len(distinct) != 1:
                    out[y0:y1, x0:x1][added_region] = 0

    for owner_id in (1, 2):
        for conn in (1, 2):
            if not _component_identity(before, out, owner_id, conn):
                raise DualOwnerLabReachHold('FROZEN_COMPONENT_IDENTITY_CHANGED')
    if (np.any((before > 0) & (out != before)) or
        np.any((out > 0) & (alpha == 0)) or
        np.any((out > 0) & (before == 0) & (class_ids != 32))):
        raise DualOwnerLabReachHold('SOURCE_OR_FROZEN_OWNER_REGRESSION')
    if (np.any((out == 1) & (before == 0) &
               ndimage.binary_dilation(out == 2, structure=structure8)) or
        np.any((out == 2) & (before == 0) &
               ndimage.binary_dilation(out == 1, structure=structure8))):
        raise DualOwnerLabReachHold('NEW_CROSS_OWNER_CONTACT')
    return out, {**receipt, 'dual_owner_domain': True,
                 'new_source_pixels': int(np.count_nonzero((before == 0) & (out > 0))),
                 'source_alpha_expansion': 0, 'frozen_owner_erasure': 0,
                 'class32_only': True,
                 'max_spatial_reach_px': MAX_SPATIAL_REACH_PX,
                 'opencv_lab_distance_limit': MAX_OPENCV_LAB_DISTANCE,
                 'competing_owner_margin_px': MIN_COMPETING_OWNER_DISTANCE_MARGIN_PX}
