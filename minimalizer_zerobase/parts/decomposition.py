from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np

from minimalize_engine.structure_face_locator import locate_structure_face

PART_NAMES = (
    "head",
    "hair",
    "face",
    "neck",
    "torso",
    "left_arm",
    "right_arm",
    "lower_body",
    "major_clothing",
    "accessory_or_held_object",
    "unknown",
)

DISPLAY_PRIORITY = (
    "unknown",
    "head",
    "torso",
    "major_clothing",
    "lower_body",
    "left_arm",
    "right_arm",
    "hair",
    "neck",
    "face",
    "accessory_or_held_object",
)


@dataclass(frozen=True)
class PartDecomposition:
    subject_mask: np.ndarray
    part_masks: dict[str, np.ndarray]
    face_bbox_xywh: tuple[int, int, int, int] | None
    face_score: float
    structural_quality: float
    accessory_kind: str
    accessory_score: float
    hair_prototype_count: int

    def coverage(self) -> dict[str, float]:
        denom = max(int(np.count_nonzero(self.subject_mask)), 1)
        return {
            name: float(np.count_nonzero(mask)) / float(denom)
            for name, mask in self.part_masks.items()
        }


def _bool_mask(mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    value = np.asarray(mask)
    if value.shape != shape:
        raise ValueError("part mask must match subject shape")
    return value.astype(bool)


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if xs.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _skin_like(rgb: np.ndarray, subject: np.ndarray) -> np.ndarray:
    ycc = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    yy, cr, cb = ycc[..., 0], ycc[..., 1], ycc[..., 2]
    mask = (
        (yy >= 72)
        & (cr >= 130)
        & (cr <= 198)
        & (cb >= 66)
        & (cb <= 158)
        & subject
    )
    return mask


def _dominant_hair_prototypes(
    rgb: np.ndarray,
    seed: np.ndarray,
    *,
    max_colors: int = 8,
) -> np.ndarray:
    pixels = rgb[seed]
    if len(pixels) == 0:
        return np.empty((0, 3), dtype=np.float32)
    quant = (pixels // 24).astype(np.int16)
    packed = quant[:, 0] * 121 + quant[:, 1] * 11 + quant[:, 2]
    values, counts = np.unique(packed, return_counts=True)
    order = np.argsort(-counts, kind="stable")[:max_colors]
    centers: list[np.ndarray] = []
    for code in values[order]:
        group = pixels[packed == code]
        if len(group):
            centers.append(np.median(group, axis=0))
    if not centers:
        return np.empty((0, 3), dtype=np.float32)
    arr = np.asarray(centers, dtype=np.uint8).reshape(-1, 1, 3)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)


def _grow_hair(
    rgb: np.ndarray,
    subject: np.ndarray,
    head: np.ndarray,
    face: np.ndarray,
    hair_hint: np.ndarray | None = None,
) -> tuple[np.ndarray, int]:
    if not np.any(head):
        return np.zeros_like(subject), 0
    face_dilated = cv2.dilate(
        face.astype(np.uint8),
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
    ).astype(bool)
    skin = _skin_like(rgb, subject)
    seed = head & ~face_dilated & ~skin
    if int(seed.sum()) < 24:
        seed = head & ~face_dilated
    prototypes = _dominant_hair_prototypes(rgb, seed)
    if len(prototypes) == 0:
        return seed, 0

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    distances = np.min(
        np.linalg.norm(lab[..., None, :] - prototypes[None, None, :, :], axis=3),
        axis=2,
    )
    color_candidate = (distances <= 27.0) & subject & ~face

    face_box = _bbox(face)
    subject_box = _bbox(subject)
    zone = np.ones_like(subject, dtype=bool)
    if face_box is not None and subject_box is not None:
        fx0, fy0, fx1, fy1 = face_box
        sx0, sy0, sx1, sy1 = subject_box
        sw = max(sx1 - sx0, 1)
        cx = (fx0 + fx1) * 0.5
        shoulder_y = min(sy1, int(round(fy1 + (fy1 - fy0) * 0.55)))
        center_half = max(10, int(round(sw * 0.18)))
        yy, xx = np.indices(subject.shape)
        deep_center = (
            (yy >= shoulder_y)
            & (xx >= int(round(cx - center_half)))
            & (xx <= int(round(cx + center_half)))
        )
        zone &= ~deep_center

    hint_seed = np.zeros_like(subject)
    hint_support = np.ones_like(subject)
    if hair_hint is not None:
        hint = np.asarray(hair_hint, dtype=np.float32)
        if hint.shape != subject.shape:
            raise ValueError("hair_hint must match subject shape")
        hint_seed = (hint >= 0.20) & subject
        hint_ratio = float(hint_seed.sum()) / max(float(subject.sum()), 1.0)
        if hint_ratio >= 0.02:
            support_radius = max(7, int(round(max(subject.shape) * 0.045)))
            support_kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (support_radius * 2 + 1, support_radius * 2 + 1),
            )
            hint_support = cv2.dilate(
                hint_seed.astype(np.uint8),
                support_kernel,
            ).astype(bool)
            if face_box is not None:
                _fx0, _fy0, _fx1, fy1 = face_box
                deep = np.indices(subject.shape)[0] >= fy1
                zone &= (~deep) | hint_support

    candidate = (color_candidate & zone) | seed | hint_seed
    candidate = cv2.morphologyEx(
        candidate.astype(np.uint8),
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    ).astype(bool)

    count, labels, _, _ = cv2.connectedComponentsWithStats(candidate.astype(np.uint8), 8)
    seed_touch = cv2.dilate(
        seed.astype(np.uint8),
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)),
    ).astype(bool)
    kept = np.zeros_like(subject)
    for label in range(1, count):
        comp = labels == label
        if np.any(comp & seed_touch):
            kept |= comp
    kept |= seed
    kept &= subject & ~face

    if hair_hint is not None:
        hint = np.asarray(hair_hint)
        if hint.shape != subject.shape:
            raise ValueError("hair_hint must match subject shape")
        if hint.dtype != np.float32:
            hint = hint.astype(np.float32)
        high = (hint >= 0.50) & subject & ~face
        high_ratio = float(np.count_nonzero(high)) / max(float(np.count_nonzero(subject)), 1.0)
        if high_ratio >= 0.02:
            face_box = _bbox(face)
            upper = np.zeros_like(subject)
            if face_box is not None:
                _, fy0, _, fy1 = face_box
                fh = max(fy1 - fy0, 1)
                upper[: min(subject.shape[0], int(round(fy1 + fh * 0.48))), :] = True
            support = cv2.dilate(
                high.astype(np.uint8),
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19)),
            ).astype(bool)
            # Keep the source-derived head seed unconditionally. Below the
            # head/face band, require proximity to reliable semantic hair evidence.
            kept = seed | (kept & (upper | support)) | high
            kept &= subject & ~face
    return kept, int(len(prototypes))


