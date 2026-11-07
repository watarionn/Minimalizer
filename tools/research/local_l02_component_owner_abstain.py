"""Exploratory class32 component-to-seed owner assignment with explicit abstention.

Frozen source-only class map and candidate pixels in, deterministic proposal out.
No human labels, thresholds tuned on character IDs, generated RGB or inpainting.
No owner or Golden promotion. Caller must authenticate private source/model SHA.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage


class ComponentOwnerHold(ValueError):
    pass


def propose_component_owners(*, class_ids, source_alpha, candidate, connectivity=4):
    """Assign entire selected class32 components only if exactly one seed type touches.

    Seed classes 5 jacket and 10 coat keep their own owner. A sleeve component
    touching both classes abstains, as does a component touching neither.
    This is an intentionally conservative *research proposal*, not semantic truth.
    """
    if type(class_ids) is not np.ndarray or class_ids.dtype != np.uint8 or class_ids.ndim != 2 or not class_ids.size:
        raise ComponentOwnerHold('INVALID_CLASS_IDS')
    shape = class_ids.shape
    if type(source_alpha) is not np.ndarray or source_alpha.dtype != np.uint8 or source_alpha.shape != shape:
        raise ComponentOwnerHold('INVALID_SOURCE_ALPHA')
    if type(candidate) is not np.ndarray or candidate.dtype != np.bool_ or candidate.shape != shape:
        raise ComponentOwnerHold('INVALID_CANDIDATE')
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ComponentOwnerHold('INVALID_CONNECTIVITY')
    present = source_alpha > 0
    if np.any(candidate & ~present):
        raise ComponentOwnerHold('CANDIDATE_OUTSIDE_SOURCE_ALPHA')
    if np.any(candidate & ~np.isin(class_ids, (5, 10, 32))):
        raise ComponentOwnerHold('NON_OUTERWEAR_CANDIDATE')
    owner = np.zeros(shape, dtype=np.uint8)
    jacket = candidate & (class_ids == 5)
    coat = candidate & (class_ids == 10)
    sleeve = candidate & (class_ids == 32)
    owner[jacket] = 1
    owner[coat] = 2
    structure = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    labels, n = ndimage.label(sleeve, structure=structure)
    counts = {'sleeve_components': int(n), 'jacket_assigned_components': 0,
              'coat_assigned_components': 0, 'ambiguous_components': 0,
              'orphan_components': 0, 'abstained_sleeve_px': 0,
              'assigned_sleeve_px': 0}
    # Only candidate seeds can claim a sleeve; background model class 5/10 is
    # not silently promoted into an owner by touching a selected sleeve.
    for index in range(1, n + 1):
        component = labels == index
        border = ndimage.binary_dilation(component, structure=structure)
        touches_jacket = bool(np.any(border & jacket))
        touches_coat = bool(np.any(border & coat))
        size = int(np.count_nonzero(component))
        if touches_jacket != touches_coat:
            oid = 1 if touches_jacket else 2
            owner[component] = oid
            counts['jacket_assigned_components' if oid == 1 else 'coat_assigned_components'] += 1
            counts['assigned_sleeve_px'] += size
        else:
            counts['ambiguous_components' if touches_jacket else 'orphan_components'] += 1
            counts['abstained_sleeve_px'] += size
    return owner, {
        'schema': 'minimalizer/local-l02/component-owner-abstain/v1',
        'connectivity': connectivity, **counts,
        'candidate_seed_jacket_px': int(np.count_nonzero(jacket)),
        'candidate_seed_coat_px': int(np.count_nonzero(coat)),
        'annotation_used_for_inference': False,
        'independent_holdout_proven': False,
        'semantic_quality_pass': False,
        'L02': 'HOLD', 'Golden': 'HOLD', 'L03': 'NO_GO', 'production': 'NO_GO',
    }
