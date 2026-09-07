from __future__ import annotations

import cv2
import numpy as np

from ..models import Region
from .models import CharacterPartCandidate, CharacterStructure
from .part_types import CharacterPartType, CharacterPreset, PART_DEFAULT_ABSTRACTION
from .heuristics import (
    get_subject_bbox,
    mask_bbox,
    mask_centroid,
    estimate_body_axis_x,
    estimate_head_bbox_from_distance,
    estimate_face_zone,
    estimate_torso_zone,
    estimate_leg_zone,
    split_mask_by_vertical_axis,
    estimate_side_hint,
    is_prop_like_region,
)
from .face_validation import validate_face_candidate
from .face_contour import fit_face_contour
from .face_boundary import apply_face_boundary_guard


def _zone_mask(
    base_mask: np.ndarray,
    bbox: tuple[int, int, int, int],
) -> np.ndarray:
    x, y, w, h = bbox
    out = np.zeros_like(base_mask, dtype=np.uint8)
    out[y:y+h, x:x+w] = base_mask[y:y+h, x:x+w]
    return out


def _largest_components(mask: np.ndarray, count: int = 1, min_area: int = 8) -> list[np.ndarray]:
    n, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    ids = [
        i for i in range(1, n)
        if int(stats[i, cv2.CC_STAT_AREA]) >= min_area
    ]
    ids.sort(key=lambda i: int(stats[i, cv2.CC_STAT_AREA]), reverse=True)
    return [((labels == i).astype(np.uint8) * 255) for i in ids[:count]]


def _region_ids_for_mask(regions: list[Region], mask: np.ndarray, min_overlap: float = 0.18) -> list[int]:
    target = mask > 0
    ids = []
    for r in regions:
        rm = r.mask > 0
        denom = max(1, int(np.count_nonzero(rm)))
        overlap = np.count_nonzero(rm & target) / denom
        if overlap >= min_overlap:
            ids.append(r.id)
    return ids


def _part(
    pid: int,
    part_type: CharacterPartType,
    mask: np.ndarray,
    image_area: int,
    regions: list[Region],
    confidence: float,
    *,
    side: str = "center",
    parent_part_id: int | None = None,
    metadata: dict | None = None,
) -> CharacterPartCandidate | None:
    area = int(np.count_nonzero(mask))
    if area <= 0:
        return None

    bbox = mask_bbox(mask)
    centroid = mask_centroid(mask)
    region_ids = _region_ids_for_mask(regions, mask)
    colors = [r for r in regions if r.id in region_ids]
    color_rgb = None
    color_lab = None
    if colors:
        total = sum(max(1, r.area) for r in colors)
        color_rgb = tuple(
            int(round(sum(r.color_rgb[k] * r.area for r in colors) / total))
            for k in range(3)
        )
        color_lab = tuple(
            float(sum(r.color_lab[k] * r.area for r in colors) / total)
            for k in range(3)
        )

    return CharacterPartCandidate(
        id=pid,
        part_type=part_type,
        mask=(mask > 0).astype(np.uint8) * 255,
        bbox=bbox,
        centroid=centroid,
        area=area,
        area_ratio=area / max(1, image_area),
        region_ids=region_ids,
        confidence=float(np.clip(confidence, 0.0, 1.0)),
        side=side,
        parent_part_id=parent_part_id,
        color_rgb=color_rgb,
        color_lab=color_lab,
        abstraction_level=PART_DEFAULT_ABSTRACTION.get(part_type, 1.0),
        metadata=metadata or {},
    )


def infer_character_preset_from_mask(
    subject_mask: np.ndarray,
    subject_bbox: tuple[int, int, int, int],
) -> str:
    h, w = subject_mask.shape[:2]
    x, y, bw, bh = subject_bbox
    aspect = bh / max(1.0, bw)
    vertical_coverage = bh / max(h, 1)

    if aspect >= 1.75 and vertical_coverage >= 0.68:
        return "full_body"
    if aspect >= 1.25 and vertical_coverage >= 0.55:
        return "upper_body"
    if aspect <= 1.18 and vertical_coverage <= 0.72:
        return "portrait"
    return "upper_body"