def _neck_mask(
    rgb: np.ndarray,
    subject: np.ndarray,
    face: np.ndarray,
    torso: np.ndarray,
) -> np.ndarray:
    face_box = _bbox(face)
    if face_box is None:
        return np.zeros_like(subject)
    fx0, fy0, fx1, fy1 = face_box
    fw, fh = max(fx1 - fx0, 1), max(fy1 - fy0, 1)
    cx = (fx0 + fx1) * 0.5
    yy, xx = np.indices(subject.shape)
    window = (
        (yy >= fy1 - int(round(fh * 0.04)))
        & (yy <= fy1 + int(round(fh * 0.52)))
        & (xx >= cx - fw * 0.34)
        & (xx <= cx + fw * 0.34)
    )
    skin = _skin_like(rgb, subject)
    neck = window & skin & (subject | torso)
    return neck & subject


def _torso_core(torso: np.ndarray, face: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if not np.any(torso):
        return torso.copy(), torso.copy()
    face_box = _bbox(face)
    kernel_size = 9
    if face_box is not None:
        kernel_size = max(5, int(round((face_box[2] - face_box[0]) * 0.22)) | 1)
    eroded = cv2.erode(
        torso.astype(np.uint8),
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)),
    ).astype(bool)
    if int(eroded.sum()) < max(24, int(torso.sum() * 0.18)):
        box = _bbox(torso)
        if box is None:
            return torso.copy(), np.zeros_like(torso)
        x0, y0, x1, y1 = box
        cx = (x0 + x1) * 0.5
        half = max(4, int(round((x1 - x0) * 0.28)))
        yy, xx = np.indices(torso.shape)
        eroded = torso & (xx >= cx - half) & (xx <= cx + half)
    clothing = torso & ~eroded
    return eroded, clothing


