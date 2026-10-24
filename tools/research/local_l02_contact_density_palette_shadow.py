"""Research-only class32 sleeve contact + source-color partition hypothesis.

This is a KNOWN-CASE-EXPOSED candidate, not an unseen-character validation or
semantic owner authority. No hand-reviewed geometry, masks or labels are used.
The baseline owner map is immutable. The model classes and original signed
RGBA are the only observations; all uncertain pixels remain unowned unless
source-supported component contact and an independent generic-clothes anchor
both exist. Every source-only proposal remains subject to postscore and HOLD.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage
from local_l02_contact_density_partition_shadow import (
    ContactDensityHold, propose_contact_density_partition_shadow,
)
import cv2
from scipy.spatial import cKDTree
from local_l02_hue_extended_owner_shadow import _assert_component_identity, ExtendedOwnerHold
from local_l02_cross_owner_contact_gate import verify_no_new_cross_owner_contacts, CrossOwnerContactHold

class ContactPaletteHold(ValueError):
    pass

# Reuse the established 2026-10-22 source-only palette policy verbatim,
# without importing the unmerged full sleeve research pipeline.
PALETTE_COLORS = 8
PALETTE_QUANTILE = 0.95
PALETTE_MAX_LAB_DISTANCE = 25.0
MIN_TRUSTED_PIXELS = 1024

def _palette_color_evidence(source_rgba, trusted, possible):
    n = int(trusted.sum())
    admitted = np.zeros_like(trusted)
    if n < MIN_TRUSTED_PIXELS or not np.any(possible):
        return admitted, None
    lab = cv2.cvtColor(source_rgba[..., :3], cv2.COLOR_RGB2LAB)
    samples = lab[trusted].astype(np.float32)
    stride = max(1, len(samples) // 20000)
    cv2.setRNGSeed(20261022)
    try:
        _, _, centers = cv2.kmeans(
            samples[::stride], PALETTE_COLORS, None,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.1),
            3, cv2.KMEANS_PP_CENTERS,
        )
    except cv2.error as exc:
        raise ContactPaletteHold('PALETTE_FIT_FAILED') from exc
    tree = cKDTree(centers)
    trusted_dist = tree.query(samples, workers=1)[0]
    threshold = min(float(np.quantile(trusted_dist, PALETTE_QUANTILE)),
                    PALETTE_MAX_LAB_DISTANCE)
    if not np.isfinite(threshold):
        raise ContactPaletteHold('INVALID_PALETTE_DISTANCE')
    admitted[possible] = tree.query(lab[possible].astype(np.float32), workers=1)[0] <= threshold
    return admitted, threshold


def propose_contact_density_palette_shadow(*, source_rgba: np.ndarray,
        class_ids: np.ndarray, anime_classes: np.ndarray,
        baseline_owner: np.ndarray, eligible_classes=(32,)) -> tuple[np.ndarray, dict]:
    """Return exclusive owner shadow, never an automatic semantic-quality PASS."""
    try:
        proposed, structural = propose_contact_density_partition_shadow(
            source_rgba=source_rgba, class_ids=class_ids,
            anime_classes=anime_classes, baseline_owner=baseline_owner,
            eligible_classes=eligible_classes)
    except ContactDensityHold as exc:
        raise ContactPaletteHold('SOURCE_CONTACT_PARTITION_HOLD:' + str(exc)) from exc
    possible = (baseline_owner == 0) & (proposed > 0)
    # Independent generic-clothes evidence is not outerwear truth; this
    # previously used palette fit only limits speculative color extension.
    trusted = ((baseline_owner > 0) & (class_ids == 32) &
               (anime_classes == 10))
    color, threshold = _palette_color_evidence(source_rgba, trusted, possible)
    out = proposed.copy()
    out[possible & ~color] = 0
    # Filtering a candidate can detach its added islands. Keep only pixels
    # reachable from an immutable owner seed via 4-neighbour source pixels.
    structure = ndimage.generate_binary_structure(2, 1)
    for owner in (1, 2):
        seeds = (baseline_owner == owner) & (out == owner)
        connected = ndimage.binary_propagation(seeds, structure=structure,
                                               mask=(out == owner))
        out[(baseline_owner == 0) & (out == owner) & ~connected] = 0
    if (np.any((baseline_owner > 0) & (out != baseline_owner)) or
            np.any((out > 0) & (source_rgba[..., 3] == 0)) or
            np.any((baseline_owner == 0) & (out > 0) & ~possible)):
        raise ContactPaletteHold('FROZEN_OWNER_OR_SOURCE_CHANGED')
    try:
        for owner in (1, 2):
            for connectivity in (4, 8):
                _assert_component_identity(baseline_owner, out, owner, connectivity)
        verify_no_new_cross_owner_contacts(before=baseline_owner, after=out)
    except (ExtendedOwnerHold, CrossOwnerContactHold) as exc:
        raise ContactPaletteHold('OWNER_TOPOLOGY_OR_CONTACT_HOLD') from exc
    return out, {
        'schema':'minimalizer/local-l02/contact-density-palette-shadow/v0',
        'contact_stage':structural['schema'],
        'source_only_contact_admitted_px':structural['new_source_supported_px'],
        'palette_trusted_class32_generic_clothes_px':int(np.count_nonzero(trusted)),
        'source_only_palette_threshold':None if threshold is None else round(float(threshold), 6),
        'new_source_supported_px':int(np.count_nonzero((baseline_owner == 0)&(out > 0))),
        'frozen_owner_changed_px':0,
        'human_annotations_used_for_inference':False,
        'unknown_pixels_not_treated_as_negative':True,
        'known_case_explored':True,'unseen_signed_blind':'PENDING',
        'semantic_quality_pass':False,'Phase4':'FAIL','L02':'HOLD',
        'L03':'NO_GO','Golden':'HOLD','production':'NO_GO',
    }
