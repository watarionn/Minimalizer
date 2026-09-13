from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class BodyPartitionResult:
    enabled: bool
    reason: str
    torso: np.ndarray | None = None
    left_arm: np.ndarray | None = None
    right_arm: np.ndarray | None = None


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 0)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _distance_to_seed(seed: np.ndarray) -> np.ndarray:
    inv = (1 - (seed > 0).astype(np.uint8))
    return cv2.distanceTransform(inv, cv2.DIST_L2, 5)
def partition_body_by_structure_seeds(
    subject_mask: np.ndarray,
    face_mask: np.ndarray,
    left_prior: np.ndarray,
    right_prior: np.ndarray,
) -> BodyPartitionResult:
    mask = (subject_mask > 0).astype(np.uint8)
    face = (face_mask > 0).astype(np.uint8)
    if mask.shape != face.shape:
        return BodyPartitionResult(False, "mask_shape_mismatch")

    box = _bbox(mask)
    face_box = _bbox(face)
    if box is None or face_box is None:
        return BodyPartitionResult(False, "bbox_missing")
    x0, y0, x1, y1 = box
    fx0, fy0, fx1, fy1 = face_box
    cx = int(round((fx0 + fx1) * 0.5))
    face_h = max(fy1 - fy0, 1)

    torso_seed = np.zeros_like(mask)
    torso_top = min(y1 - 1, fy1 + max(2, int(round(face_h * 0.20))))
    torso_bottom = y1
    torso_half = max(2, int(round((fx1 - fx0) * 0.16)))
    cv2.line(torso_seed, (cx, torso_top), (cx, torso_bottom - 1), 1, max(3, torso_half * 2 + 1))

    left_seed = (left_prior > 0).astype(np.uint8)
    right_seed = (right_prior > 0).astype(np.uint8)
    if not np.any(left_seed) and not np.any(right_seed):
        return BodyPartitionResult(False, "arm_seed_missing")
    body = mask.copy()
    body[:max(y0, fy1), :] = 0

    d_torso = _distance_to_seed(torso_seed)
    d_left = _distance_to_seed(left_seed) if np.any(left_seed) else np.full(mask.shape, 1e6, dtype=np.float32)
    d_right = _distance_to_seed(right_seed) if np.any(right_seed) else np.full(mask.shape, 1e6, dtype=np.float32)

    # Bias the center slightly toward torso, while keeping arm anchors dominant near hands/sleeves.
    d_torso = d_torso * 0.90
    stack = np.stack([d_torso, d_left, d_right], axis=0)
    labels = np.argmin(stack, axis=0)

    torso = ((labels == 0) & (body > 0)).astype(np.uint8)
    left_arm = ((labels == 1) & (body > 0)).astype(np.uint8)
    right_arm = ((labels == 2) & (body > 0)).astype(np.uint8)

    # Keep arm partitions on their natural side with only a small central overlap.
    bbox_width = max(x1 - x0, 1)
    overlap = max(4, int(round(bbox_width * 0.10)))
    left_arm[:, min(mask.shape[1], cx + overlap) :] = 0
    right_arm[:, : max(0, cx - overlap)] = 0

    # Reassign any pixels cut by side guards back to torso so coverage stays complete.
    assigned = (torso | left_arm | right_arm).astype(np.uint8)
    torso |= (body & (1 - assigned)).astype(np.uint8)

    return BodyPartitionResult(True, "ok", torso, left_arm, right_arm)
