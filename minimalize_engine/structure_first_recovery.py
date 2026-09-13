from __future__ import annotations

import cv2
import numpy as np


def _largest(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if count <= 1:
        return mask.astype(np.uint8)
    index = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    return (labels == index).astype(np.uint8)


def _median_color(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    pixels = rgb[mask > 0]
    if len(pixels) == 0:
        return 160, 160, 160
    color = np.median(pixels, axis=0).astype(np.uint8)
    return tuple(int(value) for value in color)


def _lab_mask(rgb: np.ndarray, color: tuple[int, int, int], threshold: float) -> np.ndarray:
    ref = np.asarray(color, dtype=np.uint8).reshape(1, 1, 3)
    ref_lab = cv2.cvtColor(ref, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
    lab = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    distance = np.linalg.norm(lab - ref_lab[None, None, :], axis=2)
    return (distance <= float(threshold)).astype(np.uint8)


def _axis(mask: np.ndarray, box: tuple[int, int, int, int]) -> float:
    _x0, y0, _x1, y1 = box
    centers: list[float] = []
    for y in range(y0, y1):
        xs = np.where(mask[y] > 0)[0]
        if len(xs):
            centers.append(float(np.median(xs)))
    return float(np.median(centers)) if centers else float(mask.shape[1]) * 0.5


def _gap(anchor: np.ndarray, endpoint: np.ndarray) -> float:
    if not np.any(anchor) or not np.any(endpoint):
        return float("inf")
    distance = cv2.distanceTransform(
        1 - (anchor > 0).astype(np.uint8), cv2.DIST_L2, 3
    )
    return float(distance[endpoint > 0].min())


def _bridge(
    anchor: np.ndarray,
    endpoint: np.ndarray,
    subject: np.ndarray,
    radius: int,
) -> np.ndarray:
    if not np.any(anchor) or not np.any(endpoint):
        return (anchor | endpoint).astype(np.uint8)
    distance = cv2.distanceTransform(
        1 - (anchor > 0).astype(np.uint8), cv2.DIST_L2, 3
    )
    corridor = ((distance <= float(radius)) & (subject > 0)).astype(np.uint8)
    merged = ((anchor > 0) | (endpoint > 0) | (corridor > 0)).astype(np.uint8)
    return _largest(merged)



def _raised_arm_corridor(subject, endpoint, side, center_x, neck_y, body_width, body_height):
    ys, xs = np.where(endpoint > 0)
    if not len(xs):
        return endpoint.astype(np.uint8)
    hand = (int(round(float(np.median(xs)))), int(round(float(np.median(ys)))))
    offset = body_width * 0.16
    shoulder_x = int(round(center_x - offset if side == "left" else center_x + offset))
    shoulder_y = int(round(neck_y + body_height * 0.12))
    corridor = np.zeros_like(subject, dtype=np.uint8)
    thickness = max(5, int(round(body_width * 0.12)))
    cv2.line(corridor, (shoulder_x, shoulder_y), hand, 1, thickness)
    rebuilt = ((corridor > 0) & (subject > 0)).astype(np.uint8)
    rebuilt |= endpoint.astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    return _largest(cv2.morphologyEx(rebuilt, cv2.MORPH_CLOSE, kernel))

def recover_upper_hand_gestures(
    rgb: np.ndarray,
    subject: np.ndarray,
    masks: dict[str, np.ndarray],
    neck_y: int,
    box: tuple[int, int, int, int],
) -> tuple[np.ndarray, np.ndarray, dict]:
    face = masks["face"]
    head = masks["head"]
    left_arm = masks["left_arm"]
    right_arm = masks["right_arm"]
    stats = {"left": False, "right": False}
    if int(face.sum()) < 20:
        return left_arm, right_arm, stats

    skin_color = _median_color(rgb, face)
    skin_like = _lab_mask(rgb, skin_color, 24.0) & subject
    x0, y0, x1, y1 = box
    body_width = max(x1 - x0, 1)
    body_height = max(y1 - y0, 1)
    center_x = _axis(subject, box)

    upper_zone = np.zeros_like(subject)
    upper_bottom = min(y1, neck_y + int(body_height * 0.08))
    upper_zone[y0:upper_bottom, x0:x1] = 1
    candidates = (skin_like & upper_zone & (1 - head)).astype(np.uint8)

    count, labels, component_stats, centroids = cv2.connectedComponentsWithStats(
        candidates, 8
    )
    min_area = max(12, int(round(subject.size * 0.0012)))
    max_area = max(min_area + 1, int(round(subject.size * 0.055)))
    max_gap = max(8.0, body_width * 0.20)
    bridge_radius = max(4, int(round(body_width * 0.18)))

    for side, arm in (("left", left_arm), ("right", right_arm)):
        best: tuple[float, np.ndarray] | None = None
        for index in range(1, count):
            area = int(component_stats[index, cv2.CC_STAT_AREA])
            if area < min_area or area > max_area:
                continue
            cx, cy = (float(value) for value in centroids[index])
            if side == "left" and cx >= center_x - body_width * 0.08:
                continue
            if side == "right" and cx <= center_x + body_width * 0.08:
                continue
            component = (labels == index).astype(np.uint8)
            gap = _gap(arm, component)
            if gap > max_gap:
                continue
            score = area / max(float(subject.size), 1.0)
            score -= gap / max(float(body_width), 1.0) * 0.02
            score -= cy / max(float(subject.shape[0]), 1.0) * 0.002
            if best is None or score > best[0]:
                best = (score, component)
        if best is not None:
            arm = _raised_arm_corridor(
                subject, best[1], side, center_x, neck_y, body_width, body_height
            )
            if int(arm.sum()) < int(best[1].sum()) * 1.4:
                arm = _bridge(arm, best[1], subject, bridge_radius)
            stats[side] = True
        if side == "left":
            left_arm = arm
        else:
            right_arm = arm

    return left_arm, right_arm, stats


def expand_long_hair(
    rgb: np.ndarray,
    subject: np.ndarray,
    hair: np.ndarray,
    face: np.ndarray,
    box: tuple[int, int, int, int],
) -> tuple[np.ndarray, dict]:
    stats = {"expanded": False, "added_pixels": 0}
    if int(hair.sum()) < 20:
        return hair, stats

    hair_color = _median_color(rgb, hair)
    candidate = _lab_mask(rgb, hair_color, 28.0) & subject
    if int(face.sum()):
        face_color = _median_color(rgb, face)
        candidate &= 1 - _lab_mask(rgb, face_color, 18.0)

    x0, y0, x1, y1 = box
    body_width = max(x1 - x0, 1)
    body_height = max(y1 - y0, 1)
    center_x = _axis(subject, box)

    side_zone = np.zeros_like(subject)
    left_limit = max(x0, int(round(center_x - body_width * 0.10)))
    right_limit = min(x1, int(round(center_x + body_width * 0.10)))
    vertical_bottom = min(y1, y0 + int(body_height * 0.82))
    side_zone[y0:vertical_bottom, x0:left_limit] = 1
    side_zone[y0:vertical_bottom, right_limit:x1] = 1
    candidate = (candidate & side_zone).astype(np.uint8)

    join_radius = max(5, int(round(min(subject.shape) * 0.040)))
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (join_radius * 2 + 1, join_radius * 2 + 1),
    )
    allowed = ((candidate > 0) | (hair > 0)).astype(np.uint8)
    grown = hair.astype(np.uint8).copy()
    step_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    for _ in range(48):
        next_grown = cv2.dilate(grown, step_kernel) & allowed
        if np.array_equal(next_grown, grown):
            break
        grown = next_grown

    merged = _largest(
        cv2.morphologyEx(grown, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    )
    added = int((merged & (1 - hair)).sum())
    if added >= max(16, int(round(subject.size * 0.0015))):
        stats["expanded"] = True
        stats["added_pixels"] = added
        return merged, stats
    return hair, stats
