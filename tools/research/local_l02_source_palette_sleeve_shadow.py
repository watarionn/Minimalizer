"""Research-only source-RGB palette sleeve recovery, with 4/8 owner topology fences.

This is a known-case-explored hypothesis, NOT an independently frozen blind model.
Only original-alpha, frozen-candidate, unowned SegFormer class32 pixels can be
assigned. AnimeSeg class10 provides trusted *generic clothes* samples, not
outerwear truth; class11 is eligible only through source-LAB palette evidence.
Neither model's classes are human annotations. No image pixels are generated.

The 8-color/95%-quantile/1024px policy was explored on known H08 and MUST NOT
be described as an unseen-character PASS or a production owner promotion.
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from local_l02_guarded_sleeve_geodesic_shadow import _distance_inside
from local_l02_sleeve_no_merge_shadow import (
    propose_sleeve_without_frozen_component_merges, _cut_collisions,
)
from local_l02_hue_extended_owner_shadow import _assert_component_identity, ExtendedOwnerHold


class PaletteSleeveHold(ValueError):
    pass


PALETTE_COLORS = 8
PALETTE_QUANTILE = 0.95
PALETTE_MAX_LAB_DISTANCE = 25.0
MIN_TRUSTED_PIXELS = 1024
MIN_COLOR_FRAGMENT = 1024
MAX_TOPOLOGY_PASSES = 16


def _topology_fixed_point(frozen: np.ndarray, current: np.ndarray) -> tuple[np.ndarray, int]:
    """Monotone deletion only; check both neighborhoods until neither changes."""
    out = current.copy()
    removed = 0
    for _ in range(MAX_TOPOLOGY_PASSES):
        previous = out.copy()
        for connectivity in (4, 8):
            for owner_id in (1, 2):
                removed += _cut_collisions(frozen, out, owner_id, connectivity)
        if np.array_equal(previous, out):
            return out, removed
    raise PaletteSleeveHold('TOPOLOGY_CUT_DID_NOT_CONVERGE')


def _palette_color_evidence(source_rgba, trusted, possible):
    """Return a source-only mask and its data-derived threshold, never a label."""
    n = int(trusted.sum())
    admitted = np.zeros_like(trusted)
    if n < MIN_TRUSTED_PIXELS or not np.any(possible):
        return admitted, None
    lab = cv2.cvtColor(source_rgba[..., :3], cv2.COLOR_RGB2LAB)
    samples = lab[trusted].astype(np.float32)
    stride = max(1, len(samples) // 20000)
    # OpenCV's local k-means RNG is pinned; no human-label inputs or coordinates.
    cv2.setRNGSeed(20261022)
    try:
        _, _, centers = cv2.kmeans(
            samples[::stride], PALETTE_COLORS, None,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.1),
            3, cv2.KMEANS_PP_CENTERS,
        )
    except cv2.error as exc:
        raise PaletteSleeveHold('PALETTE_FIT_FAILED') from exc
    tree = cKDTree(centers)
    trusted_dist = tree.query(samples, workers=1)[0]
    threshold = min(float(np.quantile(trusted_dist, PALETTE_QUANTILE)),
                    PALETTE_MAX_LAB_DISTANCE)
    if not np.isfinite(threshold):
        raise PaletteSleeveHold('INVALID_PALETTE_DISTANCE')
    admitted[possible] = tree.query(lab[possible].astype(np.float32), workers=1)[0] <= threshold
    return admitted, threshold


def propose_source_palette_sleeve_shadow(*, source_rgba, class_ids,
        anime_classes, frozen_candidate, frozen_owner, connectivity=4):
    """Produce a fail-closed source-only owner shadow, never a quality PASS.

    The already-safe generic-clothes candidate is the fallback. New class11
    candidates need source-color agreement, seeded geodesic reachability,
    >=1024-pixel connected color fragments, and 4/8 component bijection.
    """
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8
            or source_rgba.ndim != 3 or source_rgba.shape[-1] != 4
            or not source_rgba.size):
        raise PaletteSleeveHold('INVALID_SIGNED_RGBA')
    shape = source_rgba.shape[:2]
    if any(type(a) is not np.ndarray or a.dtype != np.uint8 or a.shape != shape
           for a in (class_ids, anime_classes, frozen_owner)):
        raise PaletteSleeveHold('INVALID_FROZEN_OBSERVERS')
    if (type(frozen_candidate) is not np.ndarray or
            frozen_candidate.dtype != np.bool_ or frozen_candidate.shape != shape):
        raise PaletteSleeveHold('INVALID_FROZEN_CANDIDATE')
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise PaletteSleeveHold('INVALID_CONNECTIVITY')
    alpha = source_rgba[..., 3]
    if np.any((frozen_owner > 0) & (alpha == 0)):
        raise PaletteSleeveHold('OWNER_OUTSIDE_SIGNED_ALPHA')
    # Existing PR's research gate authenticates class domains and baseline.
    baseline, upstream = propose_sleeve_without_frozen_component_merges(
        class_ids=class_ids, anime_classes=anime_classes,
        source_alpha=alpha, frozen_candidate=frozen_candidate,
        frozen_owner=frozen_owner, connectivity=connectivity)
    abstained = frozen_candidate & (class_ids == 32) & (frozen_owner == 0)
    trusted = abstained & (anime_classes == 10)
    possible = abstained & (anime_classes == 11)
    color, threshold = _palette_color_evidence(source_rgba, trusted, possible)
    if threshold is None or not np.any(color):
        return baseline, {
            'schema': 'minimalizer/local-l02/source-palette-sleeve-shadow/v1',
            'color_policy_applied': False, 'color_added_pixels': 0,
            'total_added_pixels': int(np.count_nonzero((baseline > 0) & (frozen_owner == 0))),
            'human_annotations_used_for_inference': False,
            'known_case_explored': True, 'independent_unseen_character_pass': False,
            'semantic_quality_pass': False, 'L02': 'HOLD', 'L03': 'NO_GO',
            'Golden': 'HOLD', 'production': 'NO_GO', 'upstream': upstream['schema'],
        }
    eligible = trusted | color
    jacket = (frozen_owner == 1) & (class_ids == 5)
    coat = (frozen_owner == 2) & (class_ids == 10)
    dj = _distance_inside(eligible, jacket, connectivity)
    dc = _distance_inside(eligible, coat, connectivity)
    raw = baseline.copy()
    raw[(baseline == 0) & (dj > 0) & ((dc < 0) | (dj < dc))] = 1
    raw[(baseline == 0) & (dc > 0) & ((dj < 0) | (dc < dj))] = 2
    # Previously verified topology-safe generic-clothes sleeves are protected
    # from a new color hypothesis, even when that hypothesis is rejected.
    safe, cut_pixels = _topology_fixed_point(baseline, raw)
    # A small palette-only island may be an arm, glove or texture. It is
    # excluded as a WHOLE component, not pixelwise tuned to known annotations.
    palette_added = (safe > 0) & (baseline == 0) & color
    ids, count = ndimage.label(palette_added, structure=np.ones((3, 3), dtype=bool))
    if count:
        sizes = np.bincount(ids.ravel())
        small = (sizes < MIN_COLOR_FRAGMENT)
        small[0] = False
        safe[(baseline == 0) & small[ids]] = 0
    safe, cut_more = _topology_fixed_point(baseline, safe)
    for owner_id in (1, 2):
        for neighborhood in (4, 8):
            try:
                _assert_component_identity(frozen_owner, safe, owner_id, neighborhood)
            except ExtendedOwnerHold as exc:
                raise PaletteSleeveHold('OWNER_COMPONENT_IDENTITY_CHANGED') from exc
    added = (safe != frozen_owner)
    if (np.any(added & ~eligible) or np.any(added & ~abstained) or
            np.any((safe > 0) & (alpha == 0)) or
            np.any((frozen_owner > 0) & (safe != frozen_owner)) or
            np.any((safe == 1) & ~np.isin(class_ids, (5, 32))) or
            np.any((safe == 2) & ~np.isin(class_ids, (10, 32)))):
        raise PaletteSleeveHold('SOURCE_FROZEN_OWNER_OR_CLASS_ESCAPE')
    if np.any((baseline > 0) & (safe == 0)):
        # A new exploratory color hypothesis cannot erase an already accepted
        # topology-safe generic-clothes proposal without explicit review.
        raise PaletteSleeveHold('BASELINE_SLEEVE_RETENTION_REGRESSION')
    return safe, {
        'schema': 'minimalizer/local-l02/source-palette-sleeve-shadow/v1',
        'color_policy_applied': True,
        'source_only_lab_threshold': round(float(threshold), 6),
        'trusted_generic_clothes_pixels': int(trusted.sum()),
        'color_supported_class11_pixels': int(color.sum()),
        'color_added_pixels': int(np.count_nonzero(added & color)),
        'total_added_pixels': int(added.sum()),
        'topology_uncertain_pixels_removed': int(cut_pixels + cut_more),
        'frozen_owner_modified_pixels': 0, 'source_pixels_generated': 0,
        'human_annotations_used_for_inference': False,
        'known_case_explored': True, 'independent_unseen_character_pass': False,
        'semantic_quality_pass': False, 'quality': 'FAIL',
        'L02': 'HOLD', 'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
        'upstream': upstream['schema'],
    }