def _line_mask(shape: tuple[int, int], a: tuple[int, int], b: tuple[int, int], thickness: int) -> np.ndarray:
    out = np.zeros(shape, dtype=np.uint8)
    cv2.line(out, a, b, 1, max(1, thickness), cv2.LINE_AA)
    return out.astype(bool)


def _detect_peripheral_linear_accessory(
    rgb: np.ndarray,
    subject: np.ndarray,
    face: np.ndarray,
) -> tuple[np.ndarray, float] | None:
    face_box = _bbox(face)
    if face_box is None:
        return None
    fx0, fy0, fx1, fy1 = face_box
    fw, fh = max(fx1 - fx0, 1), max(fy1 - fy0, 1)
    fcx, fcy = (fx0 + fx1) * 0.5, (fy0 + fy1) * 0.5

    distance = cv2.distanceTransform(subject.astype(np.uint8), cv2.DIST_L2, 5)
    thin = ((distance > 0.0) & (distance <= max(3.5, fw * 0.075))).astype(np.uint8)
    yy, xx = np.indices(subject.shape)
    thin[(yy > fcy + fh * 0.35)] = 0
    lines = cv2.HoughLinesP(
        thin * 255,
        1,
        np.pi / 180,
        threshold=max(8, int(round(fw * 0.16))),
        minLineLength=max(20, int(round(fw * 0.62))),
        maxLineGap=max(5, int(round(fw * 0.14))),
    )
    if lines is None:
        return None

    best: tuple[float, np.ndarray] | None = None
    for row in lines[:, 0]:
        x1, y1, x2, y2 = [int(v) for v in row]
        length = float(np.hypot(x2 - x1, y2 - y1))
        mx, my = (x1 + x2) * 0.5, (y1 + y2) * 0.5
        lateral = abs(mx - fcx) / max(float(fw), 1.0)
        if lateral < 1.12 or my > fcy + fh * 0.20:
            continue
        sample = _line_mask(subject.shape, (x1, y1), (x2, y2), max(3, int(round(fw * 0.08))))
        support = float(np.count_nonzero(sample & subject)) / max(float(np.count_nonzero(sample)), 1.0)
        if support < 0.72:
            continue
        surround_radius = max(5, int(round(fw * 0.18)))
        surround_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (surround_radius * 2 + 1, surround_radius * 2 + 1),
        )
        band = cv2.dilate(sample.astype(np.uint8), surround_kernel).astype(bool)
        surround = band & ~sample
        surround_occupancy = float(np.count_nonzero(surround & subject)) / max(
            float(np.count_nonzero(surround)),
            1.0,
        )
        if surround_occupancy > 0.40:
            continue
        pixels = rgb[sample & subject]
        if len(pixels) == 0:
            continue
        mean = np.mean(pixels, axis=0)
        # Reject bright skin-like strokes; held props are expected to differ from skin.
        if mean[0] > 150 and mean[1] > 95 and mean[2] > 75 and mean[0] >= mean[2] + 10:
            continue
        score = min(1.0, 0.40 + min(0.28, length / max(fw, 1.0) * 0.16) + min(0.22, (lateral - 1.0) * 0.16) + 0.10 * support)
        mask = sample & subject
        if best is None or score > best[0]:
            best = (score, mask)
    if best is None:
        return None
    return best[1], float(best[0])


