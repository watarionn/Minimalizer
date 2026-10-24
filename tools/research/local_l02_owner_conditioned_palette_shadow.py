"""Lane A research: owner-conditioned source-RGB palette abstention.

Fail-closed *post-proposal* filter. It can only REMOVE newly proposed owner
pixels, never create pixels or change frozen owners. It uses no reviewed labels,
coordinates or known-case identifiers. Not a Phase4 semantic approval.
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy import ndimage


class OwnerPaletteHold(ValueError):
    pass


MIN_TRUSTED_PIXELS = 1024
PALETTE_COLORS = 8
PALETTE_QUANTILE = 0.95
PALETTE_MAX_LAB_DISTANCE = 25.0


def _owner_palette(lab: np.ndarray, trusted: np.ndarray, owner: int):
    samples = lab[trusted].astype(np.float32)
    if len(samples) < MIN_TRUSTED_PIXELS:
        return None
    stride = max(1, len(samples) // 20000)
    cv2.setRNGSeed(20261022 + owner)
    try:
        _, _, centers = cv2.kmeans(
            samples[::stride], PALETTE_COLORS, None,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.1),
            3, cv2.KMEANS_PP_CENTERS)
    except cv2.error as exc:
        raise OwnerPaletteHold('OWNER_PALETTE_FIT_FAILED') from exc
    if not np.all(np.isfinite(centers)):
        raise OwnerPaletteHold('NONFINITE_OWNER_PALETTE')
    from scipy.spatial import cKDTree
    tree = cKDTree(centers)
    distances = tree.query(samples, workers=1)[0]
    threshold = min(float(np.quantile(distances, PALETTE_QUANTILE)),
                    PALETTE_MAX_LAB_DISTANCE)
    if not np.isfinite(threshold):
        raise OwnerPaletteHold('NONFINITE_OWNER_THRESHOLD')
    return tree, threshold


def propose_owner_conditioned_palette_abstention(*, source_rgba: np.ndarray,
        class_ids: np.ndarray, anime_classes: np.ndarray,
        baseline_owner: np.ndarray, candidate_owner: np.ndarray):
    """Abstain on owner-color leakage; return guarded research-only owner map.

    Candidate must already have passed source-only contact and component gates.
    Human masks must be opened *after* this result is frozen, for postscore only.
    """
    shape = getattr(baseline_owner, 'shape', None)
    if (type(baseline_owner) is not np.ndarray or baseline_owner.dtype != np.uint8 or
            baseline_owner.ndim != 2 or baseline_owner.size == 0 or
            type(candidate_owner) is not np.ndarray or candidate_owner.dtype != np.uint8 or
            candidate_owner.shape != shape or
            type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8 or
            source_rgba.shape != (*shape, 4) or
            any(type(a) is not np.ndarray or a.dtype != np.uint8 or a.shape != shape
                for a in (class_ids, anime_classes))):
        raise OwnerPaletteHold('INVALID_SIGNED_INPUT')
    if (np.any(baseline_owner > 2) or np.any(candidate_owner > 2) or
            np.any(class_ids >= 47) or np.any(anime_classes >= 12) or
            np.any((baseline_owner > 0) & (baseline_owner != candidate_owner)) or
            np.any((candidate_owner > 0) & (source_rgba[..., 3] == 0)) or
            np.any((baseline_owner > 0) & (source_rgba[..., 3] == 0))):
        raise OwnerPaletteHold('FROZEN_OWNER_SOURCE_OR_CLASS_VIOLATION')
    added = (baseline_owner == 0) & (candidate_owner > 0)
    if np.any(added & (class_ids != 32)):
        raise OwnerPaletteHold('UNSUPPORTED_ADDED_CLASS')

    lab = cv2.cvtColor(source_rgba[..., :3], cv2.COLOR_RGB2LAB)
    palettes = {}
    for owner in (1, 2):
        trusted = ((baseline_owner == owner) & (class_ids == 32) &
                   (anime_classes == 10))
        palettes[owner] = _owner_palette(lab, trusted, owner)
    out = candidate_owner.copy()
    for owner in (1, 2):
        possible = added & (candidate_owner == owner)
        if not np.any(possible):
            continue
        own = palettes[owner]
        if own is None:
            out[possible] = 0
            continue
        colors = lab[possible].astype(np.float32)
        own_dist = own[0].query(colors, workers=1)[0]
        accepted = own_dist <= own[1]
        other = palettes[3 - owner]
        if other is not None:
            other_dist = other[0].query(colors, workers=1)[0]
            # Exact ties are ambiguous; never let one owner's palette
            # justify additions belonging to the other frozen owner.
            accepted &= own_dist < other_dist
        ys, xs = np.nonzero(possible)
        out[ys[~accepted], xs[~accepted]] = 0

    # Color filtering may sever a large sleeve from its frozen owner.
    # Remove detached new pixels rather than leaving unsupported islands.
    structure = ndimage.generate_binary_structure(2, 1)
    for owner in (1, 2):
        seeds = baseline_owner == owner
        connected = ndimage.binary_propagation(
            seeds, structure=structure, mask=(out == owner))
        out[added & (out == owner) & ~connected] = 0
    if (np.any((baseline_owner > 0) & (out != baseline_owner)) or
            np.any((out > 0) & (source_rgba[..., 3] == 0)) or
            np.any((baseline_owner == 0) & (out > 0) & ~added)):
        raise OwnerPaletteHold('FROZEN_OWNER_OR_SOURCE_CHANGED')

    # Reuse existing source-only invariants, not a newly relaxed gate.
    from local_l02_hue_extended_owner_shadow import _assert_component_identity, ExtendedOwnerHold
    from local_l02_cross_owner_contact_gate import verify_no_new_cross_owner_contacts, CrossOwnerContactHold
    try:
        for owner in (1, 2):
            for connectivity in (4, 8):
                _assert_component_identity(baseline_owner, out, owner, connectivity)
        verify_no_new_cross_owner_contacts(before=baseline_owner, after=out)
    except (ExtendedOwnerHold, CrossOwnerContactHold) as exc:
        raise OwnerPaletteHold('OWNER_TOPOLOGY_OR_CONTACT_HOLD') from exc
    return out, {
        'schema': 'minimalizer/local-l02/owner-conditioned-palette-abstention/v0',
        'source_only_candidate_added_px': int(added.sum()),
        'source_only_retained_added_px': int(np.count_nonzero(added & (out > 0))),
        'source_only_abstained_added_px': int(np.count_nonzero(added & (out == 0))),
        'owner_palette_available': {str(owner): palettes[owner] is not None for owner in (1, 2)},
        'frozen_owner_changed_px': 0,
        'human_annotations_used_for_inference': False,
        'known_case_explored': True,
        'unseen_signed_blind': 'PENDING',
        'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
