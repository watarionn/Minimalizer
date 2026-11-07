"""Lane A research-only: conservatively admit disputed class32 clothing fragments.

Source-only exploratory hypothesis, NOT semantic or unseen-character evidence.
Only original-alpha class32 / independent generic-clothes-unknown (AnimeSeg 11)
pixels are eligible. An 8-connected component must have a substantial contact
boundary with ALREADY-OWNED class32 / independent generic-clothes (AnimeSeg 10)
pixels and exactly one owner type touching the component. Entire ambiguous
components abstain. No human labels, character IDs, hand coordinates, painting,
or model inference are used. This is not an approved Phase4 owner gate.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
import cv2
from local_l02_source_palette_sleeve_shadow import _topology_fixed_point
from local_l02_hue_extended_owner_shadow import _assert_component_identity, ExtendedOwnerHold

class IndependentContactHold(ValueError):
    pass

# Source-only structural support policy, frozen before evaluation.
MIN_CONTACT_PIXELS = 16
MIN_CONTACT_FRACTION = 0.01
# Reuse the pre-existing exploratory source-palette LAB cap.
MAX_LOCAL_LAB_DISTANCE = 25.0
MIN_COLOR_COHERENT_FRACTION = 0.75


def propose_independent_contact_shadow(*, source_rgba: np.ndarray,
                                        class_ids: np.ndarray,
                                        anime_classes: np.ndarray,
                                        baseline_owner: np.ndarray):
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8 or
            source_rgba.ndim != 3 or source_rgba.shape[-1] != 4 or not source_rgba.size):
        raise IndependentContactHold('INVALID_SOURCE')
    shape = source_rgba.shape[:2]
    if any(type(x) is not np.ndarray or x.dtype != np.uint8 or x.shape != shape
           for x in (class_ids, anime_classes, baseline_owner)):
        raise IndependentContactHold('INVALID_OBSERVER')
    if (np.any(class_ids >= 47) or np.any(anime_classes >= 12) or
            np.any(baseline_owner > 2) or
            np.any((baseline_owner > 0) & (source_rgba[..., 3] == 0))):
        raise IndependentContactHold('INVALID_DOMAIN_OR_ALPHA')
    # Only previously unowned class32 pixels with an independent unknown-class
    # observation are candidates. Unknown is NOT counted as a negative.
    candidate = ((class_ids == 32) & (anime_classes == 11) &
                 (baseline_owner == 0) & (source_rgba[..., 3] > 0))
    st8 = np.ones((3, 3), dtype=bool)
    labels, count = ndimage.label(candidate, structure=st8)
    # Distinct independent clothes-supported sleeve contacts, not any garment.
    anchor = (class_ids == 32) & (anime_classes == 10) & (baseline_owner > 0)
    anchor_touch = ndimage.binary_dilation(anchor, structure=st8) & candidate
    touch_j = ndimage.binary_dilation(baseline_owner == 1, structure=st8) & candidate
    touch_c = ndimage.binary_dilation(baseline_owner == 2, structure=st8) & candidate
    out = baseline_owner.copy()
    lab = cv2.cvtColor(source_rgba[..., :3], cv2.COLOR_RGB2LAB)
    admitted = 0
    ambiguous = 0
    unsupported = 0
    color_rejected = 0
    # Processing every component as a full-frame boolean array is quadratic
    # in frame area times component count. Use exact component bounding boxes,
    # with a one-pixel halo for the same 8-neighbour contact semantics. This
    # changes neither source evidence nor the frozen acceptance thresholds.
    boxes = ndimage.find_objects(labels)
    height, width = candidate.shape
    for component_id, box in enumerate(boxes, 1):
        if box is None:
            continue
        ys, xs = box
        component = labels[ys, xs] == component_id
        size = int(np.count_nonzero(component))
        j = bool(np.any(component & touch_j[ys, xs]))
        c = bool(np.any(component & touch_c[ys, xs]))
        contacts = int(np.count_nonzero(component & anchor_touch[ys, xs]))
        if j and c:
            ambiguous += size
            continue
        if not (j or c) or contacts < max(MIN_CONTACT_PIXELS,
                                         int(np.ceil(MIN_CONTACT_FRACTION * size))):
            unsupported += size
            continue
        owner_id = 1 if j else 2
        expanded = (slice(max(0, ys.start - 1), min(height, ys.stop + 1)),
                    slice(max(0, xs.start - 1), min(width, xs.stop + 1)))
        local_component = labels[expanded] == component_id
        local_anchors = (ndimage.binary_dilation(local_component, structure=st8) &
                         anchor[expanded] & (baseline_owner[expanded] == owner_id))
        if not np.any(local_anchors):
            unsupported += size
            continue
        local_lab = lab[expanded]
        tree = cKDTree(local_lab[local_anchors].astype(np.float32))
        distances = tree.query(local_lab[local_component].astype(np.float32), workers=1)[0]
        coherent_fraction = float(np.mean(distances <= MAX_LOCAL_LAB_DISTANCE))
        if coherent_fraction < MIN_COLOR_COHERENT_FRACTION:
            color_rejected += size
            continue
        coherent = np.zeros(local_component.shape, dtype=bool)
        coherent[local_component] = distances <= MAX_LOCAL_LAB_DISTANCE
        owner_seed = (ndimage.binary_dilation(baseline_owner[expanded] == owner_id,
                                             structure=st8) & coherent)
        reachable = ndimage.binary_propagation(owner_seed, structure=st8, mask=coherent)
        out[expanded][reachable] = owner_id
        admitted += int(np.count_nonzero(reachable))
        color_rejected += size - int(np.count_nonzero(reachable))
    try:
        out, removed = _topology_fixed_point(baseline_owner, out)
        for owner_id in (1, 2):
            for connectivity in (4, 8):
                _assert_component_identity(baseline_owner, out, owner_id, connectivity)
    except (ExtendedOwnerHold, ValueError) as exc:
        raise IndependentContactHold('OWNER_TOPOLOGY_UNSAFE') from exc
    added = (baseline_owner == 0) & (out > 0)
    if (np.any((baseline_owner > 0) & (out != baseline_owner)) or
            np.any(added & ~candidate) or
            np.any((out > 0) & (source_rgba[..., 3] == 0))):
        raise IndependentContactHold('SOURCE_OR_BASELINE_CHANGED')
    return out, {
        'schema': 'minimalizer/local-l02/class32-independent-contact-shadow/v0',
        'candidate_fragments': int(count),
        'proposed_pixels_before_topology': int(admitted),
        'added_source_pixels_after_topology': int(np.count_nonzero(added)),
        'ambiguous_dual_owner_pixels_abstained': int(ambiguous),
        'unsupported_pixels_abstained': int(unsupported),
        'color_incoherent_pixels_abstained': int(color_rejected),
        'topology_guard_removed_pixels': int(removed),
        'human_annotations_used_for_inference': False,
        'unknown_treated_as_negative': False,
        'known_case_explored': True, 'unseen_character_pass': False,
        'semantic_quality_pass': False, 'quality': 'FAIL',
        'L02': 'HOLD', 'Phase4': 'FAIL', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
