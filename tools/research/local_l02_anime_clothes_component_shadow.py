"""A-only, dormant source-only class32 component recovery hypothesis.

The independent AnimeSeg class10 observation is *general clothing*, not an
outerwear or skin exclusion oracle. The caller must independently authenticate
original RGBA, class maps, frozen owner, and AnimeSeg observation BEFORE this
function. No human annotation is an inference input. This is not a Phase4,
Golden, L03, or production approval. Tested on exposed H06/H08 only.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi


class AnimeClothesComponentHold(ValueError):
    """The source-only hypothesis violates a frozen-owner safety contract."""


def _component_identity(before: np.ndarray, after: np.ndarray,
                        owner_id: int, connectivity: int) -> tuple[int, int]:
    st = ndi.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    old, n_old = ndi.label(before == owner_id, structure=st)
    new, n_new = ndi.label(after == owner_id, structure=st)
    if n_old != n_new:
        raise AnimeClothesComponentHold('FROZEN_COMPONENT_COUNT_CHANGED')
    if n_old:
        frozen = before == owner_id
        pairs = np.unique(np.stack((old[frozen], new[frozen]), axis=1), axis=0)
        if (len(pairs) != n_old or np.any(pairs == 0) or
                len(np.unique(pairs[:, 0])) != n_old or
                len(np.unique(pairs[:, 1])) != n_old):
            raise AnimeClothesComponentHold('FROZEN_COMPONENT_IDENTITY_CHANGED')
    return n_old, n_new


def propose_anime_clothes_component_shadow(*, source_rgba: np.ndarray,
                                           class_ids: np.ndarray,
                                           anime_classes: np.ndarray,
                                           frozen_owner: np.ndarray
                                           ) -> tuple[np.ndarray, dict]:
    """Propose original-source opaque class32 ∩ independent clothes pixels.

    Assign a whole class32 component's *hypothesized owner* by dominant
    eight-neighbor boundary contact (>= 1.5x the competitor). Only the
    AnimeSeg clothes-supported subset may be added. A nearest-frozen-component
    Voronoi seam and connectivity pruning forbid merging old owner islands.
    Every accepted new pixel must attach to an original 4-connected owner
    component. Unknown/other classes are abstentions, never negatives.
    """
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8 or
            source_rgba.ndim != 3 or source_rgba.shape[2] != 4 or
            not source_rgba.size):
        raise AnimeClothesComponentHold('INVALID_SOURCE_RGBA')
    shape = source_rgba.shape[:2]
    if any(type(a) is not np.ndarray or a.dtype != np.uint8 or a.shape != shape
           for a in (class_ids, anime_classes, frozen_owner)):
        raise AnimeClothesComponentHold('INVALID_MODEL_OR_OWNER_ARRAY')
    if (np.any(class_ids >= 47) or np.any(anime_classes >= 12) or
            np.any(frozen_owner > 2) or
            np.any((frozen_owner > 0) & (source_rgba[..., 3] == 0))):
        raise AnimeClothesComponentHold('INVALID_FROZEN_SOURCE_DOMAIN')

    eight = np.ones((3, 3), dtype=bool)
    eligible = (class_ids == 32) & (source_rgba[..., 3] == 255)
    class32_regions, n_regions = ndi.label(eligible, structure=eight)
    region_sizes = np.bincount(class32_regions.ravel(), minlength=n_regions + 1)
    out = frozen_owner.copy()
    admitted_regions = 0

    for region_id in range(1, n_regions + 1):
        if region_sizes[region_id] < 500:
            continue
        region = class32_regions == region_id
        edge = ndi.binary_dilation(region, structure=eight)
        touches = [int(np.count_nonzero(edge & (frozen_owner == owner)))
                   for owner in (1, 2)]
        winner = int(np.argmax(touches)) + 1
        high, low = sorted(touches, reverse=True)
        if high < 10 or high * 2 < low * 3:
            continue
        other = 3 - winner
        proposed = (region & (anime_classes == 10) & (frozen_owner == 0) &
                    ~ndi.binary_dilation(frozen_owner == other, structure=eight))
        if not np.any(proposed):
            continue

        old_labels, n_old = ndi.label(
            frozen_owner == winner, structure=ndi.generate_binary_structure(2, 1))
        if not n_old:
            continue
        _, nearest_indices = ndi.distance_transform_edt(
            frozen_owner != winner, return_indices=True)
        nearest_label = old_labels[nearest_indices[0], nearest_indices[1]]
        # Reject both sides of any nearest-component boundary (8-neighbor).
        proposed &= ((nearest_label > 0) &
                     (ndi.minimum_filter(nearest_label, size=3) ==
                      ndi.maximum_filter(nearest_label, size=3)))
        if not np.any(proposed):
            continue
        added_labels, _ = ndi.label(proposed, structure=eight)
        touching = ndi.binary_dilation(frozen_owner == winner, structure=eight)
        connected_ids = np.unique(added_labels[touching & proposed])
        proposed &= np.isin(added_labels, connected_ids[connected_ids > 0])
        if np.any(proposed):
            out[proposed] = winner
            admitted_regions += 1

    # An 8-connected island can still be 4-disconnected. Reject all newly
    # created 4-islands instead of declaring the owner topology successful.
    for owner in (1, 2):
        labels, _ = ndi.label(out == owner,
                              structure=ndi.generate_binary_structure(2, 1))
        frozen_labels = np.unique(labels[frozen_owner == owner])
        orphan = ((out == owner) & (frozen_owner == 0) &
                  ~np.isin(labels, frozen_labels[frozen_labels > 0]))
        out[orphan] = 0

    for owner in (1, 2):
        for connectivity in (4, 8):
            _component_identity(frozen_owner, out, owner, connectivity)
    added = (frozen_owner == 0) & (out > 0)
    if (np.any((frozen_owner > 0) & (out != frozen_owner)) or
            np.any(added & ((class_ids != 32) | (anime_classes != 10) |
                            (source_rgba[..., 3] != 255)))):
        raise AnimeClothesComponentHold('FROZEN_OWNER_OR_SOURCE_REGRESSION')
    for owner in (1, 2):
        if np.any(added & (out == owner) &
                  ndi.binary_dilation(out == 3 - owner, structure=eight)):
            raise AnimeClothesComponentHold('NEW_CROSS_OWNER_CONTACT')
    return out, {
        'schema': 'minimalizer/local-l02/anime-clothes-component-shadow/v0',
        'added_source_pixels': int(np.count_nonzero(added)),
        'admitted_class32_regions': admitted_regions,
        'owner_reassigned_or_erased_pixels': 0,
        'new_cross_owner_contacts': 0,
        'source_pixels_generated': 0,
        'independent_anime_class10_is_general_clothing_only': True,
        'source_observer_owner_pins_verified_by_this_function': False,
        'human_annotations_used_for_inference': False,
        'known_cases_exposed': True,
        'unseen_signed_blind': 'PENDING',
        'semantic_quality_pass': False, 'quality': 'FAIL',
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
