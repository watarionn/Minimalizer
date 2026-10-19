"""Source-only L02 owner-topology witness. Research gate, never release approval.

Detects joins/splits of *frozen* owner components, even if total component
counts cancel. Accepts no human labels, masks, ROI, or annotation coordinates.
The function does not edit owner arrays or claim semantic correctness.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage


class ComponentJoinHold(ValueError):
    """Invalid provenance or forbidden owner transition."""


def audit_owner_component_joins(*, source_alpha: np.ndarray,
                                frozen_owner: np.ndarray,
                                proposed_owner: np.ndarray) -> dict:
    """Return source-only component-identity witness for 4 and 8 neighbors.

    0=ABSTAIN, 1=jacket, 2=coat. Previously assigned pixels must remain
    immutable. Newly owned pixels must belong to the signed source alpha.
    Component joins require a separate semantic/occlusion review. A zero-join
    result alone does NOT establish Phase4 semantic quality.
    """
    arrays = (source_alpha, frozen_owner, proposed_owner)
    if any(type(a) is not np.ndarray or a.dtype != np.uint8 or a.ndim != 2
           or not a.size for a in arrays):
        raise ComponentJoinHold('INVALID_UINT8_ARRAY')
    if any(a.shape != source_alpha.shape for a in arrays):
        raise ComponentJoinHold('SHAPE_MISMATCH')
    if np.any(frozen_owner > 2) or np.any(proposed_owner > 2):
        raise ComponentJoinHold('INVALID_OWNER')
    if np.any(((frozen_owner != 0) | (proposed_owner != 0)) & (source_alpha == 0)):
        raise ComponentJoinHold('OWNER_OUTSIDE_SOURCE')
    if np.any((frozen_owner != 0) & (frozen_owner != proposed_owner)):
        raise ComponentJoinHold('FROZEN_OWNER_CHANGED')

    details = {}
    for owner in (1, 2):
        for connectivity in (4, 8):
            structure = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
            old_ids, old_count = ndimage.label(frozen_owner == owner, structure=structure)
            new_ids, new_count = ndimage.label(proposed_owner == owner, structure=structure)
            frozen = frozen_owner == owner
            old_on_frozen = old_ids[frozen].astype(np.int64)
            new_on_frozen = new_ids[frozen].astype(np.int64)
            if np.any(new_on_frozen == 0):
                raise ComponentJoinHold('FROZEN_COMPONENT_ERASURE')
            pairs = np.unique(old_on_frozen * (new_count + 1) + new_on_frozen)
            old_seen = pairs // (new_count + 1)
            new_seen = pairs % (new_count + 1)
            old_pair_counts = np.bincount(old_seen, minlength=old_count + 1)
            new_pair_counts = np.bincount(new_seen, minlength=new_count + 1)
            joined = int(np.count_nonzero(new_pair_counts[1:] > 1))
            split = int(np.count_nonzero(old_pair_counts[1:] > 1))
            max_joined = int(new_pair_counts[1:].max()) if new_count else 0
            details[f'owner{owner}_{connectivity}'] = {
                'frozen_components': int(old_count),
                'proposed_components': int(new_count),
                'merged_component_groups': joined,
                'split_component_groups': split,
                'max_frozen_components_in_one_proposed': max_joined,
            }
    joins = sum(v['merged_component_groups'] for v in details.values())
    splits = sum(v['split_component_groups'] for v in details.values())
    return {
        'schema': 'minimalizer/local-l02/component-join-witness/v1',
        'component_witnesses': details,
        'merged_component_groups_total': joins,
        'split_component_groups_total': splits,
        'topology_review_required': bool(joins or splits),
        'source_pixels_generated': 0,
        'frozen_owner_changed_pixels': 0,
        'human_annotations_used_for_inference': False,
        'semantic_quality_pass': False,
        'independent_unseen_character_pass': False,
        'source_only_phase4_quality_pass': False,
        'L02': 'HOLD', 'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
    }
