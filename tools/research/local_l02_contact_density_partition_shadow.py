"""Research-only, known-case-exposed class32 sleeve component hypothesis.

Promotes no model to semantic authority. Proposals are frozen before any
human postscore. Only source-alpha class32 with independent generic clothes
observation and substantial attachment to preexisting owner are eligible.
A multi-owner partition prevents merging frozen components.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage

class ContactDensityHold(ValueError):
    pass

MIN_COMPONENT_PIXELS = 1024
MIN_OWNER_CONTACT_FRACTION = 0.10
MIN_INDEPENDENT_GENERIC_CLOTHES = 32


def propose_contact_density_partition_shadow(*, source_rgba, class_ids,
                                               anime_classes, baseline_owner):
    shape = getattr(baseline_owner, 'shape', None)
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8 or
            source_rgba.ndim != 3 or source_rgba.shape[-1] != 4 or
            type(baseline_owner) is not np.ndarray or baseline_owner.dtype != np.uint8 or
            baseline_owner.ndim != 2 or baseline_owner.size == 0 or
            source_rgba.shape[:2] != shape):
        raise ContactDensityHold('INVALID_SIGNED_RGBA_OR_OWNER')
    if any(type(a) is not np.ndarray or a.dtype != np.uint8 or a.shape != shape
           for a in (class_ids, anime_classes)):
        raise ContactDensityHold('INVALID_FROZEN_OBSERVERS')
    if (np.any(class_ids >= 47) or np.any(anime_classes >= 12) or
            np.any(baseline_owner > 2) or
            np.any((baseline_owner > 0) & (source_rgba[..., 3] == 0))):
        raise ContactDensityHold('INVALID_DOMAIN_OR_SOURCE')
    st8 = np.ones((3, 3), dtype=bool)
    eligible = ((class_ids == 32) & (baseline_owner == 0) &
                (source_rgba[..., 3] > 0))
    islands, n_islands = ndimage.label(eligible, structure=st8)
    sizes = np.bincount(islands.ravel())
    contact = ndimage.binary_dilation(baseline_owner > 0, structure=st8) & eligible
    contacts = np.bincount(islands[contact], minlength=n_islands+1)
    independent = np.bincount(islands[eligible & (anime_classes == 10)], minlength=n_islands+1)
    keep_ids = ((sizes >= MIN_COMPONENT_PIXELS) &
                (contacts >= np.ceil(MIN_OWNER_CONTACT_FRACTION * sizes)) &
                (independent >= MIN_INDEPENDENT_GENERIC_CLOTHES))
    keep_ids[0] = False
    possible = eligible & keep_ids[islands]
    # Distinct immutable 4-connected component identities across both owners.
    st4 = ndimage.generate_binary_structure(2, 1)
    original_components = np.zeros(shape, dtype=np.int32)
    label_owner = {}
    n_components = 0
    for owner in (1, 2):
        ids, count = ndimage.label(baseline_owner == owner, structure=st4)
        original_components[ids > 0] = ids[ids > 0] + n_components
        for local in range(1, count + 1):
            label_owner[n_components+local] = owner
        n_components += count
    if n_components == 0:
        raise ContactDensityHold('NO_FROZEN_OWNER_SEED')
    _, nearest = ndimage.distance_transform_edt(original_components == 0,
                                                return_indices=True)
    assign = np.zeros(shape, dtype=np.int32)
    assign[possible] = original_components[nearest[0][possible], nearest[1][possible]]
    # Strip added pixels touching a different positive frozen component,
    # including diagonal contacts, without changing any original owner.
    full_labels = original_components.copy()
    full_labels[possible] = assign[possible]
    h, w = shape
    conflict = np.zeros(shape, dtype=bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == dx == 0:
                continue
            ya, yb = slice(max(0, -dy), h-max(0, dy)), slice(max(0, dy), h-max(0, -dy))
            xa, xb = slice(max(0, -dx), w-max(0, dx)), slice(max(0, dx), w-max(0, -dx))
            a, b = full_labels[ya, xa], full_labels[yb, xb]
            conflict[ya, xa] |= (a > 0) & (b > 0) & (a != b)
    assign[possible & conflict] = 0
    # Retain only additions connected via 4-neighbour paths to their frozen seed.
    out = baseline_owner.copy()
    for comp_id, owner in label_owner.items():
        mask = assign == comp_id
        if not np.any(mask):
            continue
        seeds = ndimage.binary_dilation(original_components == comp_id, structure=st4) & mask
        reached = ndimage.binary_propagation(seeds, structure=st4, mask=mask)
        out[reached] = owner
    if np.any((baseline_owner > 0) & (out != baseline_owner)) or np.any(
            (out > 0) & (source_rgba[..., 3] == 0)) or np.any(
            (baseline_owner == 0) & (out > 0) & ~possible):
        raise ContactDensityHold('FROZEN_SOURCE_INVARIANT')
    from local_l02_hue_extended_owner_shadow import _assert_component_identity, ExtendedOwnerHold
    try:
        for owner in (1, 2):
            for neighborhood in (4, 8):
                _assert_component_identity(baseline_owner, out, owner, neighborhood)
    except ExtendedOwnerHold as exc:
        raise ContactDensityHold('OWNER_COMPONENT_IDENTITY_HOLD') from exc
    from local_l02_cross_owner_contact_gate import verify_no_new_cross_owner_contacts, CrossOwnerContactHold
    try:
        verify_no_new_cross_owner_contacts(before=baseline_owner, after=out)
    except CrossOwnerContactHold as exc:
        raise ContactDensityHold('CROSS_OWNER_CONTACT_HOLD') from exc
    return out, {
        'schema':'minimalizer/local-l02/contact-density-partition-shadow/v0',
        'source_only_eligible_px':int(np.count_nonzero(possible)),
        'new_source_supported_px':int(np.count_nonzero((baseline_owner == 0)&(out > 0))),
        'eligible_components':int(np.count_nonzero(keep_ids)),
        'frozen_owner_changes':0,
        'human_annotations_used_for_inference':False,
        'known_case_explored':True,
        'unseen_character_pass':False,'Phase4':'FAIL','L02':'HOLD','L03':'NO_GO',
        'Golden':'HOLD','production':'NO_GO',
    }
