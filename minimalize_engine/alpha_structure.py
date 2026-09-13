from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .models import Shape
from .structure_body_planes import build_structure_body_planes
from .structure_carrier_guard import build_carrier_guard
from .structure_geometry import simplify_mask_polygon


@dataclass
class AlphaStructureResult:
    enabled: bool
    reason: str
    shapes: tuple[Shape, ...] = ()
    carrier_area_ratio: float = 0.0
    color_plane_count: int = 0
    carrier_exposure_ratio: float = 0.0
    carrier_patch_count: int = 0

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "shape_count": len(self.shapes),
            "carrier_area_ratio": round(float(self.carrier_area_ratio), 6),
            "color_plane_count": int(self.color_plane_count),
            "carrier_exposure_ratio": round(float(self.carrier_exposure_ratio), 6),
            "carrier_patch_count": int(self.carrier_patch_count),
        }


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _largest_component(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if count <= 1:
        return mask.astype(np.uint8)
    index = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    return (labels == index).astype(np.uint8)


def _polygon(mask: np.ndarray, max_points: int = 16) -> list[tuple[float, float]] | None:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    perimeter = float(cv2.arcLength(contour, True))
    chosen = None
    for ratio in (0.008, 0.012, 0.018, 0.025, 0.035, 0.05):
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
    return tuple(int(value) for value in np.median(pixels, axis=0).astype(np.uint8))


def _dominant_color(rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    pixels = rgb[mask > 0]
    if len(pixels) == 0:
        return 160, 160, 160
    if len(pixels) > 12000:
        indexes = np.linspace(0, len(pixels) - 1, 12000).astype(np.int32)
        pixels = pixels[indexes]
    lab = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    clusters = min(4, max(1, len(lab) // 120))
    if clusters < 2:
        return _median_color(rgb, mask)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.8)
    cv2.setRNGSeed(1701)
    _score, labels, _centers = cv2.kmeans(lab, clusters, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=clusters)
    selected = pixels[labels.ravel() == int(np.argmax(counts))]
    return tuple(int(value) for value in np.median(selected, axis=0).astype(np.uint8))


def _cluster_components(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    *,
    max_colors: int,
    max_planes: int,
) -> list[tuple[np.ndarray, tuple[int, int, int], float]]:
    ys, xs = np.where(subject_mask > 0)
    if len(xs) < 100:
        return []
    pixels = rgb[ys, xs]
    lab = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 35, 0.8)
    _score, labels, _centers = cv2.kmeans(
        lab,
        int(max_colors),
        None,
        criteria,
        4,
        cv2.KMEANS_PP_CENTERS,
    )
    labels = labels.ravel()
    total = max(int(subject_mask.sum()), 1)
    height, width = subject_mask.shape
    close_k = max(3, int(round(min(height, width) * 0.018)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k))
    candidates: list[tuple[np.ndarray, tuple[int, int, int], float]] = []
    for label in range(int(max_colors)):
        cluster = np.zeros_like(subject_mask, dtype=np.uint8)
        selected = labels == label
        cluster[ys[selected], xs[selected]] = 1
        cluster = cv2.morphologyEx(cluster, cv2.MORPH_CLOSE, kernel) & subject_mask
        count, components, stats, _ = cv2.connectedComponentsWithStats(cluster.astype(np.uint8), 8)
        for index in range(1, count):
            area = int(stats[index, cv2.CC_STAT_AREA])
            if area < total * 0.012:
                continue
            component = (components == index).astype(np.uint8)
            color = _median_color(rgb, component)
            hsv = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_RGB2HSV)[0, 0]
            importance = area / total + float(hsv[1]) / 255.0 * 0.03
            candidates.append((component, color, importance))

    candidates.sort(key=lambda item: item[2], reverse=True)
    return candidates[: int(max_planes)]



def _constrain_hair_envelope(
    hair: np.ndarray,
    head_mask: np.ndarray | None,
    face_mask: np.ndarray | None,
) -> np.ndarray:
    result = (hair > 0).astype(np.uint8)
    if face_mask is None or face_mask.shape != result.shape:
        return result
    face_box = _bbox(face_mask)
    if face_box is None:
        return result
    fx0, fy0, fx1, fy1 = face_box
    fw, fh = max(fx1 - fx0, 1), max(fy1 - fy0, 1)
    h, w = result.shape
    envelope = np.zeros_like(result)
    x0 = max(0, int(round(fx0 - fw * 1.45)))
    x1 = min(w, int(round(fx1 + fw * 1.45)))
    y0 = max(0, int(round(fy0 - fh * 1.25)))
    y1 = min(h, int(round(fy1 + fh * 3.20)))
    envelope[y0:y1, x0:x1] = 1
    if head_mask is not None and head_mask.shape == result.shape:
        head = (head_mask > 0).astype(np.uint8)
        head_dilated = cv2.dilate(
            head, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        )
        envelope |= head_dilated
    center_x0 = max(0, int(round(fx0 + fw * 0.15)))
    center_x1 = min(w, int(round(fx1 - fw * 0.15)))
    center_y0 = min(h, int(round(fy1 + fh * 0.55)))
    envelope[center_y0:y1, center_x0:center_x1] = 0
    return (result & envelope).astype(np.uint8)


def _coarsen_hair_mask(mask: np.ndarray, *, strong: bool = False) -> np.ndarray:
    hair = (mask > 0).astype(np.uint8)
    if int(hair.sum()) < 24:
        return hair
    h, w = hair.shape
    close_ratio = 0.034 if strong else 0.026
    open_ratio = 0.014 if strong else 0.010
    close_k = max(5, int(round(min(h, w) * close_ratio)) | 1)
    open_k = max(3, int(round(min(h, w) * open_ratio)) | 1)
    hair = cv2.morphologyEx(hair, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k)))
    hair = cv2.morphologyEx(hair, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k)))
    return hair.astype(np.uint8)


