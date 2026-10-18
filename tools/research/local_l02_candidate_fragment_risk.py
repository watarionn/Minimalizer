"""L02 research-only fragment audit of frozen sleeve proposals.

Source-only observations. A class32 parent touching a jacket/coat seed does
NOT imply that a retained fragment still touches a retained seed. Neither
kind of contact proves clothing ownership. No source images or masks emitted.
"""
from __future__ import annotations

import cv2
import numpy as np

from local_l02_sleeve_component_evidence import _validate_source


class FragmentAuditHold(ValueError):
    pass


def audit_candidate_fragments(*, rgba: np.ndarray, classids: np.ndarray,
                              candidate: np.ndarray) -> dict:
    alpha = _validate_source(rgba, classids, candidate)
    seed = np.isin(classids, (5, 10)) & alpha
    retained_seed = seed & candidate
    sleeve = (classids == 32) & alpha
    retained_sleeve = sleeve & candidate

    parent_count, parent_labels = cv2.connectedComponents(
        sleeve.astype(np.uint8), connectivity=8)
    child_count, child_labels = cv2.connectedComponents(
        retained_sleeve.astype(np.uint8), connectivity=8)
    cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    square = np.ones((3, 3), dtype=np.uint8)

    def touch(seed_mask: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        return cv2.dilate(seed_mask.astype(np.uint8), kernel, iterations=1).astype(bool)

    parent_contact = touch(seed, square) & sleeve
    parent_touch_by_id = np.bincount(parent_labels[parent_contact], minlength=parent_count) > 0
    parent_touch_by_id[0] = False
    inherited_parent_contact = parent_touch_by_id[parent_labels] & retained_sleeve
    inherited_touch_by_child = np.bincount(
        child_labels[inherited_parent_contact], minlength=child_count) > 0

    child_touch4 = np.bincount(
        child_labels[touch(retained_seed, cross) & retained_sleeve], minlength=child_count) > 0
    child_touch8 = np.bincount(
        child_labels[touch(retained_seed, square) & retained_sleeve], minlength=child_count) > 0
    child_touch4[0] = child_touch8[0] = inherited_touch_by_child[0] = False
    if np.any(child_touch4 & ~child_touch8):
        raise FragmentAuditHold("FOUR_CONTACT_WITHOUT_EIGHT_CONTACT")

    disconnected_inherited = inherited_touch_by_child & ~child_touch8
    orphan = ~inherited_touch_by_child & ~child_touch8
    orphan[0] = False
    by_type = {
        "retained_seed_contact4": int(np.count_nonzero(child_touch4)),
        "retained_seed_diagonal_only": int(np.count_nonzero(child_touch8 & ~child_touch4)),
        "inherited_parent_contact_only": int(np.count_nonzero(disconnected_inherited)),
        "no_parent_or_retained_seed_contact": int(np.count_nonzero(orphan)),
    }
    if sum(by_type.values()) != child_count - 1:
        raise FragmentAuditHold("FRAGMENT_PARTITION_MISMATCH")

    sizes = np.bincount(child_labels[retained_sleeve], minlength=child_count)
    retained_pixels_by_type = {
        "retained_seed_contact4": int(sizes[child_touch4].sum()),
        "retained_seed_diagonal_only": int(sizes[child_touch8 & ~child_touch4].sum()),
        "inherited_parent_contact_only": int(sizes[disconnected_inherited].sum()),
        "no_parent_or_retained_seed_contact": int(sizes[orphan].sum()),
    }
    if sum(retained_pixels_by_type.values()) != int(retained_sleeve.sum()):
        raise FragmentAuditHold("FRAGMENT_PIXEL_PARTITION_MISMATCH")
    return {
        "schema": "minimalizer/local-l02/candidate-fragment-risk/v1",
        "source_class32_components": int(parent_count - 1),
        "candidate_class32_components": int(child_count - 1),
        "source_seed_pixels": int(seed.sum()),
        "retained_seed_pixels": int(retained_seed.sum()),
        "candidate_class32_pixels": int(retained_sleeve.sum()),
        "fragment_counts": by_type,
        "fragment_pixels": retained_pixels_by_type,
        "retained_fragment_contact_is_owner_proof": False,
        "inherited_source_contact_is_owner_proof": False,
        "source_pixels_synthesized": 0,
        "human_annotation_used": False,
        "independent_holdout_proven": False,
        "semantic_quality_pass": False,
        "L02": "HOLD", "Golden": "HOLD", "L03": "NO_GO", "production": "NO_GO",
    }
