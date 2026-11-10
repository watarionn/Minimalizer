"""Source-only Phase4 research gate: protect jacket/coat seeds and topology.

No pixel painting, owner assignment, human annotation or release promotion.
A PASS here is structural only and never proves garment semantics.
"""
import numpy as np
from scipy import ndimage

class OwnerSeedIntegrityHold(ValueError):
    pass


def verify_owner_seed_integrity(*, before, after, class_ids, source_alpha):
    arrays = (before, after, class_ids, source_alpha)
    if any(type(a) is not np.ndarray or a.dtype != np.uint8 or a.ndim != 2 or not a.size for a in arrays):
        raise OwnerSeedIntegrityHold('INVALID_UINT8_INPUT')
    if any(a.shape != before.shape for a in arrays):
        raise OwnerSeedIntegrityHold('SHAPE_MISMATCH')
    if np.any(before > 2) or np.any(after > 2) or np.any(class_ids >= 47):
        raise OwnerSeedIntegrityHold('INVALID_CLASS_OR_OWNER')
    if np.any(((before != 0) | (after != 0)) & (source_alpha == 0)):
        raise OwnerSeedIntegrityHold('OWNER_OUTSIDE_SOURCE')
    if np.any((after != 0) & (after != before)):
        raise OwnerSeedIntegrityHold('OWNER_PROMOTION_OR_REASSIGNMENT')
    for owners in (before, after):
        if np.any((owners == 1) & ~np.isin(class_ids, (5, 32))) or np.any((owners == 2) & ~np.isin(class_ids, (10, 32))):
            raise OwnerSeedIntegrityHold('OWNER_CLASS_CONFLICT')
    count = 0
    for owner, seed in ((1, 5), (2, 10)):
        old = before == owner
        new = after == owner
        for connectivity in (4, 8):
            structure = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
            old_ids, n_old = ndimage.label(old, structure)
            new_ids, n_new = ndimage.label(new, structure)
            if n_old != n_new:
                raise OwnerSeedIntegrityHold(f'OWNER_COMPONENT_LOSS_OR_SPLIT_{owner}_{connectivity}')
            if not n_old:
                continue
            pairs = np.unique(old_ids[new].astype(np.int64) * (n_new + 1) + new_ids[new])
            if not np.array_equal(pairs // (n_new + 1), np.arange(1, n_old + 1)):
                raise OwnerSeedIntegrityHold(f'OWNER_COMPONENT_REMAP_{owner}_{connectivity}')
            had = np.bincount(old_ids[old & (class_ids == seed)], minlength=n_old + 1) > 0
            retained = np.bincount(old_ids[new & (class_ids == seed)], minlength=n_old + 1) > 0
            if np.any(had[1:] & ~retained[1:]) or np.any(~had[1:]):
                raise OwnerSeedIntegrityHold(f'OWNER_SEED_ERASURE_OR_ABSENCE_{owner}_{connectivity}')
            count += n_old
    return {'schema':'minimalizer/local-l02/owner-seed-integrity/v1',
            'verified_owner_components_4_and_8':int(count),
            'added_or_reassigned_pixels':0,
            'human_annotations_used_for_inference':False,
            'semantic_quality_pass':False,'independent_unseen_character_pass':False,
            'L02':'HOLD','L03':'NO_GO','Golden':'HOLD','production':'NO_GO'}
