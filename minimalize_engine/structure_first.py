from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from .models import Shape
from .structure_arm_prior import build_structure_arm_priors
from .structure_arm_growth import grow_arm_from_prior
from .structure_body_partition import partition_body_by_structure_seeds
from .structure_first_recovery import expand_long_hair, recover_upper_hand_gestures


@dataclass
class StructureFirstResult:
    enabled: bool
    reason: str
    shapes: tuple[Shape, ...] = ()
    masks: dict[str, np.ndarray] = field(default_factory=dict)
    neck_y: int | None = None
    foreground_bbox: tuple[int, int, int, int] | None = None
    recovery_stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "shape_count": len(self.shapes),
            "parts": [shape.character_part for shape in self.shapes],
            "neck_y": self.neck_y,
            "foreground_bbox": list(self.foreground_bbox) if self.foreground_bbox else None,
            "recovery_stats": self.recovery_stats,
        }


def _largest_component(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if count <= 1:
        return mask.astype(np.uint8)
    index = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    return (labels == index).astype(np.uint8)


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _neck_y(mask: np.ndarray, box: tuple[int, int, int, int]) -> int:
    _x0, y0, _x1, y1 = box
    body_height = max(y1 - y0, 1)
    widths = np.asarray([(mask[y] > 0).sum() for y in range(y0, y1)], dtype=np.float32)
    kernel = max(5, int(round(body_height * 0.04)) | 1)
    smooth = cv2.GaussianBlur(widths.reshape(-1, 1), (1, kernel), 0).ravel()
    lo, hi = int(body_height * 0.18), int(body_height * 0.48)
    if hi <= lo + 2:
        return y0 + int(body_height * 0.34)
    best_score = float("-inf")
    best_row = int(body_height * 0.34)
    before_span = max(2, int(body_height * 0.10))
    after_span = max(2, int(body_height * 0.12))
    for row in range(lo, hi):
        before = smooth[max(0, row - before_span):row]
        after = smooth[row:min(len(smooth), row + after_span)]
        if len(before) < 2 or len(after) < 2:
            continue
        valley = (float(before.mean()) + float(after.mean())) * 0.5 - float(smooth[row])
        position_penalty = abs(row / body_height - 0.34) * 0.15 * max(float(smooth.max()), 1.0)
        score = valley - position_penalty
        if score > best_score:
            best_score = score
            best_row = row
    return y0 + best_row


def _subject_axis(mask: np.ndarray, box: tuple[int, int, int, int]) -> float:
    _x0, y0, _x1, y1 = box
    centers: list[float] = []
    for y in range(y0, y1):
        xs = np.where(mask[y] > 0)[0]
        if len(xs):
            centers.append(float(np.median(xs)))
    return float(np.median(centers)) if centers else float(mask.shape[1]) * 0.5


def _split_masks(mask: np.ndarray) -> tuple[dict[str, np.ndarray], int]:
    height, width = mask.shape
    box = _bbox(mask)
    if box is None:
        return {}, 0
    x0, y0, x1, y1 = box
    body_width, body_height = max(x1 - x0, 1), max(y1 - y0, 1)
    center_x = _subject_axis(mask, box)
    neck_y = _neck_y(mask, box)

    head_zone = np.zeros_like(mask)
    head_bottom = min(y1, neck_y + int(body_height * 0.035))
    head_zone[y0:head_bottom, :] = 1
    central = np.zeros_like(mask)
    hx0 = max(0, int(center_x - body_width * 0.30))
    hx1 = min(width, int(center_x + body_width * 0.30))
    central[:, hx0:hx1] = 1
    head = _largest_component(mask & head_zone & central)
    if int(head.sum()) < max(24, int(mask.sum() * 0.03)):
        head = _largest_component(mask & head_zone)

    torso = np.zeros_like(mask)
    torso_bottom = min(y1, y0 + int(body_height * 0.86))
    for y in range(max(neck_y - 2, y0), torso_bottom):
        xs = np.where(mask[y] > 0)[0]
        if len(xs) < 4:
            continue
        row_center = float(np.median(xs))
        span = float(xs.max() - xs.min() + 1)
        half = max(4, int(span * 0.24))
        lo = max(int(xs.min()), int(row_center - half))
        hi = min(int(xs.max()) + 1, int(row_center + half) + 1)
        torso[y, lo:hi] = mask[y, lo:hi]
    torso = _largest_component(torso)

    arms = np.zeros_like(mask)
    arm_top = max(y0, neck_y - int(body_height * 0.04))
    arm_bottom = min(y1, y0 + int(body_height * 0.82))
    for y in range(arm_top, arm_bottom):
        xs = np.where(mask[y] > 0)[0]
        if len(xs) < 4:
            continue
        row_center = float(np.median(xs))
        span = float(xs.max() - xs.min() + 1)
        half = max(4, int(span * 0.24))
        left_end = max(int(xs.min()), int(row_center - half))
        right_start = min(int(xs.max()) + 1, int(row_center + half) + 1)
        arms[y, int(xs.min()):left_end] = mask[y, int(xs.min()):left_end]
        arms[y, right_start:int(xs.max()) + 1] = mask[y, right_start:int(xs.max()) + 1]

    left_arm = np.zeros_like(mask)
    right_arm = np.zeros_like(mask)
    split_x = int(round(center_x))
    left_arm[:, :split_x] = arms[:, :split_x]
    right_arm[:, split_x:] = arms[:, split_x:]
    bridge = max(3, int(round(min(height, width) * 0.025)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (bridge, bridge))
    left_arm = _largest_component(cv2.morphologyEx(left_arm, cv2.MORPH_CLOSE, kernel))
    right_arm = _largest_component(cv2.morphologyEx(right_arm, cv2.MORPH_CLOSE, kernel))

    face = np.zeros_like(mask)
    head_box = _bbox(head)
    if head_box is not None:
        hx0, hy0, hx1, hy1 = head_box
        head_width, head_height = max(hx1 - hx0, 1), max(hy1 - hy0, 1)
        center = (int(round((hx0 + hx1) * 0.5)), int(round(hy0 + head_height * 0.58)))
        axes = (max(3, int(round(head_width * 0.24))), max(3, int(round(head_height * 0.30))))
        cv2.ellipse(face, center, axes, 0, 0, 360, 1, -1)
        face &= head
    hair = cv2.morphologyEx(head & (1 - face), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    body_seed = (torso | left_arm | right_arm).astype(np.uint8)
    carrier_k = max(5, int(round(min(height, width) * 0.055)) | 1)
    carrier_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (carrier_k, carrier_k))
    body = cv2.morphologyEx(body_seed, cv2.MORPH_CLOSE, carrier_kernel)
    body &= mask
    body = _largest_component(body)

    return {
        "head": head,
        "face": face,
        "hair": hair,
        "body": body,
        "torso": torso,
        "left_arm": left_arm,
        "right_arm": right_arm,
    }, neck_y


def _polygon(mask: np.ndarray, *, max_points: int = 10) -> list[tuple[float, float]] | None:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    perimeter = float(cv2.arcLength(contour, True))
    chosen = None
    for ratio in (0.018, 0.024, 0.032, 0.045, 0.060):
        approx = cv2.approxPolyDP(contour, max(1.5, perimeter * ratio), True).reshape(-1, 2)
        chosen = approx
        if 3 <= len(approx) <= max_points:
            break
    if chosen is None or len(chosen) < 3:
        return None
    return [(float(x), float(y)) for x, y in chosen]


def _median_color(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    pixels = rgb[mask > 0]
    if len(pixels) == 0:
        return 160, 160, 160
    color = np.median(pixels, axis=0).astype(np.uint8)
    return tuple(int(value) for value in color)


def _shape_from_mask(
    rgb: np.ndarray,
    mask: np.ndarray,
    *,
    shape_id: int,
    part: str,
    z_index: int,
) -> Shape | None:
    if int(mask.sum()) < 24:
        return None
    points = _polygon(mask, max_points=8 if part == "face" else 10)
    if points is None:
        return None
    side_hint = "left" if part == "left_arm" else "right" if part == "right_arm" else "unknown"
    return Shape(
        id=shape_id,
        shape_type="polygon",
        fill_color=_median_color(rgb, mask),
        points=points,
        z_index=z_index,
        importance=0.995,
        source_role=f"phase17_structure_{part}",
        layer_name="foreground",
        semantic_type=f"character_{part}",
        character_part=part,
        part_confidence=0.86,
        side_hint=side_hint,
    )


def build_structure_first_parts(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    *,
    face_anchor_mask: np.ndarray | None = None,
    start_id: int = 960000,
) -> StructureFirstResult:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return StructureFirstResult(False, "rgb_required")
    if subject_mask.ndim != 2 or subject_mask.shape != rgb.shape[:2]:
        return StructureFirstResult(False, "mask_shape_mismatch")

    mask = _largest_component((subject_mask > 0).astype(np.uint8))
    area_ratio = float(mask.mean())
    if area_ratio < 0.08 or area_ratio > 0.88:
        return StructureFirstResult(False, "foreground_area_gate")
    box = _bbox(mask)
    if box is None:
        return StructureFirstResult(False, "empty_mask")

    masks, neck_y = _split_masks(mask)
    arm_prior_stats = {"enabled": False, "reason": "not_requested"}
    arm_priors = None
    if face_anchor_mask is not None and face_anchor_mask.shape == mask.shape:
        priors = build_structure_arm_priors(rgb, mask, face_anchor_mask)
        arm_priors = priors
        arm_prior_stats = {
            "enabled": bool(priors.enabled),
            "reason": priors.reason,
            "left_hand_pixels": int(priors.left_hand_pixels),
            "right_hand_pixels": int(priors.right_hand_pixels),
        }
        if priors.enabled:
            for key, prior in (("left_arm", priors.left_arm), ("right_arm", priors.right_arm)):
                if prior is None or not np.any(prior):
                    continue
                center_x = int(round(_subject_axis(mask, box)))
                grown = grow_arm_from_prior(
                    mask,
                    prior.astype(np.uint8),
                    side="left" if key == "left_arm" else "right",
                    center_x=center_x,
                    bbox_width=max(box[2] - box[0], 1),
                )
                candidate = (masks[key] | prior.astype(np.uint8) | grown).astype(np.uint8)
                candidate = cv2.morphologyEx(
                    candidate,
                    cv2.MORPH_CLOSE,
                    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
                )
                count, labels, stats, _ = cv2.connectedComponentsWithStats(candidate, 8)
                best = np.zeros_like(candidate)
                best_area = 0
                for index in range(1, count):
                    comp = labels == index
                    if not np.any(comp & (prior > 0)):
                        continue
                    area = int(stats[index, cv2.CC_STAT_AREA])
                    if area > best_area:
                        best_area = area
                        best = comp.astype(np.uint8)
                if np.any(best):
                    masks[key] = best

    partition_stats = {"enabled": False, "reason": "not_requested"}
    if (
        arm_priors is not None
        and arm_priors.enabled
        and arm_priors.left_arm is not None
        and arm_priors.right_arm is not None
        and np.any(arm_priors.left_arm)
        and np.any(arm_priors.right_arm)
        and face_anchor_mask is not None
    ):
        partition = partition_body_by_structure_seeds(
            mask, face_anchor_mask, arm_priors.left_arm, arm_priors.right_arm
        )
        if partition.enabled:
            partition_area = max(
                float(partition.torso.sum() + partition.left_arm.sum() + partition.right_arm.sum()),
                1.0,
            )
            torso_ratio = float(partition.torso.sum()) / partition_area
            left_ratio = float(partition.left_arm.sum()) / partition_area
            right_ratio = float(partition.right_arm.sum()) / partition_area
            partition_stats = {
                "enabled": True, "reason": "ok",
                "torso_ratio": round(torso_ratio, 6),
                "left_arm_ratio": round(left_ratio, 6),
                "right_arm_ratio": round(right_ratio, 6),
            }
            if (
                0.22 <= torso_ratio <= 0.55
                and left_ratio >= 0.08
                and right_ratio >= 0.08
            ):
                masks["torso"] = partition.torso
                masks["left_arm"] = partition.left_arm
                masks["right_arm"] = partition.right_arm
                partition_stats["accepted"] = True
            else:
                partition_stats["accepted"] = False

    left_arm, right_arm, gesture_stats = recover_upper_hand_gestures(
        rgb, mask, masks, neck_y, box
    )
    masks["left_arm"] = left_arm
    masks["right_arm"] = right_arm

    if arm_prior_stats.get("enabled"):
        arm_union = (left_arm | right_arm).astype(np.uint8)
        residual = (mask & (1 - arm_union)).astype(np.uint8)
        residual[:max(0, neck_y - 2), :] = 0
        center_x = int(round(_subject_axis(mask, box)))
        x0, _y0, x1, y1 = box
        seed_half = max(6, int(round((x1 - x0) * 0.14)))
        seed = np.zeros_like(mask)
        seed[max(0, neck_y - 1):y1, max(0, center_x-seed_half):min(mask.shape[1], center_x+seed_half+1)] = 1
        count, labels, stats, _ = cv2.connectedComponentsWithStats(residual, 8)
        best = np.zeros_like(residual)
        best_area = 0
        for index in range(1, count):
            comp = labels == index
            if not np.any(comp & (seed > 0)):
                continue
            area = int(stats[index, cv2.CC_STAT_AREA])
            if area > best_area:
                best_area = area
                best = comp.astype(np.uint8)
        if np.any(best):
            best = cv2.morphologyEx(best, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))) & mask
            ratio = float(best.sum()) / max(float(mask.sum()), 1.0)
            if 0.12 <= ratio <= 0.42:
                masks["torso"] = best
                body_seed = (best | left_arm | right_arm).astype(np.uint8)
                carrier_k = max(5, int(round(min(mask.shape) * 0.045)) | 1)
                body = cv2.morphologyEx(body_seed, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (carrier_k, carrier_k))) & mask
                masks["body"] = _largest_component(body)
                arm_prior_stats["residual_torso"] = True
                arm_prior_stats["residual_torso_ratio"] = round(ratio, 6)
            else:
                arm_prior_stats["residual_torso"] = False
                arm_prior_stats["residual_torso_ratio"] = round(ratio, 6)

    masks["hair"], hair_stats = expand_long_hair(
        rgb, mask, masks["hair"], masks["face"], box
    )
    recovery_stats = {
        "upper_gesture": gesture_stats,
        "long_hair": hair_stats,
        "arm_prior": arm_prior_stats,
        "body_partition": partition_stats,
    }
    order = (
        ("body", 30300),
        ("hair", 30400),
        ("left_arm", 30500),
        ("right_arm", 30510),
        ("torso", 30600),
        ("face", 30700),
    )
    shapes: list[Shape] = []
    for offset, (part, z_index) in enumerate(order):
        shape = _shape_from_mask(
            rgb,
            masks[part],
            shape_id=start_id + offset,
            part=part,
            z_index=z_index,
        )
        if shape is not None:
            shapes.append(shape)

    required = {"torso", "face"}
    present = {shape.character_part for shape in shapes}
    if not required.issubset(present):
        return StructureFirstResult(
            False,
            "required_part_missing",
            tuple(shapes),
            masks,
            neck_y,
            box,
        )
    return StructureFirstResult(True, "ok", tuple(shapes), masks, neck_y, box, recovery_stats)
