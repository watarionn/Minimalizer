from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .structure_first_recovery import expand_long_hair


@dataclass
class StructureHeadAnchorResult:
    enabled: bool
    reason: str
    head_mask: np.ndarray | None = None
    hair_mask: np.ndarray | None = None
    expanded_hair: bool = False

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "expanded_hair": bool(self.expanded_hair),
        }


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1

def build_face_anchored_head(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    face_mask: np.ndarray,
) -> StructureHeadAnchorResult:
    if subject_mask.shape != face_mask.shape or subject_mask.shape != rgb.shape[:2]:
        return StructureHeadAnchorResult(False, "mask_shape_mismatch")
    face_box = _bbox(face_mask)
    subject_box = _bbox(subject_mask)
    if face_box is None or subject_box is None:
        return StructureHeadAnchorResult(False, "required_mask_missing")

    fx0, fy0, fx1, fy1 = face_box
    fw, fh = max(fx1 - fx0, 1), max(fy1 - fy0, 1)
    h, w = subject_mask.shape
    subject_area = max(int((subject_mask > 0).sum()), 1)
    face_area = int((face_mask > 0).sum())
    if face_area / subject_area > 0.20:
        return StructureHeadAnchorResult(False, "face_area_ratio_gate")

    center = (
        int(round((fx0 + fx1) * 0.5)),
        int(round((fy0 + fy1) * 0.5 - fh * 0.08)),
    )
    axes = (
        max(6, int(round(fw * 0.75))),
        max(8, int(round(fh * 0.90))),
    )
    head = np.zeros_like(subject_mask, dtype=np.uint8)
    cv2.ellipse(head, center, axes, 0, 0, 360, 1, -1)
    head &= (subject_mask > 0).astype(np.uint8)
    if int(head.sum()) < 48:
        return StructureHeadAnchorResult(False, "head_area_gate")

    face_dilated = cv2.dilate(
        (face_mask > 0).astype(np.uint8),
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
    )
    hair_seed = (head & (1 - face_dilated)).astype(np.uint8)
    if int(hair_seed.sum()) < 24:
        return StructureHeadAnchorResult(False, "hair_seed_gate")

    hair, stats = expand_long_hair(
        rgb,
        (subject_mask > 0).astype(np.uint8),
        hair_seed,
        (face_mask > 0).astype(np.uint8),
        subject_box,
    )
    return StructureHeadAnchorResult(
        True,
        "ok",
        head_mask=head,
        hair_mask=hair,
        expanded_hair=bool(stats.get("expanded")),
    )
