from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .structure_first_recovery import expand_long_hair


@dataclass
class StructureSilhouetteHeadResult:
    enabled: bool
    reason: str
    head_mask: np.ndarray | None = None
    hair_mask: np.ndarray | None = None
    face_mask: np.ndarray | None = None
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

def _component_touching(mask: np.ndarray, seed: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    best = np.zeros_like(mask, dtype=np.uint8)
    best_area = 0
    for index in range(1, count):
        comp = labels == index
        if not np.any(comp & (seed > 0)):
            continue
        area = int(stats[index, cv2.CC_STAT_AREA])
        if area > best_area:
            best_area = area
            best = comp.astype(np.uint8)
    return best


def _compact_face(face_mask: np.ndarray) -> np.ndarray:
    box = _bbox(face_mask)
    if box is None:
        return np.zeros_like(face_mask, dtype=np.uint8)
    x0, y0, x1, y1 = box
    fw, fh = max(x1 - x0, 1), max(y1 - y0, 1)
    center = (int(round((x0 + x1) * 0.5)), int(round((y0 + y1) * 0.5)))
    axes = (max(4, int(round(fw * 0.33))), max(5, int(round(fh * 0.38))))
    compact = np.zeros_like(face_mask, dtype=np.uint8)
    cv2.ellipse(compact, center, axes, 0, 0, 360, 1, -1)
    return compact & (face_mask > 0).astype(np.uint8)


def _compact_face_from_head(face_mask: np.ndarray, head_mask: np.ndarray) -> np.ndarray:
    face_box = _bbox(face_mask)
    head_box = _bbox(head_mask)
    if face_box is None or head_box is None:
        return np.zeros_like(face_mask, dtype=np.uint8)
    fx0, fy0, fx1, fy1 = face_box
    hx0, hy0, hx1, hy1 = head_box
    hw, hh = max(hx1 - hx0, 1), max(hy1 - hy0, 1)
    cx = int(round((fx0 + fx1) * 0.5))
    cy = int(round((fy0 + fy1) * 0.5))

    def make_face(scale: float) -> np.ndarray:
        half_w = max(4, int(round(hw * 0.15 * scale)))
        half_h = max(5, int(round(hh * 0.18 * scale)))
        pts = np.asarray([
            (cx - int(half_w * 0.62), cy - half_h),
            (cx + int(half_w * 0.62), cy - half_h),
            (cx + half_w, cy - int(half_h * 0.55)),
            (cx + int(half_w * 0.92), cy + int(half_h * 0.40)),
            (cx + int(half_w * 0.48), cy + half_h),
            (cx - int(half_w * 0.48), cy + half_h),
            (cx - int(half_w * 0.92), cy + int(half_h * 0.40)),
            (cx - half_w, cy - int(half_h * 0.55)),
        ], dtype=np.int32)
        result = np.zeros_like(face_mask, dtype=np.uint8)
        cv2.fillPoly(result, [pts], 1)
        result &= (head_mask > 0).astype(np.uint8)
        face_hint = cv2.dilate(
            (face_mask > 0).astype(np.uint8),
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )
        return result & face_hint

    head_area = max(int((head_mask > 0).sum()), 1)
    scale = 1.0
    compact = make_face(scale)
    while int(compact.sum()) / head_area > 0.22 and scale > 0.72:
        scale *= 0.90
        compact = make_face(scale)
    while int(compact.sum()) / head_area < 0.08 and scale < 1.30:
        scale *= 1.08
        compact = make_face(scale)
    return compact

def build_silhouette_head(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    face_mask: np.ndarray,
) -> StructureSilhouetteHeadResult:
    if subject_mask.shape != face_mask.shape or subject_mask.shape != rgb.shape[:2]:
        return StructureSilhouetteHeadResult(False, "mask_shape_mismatch")
    face_box = _bbox(face_mask)
    subject_box = _bbox(subject_mask)
    if face_box is None or subject_box is None:
        return StructureSilhouetteHeadResult(False, "required_mask_missing")

    x0, y0, x1, y1 = face_box
    fw, fh = max(x1 - x0, 1), max(y1 - y0, 1)
    h, w = subject_mask.shape
    cx = int(round((x0 + x1) * 0.5))

    roi = np.zeros_like(subject_mask, dtype=np.uint8)
    rx0 = max(0, int(round(cx - fw * 1.35)))
    rx1 = min(w, int(round(cx + fw * 1.35)))
    ry0 = max(0, int(round(y0 - fh * 1.25)))
    ry1 = min(h, int(round(y1 + fh * 0.55)))
    roi[ry0:ry1, rx0:rx1] = 1

    subject = (subject_mask > 0).astype(np.uint8)
    compact_face = _compact_face(face_mask) & subject
    touch_seed = cv2.dilate(
        compact_face,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
    )
    head_candidate = subject & roi
    head = _component_touching(head_candidate, touch_seed)
    if int(head.sum()) < 48:
        return StructureSilhouetteHeadResult(False, "head_component_gate")

    # Keep head local to the real upper silhouette; only hair may grow beyond it.
    close_k = max(3, int(round(min(h, w) * 0.018)) | 1)
    head = cv2.morphologyEx(
        head,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k)),
    ) & subject & roi

    compact_face = _compact_face_from_head(face_mask, head)
    if int(compact_face.sum()) < 18:
        return StructureSilhouetteHeadResult(False, "compact_face_gate")

    face_dilated = cv2.dilate(
        compact_face,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    )
    hair_seed = (head & (1 - face_dilated)).astype(np.uint8)
    if int(hair_seed.sum()) < 24:
        return StructureSilhouetteHeadResult(False, "hair_seed_gate")

    hair, stats = expand_long_hair(
        rgb,
        subject,
        hair_seed,
        compact_face,
        subject_box,
    )
    return StructureSilhouetteHeadResult(
        True,
        "ok",
        head_mask=head,
        hair_mask=hair,
        face_mask=compact_face,
        expanded_hair=bool(stats.get("expanded")),
    )
