from __future__ import annotations

import cv2
import numpy as np

from ..models import Region


def _brightness(rgb) -> float:
    r, g, b = (v / 255.0 for v in rgb)
    return float(0.299 * r + 0.587 * g + 0.114 * b)


def _mask_union(regions: list[Region], h: int, w: int) -> np.ndarray:
    union = np.zeros((h, w), dtype=np.uint8)
    for r in regions:
        union = cv2.bitwise_or(union, (r.mask > 0).astype(np.uint8))
    return union


def _build_region(members: list[Region], mask: np.ndarray, image_area: int, new_id: int, role: str) -> Region | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None

    total_weight = sum(max(r.area, 1) for r in members)
    rgb = tuple(int(round(sum(r.color_rgb[k] * r.area for r in members) / total_weight)) for k in range(3))
    lab = tuple(float(sum(r.color_lab[k] * r.area for r in members) / total_weight) for k in range(3))

    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    out = Region(
        id=new_id,
        palette_id=members[0].palette_id if len({m.palette_id for m in members}) == 1 else -1,
        mask=(mask.astype(np.uint8) * 255),
        area=int(mask.sum()),
        area_ratio=float(mask.sum()) / image_area,
        color_rgb=rgb,
        color_lab=lab,
        bbox=(x0, y0, x1 - x0 + 1, y1 - y0 + 1),
        centroid=(float(xs.mean()), float(ys.mean())),
        area_score=max((r.area_score for r in members), default=0.0),
        contrast_score=max((r.contrast_score for r in members), default=0.0),
        rarity_score=max((r.rarity_score for r in members), default=0.0),
        structure_score=max((r.structure_score for r in members), default=0.0),
        importance_score=max((r.importance_score for r in members), default=0.0),
        is_accent=any(r.is_accent for r in members),
        touches_edge=(
            x0 == 0 or y0 == 0
            or x1 >= mask.shape[1] - 1
            or y1 >= mask.shape[0] - 1
        ),
        role=role,
    )
    return out


def _reconstruct_group(
    groups: list[list[Region]],
    image_shape,
    kernel_kind: str,
    ratio_x: float,
    ratio_y: float,
    out_role: str,
    min_area_ratio: float,
    next_id_start: int,
) -> tuple[list[Region], int]:
    h, w = image_shape[:2]
    image_area = h * w
    next_id = next_id_start
    built: list[Region] = []

    for members in groups:
        if not members:
            continue

        original = _mask_union(members, h, w)
        kx = max(3, int(round(w * ratio_x)) | 1)
        ky = max(3, int(round(h * ratio_y)) | 1)
        if kernel_kind == "rect":
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kx, ky))
        else:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kx, ky))

        closed = cv2.morphologyEx(original, cv2.MORPH_CLOSE, kernel)
        open_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        smoothed = cv2.morphologyEx(closed, cv2.MORPH_OPEN, open_k)

        n, labels, stats, _ = cv2.connectedComponentsWithStats(smoothed, connectivity=8)
        for cid in range(1, n):
            comp = labels == cid
            if comp.sum() / image_area < min_area_ratio:
                continue

            piece = comp & (smoothed > 0)
            touched = [r for r in members if np.any(piece & (r.mask > 0))]
            if not touched:
                touched = members

            region = _build_region(touched, piece, image_area, next_id, out_role)
            if region is not None:
                built.append(region)
                next_id += 1

    return built, next_id


def reconstruct_silhouettes(
    regions: list[Region],
    image_shape,
    *,
    skyline_merge_ratio_x: float = 0.040,
    skyline_merge_ratio_y: float = 0.020,
    water_band_merge_ratio_x: float = 0.080,
    water_band_merge_ratio_y: float = 0.020,
    boat_merge_ratio_x: float = 0.020,
    boat_merge_ratio_y: float = 0.012,
    min_area_ratio: float = 0.0010,
) -> list[Region]:
    if not regions:
        return regions

    next_id = max((r.id for r in regions), default=-1) + 1

    passthrough = [r for r in regions if r.role in {"accent", "vertical"}]
    misc = [r for r in regions if r.role == "misc"]
    reflections = [r for r in regions if r.role == "reflection"]

    structures = [r for r in regions if r.role == "structure"]
    waters = [r for r in regions if r.role == "water"]
    boats = [r for r in regions if r.role == "boat"]

    dark_struct = [r for r in structures if _brightness(r.color_rgb) < 0.42]
    light_struct = [r for r in structures if _brightness(r.color_rgb) >= 0.42]

    rebuilt: list[Region] = []
    built, next_id = _reconstruct_group(
        [dark_struct, light_struct],
        image_shape,
        kernel_kind="ellipse",
        ratio_x=skyline_merge_ratio_x,
        ratio_y=skyline_merge_ratio_y,
        out_role="structure",
        min_area_ratio=min_area_ratio,
        next_id_start=next_id,
    )
    rebuilt.extend(built)

    water_built, next_id = _reconstruct_group(
        [waters],
        image_shape,
        kernel_kind="rect",
        ratio_x=water_band_merge_ratio_x,
        ratio_y=water_band_merge_ratio_y,
        out_role="water",
        min_area_ratio=max(min_area_ratio, 0.0020),
        next_id_start=next_id,
    )
    water_built.sort(key=lambda r: r.area, reverse=True)
    rebuilt.extend(water_built[:2])

    boat_built, next_id = _reconstruct_group(
        [boats],
        image_shape,
        kernel_kind="rect",
        ratio_x=boat_merge_ratio_x,
        ratio_y=boat_merge_ratio_y,
        out_role="boat",
        min_area_ratio=max(min_area_ratio, 0.0008),
        next_id_start=next_id,
    )
    boat_built.sort(key=lambda r: (r.importance_score, r.area), reverse=True)
    rebuilt.extend(boat_built[:8])

    reflections.sort(key=lambda r: (r.importance_score, r.area), reverse=True)
    rebuilt.extend(reflections[:3])

    rebuilt.extend([r for r in misc if r.area_ratio >= max(0.0012, min_area_ratio * 1.2)])

    rebuilt.extend(passthrough)
    rebuilt.sort(key=lambda r: r.area, reverse=True)
    return rebuilt
