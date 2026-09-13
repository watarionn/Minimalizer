from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .structure_sleeve_completion import _face_box, _hand_component, _skin_like_from_face


@dataclass
class StructureArmPriorResult:
    enabled: bool
    reason: str
    left_arm: np.ndarray | None = None
    right_arm: np.ndarray | None = None
    left_hand_pixels: int = 0
    right_hand_pixels: int = 0

def _arm_corridor(shape: tuple[int, int], shoulder: tuple[int, int], hand: np.ndarray, face_w: int) -> np.ndarray:
    h, w = shape
    ys, xs = np.where(hand > 0)
    if not len(xs):
        return np.zeros((h, w), dtype=np.uint8)
    center = (int(round(float(np.median(xs)))), int(round(float(np.median(ys)))))
    outer = np.zeros((h, w), dtype=np.uint8)
    cv2.line(outer, shoulder, center, 1, max(9, int(round(face_w * 1.20))))
    outer |= hand.astype(np.uint8)
    return outer


def build_structure_arm_priors(rgb: np.ndarray, subject_mask: np.ndarray, face_mask: np.ndarray) -> StructureArmPriorResult:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return StructureArmPriorResult(False, "rgb_required")
    if subject_mask.shape != rgb.shape[:2] or face_mask.shape != rgb.shape[:2]:
        return StructureArmPriorResult(False, "mask_shape_mismatch")
    box = _face_box(face_mask)
    if box is None:
        return StructureArmPriorResult(False, "face_missing")
    fx0, _fy0, fx1, fy1 = box
    face_w = max(fx1 - fx0, 1)
    face_h = max(box[3] - box[1], 1)
    cx = (fx0 + fx1) * 0.5
    shoulder_y = min(subject_mask.shape[0] - 1, int(round(fy1 + face_h * 0.35)))
    shoulder_half = max(int(round(face_w * 0.75)), int(round(subject_mask.shape[1] * 0.07)))
    skin = _skin_like_from_face(rgb, face_mask)
    left_hand = _hand_component(skin, face_mask, "left", box)
    right_hand = _hand_component(skin, face_mask, "right", box)
    left = _arm_corridor(
        subject_mask.shape,
        (int(round(cx - shoulder_half)), shoulder_y),
        left_hand,
        face_w,
    )
    right = _arm_corridor(
        subject_mask.shape,
        (int(round(cx + shoulder_half)), shoulder_y),
        right_hand,
        face_w,
    )
    left &= subject_mask.astype(np.uint8)
    right &= subject_mask.astype(np.uint8)
    if not np.any(left) and not np.any(right):
        return StructureArmPriorResult(False, "hand_anchor_missing")
    return StructureArmPriorResult(
        True,
        "ok",
        left_arm=left,
        right_arm=right,
        left_hand_pixels=int(left_hand.sum()),
        right_hand_pixels=int(right_hand.sum()),
    )
