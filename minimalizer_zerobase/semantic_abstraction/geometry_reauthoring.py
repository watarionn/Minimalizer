from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import cv2
import numpy as np

from minimalizer_zerobase.compose.composer import ComposedPrimitive, VectorScene
from minimalizer_zerobase.production.structural_motifs import (
    major_color_masses,
    reserve_identity_accents,
)
from .ir import AbstractionPlan, AbstractionPolicy


def _median_hex(rgb: np.ndarray, mask: np.ndarray) -> str:
    pixels = np.asarray(rgb)[np.asarray(mask).astype(bool)]
    if len(pixels) == 0:
        return "#808080"
    value = np.median(pixels, axis=0).astype(int)
    return "#%02x%02x%02x" % tuple(int(v) for v in value[:3])


def _rgb_hex(value: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % tuple(int(v) for v in value)


def _bbox(mask: np.ndarray) -> tuple[float, float, float, float] | None:
    ys, xs = np.where(np.asarray(mask).astype(bool))
    if xs.size == 0:
        return None
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    return float(x0), float(y0), float(x1 - x0), float(y1 - y0)


def _coarse_hull(mask: np.ndarray, max_vertices: int) -> list[list[float]] | None:
    binary = np.asarray(mask).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(contour)
    if len(hull) < 3:
        return None
    perimeter = max(float(cv2.arcLength(hull, True)), 1.0)
    approx = cv2.approxPolyDP(hull, perimeter * 0.025, True).reshape(-1, 2)
    if len(approx) > max_vertices:
        indexes = np.linspace(0, len(approx) - 1, max_vertices, dtype=int)
        approx = approx[indexes]
    if len(approx) < 3:
        return None
    return [[float(x), float(y)] for x, y in approx]


def _axis_quad(mask: np.ndarray) -> list[list[float]] | None:
    ys, xs = np.where(np.asarray(mask).astype(bool))
    if xs.size < 4:
        return None
    points = np.column_stack([xs.astype(float), ys.astype(float)])
    center = points.mean(axis=0)
    centered = points - center
    covariance = centered.T @ centered / max(len(points), 1)
    values, vectors = np.linalg.eigh(covariance)
    major = vectors[:, int(np.argmax(values))]
    minor = np.asarray([-major[1], major[0]])
    t = centered @ major
    u = centered @ minor
    t0, t1 = np.percentile(t, [3.0, 97.0])
    half_width = max(1.5, float(np.percentile(np.abs(u), 88.0)))
    corners = (
        center + major * t0 - minor * half_width,
        center + major * t0 + minor * half_width,
        center + major * t1 + minor * half_width,
        center + major * t1 - minor * half_width,
    )
    return [[round(float(p[0]), 6), round(float(p[1]), 6)] for p in corners]


def _split_arm(mask: np.ndarray) -> tuple[np.ndarray, ...]:
    binary = np.asarray(mask).astype(bool)
    ys, _ = np.where(binary)
    if ys.size < 16:
        return (binary,)
    split_y = int(round(float(np.median(ys))))
    upper = binary.copy()
    upper[split_y + 1 :] = False
    lower = binary.copy()
    lower[: split_y + 1] = False
    threshold = max(6, int(round(np.count_nonzero(binary) * 0.18)))
    pieces = tuple(piece for piece in (upper, lower) if np.count_nonzero(piece) >= threshold)
    return pieces or (binary,)


def _hair_masses(mask: np.ndarray, max_masses: int = 3) -> tuple[np.ndarray, ...]:
    binary = np.asarray(mask).astype(np.uint8)
    total = max(int(np.count_nonzero(binary)), 1)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    rows = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= max(8, int(round(total * 0.06))):
            rows.append((area, label))
    rows.sort(key=lambda item: (-item[0], item[1]))
    masses = tuple(labels == label for _, label in rows[:max_masses])
    return masses or ((binary > 0),)


def _primitive(
    primitive_id: str,
    source_id: str,
    primitive_type: str,
    parameters: dict,
    fill: str,
    z_order: int,
) -> ComposedPrimitive:
    return ComposedPrimitive(
        primitive_id=primitive_id,
        source_region_id=source_id,
        selected_candidate_id=f"semantic-reauthor:{primitive_id}",
        primitive_type=primitive_type,
        parameters=parameters,
        fill_ref=fill,
        z_order=z_order,
    )


def _policy_map(plan: AbstractionPlan) -> dict[str, AbstractionPolicy]:
    return {part.id: part.abstraction_policy for part in plan.parts}


def semantic_reauthor_scene(
    rgb: np.ndarray,
    masks: Mapping[str, np.ndarray],
    plan: AbstractionPlan,
) -> VectorScene:
    image = np.asarray(rgb)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("rgb must be HxWx3")
    height, width = image.shape[:2]
    policies = _policy_map(plan)
    primitives: list[ComposedPrimitive] = []
    z = 0

    primitives.append(
        _primitive(
            "semantic:bg",
            "background",
            "rectangle",
            {"bbox": [0.0, 0.0, float(width), float(height)]},
            "#ffffff",
            z,
        )
    )
    z += 1

    def allowed(part_id: str) -> bool:
        return (
            part_id in masks
            and np.any(np.asarray(masks[part_id]).astype(bool))
            and policies.get(part_id, AbstractionPolicy.CONDITIONAL)
            is not AbstractionPolicy.SUPPRESS
        )

    for part_id, max_vertices in (("lower_body", 6), ("torso", 6)):
        if not allowed(part_id):
            continue
        points = _coarse_hull(masks[part_id], max_vertices)
        if points:
            primitives.append(
                _primitive(
                    f"semantic:{part_id}",
                    part_id,
                    "convex_polygon",
                    {"points": points},
                    _median_hex(image, masks[part_id]),
                    z,
                )
            )
            z += 1

    for arm_id in ("left_arm", "right_arm"):
        if not allowed(arm_id):
            continue
        for index, piece in enumerate(_split_arm(masks[arm_id])):
            points = _axis_quad(piece)
            if not points:
                continue
            primitives.append(
                _primitive(
                    f"semantic:{arm_id}:{index}",
                    arm_id,
                    "convex_polygon",
                    {"points": points},
                    _median_hex(image, piece),
                    z,
                )
            )
            z += 1

    if allowed("head"):
        box = _bbox(masks["head"])
        if box:
            x, y, w, h = box
            primitives.append(
                _primitive(
                    "semantic:head",
                    "head",
                    "ellipse",
                    {"cx": x + w / 2, "cy": y + h / 2, "rx": w / 2, "ry": h / 2},
                    _median_hex(image, masks["head"]),
                    z,
                )
            )
            z += 1

    if allowed("face"):
        box = _bbox(masks["face"])
        if box:
            x, y, w, h = box
            primitives.append(
                _primitive(
                    "semantic:face-surface",
                    "face",
                    "ellipse",
                    {"cx": x + w / 2, "cy": y + h / 2, "rx": w * 0.48, "ry": h * 0.48},
                    _median_hex(image, masks["face"]),
                    z,
                )
            )
            z += 1

    if allowed("hair"):
        for index, mass in enumerate(_hair_masses(masks["hair"], 3)):
            points = _coarse_hull(mass, 8)
            if not points:
                continue
            primitives.append(
                _primitive(
                    f"semantic:hair:{index}",
                    "hair",
                    "convex_polygon",
                    {"points": points},
                    _median_hex(image, mass),
                    z,
                )
            )
            z += 1

    if allowed("head"):
        head_authority = np.asarray(masks["head"]).astype(bool)
        if "face" in masks:
            head_authority &= ~np.asarray(masks["face"]).astype(bool)
        for index, (accent, color) in enumerate(
            reserve_identity_accents(
                image,
                head_authority,
                max_accents=2,
                min_ratio=0.0015,
                max_ratio=0.12,
            )
        ):
            points = _coarse_hull(accent, 6)
            if not points:
                continue
            primitives.append(
                _primitive(
                    f"semantic:head-accent:{index}",
                    "head",
                    "convex_polygon",
                    {"points": points},
                    _rgb_hex(tuple(int(v) for v in color)),
                    z,
                )
            )
            z += 1

    # Preserve a tiny bounded set of source-supported identity accents on major body/limb masses.
    # This is generic feature reservation: semantic authority decides where an accent may survive,
    # while source pixels decide its color and shape.
    for part_id, max_accents in (("torso", 2), ("lower_body", 2), ("left_arm", 1), ("right_arm", 1)):
        if not allowed(part_id):
            continue
        authority = np.asarray(masks[part_id]).astype(bool)
        for index, (accent, color) in enumerate(
            reserve_identity_accents(
                image,
                authority,
                max_accents=max_accents,
                min_ratio=0.0015,
                max_ratio=0.10,
            )
        ):
            points = _coarse_hull(accent, 6)
            if not points:
                continue
            primitives.append(
                _primitive(
                    f"semantic:{part_id}-accent:{index}",
                    part_id,
                    "convex_polygon",
                    {"points": points},
                    _rgb_hex(tuple(int(v) for v in color)),
                    z,
                )
            )
            z += 1

    if allowed("major_clothing"):
        clothing = np.asarray(masks["major_clothing"]).astype(bool)
        masses = major_color_masses(
            image,
            clothing,
            max_masses=3,
            min_ratio=0.10,
        )
        if not masses:
            masses = ((clothing, tuple(int(v) for v in np.median(image[clothing], axis=0))),)
        for index, (mass, color) in enumerate(masses[:3]):
            points = _coarse_hull(mass, 8)
            if not points:
                continue
            primitives.append(
                _primitive(
                    f"semantic:clothing:{index}",
                    "major_clothing",
                    "convex_polygon",
                    {"points": points},
                    _rgb_hex(tuple(int(v) for v in color)),
                    z,
                )
            )
            z += 1
        for index, (accent, color) in enumerate(
            reserve_identity_accents(image, clothing, max_accents=3)
        ):
            points = _coarse_hull(accent, 6)
            if not points:
                continue
            primitives.append(
                _primitive(
                    f"semantic:clothing-accent:{index}",
                    "major_clothing",
                    "convex_polygon",
                    {"points": points},
                    _rgb_hex(tuple(int(v) for v in color)),
                    z,
                )
            )
            z += 1

    if allowed("accessory_or_held_object"):
        points = _coarse_hull(masks["accessory_or_held_object"], 6)
        if points:
            primitives.append(
                _primitive(
                    "semantic:accessory",
                    "accessory_or_held_object",
                    "convex_polygon",
                    {"points": points},
                    _median_hex(image, masks["accessory_or_held_object"]),
                    z,
                )
            )

    return VectorScene(
        width=width,
        height=height,
        primitives=tuple(primitives),
        provenance={
            "producer": "SemanticGeometryReauthor",
            "producer_version": "1.0",
            "generation": False,
            "golden_raster_used": False,
            "semantic_authority": "SemanticPart+Phase4 masks",
            "face_internal_features_rendered": False,
            "arm_max_primitives_each": 2,
            "hair_max_masses": 3,
            "clothing_major_masses": 3,
            "identity_accents_protected": True,
            "head_identity_accents_max": 2,
            "head_identity_accents_exclude_face": True,
            "body_identity_accents_max": {"torso": 2, "lower_body": 2, "left_arm": 1, "right_arm": 1},
        },
    )
