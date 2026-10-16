"""Source-only L02 geodesic sleeve *shadow*, never an owner promotion.

Runs the pinned exploratory SegFormer class5/10/32 color proposal first, then
ABSTAINS on every proposed sleeve pixel not 8-connected to an original
jacket/coat seed through the candidate itself. No source pixels are added.
H04/H06/H08 selected the underlying LAB threshold, so this is NOT an
independent generalization test or Golden authority. Do not call from Worker.
"""
from __future__ import annotations

import hashlib
import numpy as np
import cv2

from local_l02_sleeve_color_attachment_shadow import (
    OWNER_IDS, ResearchHold, propose,
)


def propose_connected(rgba: np.ndarray, classids: np.ndarray):
    """Return (subtractive candidate, source-only aggregate), never human labels.

    Inputs are original RGBA uint8 and independently predicted SegFormer IDs.
    Human annotations are forbidden in this signature and in this inference.
    """
    before_rgba = hashlib.sha256(rgba.tobytes()).hexdigest()
    before_classes = hashlib.sha256(classids.tobytes()).hexdigest()
    candidate, original_report = propose(rgba, classids)
    alpha = rgba[:, :, 3] > 0
    seeds = np.isin(classids, OWNER_IDS) & alpha
    if not np.any(seeds):
        if np.any(candidate):
            raise ResearchHold("NONEMPTY_PROPOSAL_WITHOUT_OUTERWEAR_SEED")
        return candidate, {
            "decision": "ABSTAIN_NO_OUTERWEAR_SEED",
            "owner_promotion_authorized": False,
            "independent_holdout_quality_proven": False,
            "candidate_pixels": 0,
            "removed_unanchored_pixels": 0,
            "source_pixels_added_outside_original": 0,
        }
    if np.any(seeds & ~candidate):
        raise ResearchHold("SOURCE_SEEDS_WERE_REMOVED")
    if np.any(candidate & ~alpha):
        raise ResearchHold("SOURCE_ALPHA_BREACH")
    n, labels = cv2.connectedComponents(candidate.astype(np.uint8), connectivity=8)
    keep_ids = np.unique(labels[seeds])
    if np.any(keep_ids == 0):
        raise ResearchHold("OUTERWEAR_SEED_NOT_IN_COMPONENT")
    connected = candidate & np.isin(labels, keep_ids)
    removed = candidate & ~connected
    if np.any(removed & seeds):
        raise ResearchHold("OUTERWEAR_SEED_REMOVED")
    if np.any(connected & ~candidate) or np.any(connected & ~alpha):
        raise ResearchHold("GEODESIC_CREATED_SOURCE_PIXELS")
    if hashlib.sha256(rgba.tobytes()).hexdigest() != before_rgba:
        raise ResearchHold("SOURCE_IMAGE_MUTATED")
    if hashlib.sha256(classids.tobytes()).hexdigest() != before_classes:
        raise ResearchHold("MODEL_CLASSIDS_MUTATED")
    return connected, {
        "decision": "SHADOW_ONLY_UNANCHORED_SLEEVE_ABSTENTION",
        "owner_promotion_authorized": False,
        "independent_holdout_quality_proven": False,
        "seed_pixels": int(seeds.sum()),
        "source_color_candidate_pixels": int(candidate.sum()),
        "candidate_pixels": int(connected.sum()),
        "removed_unanchored_pixels": int(removed.sum()),
        "retained_seed_components": int(len(keep_ids)),
        "source_pixels_added_outside_original": 0,
        "parent_observation_decision": original_report["decision"],
        "prediction_sha256": hashlib.sha256(connected.tobytes()).hexdigest(),
    }
