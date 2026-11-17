"""Post-inference audit of mixed semantic evidence inside frozen class32 islands.

This function is NEVER an inference component. It consumes human-reviewed
masks only after a source-only candidate and its digest have been frozen.
Unknown pixels are neither negatives nor safe-to-delete pixels. It returns
source-free aggregate counts, never masks, coordinates or pixel samples.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi


class Class32PostscoreHold(ValueError):
    """An incomplete or inconsistent postscore domain was provided."""


def audit_class32_component_semantics(*, class_ids: np.ndarray,
                                     source_alpha: np.ndarray,
                                     reviewed_outerwear: np.ndarray,
                                     reviewed_underlayer: np.ndarray,
                                     reviewed_arm_skin: np.ndarray,
                                     reviewed_labelled: np.ndarray,
                                     connectivity: int = 4,
                                     minimum_component_pixels: int = 500) -> dict:
    """Score model class32 islands; never derive a proposal from human labels.

    The mixed_* counts establish that deleting an entire class32 island
    would erase reviewed true garment. Unreviewed is strictly unknown, not
    a known negative. Components are reported by size only, without geometry.
    """
    arrays = (class_ids, source_alpha, reviewed_outerwear,
              reviewed_underlayer, reviewed_arm_skin, reviewed_labelled)
    if (any(type(a) is not np.ndarray or a.dtype != np.uint8 or a.ndim != 2
            for a in arrays) or not class_ids.size or
            any(a.shape != class_ids.shape for a in arrays) or
            connectivity not in (4, 8) or
            type(minimum_component_pixels) is not int or
            minimum_component_pixels < 1):
        raise Class32PostscoreHold('INVALID_POSTSCORE_DOMAIN')
    garment = reviewed_outerwear > 0
    underlayer = reviewed_underlayer > 0
    arm = reviewed_arm_skin > 0
    labelled = reviewed_labelled > 0
    opaque = source_alpha > 0
    if (np.any((garment | underlayer | arm) & ~labelled) or
            np.any(labelled & ~opaque) or
            np.any(garment & underlayer) or np.any(garment & arm) or
            np.any(underlayer & arm)):
        raise Class32PostscoreHold('CONFLICTING_REVIEWED_LABELS')
    mask = (class_ids == 32) & opaque
    structure = ndi.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    components, count = ndi.label(mask, structure=structure)
    # Aggregate once instead of allocating a full-image mask per component.
    sizes = np.bincount(components[mask], minlength=count + 1)
    outerwear_counts = np.bincount(components[mask & garment], minlength=count + 1)
    underlayer_counts = np.bincount(components[mask & underlayer], minlength=count + 1)
    arm_counts = np.bincount(components[mask & arm], minlength=count + 1)
    unknown_counts = np.bincount(components[mask & ~labelled], minlength=count + 1)
    result = []
    for component_id in np.flatnonzero(sizes[1:] >= minimum_component_pixels) + 1:
        size = int(sizes[component_id])
        true = int(outerwear_counts[component_id])
        lower = int(underlayer_counts[component_id])
        skin = int(arm_counts[component_id])
        unknown = int(unknown_counts[component_id])
        result.append({
            'class32_source_pixels': size,
            'reviewed_outerwear_pixels': true,
            'reviewed_underlayer_pixels': lower,
            'reviewed_arm_skin_pixels': skin,
            'other_reviewed_pixels': size - true - lower - skin - unknown,
            'unreviewed_unknown_pixels': unknown,
            'mixed_outerwear_underlayer': true > 0 and lower > 0,
            'mixed_outerwear_arm': true > 0 and skin > 0,
            'whole_component_removal_would_erase_reviewed_outerwear': true > 0,
        })
    result.sort(key=lambda x: x['class32_source_pixels'], reverse=True)
    return {
        'schema': 'minimalizer/local-l02/class32-component-semantic-postscore/v1',
        'connectivity': connectivity,
        'minimum_component_pixels': minimum_component_pixels,
        'component_count_all_sizes': count,
        'components_above_minimum': result,
        'unknown_is_not_negative': True,
        'human_labels_used_only_for_postscore': True,
        'semantic_owner_authorized': False,
        'quality': 'FAIL', 'Phase4': 'FAIL', 'L02': 'HOLD',
        'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
    }
