from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class StructureSleeveCompletionResult:
    enabled: bool
    reason: str
    mask: np.ndarray | None = None
    added_area_ratio: float = 0.0
    border_leak_ratio: float = 0.0
    left_added: bool = False
    right_added: bool = False

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "added_area_ratio": round(float(self.added_area_ratio), 6),
            "border_leak_ratio": round(float(self.border_leak_ratio), 6),
            "left_added": bool(self.left_added),
            "right_added": bool(self.right_added),
        }


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


def _face_box(face_mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(face_mask > 0)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _largest_connected_to(mask: np.ndarray, seed: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    best = None
    best_area = 0
    for index in range(1, count):
        component = labels == index
        if not np.any(component & (seed > 0)):
            continue
        area = int(stats[index, cv2.CC_STAT_AREA])
        if area > best_area:
            best_area = area
            best = component
    return best.astype(np.uint8) if best is not None else np.zeros_like(mask, dtype=np.uint8)


def _median_color(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    pixels = rgb[mask > 0]
    if not len(pixels):
        return np.asarray((190, 160, 150), dtype=np.uint8)
    return np.median(pixels, axis=0).astype(np.uint8)


def _skin_like_from_face(rgb: np.ndarray, face_mask: np.ndarray) -> np.ndarray:
    color = _median_color(rgb, face_mask).reshape(1, 1, 3)
    lab = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    ref = cv2.cvtColor(color, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
    distance = np.linalg.norm(lab - ref[None, None, :], axis=2)
    return (distance <= 26.0).astype(np.uint8)


def _hand_component(
    skin_like: np.ndarray,
    face_mask: np.ndarray,
    side: str,
    face_box: tuple[int, int, int, int],
) -> np.ndarray:
    h, w = skin_like.shape
    fx0, fy0, fx1, fy1 = face_box
    face_w = max(fx1 - fx0, 1)
    face_h = max(fy1 - fy0, 1)
    cx = (fx0 + fx1) * 0.5
    zone = np.zeros_like(skin_like)
    y0 = max(0, fy0 - int(face_h * 0.55))
    y1 = min(h, fy1 + int(face_h * 1.10))
    if side == "left":
        zone[y0:y1, : max(0, int(round(cx - face_w * 0.75)))] = 1
    else:
        zone[y0:y1, min(w, int(round(cx + face_w * 0.75))) :] = 1
    candidates = skin_like & zone & (1 - face_mask.astype(np.uint8))
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(candidates, 8)
    face_area = max(int((face_mask > 0).sum()), 1)
    best = None
    best_score = -1.0
    for index in range(1, count):
        area = int(stats[index, cv2.CC_STAT_AREA])
        width = int(stats[index, cv2.CC_STAT_WIDTH])
        height = int(stats[index, cv2.CC_STAT_HEIGHT])
        area_to_face = area / float(face_area)
        aspect = width / max(float(height), 1.0)
        if area < max(8, int(round(h * w * 0.0003))) or area > int(round(h * w * 0.03)):
            continue
        if area_to_face > 0.80 or not 0.22 <= aspect <= 3.0:
            continue
        x, y = centroids[index]
        horizontal = abs(float(x) - cx) / max(float(w), 1.0)
        vertical = 1.0 - min(abs(float(y) - fy1) / max(float(h) * 0.35, 1.0), 1.0)
        score = area / max(float(h * w), 1.0) + 0.03 * horizontal + 0.02 * vertical
        if score > best_score:
            best_score = score
            best = labels == index
    return best.astype(np.uint8) if best is not None else np.zeros_like(skin_like)


def complete_structure_sleeves(
    rgb: np.ndarray,
    coarse_mask: np.ndarray,
    face_mask: np.ndarray,
) -> StructureSleeveCompletionResult:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return StructureSleeveCompletionResult(False, "rgb_required")
    if coarse_mask.shape != rgb.shape[:2] or face_mask.shape != rgb.shape[:2]:
        return StructureSleeveCompletionResult(False, "mask_shape_mismatch")
    face_box = _face_box(face_mask)
    if face_box is None:
        return StructureSleeveCompletionResult(False, "face_missing")

    h, w = coarse_mask.shape
    fx0, fy0, fx1, fy1 = face_box
    face_w = max(fx1 - fx0, 1)
    face_h = max(fy1 - fy0, 1)
    cx = (fx0 + fx1) * 0.5
    shoulder_y = min(h - 1, int(round(fy1 + face_h * 0.35)))
    sleeve_bottom = min(h, int(round(fy1 + face_h * 2.7)))

    grab = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)
    edge = max(2, int(round(min(h, w) * 0.02)))
    grab[:edge, :] = cv2.GC_BGD
    grab[-edge:, :] = cv2.GC_BGD
    grab[:, :edge] = cv2.GC_BGD
    grab[:, -edge:] = cv2.GC_BGD
    grab[coarse_mask > 0] = cv2.GC_FGD
    grab[face_mask > 0] = cv2.GC_FGD

    shoulder_half = max(int(round(face_w * 0.75)), int(round(w * 0.07)))
    left_shoulder = int(round(cx - shoulder_half))
    right_shoulder = int(round(cx + shoulder_half))
    left_tip = max(edge + 1, int(round(cx - max(face_w * 2.6, w * 0.32))))
    right_tip = min(w - edge - 2, int(round(cx + max(face_w * 2.6, w * 0.32))))

    left_poly = np.asarray(
        [
            (left_shoulder, shoulder_y),
            (left_tip, shoulder_y + int(face_h * 0.25)),
            (left_tip, sleeve_bottom),
            (int(round(cx - face_w * 0.20)), sleeve_bottom),
        ],
        dtype=np.int32,
    )
    right_poly = np.asarray(
        [
            (right_shoulder, shoulder_y),
            (right_tip, shoulder_y + int(face_h * 0.25)),
            (right_tip, sleeve_bottom),
            (int(round(cx + face_w * 0.20)), sleeve_bottom),
        ],
        dtype=np.int32,
    )
    cv2.fillPoly(grab, [left_poly, right_poly], cv2.GC_PR_FGD)
    grab[coarse_mask > 0] = cv2.GC_FGD
    grab[face_mask > 0] = cv2.GC_FGD

    skin_like = _skin_like_from_face(rgb, face_mask)
    left_hand = _hand_component(skin_like, face_mask, "left", face_box)
    right_hand = _hand_component(skin_like, face_mask, "right", face_box)
    for hand, shoulder_x in ((left_hand, left_shoulder), (right_hand, right_shoulder)):
        ys, xs = np.where(hand > 0)
        if not len(xs):
            continue
        hand_center = (int(round(float(np.median(xs)))), int(round(float(np.median(ys)))))
        outer = np.zeros((h, w), dtype=np.uint8)
        core = np.zeros((h, w), dtype=np.uint8)
        cv2.line(
            outer,
            (shoulder_x, shoulder_y),
            hand_center,
            1,
            max(9, int(round(face_w * 1.25))),
        )
        cv2.line(
            core,
            (shoulder_x, shoulder_y),
            hand_center,
            1,
            max(3, int(round(face_w * 0.28))),
        )
        grab[outer > 0] = cv2.GC_PR_FGD
        grab[core > 0] = cv2.GC_FGD
        grab[hand > 0] = cv2.GC_FGD
    grab[:edge, :] = cv2.GC_BGD
    grab[-edge:, :] = cv2.GC_BGD
    grab[:, :edge] = cv2.GC_BGD
    grab[:, -edge:] = cv2.GC_BGD
    grab[coarse_mask > 0] = cv2.GC_FGD
    grab[face_mask > 0] = cv2.GC_FGD

    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    bg_model = np.zeros((1, 65), dtype=np.float64)
    fg_model = np.zeros((1, 65), dtype=np.float64)
    cv2.setRNGSeed(1701)
    cv2.grabCut(bgr, grab, None, bg_model, fg_model, 4, cv2.GC_INIT_WITH_MASK)
    candidate = np.isin(grab, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)

    upper = np.zeros_like(candidate)
    upper[max(0, fy0 - face_h):sleeve_bottom, :] = 1
    candidate &= upper
    candidate |= coarse_mask.astype(np.uint8)
    candidate = cv2.morphologyEx(
        candidate,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
    )

    shoulder_seed = np.zeros_like(candidate)
    seed_y0 = max(0, shoulder_y - int(face_h * 0.40))
    seed_y1 = min(h, shoulder_y + int(face_h * 0.70))
    seed_x0 = max(0, int(round(cx - face_w * 1.35)))
    seed_x1 = min(w, int(round(cx + face_w * 1.35)))
    shoulder_seed[seed_y0:seed_y1, seed_x0:seed_x1] = coarse_mask[seed_y0:seed_y1, seed_x0:seed_x1]

    connected = _largest_connected_to(candidate, shoulder_seed)
    if not np.any(connected):
        return StructureSleeveCompletionResult(False, "shoulder_connection_missing")

    added = connected & (1 - coarse_mask.astype(np.uint8))
    added_ratio = float(added.mean())
    leak = _border_leak(connected)
    if added_ratio < 0.003:
        return StructureSleeveCompletionResult(
            False,
            "sleeve_gain_too_small",
            mask=coarse_mask.astype(np.uint8),
            added_area_ratio=added_ratio,
            border_leak_ratio=leak,
        )
    if leak > 0.08:
        return StructureSleeveCompletionResult(
            False,
            "sleeve_leak_gate",
            mask=coarse_mask.astype(np.uint8),
            added_area_ratio=added_ratio,
            border_leak_ratio=leak,
        )

    left_added = bool(np.any(added[:, : int(round(cx))]))
    right_added = bool(np.any(added[:, int(round(cx)) :]))
    return StructureSleeveCompletionResult(
        True,
        "ok",
        mask=connected.astype(np.uint8),
        added_area_ratio=added_ratio,
        border_leak_ratio=leak,
        left_added=left_added,
        right_added=right_added,
    )


def accept_structure_sleeve_completion(
    result: StructureSleeveCompletionResult,
    original_score: float,
    completed_score: float,
    original_face_score: float,
    completed_face_score: float,
) -> bool:
    if not result.enabled or result.mask is None:
        return False
    added = float(result.added_area_ratio)
    leak = float(result.border_leak_ratio)
    if completed_score < original_score - 0.02:
        return False
    if completed_face_score < original_face_score - 0.15:
        return False
    if added > 0.12 and leak > 0.06:
        return False
    return True
