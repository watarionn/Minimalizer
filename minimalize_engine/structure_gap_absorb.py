from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class GapAbsorbResult:
    masks: tuple[np.ndarray, ...]
    remaining: np.ndarray
    absorbed_ratio: float


def absorb_small_gaps(
    subject_mask: np.ndarray,
    zone_masks: tuple[np.ndarray, ...],
    *,
    max_gap_ratio: float = 0.035,
) -> GapAbsorbResult:
    subject = (subject_mask > 0).astype(np.uint8)
    zones = [(mask > 0).astype(np.uint8) for mask in zone_masks]
    covered = np.zeros_like(subject)
    for zone in zones:
        covered |= zone
    gap = subject & (1 - covered)
    subject_area = max(int(subject.sum()), 1)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(gap.astype(np.uint8), 8)
    absorbed = 0
    for index in range(1, count):
        component = (labels == index).astype(np.uint8)
        area = int(stats[index, cv2.CC_STAT_AREA])
        if area <= 0:
            continue
        ratio = area / subject_area
        if ratio > max_gap_ratio:
            continue

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        ring = cv2.dilate(component, kernel) & (1 - component)
        best_index = None
        best_touch = 0
        for zone_index, zone in enumerate(zones):
            touch = int(np.count_nonzero(ring & zone))
            if touch > best_touch:
                best_touch = touch
                best_index = zone_index
        if best_index is None or best_touch <= 0:
            continue
        zones[best_index] |= component
        absorbed += area

    covered = np.zeros_like(subject)
    for zone in zones:
        covered |= zone
    remaining = subject & (1 - covered)
    return GapAbsorbResult(tuple(zones), remaining, absorbed / subject_area)