def _skin_like_mask(image_rgb: np.ndarray, alpha_mask: np.ndarray) -> np.ndarray:
    rgb = image_rgb.astype(np.uint8)
    r, g, b = [rgb[:, :, i].astype(np.int16) for i in range(3)]

    # Broad anime-friendly skin rule. It intentionally favors recall.
    rgb_rule = (
        (r >= 145)
        & (g >= 85)
        & (b >= 70)
        & (r >= g - 8)
        & (r >= b + 8)
        & ((r - np.minimum(g, b)) <= 125)
    )

    ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    cr = ycrcb[:, :, 1]
    cb = ycrcb[:, :, 2]
    ycc_rule = (cr >= 132) & (cr <= 190) & (cb >= 70) & (cb <= 138)

    out = (rgb_rule | ycc_rule) & (alpha_mask > 0)
    return out.astype(np.uint8) * 255




def _component_nearest_center(
    mask: np.ndarray,
    center: tuple[float, float],
    *,
    min_area: int = 6,
) -> np.ndarray:
    comps = _largest_components(mask, count=6, min_area=min_area)
    if not comps:
        return mask
    comps.sort(
        key=lambda m: (
            (mask_centroid(m)[0] - center[0]) ** 2
            + (mask_centroid(m)[1] - center[1]) ** 2,
            -np.count_nonzero(m),
        )
    )
    return comps[0]


def _bbox_mask(
    base_mask: np.ndarray,
    bbox: tuple[int, int, int, int],
) -> np.ndarray:
    x, y, w, h = bbox
    out = np.zeros_like(base_mask, dtype=np.uint8)
    out[y:y+h, x:x+w] = 255
    return out


