"""Source-only, conservative postguard for hue-conflict class32 abstention.

No human annotations, masks or coordinates are read. A removed class32 island
with *direct* original class5/10 owner-seed contact is restored to its frozen
owner instead of being treated as an untrusted underlayer. This is an
exploratory structural safeguard, not a semantic owner approval.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from local_l02_hue_conflict_abstain import (
    ColorConflictHold, propose_class32_hue_conflict_abstention,
)


def propose_hue_conflict_seed_contact_guard(source_rgba, class_ids, frozen_owner):
    """Return (shadow_owner, aggregate). Preserve direct seed-attached losses.

    Only source RGBA, frozen model class IDs and frozen owner are inference
    inputs. No image synthesis or owner promotion. Unknown owner stays unknown.
    """
    provisional, base = propose_class32_hue_conflict_abstention(
        source_rgba, class_ids, frozen_owner
    )
    # The underlying function already checks shape, dtype, owner and alpha.
    structure = np.ones((3, 3), dtype=np.uint8)
    result = provisional.copy()
    restored_regions = 0
    restored_pixels = 0
    ambiguous_veto_regions = 0
    ambiguous_veto_pixels = 0
    # Work within each *frozen owner ID* independently. This prevents a
    # touching jacket/coat abstention region from restoring another owner.
    # Vectorized label membership avoids a full-image dilation per component.
    for owner_id, seed_class in ((1, 5), (2, 10)):
        removed_owner = (frozen_owner == owner_id) & (provisional == 0)
        labels, n = ndimage.label(removed_owner, structure=structure)
        if not n:
            continue
        seed = (frozen_owner == owner_id) & (class_ids == seed_class)
        seed_neighbour = ndimage.binary_dilation(seed, structure=structure)
        touching = np.unique(labels[removed_owner & seed_neighbour])
        touching = touching[touching > 0]
        if not touching.size:
            continue
        # A class32 fragment that contacts both jacket and coat cannot be
        # promoted back to a single owner just because its frozen label says so.
        # An opposite-owner contact is a source-only ambiguity signal, not
        # proof of which garment is correct. Keep that fragment abstained.
        other_owner = (frozen_owner != 0) & (frozen_owner != owner_id)
        other_neighbour = ndimage.binary_dilation(other_owner, structure=structure)
        ambiguous = np.unique(labels[removed_owner & other_neighbour])
        ambiguous = ambiguous[ambiguous > 0]
        vetoed = np.intersect1d(touching, ambiguous)
        ambiguous_veto_regions += int(vetoed.size)
        veto_lookup = np.zeros(n + 1, dtype=bool)
        veto_lookup[vetoed] = True
        ambiguous_veto_pixels += int(np.count_nonzero(veto_lookup[labels] & removed_owner))
        protect_lookup = np.zeros(n + 1, dtype=bool)
        protect_lookup[touching] = True
        protect_lookup[vetoed] = False
        protected = protect_lookup[labels]
        result[protected] = frozen_owner[protected]
        restored_regions += int(touching.size)
        restored_pixels += int(protected.sum())
    if np.any((result != 0) & (result != frozen_owner)):
        raise ColorConflictHold('POSTGUARD_OWNER_PROMOTION')
    if np.any((frozen_owner == 0) & (result != 0)):
        raise ColorConflictHold('POSTGUARD_UNKNOWN_PROMOTION')
    if np.any((result != 0) & (source_rgba[:, :, 3] == 0)):
        raise ColorConflictHold('POSTGUARD_ALPHA')
    return result, {
        'schema': 'minimalizer/l02/hue-seed-contact-shadow/v1',
        'provisional_abstained': base['abstained_pixels'],
        'seed_contact_restored_regions': restored_regions,
        'seed_contact_restored_pixels': restored_pixels,
        'dual_owner_contact_veto_regions': ambiguous_veto_regions,
        'dual_owner_contact_veto_pixels': ambiguous_veto_pixels,
        'final_abstained_pixels': int(np.count_nonzero(result != frozen_owner)),
        'owner_promotions': 0,
        'human_annotations_used_for_inference': False,
        'semantic_quality_pass': False,
        'independent_unseen_character_pass': False,
        'release_authorized': False,
    }
