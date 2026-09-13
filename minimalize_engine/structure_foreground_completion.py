from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class StructureForegroundCompletionResult:
    enabled: bool
    reason: str
    mask: np.ndarray | None = None
    original_area_ratio: float = 0.0
    completed_area_ratio: float = 0.0
    added_area_ratio: float = 0.0
    border_leak_ratio: float = 0.0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "original_area_ratio": round(float(self.original_area_ratio), 6),
            "completed_area_ratio": round(float(self.completed_area_ratio), 6),
            "added_area_ratio": round(float(self.added_area_ratio), 6),
            "border_leak_ratio": round(float(self.border_leak_ratio), 6),
        }


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _border_leak(mask: np.ndarray) -> float:
    h, w = mask.shape
    thick = max(2, int(round(min(h, w) * 0.03)))
    border = np.concatenate(
        [
            mask[:thick].ravel(),
            mask[-thick:].ravel(),
            mask[thick:-thick, :thick].ravel(),
            mask[thick:-thick, -thick:].ravel(),
        ]
    )
    return float(border.mean()) if len(border) else 0.0


def _body_prior(face_mask: np.ndarray, subject_box: tuple[int, int, int, int]) -> np.ndarray:
    prior = np.zeros_like(face_mask, dtype=np.uint8)
    face_box = _bbox(face_mask)
    if face_box is None:
        return prior
    fx0, fy0, fx1, fy1 = face_box
    sx0, sy0, sx1, sy1 = subject_box
    fw = max(fx1 - fx0, 1)
    fh = max(fy1 - fy0, 1)
    cx = int(round((fx0 + fx1) * 0.5))

    shoulder_y = min(sy1 - 1, fy1 + max(2, int(round(fh * 0.18))))
    bottom_y = min(sy1, max(shoulder_y + 1, fy1 + int(round(fh * 4.6))))
    top_half = max(int(round(fw * 1.9)), 8)
    bottom_half = max(int(round(fw * 2.5)), top_half)
    points = np.asarray(
        [
            (max(sx0, cx - top_half), shoulder_y),
            (min(sx1 - 1, cx + top_half), shoulder_y),
            (min(sx1 - 1, cx + bottom_half), bottom_y),
            (max(sx0, cx - bottom_half), bottom_y),
        ],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(prior, points, 1)
    return prior


def _largest_connected_to_face(mask: np.ndarray, face_mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if count <= 1:
        return mask.astype(np.uint8)
    face_labels = labels[face_mask > 0]
    face_labels = face_labels[face_labels > 0]
    if len(face_labels):
        values, counts = np.unique(face_labels, return_counts=True)
        index = int(values[int(np.argmax(counts))])
    else:
        index = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    return (labels == index).astype(np.uint8)


def complete_structure_foreground(
    rgb: np.ndarray,
    coarse_mask: np.ndarray,
    face_mask: np.ndarray,
) -> StructureForegroundCompletionResult:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return StructureForegroundCompletionResult(False, "rgb_required")
    if coarse_mask.shape != rgb.shape[:2] or face_mask.shape != rgb.shape[:2]:
        return StructureForegroundCompletionResult(False, "mask_shape_mismatch")
    coarse = (coarse_mask > 0).astype(np.uint8)
    face = (face_mask > 0).astype(np.uint8)
    if int(coarse.sum()) < 32 or int(face.sum()) < 16:
        return StructureForegroundCompletionResult(False, "seed_area_gate")

    subject_box = _bbox(coarse)
    if subject_box is None:
        return StructureForegroundCompletionResult(False, "empty_subject")
    h, w = coarse.shape
    original_area = float(coarse.mean())
    body_prior = _body_prior(face, subject_box)

    grab = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)
    edge = max(2, int(round(min(h, w) * 0.02)))
    grab[:edge, :] = cv2.GC_BGD
    grab[-edge:, :] = cv2.GC_BGD
    grab[:, :edge] = cv2.GC_BGD
    grab[:, -edge:] = cv2.GC_BGD
    dilation_radius = max(3, int(round(min(h, w) * 0.035)))
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (dilation_radius * 2 + 1, dilation_radius * 2 + 1),
    )
    recovery_zone = cv2.dilate(coarse, kernel)
    grab[recovery_zone > 0] = cv2.GC_PR_FGD
    grab[body_prior > 0] = cv2.GC_PR_FGD

    inner_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    definite_subject = cv2.erode(coarse, inner_kernel)
    grab[definite_subject > 0] = cv2.GC_FGD
    grab[face > 0] = cv2.GC_FGD

    bgr = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2BGR)
    bg_model = np.zeros((1, 65), dtype=np.float64)
    fg_model = np.zeros((1, 65), dtype=np.float64)
    cv2.setRNGSeed(1701)
    try:
        cv2.grabCut(bgr, grab, None, bg_model, fg_model, 4, cv2.GC_INIT_WITH_MASK)
    except cv2.error:
        return StructureForegroundCompletionResult(False, "grabcut_error")

    completed = np.isin(grab, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)
    completed |= coarse
    completed = cv2.morphologyEx(
        completed,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
    )
    completed = _largest_connected_to_face(completed, face)
    completed_area = float(completed.mean())
    added = completed & (1 - coarse)
    added_area = float(added.mean())
    leak = _border_leak(completed)

    if completed_area < original_area * 0.98:
        return StructureForegroundCompletionResult(
            False,
            "area_regression",
            mask=coarse,
            original_area_ratio=original_area,
            completed_area_ratio=completed_area,
            added_area_ratio=added_area,
            border_leak_ratio=leak,
        )
    excessive_growth = added_area > 0.45
    leaky_growth = leak > 0.18
    large_and_leaky = added_area > 0.30 and leak > 0.08
    if excessive_growth or leaky_growth or large_and_leaky:
        return StructureForegroundCompletionResult(
            False,
            "completion_leak_gate",
            mask=coarse,
            original_area_ratio=original_area,
            completed_area_ratio=completed_area,
            added_area_ratio=added_area,
            border_leak_ratio=leak,
        )
    return StructureForegroundCompletionResult(
        True,
        "ok",
        mask=completed,
        original_area_ratio=original_area,
        completed_area_ratio=completed_area,
        added_area_ratio=added_area,
        border_leak_ratio=leak,
    )


def accept_structure_foreground_completion(
    result: StructureForegroundCompletionResult,
    original_score: float,
    completed_score: float,
) -> bool:
    if not result.enabled or result.mask is None:
        return False
    added = float(result.added_area_ratio)
    gain = float(completed_score) - float(original_score)
    if added < 0.001:
        return False
    leak = float(result.border_leak_ratio)
    if leak > 0.18:
        return False
    if added <= 0.08:
        return gain >= 0.010
    if leak <= 0.03:
        return gain >= -0.020
    if leak <= 0.08:
        return gain >= 0.025
    return gain >= 0.080