def _clamp_bbox(
    bbox: tuple[float, float, float, float],
    bounds: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    bx, by, bw, bh = bounds
    x, y, w, h = bbox
    x0 = max(bx, int(round(x)))
    y0 = max(by, int(round(y)))
    x1 = min(bx + bw, int(round(x + w)))
    y1 = min(by + bh, int(round(y + h)))
    return (x0, y0, max(1, x1 - x0), max(1, y1 - y0))


def _refine_face_candidate_mask(
    face_candidate_mask: np.ndarray,
    head_mask: np.ndarray,
    head_bbox: tuple[int, int, int, int],
    expected_face_bbox: tuple[int, int, int, int],
    validation: dict | None,
    *,
    skin_mask: np.ndarray | None = None,
) -> tuple[np.ndarray, dict]:
    face_area = int(np.count_nonzero(face_candidate_mask))
    if face_area <= 0:
        return face_candidate_mask, {"applied": False, "reason": "empty_candidate"}

    cand_bbox = mask_bbox(face_candidate_mask)
    cx, cy = mask_centroid(face_candidate_mask)
    hx, hy, hw, hh = head_bbox
    ex, ey, ew, eh = expected_face_bbox
    metrics = (validation or {}).get("metrics") or {}
    left_eye = (validation or {}).get("left_eye")
    right_eye = (validation or {}).get("right_eye")
    mouth = (validation or {}).get("mouth")

    feature_points: list[tuple[float, float]] = []
    eye_points: list[tuple[float, float]] = []
    for eye in [left_eye, right_eye]:
        if eye is not None:
            pt = (float(eye[0]), float(eye[1]))
            feature_points.append(pt)
            eye_points.append(pt)
    if mouth is not None:
        feature_points.append((float(mouth[0]), float(mouth[1])))

    target_bbox = cand_bbox
    strategy = "candidate_bbox"
    if feature_points:
        xs = [p[0] for p in feature_points]
        ys = [p[1] for p in feature_points]
        center_x = float(sum(xs) / len(xs))
        if eye_points and mouth is not None:
            eye_y = float(sum(p[1] for p in eye_points) / len(eye_points))
            center_y = eye_y * 0.44 + float(mouth[1]) * 0.56
        else:
            center_y = float(sum(ys) / len(ys))

        if len(eye_points) >= 2:
            eye_span = abs(eye_points[1][0] - eye_points[0][0])
        else:
            eye_span = ew * 0.28
        feature_w = max(xs) - min(xs) if len(xs) >= 2 else 0.0
        feature_h = max(ys) - min(ys) if len(ys) >= 2 else 0.0

        width = max(ew * 0.78, cand_bbox[2] * 0.58, eye_span * 1.90, feature_w * 1.55)
        width = min(width, hw * 0.74)
        height = max(eh * 0.80, cand_bbox[3] * 0.56, width * 1.12, feature_h * 2.65)
        height = min(height, hh * 0.82)

        if eye_points:
            eye_y = float(sum(p[1] for p in eye_points) / len(eye_points))
            top = eye_y - height * 0.30
        else:
            top = center_y - height * 0.38
        left = center_x - width / 2.0
        target_bbox = _clamp_bbox((left, top, width, height), head_bbox)
        strategy = "feature_guided_bbox"
    else:
        width = min(cand_bbox[2], max(ew, cand_bbox[2] * 0.76))
        height = min(cand_bbox[3], max(eh, cand_bbox[3] * 0.78))
        left = cx - width / 2.0
        top = cy - height * 0.42
        target_bbox = _clamp_bbox((left, top, width, height), head_bbox)
        strategy = "central_shrink"

    refined = cv2.bitwise_and(face_candidate_mask, _bbox_mask(face_candidate_mask, target_bbox))

    if skin_mask is not None and np.count_nonzero(refined) > 0:
        skin_refined = cv2.bitwise_and(refined, skin_mask)
        if np.count_nonzero(skin_refined) >= max(5, int(np.count_nonzero(refined) * 0.45)):
            refined = skin_refined
            strategy += "+skin_filter"

    if np.count_nonzero(refined) > 0:
        refined = _component_nearest_center(refined, (target_bbox[0] + target_bbox[2] / 2.0, target_bbox[1] + target_bbox[3] / 2.0), min_area=max(5, int(face_area * 0.08)))

    refined = cv2.morphologyEx(
        refined.astype(np.uint8),
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
    )

    if np.count_nonzero(refined) < max(5, int(face_area * 0.26)):
        return face_candidate_mask, {
            "applied": False,
            "reason": "refined_mask_too_small",
            "strategy": strategy,
            "candidate_bbox": list(cand_bbox),
            "target_bbox": list(target_bbox),
        }

    refined_bbox = mask_bbox(refined)
    refined_ratio = np.count_nonzero(refined) / max(1, np.count_nonzero(head_mask))
    target_area_ratio = float(metrics.get("area_ratio", 0.0))
    return refined, {
        "applied": True,
        "strategy": strategy,
        "candidate_bbox": list(cand_bbox),
        "target_bbox": list(target_bbox),
        "refined_bbox": list(refined_bbox),
        "candidate_area": int(face_area),
        "refined_area": int(np.count_nonzero(refined)),
        "candidate_head_area_ratio": float(target_area_ratio),
        "refined_head_area_ratio": float(refined_ratio),
    }


def _hair_seed_mask(
    image_rgb: np.ndarray,
    head_mask: np.ndarray,
    face_mask: np.ndarray,
    skin_mask: np.ndarray | None,
) -> np.ndarray:
    seed = cv2.bitwise_and(
        head_mask,
        cv2.bitwise_not(
            cv2.dilate(face_mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        ),
    )
    hx, hy, hw, hh = mask_bbox(head_mask)
    upper = np.zeros_like(seed, dtype=np.uint8)
    upper[hy:hy + max(1, int(round(hh * 0.62))), hx:hx+hw] = 255
    seed = cv2.bitwise_and(seed, upper)
    if skin_mask is not None and np.count_nonzero(seed) > 0:
        non_skin = cv2.bitwise_and(seed, cv2.bitwise_not(skin_mask))
        if np.count_nonzero(non_skin) >= max(6, int(np.count_nonzero(seed) * 0.18)):
            seed = non_skin
    return seed


def _build_hair_mask(
    image_rgb: np.ndarray | None,
    subject_mask: np.ndarray,
    head_mask: np.ndarray,
    face_mask: np.ndarray,
    head_bbox: tuple[int, int, int, int],
    subject_bbox: tuple[int, int, int, int],
    preset: str,
    *,
    body_axis: float,
    torso_bbox: tuple[int, int, int, int],
    skin_mask: np.ndarray | None = None,
) -> tuple[np.ndarray, dict]:
    h, w = subject_mask.shape[:2]
    hx, hy, hw, hh = head_bbox
    sx, sy, sw, sh = subject_bbox
    tx, ty, tw, th = torso_bbox

    extend_h = int(round(hh * (1.52 if preset == "full_body" else 1.28)))
    pad_x = int(round(hw * 0.22))
    hy1 = min(h, hy + extend_h)
    hx0 = max(0, hx - pad_x)
    hx1 = min(w, hx + hw + pad_x)

    hair_zone = np.zeros_like(subject_mask, dtype=np.uint8)
    hair_zone[hy:hy1, hx0:hx1] = subject_mask[hy:hy1, hx0:hx1]

    face_dilated = cv2.dilate(
        face_mask.astype(np.uint8),
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    )
    candidate = cv2.bitwise_and(hair_zone, cv2.bitwise_not(face_dilated))

    # Prevent the central torso corridor from being swallowed by very long hair.
    corridor = np.zeros_like(candidate, dtype=np.uint8)
    corridor_half = max(4, int(round(tw * 0.18)))
    corridor_x0 = max(0, int(round(body_axis - corridor_half)))
    corridor_x1 = min(w, int(round(body_axis + corridor_half)))
    corridor_y0 = max(hy, int(round(hy + hh * 0.68)))
    corridor_y1 = min(h, int(round(ty + th * 0.92)))
    corridor[corridor_y0:corridor_y1, corridor_x0:corridor_x1] = 255
    candidate = cv2.bitwise_and(candidate, cv2.bitwise_not(corridor))

    seed = _hair_seed_mask(image_rgb, head_mask, face_mask, skin_mask) if image_rgb is not None else cv2.bitwise_and(head_mask, cv2.bitwise_not(face_dilated))
    if np.count_nonzero(seed) < 8:
        fallback_seed = np.zeros_like(candidate, dtype=np.uint8)
        fallback_seed[hy:hy + max(1, int(round(hh * 0.55))), hx0:hx1] = candidate[hy:hy + max(1, int(round(hh * 0.55))), hx0:hx1]
        if np.count_nonzero(fallback_seed) > 0:
            seed = fallback_seed

    strategy = "legacy_zone"
    result = cv2.bitwise_and(candidate, cv2.bitwise_or(seed, candidate))

    if image_rgb is not None and np.count_nonzero(seed) >= 8:
        lab = cv2.cvtColor(image_rgb.astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
        seed_pixels = lab[seed > 0]
        seed_med = np.median(seed_pixels, axis=0)
        seed_dist = np.linalg.norm(seed_pixels - seed_med, axis=1)
        mad = float(np.median(np.abs(seed_dist - np.median(seed_dist)))) if len(seed_dist) else 0.0
        threshold = float(np.clip(np.percentile(seed_dist, 80) + max(4.5, mad * 2.6), 10.0, 34.0))
        dist = np.linalg.norm(lab - seed_med, axis=2)
        similar = ((dist <= threshold) & (candidate > 0)).astype(np.uint8) * 255

        if skin_mask is not None:
            similar = cv2.bitwise_and(similar, cv2.bitwise_not(cv2.dilate(skin_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))))

        anchor = cv2.dilate(seed.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        connected = cv2.bitwise_and(similar, anchor)
        grown = connected.copy()
        for _ in range(4):
            expanded = cv2.dilate(grown, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
            grown = cv2.bitwise_and(similar, cv2.bitwise_or(grown, expanded))
        if np.count_nonzero(grown) >= max(12, int(np.count_nonzero(seed) * 1.05)):
            result = grown
            strategy = "seed_connected_color"

    result = cv2.morphologyEx(
        result.astype(np.uint8),
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    )
    comps = _largest_components(result, count=4, min_area=max(8, int(np.count_nonzero(head_mask) * 0.045)))
    filtered = []
    touch_band = np.zeros_like(result, dtype=np.uint8)
    touch_band[hy:hy + max(1, int(round(hh * 0.72))), hx0:hx1] = 255
    for comp in comps:
        if np.count_nonzero(cv2.bitwise_and(comp, touch_band)) > 0:
            filtered.append(comp)
    if filtered:
        result = filtered[0]
        for comp in filtered[1:3]:
            result = cv2.bitwise_or(result, comp)
    else:
        result = candidate
        strategy = "candidate_fallback"

    return result, {
        "strategy": strategy,
        "seed_pixels": int(np.count_nonzero(seed)),
        "candidate_pixels": int(np.count_nonzero(candidate)),
        "hair_pixels": int(np.count_nonzero(result)),
    }


def _pick_face_candidate(
    subject_mask: np.ndarray,
    head_mask: np.ndarray,
    face_zone: np.ndarray,
    *,
    image_area: int,
    image_rgb: np.ndarray | None = None,
    skin_mask: np.ndarray | None = None,
) -> tuple[np.ndarray, str]:
    if image_rgb is not None and skin_mask is not None:
        face_mask = cv2.bitwise_and(skin_mask, face_zone)
        comps = _largest_components(
            face_mask,
            count=3,
            min_area=max(5, int(image_area * 0.00015)),
        )
        if comps:
            fx, fy, fw, fh = mask_bbox(face_zone)
            center = (fx + fw / 2.0, fy + fh / 2.0)
            comps.sort(
                key=lambda m: (
                    (mask_centroid(m)[0] - center[0]) ** 2
                    + (mask_centroid(m)[1] - center[1]) ** 2
                )
            )
            face_mask = comps[0]
            if np.count_nonzero(face_mask) >= max(5, int(np.count_nonzero(head_mask) * 0.055)):
                return face_mask, "skin_component"
        if np.count_nonzero(face_mask) >= max(5, int(np.count_nonzero(head_mask) * 0.040)):
            return face_mask, "skin_zone"
    return face_zone, "face_zone"


def detect_character_structure(
    regions: list[Region],
    alpha_mask: np.ndarray,
    image_shape: tuple[int, ...],
    *,
    image_rgb: np.ndarray | None = None,
    preset: CharacterPreset = "auto",
    enable_face_validation: bool = True,
    face_validation_threshold: float = 0.52,
    enable_face_contour_fit: bool = True,
    face_contour_shrink_strength: float = 0.22,
    face_contour_chin_trim_strength: float = 0.18,
    face_contour_forehead_expand_strength: float = 0.10,
    face_contour_width_scale: float = 1.00,
    face_contour_height_scale: float = 1.00,
    face_contour_center_x_shift_ratio: float = 0.00,
    face_contour_center_y_shift_ratio: float = 0.00,
    enable_face_boundary_guard: bool = True,
    face_boundary_guard_strength: float = 0.65,
    face_boundary_eye_protect_strength: float = 0.80,
    face_boundary_cheek_protect_strength: float = 0.72,
    face_boundary_chin_protect_strength: float = 0.85,
    face_boundary_forehead_allowance: float = 0.18,
) -> CharacterStructure:
    h, w = image_shape[:2]
    image_area = h * w
    subject_mask = (alpha_mask > 0).astype(np.uint8) * 255
    subject_bbox = get_subject_bbox(subject_mask)
    if preset == "auto":
        preset = infer_character_preset_from_mask(subject_mask, subject_bbox)

    body_axis = estimate_body_axis_x(subject_mask)
    head_bbox = estimate_head_bbox_from_distance(
        subject_mask,
        subject_bbox,
        body_axis,
        preset,
    )
    torso_bbox = estimate_torso_zone(
        subject_bbox,
        head_bbox,
        preset,
        body_axis,
    )
    leg_bbox = estimate_leg_zone(subject_bbox, torso_bbox)

    parts: list[CharacterPartCandidate] = []
    pid = 0

    subject = _part(
        pid,
        CharacterPartType.SUBJECT,
        subject_mask,
        image_area,
        regions,
        1.0,
        metadata={"body_axis_x": body_axis},
    )
    if subject:
        parts.append(subject)
        pid += 1

    head_mask = _zone_mask(subject_mask, head_bbox)
    # Restrict to a central connected component when possible.
    hc = _largest_components(head_mask, count=3, min_area=max(6, int(image_area * 0.0003)))
    if hc:
        # Prefer component nearest body axis.
        hc.sort(key=lambda m: abs(mask_centroid(m)[0] - body_axis))
        head_mask = hc[0]

    head = _part(
        pid,
        CharacterPartType.HEAD,
        head_mask,
        image_area,
        regions,
        0.76,
        parent_part_id=subject.id if subject else None,
        metadata={"estimated_bbox": list(head_bbox)},
    )
    if head:
        parts.append(head)
        head_id = pid
        pid += 1
    else:
        head_id = None

    face = None
    face_bbox = estimate_face_zone(head.bbox if head else head_bbox)
    face_zone = _zone_mask(subject_mask, face_bbox)
    skin = _skin_like_mask(image_rgb, subject_mask) if image_rgb is not None else None

    face_validation = {
        "enabled": bool(enable_face_validation and image_rgb is not None),
        "accepted": False,
        "confidence": 0.0,
        "threshold": float(face_validation_threshold),
        "candidate_source": "none",
        "candidate_bbox": list(face_bbox),
        "expected_bbox": list(face_bbox),
        "reasons": [],
        "warnings": [],
        "metrics": {},
    }

    face_candidate_mask, candidate_source = _pick_face_candidate(
        subject_mask,
        head_mask,
        face_zone,
        image_area=image_area,
        image_rgb=image_rgb,
        skin_mask=skin,
    )

    if np.count_nonzero(face_candidate_mask) >= max(5, int(np.count_nonzero(head_mask) * 0.045)):
        accepted = True
        part_conf = 0.64 if image_rgb is not None else 0.48
        validation_result = None
        if enable_face_validation and image_rgb is not None:
            validation_result = validate_face_candidate(
                image_rgb,
                face_candidate_mask,
                head_mask,
                head.bbox if head else head_bbox,
                face_bbox,
                candidate_source=candidate_source,
                skin_mask=skin,
                threshold=face_validation_threshold,
            )
            face_validation = validation_result.to_dict()
            accepted = validation_result.accepted
            part_conf = 0.42 + 0.45 * validation_result.confidence
        else:
            face_validation.update({
                "candidate_source": candidate_source,
                "candidate_bbox": list(mask_bbox(face_candidate_mask)),
                "accepted": True,
                "confidence": part_conf,
            })

        if accepted:
            refined_face_mask, refine_meta = _refine_face_candidate_mask(
                face_candidate_mask,
                head_mask,
                head.bbox if head else head_bbox,
                face_bbox,
                face_validation,
                skin_mask=skin,
            )
            face_validation["refinement"] = refine_meta

            contour_meta = {
                "enabled": False,
                "strategy": "disabled",
            }
            if enable_face_contour_fit:
                contour_result = fit_face_contour(
                    image_rgb,
                    head_mask,
                    refined_face_mask,
                    face_bbox_hint=face_bbox,
                    validation=face_validation,
                    skin_mask=skin,
                    shrink_strength=face_contour_shrink_strength,
                    chin_trim_strength=face_contour_chin_trim_strength,
                    forehead_expand_strength=face_contour_forehead_expand_strength,
                    width_scale=face_contour_width_scale,
                    height_scale=face_contour_height_scale,
                    center_x_shift_ratio=face_contour_center_x_shift_ratio,
                    center_y_shift_ratio=face_contour_center_y_shift_ratio,
                )
                contour_meta = contour_result.to_dict()
                refined_face_mask = contour_result.refined_mask

            face = _part(
                pid,
                CharacterPartType.FACE,
                refined_face_mask,
                image_area,
                regions,
                part_conf,
                parent_part_id=head_id,
                metadata={
                    "estimated_bbox": list(face_bbox),
                    "validation": face_validation,
                    "contour_fit": contour_meta,
                },
            )
            if face:
                parts.append(face)
                face_id = pid
                pid += 1
            else:
                face_id = None
        else:
            face_id = None
    else:
        face_id = None
        face_validation.update({
            "candidate_source": candidate_source,
            "accepted": False,
            "reasons": ["face candidate below minimum area"],
            "candidate_bbox": list(mask_bbox(face_candidate_mask)) if np.count_nonzero(face_candidate_mask) > 0 else list(face_bbox),
        })

    hair_mask, hair_meta = _build_hair_mask(
        image_rgb,
        subject_mask,
        head_mask,
        face.mask if face is not None else face_zone,
        head.bbox if head else head_bbox,
        subject_bbox,
        str(preset),
        body_axis=body_axis,
        torso_bbox=torso_bbox,
        skin_mask=skin,
    )

    boundary_meta = {
        "enabled": False,
        "strategy": "disabled",
        "boundary_score_hint": None,
        "diagnostics": {},
    }
    if enable_face_boundary_guard and face is not None:
        boundary_result = apply_face_boundary_guard(
            image_rgb,
            face_mask=face.mask,
            hair_mask=hair_mask,
            head_mask=head_mask,
            subject_mask=subject_mask,
            skin_mask=skin,
            validation=face_validation,
            guard_strength=face_boundary_guard_strength,
            eye_protect_strength=face_boundary_eye_protect_strength,
            cheek_protect_strength=face_boundary_cheek_protect_strength,
            chin_protect_strength=face_boundary_chin_protect_strength,
            forehead_allowance=face_boundary_forehead_allowance,
        )
        hair_mask = boundary_result.hair_mask
        boundary_meta = boundary_result.to_dict()
        face.metadata["boundary_guard"] = boundary_meta

    hair_meta = {**hair_meta, "boundary_guard": boundary_meta}
    hair = _part(
        pid,
        CharacterPartType.HAIR,
        hair_mask,
        image_area,
        regions,
        0.68,
        parent_part_id=head_id,
        metadata=hair_meta,
    )
    if hair:
        parts.append(hair)
        pid += 1

    torso_mask = _zone_mask(subject_mask, torso_bbox)
    # Keep a central torso core; lateral material is likely sleeves/hair/props.
    tx, ty, tw, th = torso_bbox
    center_width = max(4, int(round(tw * 0.86)))
    center_x0 = int(round(body_axis - center_width / 2))
    torso_core = np.zeros_like(subject_mask)
    xa = max(0, center_x0)
    xb = min(w, center_x0 + center_width)
    torso_core[ty:ty+th, xa:xb] = torso_mask[ty:ty+th, xa:xb]
    torso = _part(
        pid,
        CharacterPartType.TORSO,
        torso_core,
        image_area,
        regions,
        0.72,
        parent_part_id=subject.id if subject else None,
    )
    if torso:
        parts.append(torso)
        torso_id = pid
        pid += 1
    else:
        torso_id = None

    # Arms: lateral subject mass between shoulder and hip, excluding head,
    # central torso, and a dilated hair core.
    # Start high enough to catch raised arms, then remove head/hair explicitly.
    shoulder_y = max(subject_bbox[1], int(round((head.bbox[1] + head.bbox[3] * 0.18) if head else ty)))
    hip_y = min(h, ty + th)
    arm_band = np.zeros_like(subject_mask)
    arm_band[shoulder_y:hip_y, :] = subject_mask[shoulder_y:hip_y, :]
    exclusion = cv2.bitwise_or(torso_core, head_mask)
    if hair is not None:
        exclusion = cv2.bitwise_or(
            exclusion,
            cv2.dilate(hair.mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))),
        )
    arm_mask = cv2.bitwise_and(arm_band, cv2.bitwise_not(exclusion))
    left_arm_mask, right_arm_mask = split_mask_by_vertical_axis(arm_mask, body_axis)

    for part_type, candidate_mask, side in [
        (CharacterPartType.LEFT_ARM, left_arm_mask, "left"),
        (CharacterPartType.RIGHT_ARM, right_arm_mask, "right"),
    ]:
        comps = _largest_components(
            candidate_mask,
            count=2,
            min_area=max(6, int(image_area * 0.0007)),
        )
        if comps:
            candidate_mask = cv2.bitwise_or(*comps[:2]) if len(comps) == 2 else comps[0]
        part = _part(
            pid,
            part_type,
            candidate_mask,
            image_area,
            regions,
            0.56 if comps else 0.36,
            side=side,
            parent_part_id=torso_id,
        )
        if part and part.area_ratio >= 0.0005:
            parts.append(part)
            pid += 1

    # Legs: split lower silhouette by body axis. Components are kept separately
    # from long coat/hair using the bottom-reaching preference.
    leg_zone = _zone_mask(subject_mask, leg_bbox)
    left_leg_mask, right_leg_mask = split_mask_by_vertical_axis(leg_zone, body_axis)

    for part_type, candidate_mask, side in [
        (CharacterPartType.LEFT_LEG, left_leg_mask, "left"),
        (CharacterPartType.RIGHT_LEG, right_leg_mask, "right"),
    ]:
        comps = _largest_components(
            candidate_mask,
            count=3,
            min_area=max(8, int(image_area * 0.0010)),
        )
        if comps:
            # Prefer components extending nearest to the subject bottom.
            subject_bottom = subject_bbox[1] + subject_bbox[3]
            comps.sort(
                key=lambda m: (
                    abs((mask_bbox(m)[1] + mask_bbox(m)[3]) - subject_bottom),
                    -np.count_nonzero(m),
                )
            )
            candidate_mask = comps[0]
        part = _part(
            pid,
            part_type,
            candidate_mask,
            image_area,
            regions,
            0.60 if comps else 0.34,
            side=side,
            parent_part_id=torso_id,
        )
        if part and part.area_ratio >= 0.0007:
            parts.append(part)
            pid += 1

    # Outfit mass is the torso plus visible central lower region. This is
    # deliberately broad; later phases will split sleeves/skirt/coat/shoes.
    outfit_mask = np.zeros_like(subject_mask)
    ox0 = max(subject_bbox[0], int(round(body_axis - subject_bbox[2] * 0.31)))
    ox1 = min(w, int(round(body_axis + subject_bbox[2] * 0.31)))
    oy0 = max(subject_bbox[1], int(round(ty)))
    oy1 = min(h, int(round(subject_bbox[1] + subject_bbox[3] * 0.72)))
    outfit_mask[oy0:oy1, ox0:ox1] = subject_mask[oy0:oy1, ox0:ox1]
    outfit = _part(
        pid,
        CharacterPartType.OUTFIT,
        outfit_mask,
        image_area,
        regions,
        0.54,
        parent_part_id=torso_id,
    )
    if outfit:
        parts.append(outfit)
        pid += 1

    # Region-level prop proposals.
    known_union = np.zeros_like(subject_mask)
    for p in parts:
        if p.part_type not in {CharacterPartType.SUBJECT, CharacterPartType.OUTFIT}:
            known_union = cv2.bitwise_or(known_union, p.mask)

    prop_candidates = []
    for r in regions:
        score = is_prop_like_region(r, subject_bbox, body_axis)
        if score < 0.58:
            continue
        overlap_known = np.count_nonzero((r.mask > 0) & (known_union > 0)) / max(1, r.area)
        if overlap_known > 0.72:
            continue
        prop_candidates.append((score, r))

    prop_candidates.sort(key=lambda x: (x[0], x[1].area), reverse=True)
    for score, r in prop_candidates[:2]:
        side = estimate_side_hint(r.centroid, body_axis, subject_width=subject_bbox[2])
        prop = _part(
            pid,
            CharacterPartType.PROP,
            r.mask,
            image_area,
            regions,
            score,
            side=side,
            parent_part_id=torso_id,
            metadata={"source_region_id": r.id},
        )
        if prop:
            parts.append(prop)
            pid += 1

    major = [
        CharacterPartType.HEAD,
        CharacterPartType.TORSO,
        CharacterPartType.LEFT_LEG,
        CharacterPartType.RIGHT_LEG,
    ]
    present = sum(any(p.part_type == t for p in parts) for t in major)
    confidence = 0.42 + 0.12 * present
    if face is not None:
        confidence += 0.08
    if hair is not None:
        confidence += 0.06

    return CharacterStructure(
        subject_bbox=subject_bbox,
        subject_mask=subject_mask,
        parts=parts,
        preset=str(preset),
        confidence=float(np.clip(confidence, 0.0, 1.0)),
        metadata={
            "body_axis_x": body_axis,
            "head_bbox_estimate": list(head_bbox),
            "torso_bbox_estimate": list(torso_bbox),
            "leg_bbox_estimate": list(leg_bbox),
            "face_validation": face_validation,
            "face_unknown": face is None,
            "face_boundary": boundary_meta,
        },
    )