def _detect_vivid_torso_accent(
    rgb: np.ndarray,
    subject: np.ndarray,
    torso: np.ndarray,
    face: np.ndarray,
) -> tuple[np.ndarray, float] | None:
    if not np.any(torso):
        return None
    face_box = _bbox(face)
    if face_box is None:
        return None
    fx0, fy0, fx1, fy1 = face_box
    fw, fh = max(fx1 - fx0, 1), max(fy1 - fy0, 1)
    fcx = (fx0 + fx1) * 0.5
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    vivid_base = (
        (hsv[..., 1] >= 105)
        & (hsv[..., 2] >= 80)
        & torso
        & subject
    )
    subject_count = max(int(subject.sum()), 1)
    torso_pixels = rgb[torso]
    if len(torso_pixels) == 0:
        return None
    torso_median = np.median(torso_pixels, axis=0).astype(np.uint8)
    torso_lab = cv2.cvtColor(
        torso_median.reshape(1, 1, 3),
        cv2.COLOR_RGB2LAB,
    ).astype(np.float32)[0, 0]

    best: tuple[float, np.ndarray] | None = None
    # Split saturated candidates by hue before connected-components. This
    # prevents a narrow accent (for example a green tie) from merging into a
    # differently-colored but equally saturated garment.
    for hue_start in range(0, 180, 15):
        hue_end = hue_start + 15
        vivid = (
            vivid_base
            & (hsv[..., 0] >= hue_start)
            & (hsv[..., 0] < hue_end)
        )
        vivid = cv2.morphologyEx(
            vivid.astype(np.uint8),
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
        )
        count, labels, stats, centroids = cv2.connectedComponentsWithStats(vivid, 8)
        for label in range(1, count):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area < max(18, int(subject_count * 0.0018)) or area > int(subject_count * 0.085):
                continue
            w = int(stats[label, cv2.CC_STAT_WIDTH])
            h = int(stats[label, cv2.CC_STAT_HEIGHT])
            aspect = max(w / max(float(h), 1.0), h / max(float(w), 1.0))
            if aspect < 1.45:
                continue
            cx, cy = [float(v) for v in centroids[label]]
            if abs(cx - fcx) > fw * 1.05 or cy < fy1 - fh * 0.12:
                continue
            comp = labels == label
            pixels = rgb[comp]
            mean_rgb = np.mean(pixels, axis=0).astype(np.uint8)
            mean_lab = cv2.cvtColor(
                mean_rgb.reshape(1, 1, 3),
                cv2.COLOR_RGB2LAB,
            ).astype(np.float32)[0, 0]
            contrast = float(np.linalg.norm(mean_lab - torso_lab))
            if contrast < 18.0:
                continue
            saturation = float(np.mean(hsv[..., 1][comp])) / 255.0
            score = min(
                1.0,
                0.38
                + min(0.20, (aspect - 1.0) * 0.08)
                + min(0.18, contrast / 120.0)
                + min(0.14, saturation * 0.14)
                + 0.10 * max(0.0, 1.0 - abs(cx - fcx) / max(fw, 1.0)),
            )
            if best is None or score > best[0]:
                best = (score, comp)
    if best is None:
        return None
    return best[1], float(best[0])


def _detect_accessory(
    rgb: np.ndarray,
    subject: np.ndarray,
    torso: np.ndarray,
    face: np.ndarray,
) -> tuple[np.ndarray, str, float]:
    linear = _detect_peripheral_linear_accessory(rgb, subject, face)
    vivid = _detect_vivid_torso_accent(rgb, subject, torso, face)
    candidates: list[tuple[float, str, np.ndarray]] = []
    if linear is not None:
        candidates.append((linear[1], "held-linear", linear[0]))
    if vivid is not None:
        candidates.append((vivid[1], "vivid-accent", vivid[0]))
    if not candidates:
        return np.zeros_like(subject), "none", 0.0
    score, kind, mask = max(candidates, key=lambda item: item[0])
    return mask & subject, kind, float(score)


