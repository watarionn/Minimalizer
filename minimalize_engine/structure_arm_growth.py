import cv2
import numpy as np


def grow_arm_from_prior(
    subject_mask: np.ndarray,
    prior: np.ndarray,
    *,
    side: str,
    center_x: int,
    bbox_width: int,
) -> np.ndarray:
    mask = (subject_mask > 0).astype(np.uint8)
    seed = (prior > 0).astype(np.uint8)
    if not np.any(seed):
        return np.zeros_like(mask)

    overlap = max(4, int(round(bbox_width * 0.10)))
    side_guard = np.zeros_like(mask)
    if side == "left":
        side_guard[:, : min(mask.shape[1], center_x + overlap)] = 1
    else:
        side_guard[:, max(0, center_x - overlap) :] = 1
    best = seed.copy()
    best_area = int(best.sum())
    subject_area = max(int(mask.sum()), 1)

    for ratio in (0.08, 0.11, 0.14, 0.17):
        radius = max(5, int(round(bbox_width * ratio)) | 1)
        near = cv2.dilate(
            seed,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius, radius)),
        )
        candidate = (mask & near & side_guard).astype(np.uint8)
        merged = (candidate | seed).astype(np.uint8)
        merged = cv2.morphologyEx(
            merged,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
        )
        count, labels, stats, _ = cv2.connectedComponentsWithStats(merged, 8)
        chosen = np.zeros_like(mask)
        chosen_area = 0
        for index in range(1, count):
            comp = labels == index
            if not np.any(comp & (seed > 0)):
                continue
            area = int(stats[index, cv2.CC_STAT_AREA])
            if area > chosen_area:
                chosen_area = area
                chosen = comp.astype(np.uint8)

        if not np.any(chosen):
            continue
        area_ratio = chosen_area / float(subject_area)
        if area_ratio > 0.34:
            break
        if chosen_area > best_area:
            best = chosen
            best_area = chosen_area

    return best.astype(np.uint8)