def _split_hair_regions(
    hair: np.ndarray,
    face_mask: np.ndarray | None,
    head_mask: np.ndarray | None = None,
) -> list[tuple[str, np.ndarray]]:
    total = int(hair.sum())
    if total < 24 or face_mask is None or face_mask.shape != hair.shape:
        return [("front", hair)] if total >= 24 else []
    face_box = _bbox(face_mask)
    if face_box is None:
        return [("front", hair)]
    fx0, fy0, fx1, fy1 = face_box
    fw, fh = max(fx1 - fx0, 1), max(fy1 - fy0, 1)
    cx = (fx0 + fx1) * 0.5
    h, w = hair.shape

    front_gate = np.zeros_like(hair, dtype=np.uint8)
    x0 = max(0, int(round(fx0 - fw * 0.60)))
    x1 = min(w, int(round(fx1 + fw * 0.60)))
    y0 = max(0, int(round(fy0 - fh * 0.80)))
    y1 = min(h, int(round(fy0 + fh * 0.48)))
    front_gate[y0:y1, x0:x1] = 1
    if head_mask is not None and head_mask.shape == hair.shape:
        front_gate &= cv2.dilate(
            (head_mask > 0).astype(np.uint8),
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
        )
    front = hair & front_gate
    residual = hair & (1 - (front > 0).astype(np.uint8))

    minimum = max(24, int(round(total * 0.07)))
    regions: list[tuple[str, np.ndarray]] = []
    if int(front.sum()) >= minimum:
        regions.append(("front", front.astype(np.uint8)))

    count, labels, stats, centroids = cv2.connectedComponentsWithStats(
        residual.astype(np.uint8), 8
    )
    candidates = []
    for index in range(1, count):
        area = int(stats[index, cv2.CC_STAT_AREA])
        if area < minimum:
            continue
        component = (labels == index).astype(np.uint8)
        x = float(centroids[index, 0])
        bx = int(stats[index, cv2.CC_STAT_LEFT])
        bw = int(stats[index, cv2.CC_STAT_WIDTH])
        crosses_center = bx < cx < (bx + bw)
        role = "back" if crosses_center and bw > fw * 1.10 else ("left" if x < cx else "right")
        candidates.append((area, role, component))
    candidates.sort(key=lambda item: item[0], reverse=True)
    merged: dict[str, np.ndarray] = {}
    for _area, role, component in candidates:
        if role not in merged:
            merged[role] = np.zeros_like(hair, dtype=np.uint8)
        merged[role] |= component

    ordered = []
    for role in ("left", "right", "back"):
        if role in merged and int(merged[role].sum()) >= minimum:
            ordered.append((int(merged[role].sum()), role, merged[role]))
    ordered.sort(key=lambda item: item[0], reverse=True)

    remaining_slots = max(0, 3 - len(regions))
    for _area, role, region in ordered[:remaining_slots]:
        regions.append((role, region.astype(np.uint8)))

    return regions or [("front", hair)]

