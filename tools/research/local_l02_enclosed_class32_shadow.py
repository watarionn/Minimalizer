"""Research-only source-bound recovery of *strictly enclosed* class32 voids.

Input contains only frozen model classes, original source alpha, and source-only
owner proposals. No human review masks, coordinates, generated pixels, or
postscore values enter the proposal. This is not Phase4 quality approval.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage


class EnclosedClass32Hold(ValueError):
    pass


def propose_enclosed_class32_shadow(*, source_alpha: np.ndarray,
                                     class_ids: np.ndarray,
                                     original_owner: np.ndarray,
                                     baseline_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    arrays = (source_alpha, class_ids, original_owner, baseline_owner)
    if any(type(a) is not np.ndarray or a.dtype != np.uint8 or a.ndim != 2 or not a.size
           for a in arrays):
        raise EnclosedClass32Hold('INVALID_SOURCE_ONLY_INPUT')
    if any(a.shape != source_alpha.shape for a in arrays):
        raise EnclosedClass32Hold('SHAPE_MISMATCH')
    if np.any(class_ids >= 47) or np.any(original_owner > 2) or np.any(baseline_owner > 2):
        raise EnclosedClass32Hold('INVALID_MODEL_OR_OWNER_DOMAIN')
    alpha = source_alpha > 0
    if np.any((original_owner > 0) & ~alpha) or np.any((baseline_owner > 0) & ~alpha):
        raise EnclosedClass32Hold('OWNER_OUTSIDE_SIGNED_SOURCE')
    if np.any((original_owner > 0) & (baseline_owner > 0) & (original_owner != baseline_owner)):
        raise EnclosedClass32Hold('ORIGINAL_OWNER_REASSIGNED')
    # 8-neighbour *background* connectivity avoids falsely filling diagonally
    # open gaps, which a 4-neighbour background definition can call enclosed.
    strictly_enclosed = ndimage.binary_fill_holes(
        baseline_owner > 0, structure=np.ones((3, 3), dtype=bool))
    eligible = (strictly_enclosed & (baseline_owner == 0) & (class_ids == 32)
                & alpha & (original_owner == 0))
    result = baseline_owner.copy()
    present = [owner for owner in (1, 2) if np.any(baseline_owner == owner)]
    if eligible.any() and present:
        # Original, source-only owner seeds. Never use a human review mask.
        distances = {owner: ndimage.distance_transform_edt(baseline_owner != owner)
                     for owner in present}
        if len(present) == 1:
            result[eligible] = present[0]
        else:
            a, b = present
            result[eligible & (distances[a] < distances[b])] = a
            result[eligible & (distances[b] < distances[a])] = b
            # Exact geodesic-equidistance ties stay unknown, not a forced OR.
    # Do not create any new 8-neighbour jacket/coat contact. Even if each
    # owner's connected-component count is unchanged, extra cross-owner
    # boundaries can silently change layering/occlusion. Retract only newly
    # proposed pixels; never alter a baseline owner or a previous veto.
    for _ in range(3):
        unsafe = np.zeros(result.shape, dtype=bool)
        for owner, other in ((1, 2), (2, 1)):
            unsafe |= ((baseline_owner == 0) & (result == owner)
                       & ndimage.binary_dilation(result == other,
                                                 structure=np.ones((3, 3), dtype=bool)))
        if not np.any(unsafe):
            break
        result[unsafe] = 0
    else:
        raise EnclosedClass32Hold('CROSS_OWNER_BOUNDARY_NOT_STABLE')
    for connectivity in (1, 2):
        structure = ndimage.generate_binary_structure(2, connectivity)
        old_contacts = ndimage.binary_dilation(baseline_owner == 1, structure=structure) & (baseline_owner == 2)
        new_contacts = ndimage.binary_dilation(result == 1, structure=structure) & (result == 2)
        if np.any(new_contacts & ~old_contacts):
            raise EnclosedClass32Hold('NEW_CROSS_OWNER_CONTACT')
    if np.any((original_owner > 0) & (result != baseline_owner)):
        raise EnclosedClass32Hold('PREVIOUS_VETO_OR_OWNER_MODIFIED')
    if np.any((result > 0) & ~alpha) or np.any((result != baseline_owner) & ~eligible):
        raise EnclosedClass32Hold('SOURCE_OR_CLASS_ESCAPE')
    # Invariant: no frozen component is erased, split, or joined in either
    # neighborhood. Count alone is insufficient; require a one-to-one mapping.
    for owner in (1, 2):
        for connectivity in (1, 2):
            structure = ndimage.generate_binary_structure(2, connectivity)
            old, n_old = ndimage.label(baseline_owner == owner, structure=structure)
            new, n_new = ndimage.label(result == owner, structure=structure)
            if n_old != n_new:
                raise EnclosedClass32Hold('OWNER_COMPONENT_TOPOLOGY_CHANGED')
            if n_old:
                old_ids = old[baseline_owner == owner]
                new_ids = new[baseline_owner == owner]
                pairs = np.unique(np.stack((old_ids, new_ids), axis=1), axis=0)
                if (len(pairs) != n_old or np.any(pairs == 0)
                        or len(np.unique(pairs[:, 0])) != n_old
                        or len(np.unique(pairs[:, 1])) != n_new):
                    raise EnclosedClass32Hold('OWNER_COMPONENT_IDENTITY_CHANGED')
    added = (result != baseline_owner)
    return result, {
        'schema': 'minimalizer/local-l02/strict-enclosed-class32-shadow/v1',
        'source_only_added_px': int(np.count_nonzero(added)),
        'still_abstained_enclosed_class32_px': int(np.count_nonzero(eligible & (result == 0))),
        'source_pixels_generated': 0,
        'original_owner_modified_px': 0,
        'new_cross_owner_contact_px': 0,
        'human_annotations_used_for_inference': False,
        'unseen_character_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
