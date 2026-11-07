"""Research-only source-bound class30 owner extension (known-case hypothesis).

Class30 is a SegFormer category, NOT outerwear ground truth. Its pixels are
eligible only when original alpha is nonzero and independent AnimeSeg says
*generic clothes*. A whole 4-connected candidate fragment touching both
jacket and coat seeds abstains. Remaining candidate pixels must be reachable
by 4-connected source-only paths. Immutable owners and both 4/8 component
identities are preserved. No human labels, manual coordinates, generation,
face-part drawing, release authority or unknown-character PASS.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage
from local_l02_guarded_sleeve_geodesic_shadow import _distance_inside
from local_l02_source_palette_sleeve_shadow import _topology_fixed_point
from local_l02_hue_extended_owner_shadow import _assert_component_identity, ExtendedOwnerHold

class Class30Hold(ValueError):
    pass


def propose_class30_extension_shadow(*, source_rgba, class_ids, anime_classes,
                                     frozen_owner, safe_baseline):
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8 or
            source_rgba.ndim != 3 or source_rgba.shape[-1] != 4 or not source_rgba.size):
        raise Class30Hold('INVALID_RGBA')
    shape = source_rgba.shape[:2]
    if (type(class_ids) is not np.ndarray or class_ids.dtype != np.uint8 or
            class_ids.shape != shape):
        raise Class30Hold('INVALID_CLASS')
    if any(type(x) is not np.ndarray or x.dtype != np.uint8 or x.shape != shape
           for x in (anime_classes, frozen_owner, safe_baseline)):
        raise Class30Hold('INVALID_OBSERVERS')
    if (np.any(class_ids >= 47) or np.any(frozen_owner > 2) or
            np.any(safe_baseline > 2)):
        raise Class30Hold('INVALID_OWNER_OR_CLASS_DOMAIN')
    if np.any((frozen_owner > 0) & (safe_baseline != frozen_owner)):
        raise Class30Hold('FROZEN_OWNER_CHANGED')
    if np.any((safe_baseline > 0) & (source_rgba[..., 3] == 0)):
        raise Class30Hold('BASELINE_ALPHA_ESCAPE')
    if (np.any((safe_baseline == 1) & ~np.isin(class_ids, (5,32,29,30,31))) or
            np.any((safe_baseline == 2) & ~np.isin(class_ids, (10,32,29,30,31)))):
        raise Class30Hold('BASELINE_CLASS_CONFLICT')

    eligible = ((source_rgba[..., 3] > 0) & (class_ids == 30) &
                (anime_classes == 10) & (safe_baseline == 0))
    jacket, coat = safe_baseline == 1, safe_baseline == 2
    st4 = ndimage.generate_binary_structure(2, 1)
    labels, n = ndimage.label(eligible, structure=st4)
    ambiguous = np.zeros_like(eligible)
    if n:
        near_j = ndimage.binary_dilation(jacket, structure=st4) & eligible
        near_c = ndimage.binary_dilation(coat, structure=st4) & eligible
        jids = np.unique(labels[near_j]); cids = np.unique(labels[near_c])
        shared = np.intersect1d(jids[jids > 0], cids[cids > 0])
        if shared.size:
            ambiguous = np.isin(labels, shared)
            eligible &= ~ambiguous
    dj = _distance_inside(eligible, jacket, 4)
    dc = _distance_inside(eligible, coat, 4)
    out = safe_baseline.copy()
    out[(dj > 0) & ((dc < 0) | (dj < dc))] = 1
    out[(dc > 0) & ((dj < 0) | (dc < dj))] = 2
    try:
        out, removed = _topology_fixed_point(safe_baseline, out)
    except Exception as exc:
        raise Class30Hold('TOPOLOGY_FIXED_POINT_FAILED') from exc
    if np.any((safe_baseline > 0) & (out != safe_baseline)):
        raise Class30Hold('BASELINE_OWNER_ERASURE')
    for owner_id in (1, 2):
        for conn in (4, 8):
            try:
                _assert_component_identity(frozen_owner, out, owner_id, conn)
            except ExtendedOwnerHold as exc:
                raise Class30Hold('OWNER_TOPOLOGY_CHANGED') from exc
    added = (out != safe_baseline)
    if (np.any(added & ~eligible) or
            np.any((out > 0) & (source_rgba[..., 3] == 0))):
        raise Class30Hold('SOURCE_CLASS_ESCAPE')
    return out, {
        'schema': 'minimalizer/local-l02/class30-source-extension-shadow/v1',
        'source_only_added_px': int(added.sum()),
        'jacket_added_px': int(np.count_nonzero(added & (out == 1))),
        'coat_added_px': int(np.count_nonzero(added & (out == 2))),
        'ambiguous_class30_abstained_px': int(ambiguous.sum()),
        'topology_guard_removed_px': int(removed),
        'source_pixels_generated': 0, 'frozen_owner_modified': 0,
        'human_annotation_used_for_inference': False,
        'known_case_explored': True, 'quality': 'FAIL', 'Phase4': 'FAIL',
        'L02': 'HOLD', 'L03': 'NO_GO', 'Golden': 'HOLD',
        'production': 'NO_GO', 'unseen_character_pass': False,
    }