def _directional_hair_polygon(mask: np.ndarray, role: str) -> list[tuple[float, float]] | None:
    ys, xs = np.where(mask > 0)
    if len(xs) < 24:
        return None
    y0, y1 = int(ys.min()), int(ys.max())
    height = max(y1 - y0, 1)

    def span(frac: float) -> tuple[float, float, float]:
        target = int(round(y0 + height * frac))
        for radius in range(0, max(3, height // 6) + 1):
            for yy in (target - radius, target + radius):
                if yy < y0 or yy > y1:
                    continue
                row = np.where(mask[yy] > 0)[0]
                if len(row):
                    return float(row.min()), float(row.max()), float(yy)
        return float(xs.min()), float(xs.max()), float(target)

    top_l, top_r, top_y = span(0.08)
    mid_l, mid_r, mid_y = span(0.48)
    low_l, low_r, low_y = span(0.90)
    if role == "front":
        center = (low_l + low_r) * 0.5
        pts = [(top_l, top_y), (top_r, top_y), (mid_r, mid_y),
               (center + (low_r - low_l) * 0.16, low_y),
               (center - (low_r - low_l) * 0.18, low_y), (mid_l, mid_y)]
    elif role == "left":
        pts = [(top_r, top_y), (top_l, top_y), (mid_l, mid_y),
               (low_l, low_y), (low_r, low_y)]
    elif role == "right":
        pts = [(top_l, top_y), (top_r, top_y), (mid_r, mid_y),
               (low_r, low_y), (low_l, low_y)]
    else:
        pts = [(top_l, top_y), (top_r, top_y), (mid_r, mid_y),
               (low_r, low_y), (low_l, low_y), (mid_l, mid_y)]
    return [(float(x), float(y)) for x, y in pts]


def build_alpha_structure_shapes(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    *,
    face_mask: np.ndarray | None = None,
    head_mask: np.ndarray | None = None,
    hair_mask: np.ndarray | None = None,
    torso_mask: np.ndarray | None = None,
    left_arm_mask: np.ndarray | None = None,
    right_arm_mask: np.ndarray | None = None,
    max_colors: int = 6,
    max_planes: int = 9,
    start_id: int = 962000,
) -> AlphaStructureResult:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        return AlphaStructureResult(False, "rgb_required")
    if subject_mask.ndim != 2 or subject_mask.shape != rgb.shape[:2]:
        return AlphaStructureResult(False, "mask_shape_mismatch")

    mask = _largest_component((subject_mask > 0).astype(np.uint8))
    area_ratio = float(mask.mean())
    if area_ratio < 0.08 or area_ratio > 0.92:
        return AlphaStructureResult(False, "foreground_area_gate", carrier_area_ratio=area_ratio)

    shapes: list[Shape] = []
    body_planes = build_structure_body_planes(
        rgb,
        mask,
        face_mask=face_mask,
        head_mask=head_mask,
        hair_mask=hair_mask,
        torso_mask=torso_mask,
        left_arm_mask=left_arm_mask,
        right_arm_mask=right_arm_mask,
        max_accents=2,
        start_id=start_id + 1,
    )
    if body_planes.enabled:
        shapes.extend(body_planes.shapes)
    shape_id = start_id + 1 + len(body_planes.shapes)

    if hair_mask is not None and hair_mask.shape == mask.shape:
        hair = _constrain_hair_envelope(
            (hair_mask > 0).astype(np.uint8) & mask, head_mask, face_mask
        )
        hair = _coarsen_hair_mask(hair, strong=False) & mask
        for hair_index, (hair_role, hair_region) in enumerate(_split_hair_regions(hair, face_mask, head_mask)):
            hair_region = _coarsen_hair_mask(hair_region, strong=(hair_role != "front")) & mask
            points = _directional_hair_polygon(hair_region, hair_role)
            if points is None:
                continue
            shapes.append(
                Shape(
                    id=shape_id,
                    shape_type="polygon",
                    fill_color=_dominant_color(rgb, hair_region),
                    points=points,
                    z_index=30720 if hair_role == "front" else 30650 + hair_index,
                    importance=0.99 if hair_role == "front" else 0.97,
                    source_role=f"phase17_alpha_hair_{hair_role}",
                    layer_name="foreground",
                    semantic_type="character_hair",
                    character_part="hair",
                    part_confidence=0.94 if hair_role == "front" else 0.90,
                )
            )
            shape_id += 1

    if face_mask is not None and face_mask.shape == mask.shape:
        face = (face_mask > 0).astype(np.uint8) & mask
        if int(face.sum()) >= 24:
            points = _polygon(face, max_points=8)
            if points is not None:
                shapes.append(
                    Shape(
                        id=shape_id,
                        shape_type="polygon",
                        fill_color=_median_color(rgb, face),
                        points=points,
                        z_index=30700,
                        importance=1.0,
                        source_role="phase17_alpha_blank_face",
                        layer_name="foreground",
                        semantic_type="character_face_anchor",
                        character_part="face",
                        part_confidence=0.96,
                    )
                )

    carrier_guard = build_carrier_guard(
        rgb,
        mask,
        tuple(shapes),
        start_id=start_id + 100,
    )
    if not carrier_guard.enabled:
        return AlphaStructureResult(
            False,
            carrier_guard.reason,
            carrier_area_ratio=area_ratio,
            color_plane_count=sum(1 for shape in shapes if shape.source_role.startswith("phase17_body_")),
            carrier_exposure_ratio=carrier_guard.exposure_ratio,
            carrier_patch_count=0,
        )
    shapes = [*carrier_guard.patches, *shapes]
    return AlphaStructureResult(
        True,
        "ok",
        tuple(shapes),
        carrier_area_ratio=area_ratio,
        color_plane_count=sum(1 for shape in shapes if shape.source_role.startswith("phase17_body_")),
        carrier_exposure_ratio=carrier_guard.exposure_ratio,
        carrier_patch_count=carrier_guard.fallback_count,
    )
