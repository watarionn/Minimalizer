"""Pinned Run30 source-only class32 positive evidence -> exclusive owner shadow.

Research only: no labels, no pixel generation, no Phase4/Golden promotion.
Only a single-owner, single-original-component 4/8-connected evidence
component can be assigned. All other candidate pixels remain unowned.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from tools.research.local_l02_class32_color_positive_shadow import (
    propose_pinned_run30_class32_positive,
)
from tools.research.local_l02_class32_topology_palette_shadow import (
    SourceOnlyAbstentionHold,
)

_CROSS = ndi.generate_binary_structure(2, 1)
_SQUARE = ndi.generate_binary_structure(2, 2)


def _single_original_owner_touch(component_ids: np.ndarray, count: int,
                                 owner: np.ndarray, structure: np.ndarray) -> np.ndarray:
    """For each component, return unique adjacent original owner or 0.

    Multiple original owner components of the same semantic owner are also
    ambiguous: joining them would change topology even if owner ID agrees.
    """
    original_components = {
        owner_id: ndi.label(owner == owner_id, structure=structure)[0]
        for owner_id in (1, 2)
    }
    assigned = np.zeros(count + 1, dtype=np.uint8)
    for component_id, bounds in enumerate(ndi.find_objects(component_ids), 1):
        if bounds is None:
            continue
        y, x = bounds
        y0, y1 = max(0, y.start - 1), min(owner.shape[0], y.stop + 1)
        x0, x1 = max(0, x.start - 1), min(owner.shape[1], x.stop + 1)
        window = np.s_[y0:y1, x0:x1]
        component = component_ids[window] == component_id
        adjacent = ndi.binary_dilation(component, structure=structure) & ~component
        touching = {
            owner_id: np.unique(labels[window][adjacent & (labels[window] != 0)])
            for owner_id, labels in original_components.items()
        }
        if touching[1].size == 1 and touching[2].size == 0:
            assigned[component_id] = 1
        elif touching[2].size == 1 and touching[1].size == 0:
            assigned[component_id] = 2
    return assigned


def _topology_safe_exclusive_assign(positive: np.ndarray,
                                    frozen_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    """Shadow owner proposal. Never use reviewed labels as input."""
    if (type(positive) is not np.ndarray or type(frozen_owner) is not np.ndarray or
            positive.dtype != np.bool_ or frozen_owner.dtype != np.uint8 or
            positive.ndim != 2 or positive.shape != frozen_owner.shape or
            positive.size == 0 or positive.size > 16_000_000 or
            np.any(frozen_owner > 2) or np.any(positive & (frozen_owner != 0))):
        raise SourceOnlyAbstentionHold('INVALID_EXCLUSIVE_POSITIVE_INPUT')
    component4, count4 = ndi.label(positive, structure=_CROSS)
    component8, count8 = ndi.label(positive, structure=_SQUARE)
    owner4 = _single_original_owner_touch(component4, count4, frozen_owner, _CROSS)
    owner8 = _single_original_owner_touch(component8, count8, frozen_owner, _SQUARE)
    eligible = positive & (owner4[component4] != 0) & (owner4[component4] == owner8[component8])
    # A component-count check alone misses an enclosed negative-space hole
    # being filled (e.g. an arm opening), even though owner count is unchanged.
    # Preserve all original 4/8 enclosed void pixels, without human labels.
    enclosed = np.zeros(positive.shape, dtype=bool)
    for oid in (1, 2):
        original = frozen_owner == oid
        for structure in (_CROSS, _SQUARE):
            enclosed |= ndi.binary_fill_holes(original, structure=structure) & ~original
    abstained_enclosed = int(np.count_nonzero(eligible & enclosed))
    eligible &= ~enclosed
    proposed = frozen_owner.copy()
    proposed[eligible] = owner4[component4[eligible]]
    before = [int(ndi.label(frozen_owner == oid, structure=structure)[1])
              for oid in (1, 2) for structure in (_CROSS, _SQUARE)]
    after = [int(ndi.label(proposed == oid, structure=structure)[1])
             for oid in (1, 2) for structure in (_CROSS, _SQUARE)]
    holes_before = [int(ndi.label(ndi.binary_fill_holes(frozen_owner == oid, structure=structure)
                                   & (frozen_owner != oid), structure=structure)[1])
                    for oid in (1, 2) for structure in (_CROSS, _SQUARE)]
    holes_after = [int(ndi.label(ndi.binary_fill_holes(proposed == oid, structure=structure)
                                  & (proposed != oid), structure=structure)[1])
                   for oid in (1, 2) for structure in (_CROSS, _SQUARE)]
    if (before != after or holes_before != holes_after or
            np.any((proposed != frozen_owner) & ~eligible) or
            np.any((proposed != frozen_owner) & (frozen_owner != 0)) or
            np.any((proposed != frozen_owner) & (proposed == 0))):
        raise SourceOnlyAbstentionHold('EXCLUSIVE_POSITIVE_TOPOLOGY_FAIL')
    return proposed, {
        'source_only_positive_px': int(positive.sum()),
        'assigned_positive_px': int(eligible.sum()),
        'abstained_positive_px': int(positive.sum() - eligible.sum()),
        'assigned_owner1_px': int(np.count_nonzero(eligible & (proposed == 1))),
        'assigned_owner2_px': int(np.count_nonzero(eligible & (proposed == 2))),
        'original_owner_4_8_components': before,
        'proposed_owner_4_8_components': after,
        'original_owner_4_8_enclosed_holes': holes_before,
        'proposed_owner_4_8_enclosed_holes': holes_after,
        'abstained_enclosed_void_px': abstained_enclosed,
        'exclusive_4_8_component_gate_pass': True,
        'enclosed_void_4_8_gate_pass': True,
    }


def propose_pinned_run30_class32_topology_positive(*, case_id: str,
        source_bytes: bytes, class_ids: np.ndarray,
        frozen_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    """Return private candidate owner map, source-free HOLD receipt."""
    evidence, evidence_receipt = propose_pinned_run30_class32_positive(
        case_id=case_id, source_bytes=source_bytes,
        class_ids=class_ids, frozen_owner=frozen_owner,
    )
    proposed, topology = _topology_safe_exclusive_assign(evidence, frozen_owner)
    return proposed, {
        'schema': 'minimalizer/l02/class32-topology-positive-shadow/v1',
        'case': case_id, 'pinned_source_class_owner': evidence_receipt['source_class_owner_sha_pinned'],
        'positive_evidence_reason': evidence_receipt['reason'],
        **topology,
        'human_labels_in_inference': False,
        'independent_model_evidence': False,
        'quality': 'UNASSESSED', 'L02': 'HOLD', 'Phase4': 'FAIL',
        'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
    }
