"""Source-only sleeve seam barrier. Research shadow, never a Phase4 owner.

Inputs must come from signed original RGBA and independently inferred fashion
classes. Human masks are prohibited as proposal inputs. The seed-internal 95th
percentile is a source-derived hypothesis, not an independently tuned quality
threshold. Return a sleeve-only abstention mask, never jacket/coat ownership.
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components


class SourceGradientHold(ValueError):
    pass


def propose_source_gradient_sleeve(
    *, rgba: np.ndarray, class_ids: np.ndarray, outerwear_seed: np.ndarray,
    sleeve_candidate: np.ndarray, seed_owner_ids: np.ndarray,
    max_candidate_pixels: int = 500_000,
) -> tuple[np.ndarray, dict]:
    """Retain only class32 pixels reachable across source-color seam-safe edges.

    The caller must separately establish source/model SHA and seed provenance.
    A returned True is *not* a semantic owner decision or quality PASS.
    """
    if (type(rgba) is not np.ndarray or rgba.dtype != np.uint8 or
            rgba.ndim != 3 or rgba.shape[2] != 4 or not rgba.size):
        raise SourceGradientHold("INVALID_SIGNED_RGBA")
    shape = rgba.shape[:2]
    if (type(class_ids) is not np.ndarray or class_ids.dtype != np.uint8 or
            class_ids.shape != shape or np.any(class_ids >= 47)):
        raise SourceGradientHold("INVALID_FASHION_CLASS_IDS")
    for name, mask in (("SEED", outerwear_seed), ("SLEEVE", sleeve_candidate)):
        if type(mask) is not np.ndarray or mask.dtype != np.bool_ or mask.shape != shape:
            raise SourceGradientHold("INVALID_" + name + "_MASK")
    # A sleeve component touching both independently seeded jacket and coat
    # cannot be assigned to either owner by source-color continuity alone.
    # Require an explicit frozen seed-owner map and abstain on dual contacts.
    if (type(seed_owner_ids) is not np.ndarray or seed_owner_ids.dtype != np.uint8 or
            seed_owner_ids.shape != shape or np.any(seed_owner_ids > 2) or
            np.any((seed_owner_ids > 0) != outerwear_seed) or
            np.any((seed_owner_ids == 1) & (class_ids != 5)) or
            np.any((seed_owner_ids == 2) & (class_ids != 10))):
        raise SourceGradientHold("INVALID_FROZEN_SEED_OWNER_DOMAIN")
    alpha = rgba[:, :, 3] > 0
    if (np.any((outerwear_seed | sleeve_candidate) & ~alpha) or
            np.any(outerwear_seed & sleeve_candidate)):
        raise SourceGradientHold("SOURCE_ALPHA_OR_SEED_OVERLAP")
    if (np.any(outerwear_seed & ~np.isin(class_ids, (5, 10))) or
            np.any(sleeve_candidate & (class_ids != 32))):
        raise SourceGradientHold("CLASS_OWNER_SEMANTIC_CONFLICT")
    n = int(np.count_nonzero(sleeve_candidate))
    if (type(max_candidate_pixels) is not int or max_candidate_pixels < 1 or
            n > max_candidate_pixels):
        raise SourceGradientHold("CANDIDATE_GRAPH_BUDGET")
    empty = np.zeros(shape, dtype=bool)
    if n == 0 or not np.any(outerwear_seed):
        return empty, {"decision": "ABSTAIN_NO_SEED_OR_SLEEVE", "retained": 0,
                       "owner_promotion_authorized": False, "Phase4": "FAIL"}

    lab = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2LAB).astype(np.float32)
    lab[:, :, 0] *= 100.0 / 255.0
    lab[:, :, 1:] -= 128.0
    edge_right = np.sqrt(np.sum(np.diff(lab, axis=1) ** 2, axis=2))
    edge_down = np.sqrt(np.sum(np.diff(lab, axis=0) ** 2, axis=2))
    internal = np.concatenate((
        edge_right[outerwear_seed[:, :-1] & outerwear_seed[:, 1:]],
        edge_down[outerwear_seed[:-1, :] & outerwear_seed[1:, :]],
    ))
    if not internal.size:
        raise SourceGradientHold("INSUFFICIENT_SEED_EDGE_EVIDENCE")
    cutoff = float(np.quantile(internal, 0.95))
    height, width = shape
    pixels = np.flatnonzero(sleeve_candidate.ravel())
    index = np.full(height * width, -1, dtype=np.int32)
    index[pixels] = np.arange(n, dtype=np.int32)
    anchor_bits = np.zeros(n, dtype=np.uint8)
    pairs = []
    for dy, dx, gradient in ((0, 1, edge_right), (1, 0, edge_down)):
        left = sleeve_candidate[:height-dy, :width-dx]
        right = sleeve_candidate[dy:, dx:]
        passable = gradient <= cutoff
        yy, xx = np.nonzero(left & right & passable)
        pairs.append((index[yy * width + xx],
                      index[(yy + dy) * width + xx + dx]))
        yy, xx = np.nonzero(left & outerwear_seed[dy:, dx:] & passable)
        source_owner = seed_owner_ids[dy:, dx:][yy, xx]
        np.bitwise_or.at(anchor_bits, index[yy * width + xx],
                         np.left_shift(np.uint8(1), source_owner - 1))
        yy, xx = np.nonzero(outerwear_seed[:height-dy, :width-dx] & right & passable)
        source_owner = seed_owner_ids[:height-dy, :width-dx][yy, xx]
        np.bitwise_or.at(anchor_bits, index[(yy + dy) * width + xx + dx],
                         np.left_shift(np.uint8(1), source_owner - 1))
    rows = np.concatenate([a for a, _ in pairs] + [b for _, b in pairs])
    cols = np.concatenate([b for _, b in pairs] + [a for a, _ in pairs])
    graph = sparse.csr_matrix((np.ones(len(rows), dtype=np.uint8), (rows, cols)),
                              shape=(n, n))
    groups, group_ids = connected_components(graph, directed=False)
    owner_bits = np.zeros(groups, dtype=np.uint8)
    np.bitwise_or.at(owner_bits, group_ids, anchor_bits)
    attached = (owner_bits == 1) | (owner_bits == 2)
    disputed = owner_bits == 3
    retained = empty.ravel()
    retained[pixels] = attached[group_ids]
    retained = retained.reshape(shape)
    if np.any(retained & ~sleeve_candidate):
        raise SourceGradientHold("CANDIDATE_ESCAPE")
    return retained, {
        "schema": "minimalizer/local-l02/source-gradient-sleeve-shadow/v1",
        "decision": "SOURCE_ONLY_HYPOTHESIS_NOT_OWNER",
        "source_seed_internal_edge_p95_deltaE76": round(cutoff, 6),
        "candidate": n, "retained": int(np.count_nonzero(retained)),
        "abstained": n - int(np.count_nonzero(retained)),
        "candidate_components": int(groups),
        "seed_attached_components": int(np.count_nonzero(attached)),
        "dual_owner_abstained_components": int(np.count_nonzero(disputed)),
        "dual_owner_abstained_source_pixels": int(np.count_nonzero(
            disputed[group_ids])),
        "manual_labels_used_for_inference": False,
        "owner_promotion_authorized": False,
        "L02": "HOLD", "Phase4": "FAIL", "L03": "NO_GO",
        "Golden": "HOLD", "production": "NO_GO",
    }
