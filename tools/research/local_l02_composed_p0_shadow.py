"""Lane A L02 research-only composition: hue veto -> palette sleeve -> class30.

Inputs are original-source pixels and frozen model observations, not human masks.
This pipeline is intentionally *not* production, Phase4 or Golden approval.
The signed-source SHA must be authenticated by the caller before invoking it.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from local_l02_hue_extended_owner_shadow import propose_hue_extended_owner_shadow
from local_l02_source_palette_sleeve_shadow import propose_source_palette_sleeve_shadow
from local_l02_class30_source_extension_shadow import propose_class30_extension_shadow
from local_l02_coat_trouser_veto_composed_shadow import propose_coat_trouser_veto_shadow
from local_l02_cross_owner_contact_gate import verify_no_new_cross_owner_contacts, prune_new_cross_owner_additions, CrossOwnerContactHold


class ComposedP0Hold(ValueError):
    pass


def _component_identity(before: np.ndarray, after: np.ndarray, owner: int, connectivity: int) -> None:
    """Prove each old owner component maps one-to-one to a new component."""
    st = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    old, n_old = ndimage.label(before == owner, structure=st)
    new, n_new = ndimage.label(after == owner, structure=st)
    if n_old != n_new:
        raise ComposedP0Hold('OWNER_COMPONENT_COUNT_CHANGED')
    if not n_old:
        return
    survivors = (before == owner) & (after == owner)
    old_ids, new_ids = old[survivors], new[survivors]
    pairs = np.unique(np.stack((old_ids, new_ids), axis=1), axis=0)
    if (len(pairs) != n_old or np.any(pairs == 0) or
            len(np.unique(pairs[:, 0])) != n_old or
            len(np.unique(pairs[:, 1])) != n_new):
        raise ComposedP0Hold('OWNER_COMPONENT_IDENTITY_CHANGED')


def _core_fragment_retention(before: np.ndarray, after: np.ndarray,
                             class_ids: np.ndarray, owner: int,
                             connectivity: int) -> int:
    """Preserve every frozen jacket/coat *core* island, not just whole-owner count.

    Class32 bridges can keep an owner connected even after a complete class5/10
    garment-core island disappears. Human labels are never consulted. A veto
    that cannot prove core-island retention must remain research HOLD.
    """
    core_class = 5 if owner == 1 else 10
    st = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    core_before = (before == owner) & (class_ids == core_class)
    core_after = core_before & (after == owner)
    old, n_old = ndimage.label(core_before, structure=st)
    new, n_new = ndimage.label(core_after, structure=st)
    if n_old != n_new:
        raise ComposedP0Hold('CORE_FRAGMENT_ERASURE_OR_SPLIT')
    if not n_old:
        return 0
    pairs = np.unique(np.stack((old[core_after], new[core_after]), axis=1), axis=0)
    if (len(pairs) != n_old or np.any(pairs == 0) or
            len(np.unique(pairs[:, 0])) != n_old or
            len(np.unique(pairs[:, 1])) != n_new):
        raise ComposedP0Hold('CORE_FRAGMENT_ERASURE_OR_SPLIT')
    return int(n_old)


def propose_composed_p0_shadow(*, source_rgba: np.ndarray, class_ids: np.ndarray,
                               anime_classes: np.ndarray, frozen_owner: np.ndarray,
                               independent_outerwear: np.ndarray | None = None):
    """Return a source-only exclusive owner proposal, always quality=FAIL.

    One generic order for both H06 and H08. Never branch on character identity,
    use evaluation labels, infer human-drawn coordinates, or fabricate pixels.
    """
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8 or
            source_rgba.ndim != 3 or source_rgba.shape[-1] != 4 or not source_rgba.size):
        raise ComposedP0Hold('INVALID_SOURCE_RGBA')
    shape = source_rgba.shape[:2]
    if any(type(a) is not np.ndarray or a.dtype != np.uint8 or a.shape != shape
           for a in (class_ids, anime_classes, frozen_owner)):
        raise ComposedP0Hold('INVALID_FROZEN_OBSERVERS')
    if (np.any(class_ids >= 47) or np.any(anime_classes >= 12) or
            np.any(frozen_owner > 2)):
        raise ComposedP0Hold('INVALID_OBSERVER_DOMAIN')
    alpha = source_rgba[..., 3] > 0
    if np.any((frozen_owner > 0) & ~alpha):
        raise ComposedP0Hold('FROZEN_OWNER_OUTSIDE_SOURCE')
    # Step 1: delete unsupported class32 owner pixels; never reassign owners.
    if independent_outerwear is None:
        hue, hue_meta = propose_hue_extended_owner_shadow(
            source_rgba=source_rgba, class_ids=class_ids, frozen_owner=frozen_owner)
        first_stage = 'hue_abstain'
    else:
        # Optional independent-model *veto* is never positive owner proof.
        # Caller must authenticate model/archive provenance before inference.
        if (type(independent_outerwear) is not np.ndarray or
                independent_outerwear.shape != shape or
                independent_outerwear.dtype != np.uint8):
            raise ComposedP0Hold('INVALID_INDEPENDENT_OBSERVER')
        hue, hue_meta = propose_coat_trouser_veto_shadow(
            source_rgba=source_rgba, class_ids=class_ids,
            independent_outerwear=independent_outerwear, frozen_owner=frozen_owner)
        first_stage = 'independent_color_veto'
    # Do not stack two competing color hypotheses. The independent-veto route
    # only removes uncertain owner; palette-based class32 recovery is a
    # separate candidate, never silently allowed to reintroduce vetoed pixels.
    if independent_outerwear is None:
        palette, palette_meta = propose_source_palette_sleeve_shadow(
            source_rgba=source_rgba, class_ids=class_ids,
            anime_classes=anime_classes,
            frozen_candidate=alpha & np.isin(class_ids, (5, 10, 32)),
            frozen_owner=hue, connectivity=4)
        stage_order = [first_stage, 'palette_class32', 'class30_extension']
        palette_stage = palette_meta['schema']
    else:
        palette = hue
        stage_order = [first_stage, 'class30_extension']
        palette_stage = 'SKIPPED_COMPETING_COLOR_HYPOTHESIS'
    # A first-stage abstention is a safety veto, not a new class32 seed.
    # A later palette or extension stage must not silently resurrect it.
    # Otherwise a previously rejected skin/underlayer owner can reappear while
    # every final topology/alpha check still passes. This is a hard HOLD, not
    # a per-character threshold or a postscore-driven adjustment.
    first_stage_veto = (frozen_owner > 0) & (hue == 0)
    if np.any(first_stage_veto & (palette != 0)):
        raise ComposedP0Hold('FIRST_STAGE_VETO_RESURRECTED_BY_PALETTE')
    # Step 3: class30 extension only on source pixels connected to an owner.
    out, class30_meta = propose_class30_extension_shadow(
        source_rgba=source_rgba, class_ids=class_ids,
        anime_classes=anime_classes, frozen_owner=palette, safe_baseline=palette)
    if np.any(first_stage_veto & (out != 0)):
        raise ComposedP0Hold('FIRST_STAGE_VETO_RESURRECTED_BY_EXTENSION')
    if np.any((out > 0) & (source_rgba[..., 3] == 0)):
        raise ComposedP0Hold('OUTPUT_OUTSIDE_SOURCE_BEFORE_REPAIR')
    # Fail-closed source-only repair: retain safe proposed sleeve pixels while
    # removing ONLY additions that would create jacket/coat contact edges.
    try:
        out, contact_repair = prune_new_cross_owner_additions(
            before=frozen_owner, proposed=out,
            allowed_abstentions=first_stage_veto)
    except CrossOwnerContactHold as exc:
        raise ComposedP0Hold('CROSS_OWNER_CONTACT_REPAIR_HOLD:' + str(exc)) from exc
    if np.any((out > 0) & ~alpha):
        raise ComposedP0Hold('OUTPUT_OUTSIDE_SOURCE')
    if np.any((frozen_owner > 0) & (out > 0) & (frozen_owner != out)):
        raise ComposedP0Hold('FROZEN_OWNER_REASSIGNMENT')
    additions = (frozen_owner == 0) & (out > 0)
    if np.any(additions & ~np.isin(class_ids, (30, 32))):
        raise ComposedP0Hold('UNAUTHORIZED_CLASS_PROMOTION')
    for owner in (1, 2):
        for connectivity in (4, 8):
            _component_identity(frozen_owner, out, owner, connectivity)
            _core_fragment_retention(frozen_owner, out, class_ids,
                                     owner, connectivity)
    try:
        verify_no_new_cross_owner_contacts(before=frozen_owner, after=out)
    except CrossOwnerContactHold as exc:
        raise ComposedP0Hold('NEW_CROSS_OWNER_CONTACT_EDGE:' + str(exc)) from exc
    return out, {
        'schema': 'minimalizer/local-l02/composed-p0-shadow/v1',
        'stage_order': stage_order,
        'source_pixels_generated': 0,
        'frozen_owner_reassigned_pixels': 0,
        'frozen_owner_abstained_pixels': int(np.count_nonzero((frozen_owner > 0) & (out == 0))),
        'added_source_supported_pixels': int(np.count_nonzero(additions)),
        'class30_added_pixels': int(np.count_nonzero(additions & (class_ids == 30))),
        'cross_owner_contact_addition_repair': contact_repair,
        'human_annotations_used_for_inference': False,
        'source_sha_verified_by_wrapper': False,
        'independent_model_sha_verified_by_wrapper': False,
        'known_case_explored': True,
        'independent_unseen_character_pass': False,
        'semantic_quality_pass': False,
        'quality': 'FAIL', 'Phase4': 'FAIL', 'L02': 'HOLD',
        'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
        'hue_stage': hue_meta['schema'],
        'palette_stage': palette_stage,
        'class30_stage': class30_meta['schema'],
    }
