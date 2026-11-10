"""Lane A research-only: compose Run32 sleeve proposal with merged contact safety.

The caller must authenticate the signed source and model predictions. No labels
or hand annotations are accepted. This is NOT semantic Phase4 approval.
"""
from __future__ import annotations

import hashlib

import numpy as np
from scipy import ndimage

from local_l02_guarded_sleeve_geodesic_shadow import propose_guarded_sleeve
from local_l02_frozen_component_gate import prune_frozen_component_joins
from local_l02_cross_owner_contact_gate import (
    prune_new_cross_owner_additions, verify_no_new_cross_owner_contacts,
)


class GuardedSleeveContactHold(ValueError):
    pass


def propose_contact_safe_sleeve(*, class_ids: np.ndarray,
                                anime_classes: np.ndarray,
                                source_alpha: np.ndarray,
                                frozen_candidate: np.ndarray,
                                frozen_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    """Conservatively keep only source-bound, 4-connected, contact-safe additions.

    Owner 0 means abstain; 1/2 mean jacket/coat. Existing owner pixels cannot
    be erased or reassigned. This wrapper does not accept an approval mask.
    """
    proposed, proposal = propose_guarded_sleeve(
        class_ids=class_ids, anime_classes=anime_classes,
        source_alpha=source_alpha, frozen_candidate=frozen_candidate,
        frozen_owner=frozen_owner, connectivity=4,
    )
    repaired, contact = prune_new_cross_owner_additions(
        before=frozen_owner, proposed=proposed,
    )
    repaired, component_receipt = prune_frozen_component_joins(
        frozen_owner=frozen_owner, proposed_owner=repaired,
    )
    if np.any((frozen_owner != 0) & (repaired != frozen_owner)):
        raise GuardedSleeveContactHold('FROZEN_OWNER_CHANGED')
    if np.any((repaired != 0) & (source_alpha == 0)):
        raise GuardedSleeveContactHold('OWNER_OUTSIDE_SOURCE_ALPHA')
    if np.any((repaired != 0) & ~frozen_candidate):
        raise GuardedSleeveContactHold('OWNER_OUTSIDE_FROZEN_CANDIDATE')
    if np.any((repaired != 0) & ~np.isin(class_ids, (5, 10, 32))):
        raise GuardedSleeveContactHold('OWNER_CLASS_INVALID')
    verify_no_new_cross_owner_contacts(before=frozen_owner, after=repaired)
    structure = ndimage.generate_binary_structure(2, 1)
    for owner_id in (1, 2):
        seeds = frozen_owner == owner_id
        mask = repaired == owner_id
        if np.any(mask & ~ndimage.binary_propagation(
                seeds, structure=structure, mask=mask)):
            raise GuardedSleeveContactHold('DISCONNECTED_OWNER_ADDITION')
    added = (frozen_owner == 0) & (repaired > 0)
    return repaired, {
        'schema': 'minimalizer/local-l02/contact-safe-run32-sleeve/v1',
        'proposed_additions_px': proposal['added_sleeve_pixels'],
        'retained_additions_px': int(np.count_nonzero(added)),
        'pruned_additions_px': proposal['added_sleeve_pixels'] - int(np.count_nonzero(added)),
        'owner_sha256': hashlib.sha256(repaired.tobytes()).hexdigest(),
        'frozen_owner_modified_px': 0,
        'new_cross_owner_edges': 0,
        'contact_receipt': contact,
        'component_receipt': component_receipt,
        'same_owner_component_identity_4_and_8': 'PRESERVED',
        'human_annotations_used_for_inference': False,
        'signed_source_authenticated_by_caller_required': True,
        'signed_source_verified_here': False,
        'unseen_character_quality': 'PENDING',
        'semantic_quality': 'FAIL',
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