def decompose_semantic_parts(
    rgb: np.ndarray,
    subject_mask: np.ndarray,
    structural_parts: Mapping[str, np.ndarray],
    *,
    structural_quality: float = 0.0,
    semantic_hints: Mapping[str, np.ndarray] | None = None,
) -> PartDecomposition:
    source = np.asarray(rgb)
    if source.dtype != np.uint8 or source.ndim != 3 or source.shape[2] != 3:
        raise ValueError("rgb must be uint8 HxWx3")
    subject = _bool_mask(subject_mask, source.shape[:2])
    if not np.any(subject):
        raise ValueError("subject mask must not be empty")

    required = ("head", "torso", "left_arm", "right_arm", "left_leg", "right_leg")
    missing = [name for name in required if name not in structural_parts]
    if missing:
        raise ValueError(f"missing structural parts: {missing}")
    structural = {
        name: _bool_mask(structural_parts[name], subject.shape) & subject
        for name in required
    }

    face_result = locate_structure_face(source, subject.astype(np.uint8))
    face = (
        face_result.mask.astype(bool) & subject
        if face_result.enabled and face_result.mask is not None
        else np.zeros_like(subject)
    )
    hair_hint = None
    if semantic_hints is not None and "hair" in semantic_hints:
        hair_hint = np.asarray(semantic_hints["hair"], dtype=np.float32)
    hair, prototype_count = _grow_hair(
        source,
        subject,
        structural["head"],
        face,
        hair_hint=hair_hint,
    )
    neck = _neck_mask(source, subject, face, structural["torso"])
    accessory, accessory_kind, accessory_score = _detect_accessory(
        source, subject, structural["torso"], face
    )

    torso_core, major_clothing = _torso_core(structural["torso"], face)
    lower = structural["left_leg"] | structural["right_leg"]

    # Appearance masks override structural ownership in the visible part map.
    hair &= ~face & ~accessory
    neck &= ~face & ~hair & ~accessory
    left_arm = structural["left_arm"] & ~hair & ~face & ~accessory
    right_arm = structural["right_arm"] & ~hair & ~face & ~accessory
    lower &= ~hair & ~accessory
    torso_core &= ~hair & ~face & ~neck & ~accessory
    major_clothing &= ~hair & ~face & ~neck & ~accessory

    assigned = (
        face
        | hair
        | neck
        | accessory
        | left_arm
        | right_arm
        | lower
        | torso_core
        | major_clothing
    )
    unknown = subject & ~assigned

    part_masks = {
        "head": structural["head"],
        "hair": hair,
        "face": face,
        "neck": neck,
        "torso": torso_core,
        "left_arm": left_arm,
        "right_arm": right_arm,
        "lower_body": lower,
        "major_clothing": major_clothing,
        "accessory_or_held_object": accessory,
        "unknown": unknown,
    }
    face_bbox = None
    if face_result.bbox is not None:
        x, y, w, h = face_result.bbox
        face_bbox = (int(x), int(y), int(w), int(h))
    return PartDecomposition(
        subject_mask=subject,
        part_masks=part_masks,
        face_bbox_xywh=face_bbox,
        face_score=float(face_result.score),
        structural_quality=float(structural_quality),
        accessory_kind=accessory_kind,
        accessory_score=float(accessory_score),
        hair_prototype_count=prototype_count,
    )


def exclusive_part_labels(result: PartDecomposition) -> np.ndarray:
    labels = np.full(result.subject_mask.shape, PART_NAMES.index("unknown"), dtype=np.uint8)
    labels[~result.subject_mask] = 255
    for name in DISPLAY_PRIORITY:
        mask = result.part_masks[name] & result.subject_mask
        labels[mask] = PART_NAMES.index(name)
    return labels
