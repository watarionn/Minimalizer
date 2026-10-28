"""Research-only A-lane frozen-order P0 composition, not release/semantic approval.

Composes previously source-only stages in a fixed order: existing composed
hue/palette/class30 proposal, strict geodesic class30 dual-owner recovery,
then independent-contact class32 uncertain-fragment recovery. No evaluation
labels, hand geometry, case IDs or character-specific thresholds are inputs.
"""
from __future__ import annotations
import numpy as np
from local_l02_composed_p0_shadow import propose_composed_p0_shadow, _component_identity, _core_fragment_retention
from local_l02_class30_dual_seed_extension_shadow import propose_class30_dual_seed_extension_shadow
from local_l02_class32_independent_contact_shadow import propose_independent_contact_shadow
from local_l02_cross_owner_contact_gate import verify_no_new_cross_owner_contacts, prune_new_cross_owner_additions, CrossOwnerContactHold
from local_l02_cross_owner_selective_veto_shadow import propose_selective_cross_owner_veto, SelectiveVetoHold

class DualContactHold(ValueError):
    pass

def propose_composed_dual_contact_shadow(*, source_rgba: np.ndarray,
        class_ids: np.ndarray, anime_classes: np.ndarray,
        frozen_owner: np.ndarray, contact_repair_mode: str = "conservative"):
    """Return exclusive owner shadow; opt-in selective mode is research-only.

    The default is byte-compatible with the established conservative replay.
    No caller may interpret either mode as Phase4 semantic quality approval.
    """
    if contact_repair_mode not in ("conservative", "selective"):
        raise DualContactHold("UNRECOGNIZED_CONTACT_REPAIR_MODE")
    core, core_meta = propose_composed_p0_shadow(
        source_rgba=source_rgba, class_ids=class_ids,
        anime_classes=anime_classes, frozen_owner=frozen_owner)
    dual, dual_meta = propose_class30_dual_seed_extension_shadow(
        source_alpha=source_rgba[..., 3], class_ids=class_ids,
        anime_classes=anime_classes, frozen_owner=core)
    out, contact_meta = propose_independent_contact_shadow(
        source_rgba=source_rgba, class_ids=class_ids,
        anime_classes=anime_classes, baseline_owner=dual)
    if np.any((out > 0) & (source_rgba[..., 3] == 0)):
        raise DualContactHold('SOURCE_ALPHA_ESCAPE')
    # Preserve the established stage-specific failure reasons before the
    # contact repair. The repair must never become a way to mask a lost owner.
    if np.any((core > 0) & (out != core)):
        raise DualContactHold('CORE_OWNER_ERASURE_OR_REASSIGNMENT')
    if np.any((dual > 0) & (out != dual)):
        raise DualContactHold('DUAL_OWNER_ERASURE_OR_REASSIGNMENT')
    initial_veto = (frozen_owner > 0) & (core == 0)
    try:
        if contact_repair_mode == "conservative":
            out, contact_repair = prune_new_cross_owner_additions(
                before=frozen_owner, proposed=out,
                allowed_abstentions=initial_veto)
        else:
            out, contact_repair = propose_selective_cross_owner_veto(
                before=frozen_owner, proposed=out,
                source_alpha=source_rgba[..., 3], class_ids=class_ids,
                allowed_abstentions=initial_veto)
    except (CrossOwnerContactHold, SelectiveVetoHold) as exc:
        raise DualContactHold('CROSS_OWNER_CONTACT_REPAIR_HOLD:' + str(exc)) from exc
    # New modules are not allowed to resurrect an earlier safety veto, change
    # any frozen owner's identity, or expand outside signed source pixels.
    if np.any(initial_veto & (out > 0)):
        raise DualContactHold('PREVIOUS_VETO_RESURRECTED')
    if np.any((frozen_owner > 0) & (out > 0) & (frozen_owner != out)):
        raise DualContactHold('FROZEN_OWNER_REASSIGNED')
    if np.any((out > 0) & (source_rgba[..., 3] == 0)):
        raise DualContactHold('SOURCE_ALPHA_ESCAPE')
    # Contact repair is allowed to discard unsafe *proposed additions* from
    # core/dual stages. It must never erase a surviving frozen owner or undo a
    # previous veto. Requiring every dual-stage proposal pixel to survive
    # would make a successful cross-owner pruning operation fail by design.
    protected = frozen_owner > 0
    if np.any((core > 0) & protected & (out != core)):
        raise DualContactHold('CORE_FROZEN_OWNER_ERASURE_OR_REASSIGNMENT')
    if np.any((dual > 0) & protected & (out != dual)):
        raise DualContactHold('DUAL_FROZEN_OWNER_ERASURE_OR_REASSIGNMENT')
    added = (frozen_owner == 0) & (out > 0)
    if np.any(added & ~np.isin(class_ids, (30, 32))):
        raise DualContactHold('UNAUTHORIZED_CLASS_PROMOTION')
    for owner in (1, 2):
        for connectivity in (4, 8):
            _component_identity(frozen_owner, out, owner, connectivity)
            _core_fragment_retention(frozen_owner, out, class_ids, owner, connectivity)
    try:
        verify_no_new_cross_owner_contacts(before=frozen_owner, after=out)
    except CrossOwnerContactHold as exc:
        raise DualContactHold('NEW_CROSS_OWNER_CONTACT_EDGE:' + str(exc)) from exc
    return out, {
        'schema': 'minimalizer/local-l02/composed-dual-contact-shadow/v1',
        'stage_order': ['composed_p0', 'dual_class30_geodesic', 'independent_contact_class32'],
        'core_stage': core_meta['schema'],
        'dual_stage': dual_meta['schema'],
        'contact_stage': contact_meta['schema'],
        'cross_owner_contact_addition_repair': contact_repair,
        'contact_repair_mode': contact_repair_mode,
        'dual_stage_added_px': int(np.count_nonzero((core == 0) & (dual > 0))),
        'pruned_earlier_stage_additions_px': int(np.count_nonzero(
            (frozen_owner == 0) & (dual > 0) & (out == 0))),
        'contact_stage_added_px': int(np.count_nonzero((dual == 0) & (out > 0))),
        'net_added_source_supported_px': int(np.count_nonzero(added)),
        'human_annotations_used_for_inference': False,
        'unknown_treated_as_negative': False,
        'independent_unseen_character_pass': False,
        'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
