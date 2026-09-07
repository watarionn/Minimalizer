from __future__ import annotations

import cv2
import numpy as np

from ..models import Region


def _build_region(members: list[Region], mask: np.ndarray, image_area: int, new_id: int) -> Region | None:
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
        palette_id=members[0].palette_id,
        mask=(mask.astype(np.uint8) * 255),
        area=int(mask.sum()),
        area_ratio=float(mask.sum()) / image_area,
        color_rgb=rgb,
        color_lab=lab,
        bbox=(x0, y0, x1 - x0 + 1, y1 - y0 + 1),
        centroid=(float(xs.mean()), float(ys.mean())),
        area_score=max(r.area_score for r in members),
        contrast_score=max(r.contrast_score for r in members),
        rarity_score=max(r.rarity_score for r in members),
        structure_score=max(r.structure_score for r in members),
        importance_score=max(r.importance_score for r in members),
        is_accent=any(r.is_accent for r in members),
        touches_edge=(
            x0 == 0 or y0 == 0
            or x1 >= mask.shape[1] - 1
            or y1 >= mask.shape[0] - 1
        ),
        role=members[0].role,
    )
    return out


def consolidate_regions_by_role(
    regions: list[Region],
    image_shape,
    structure_close_ratio_x: float = 0.018,
    structure_close_ratio_y: float = 0.010,
    water_close_ratio_x: float = 0.028,
    water_close_ratio_y: float = 0.008,
) -> list[Region]:
    """
    Role-aware consolidation:

    - structure: gently connect nearby façade / tree / rooftop pieces
    - water: connect nearby low horizontal pieces so the lower scene becomes calmer
    - other roles: left untouched
    """
    if not regions:
        return regions

    h, w = image_shape[:2]
    image_area = h * w
    next_id = max((r.id for r in regions), default=-1) + 1
    out: list[Region] = []
    grouped: dict[tuple[str, int], list[Region]] = {}

    passthrough_roles = {"accent", "vertical", "reflection", "misc"}

    for r in regions:
        if r.role in passthrough_roles:
            out.append(r)
            continue
        grouped.setdefault((r.role, r.palette_id), []).append(r)

    for (role, palette_id), members in grouped.items():
        if len(members) == 1:
            out.extend(members)
            continue

        union = np.zeros((h, w), dtype=np.uint8)
        original = np.zeros((h, w), dtype=np.uint8)
        for r in members:
            m = (r.mask > 0).astype(np.uint8)
            original = cv2.bitwise_or(original, m)
            union = cv2.bitwise_or(union, m)

        if role == "water":
            kx = max(3, int(round(w * water_close_ratio_x)) | 1)
            ky = max(3, int(round(h * water_close_ratio_y)) | 1)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kx, ky))
        else:
            kx = max(3, int(round(w * structure_close_ratio_x)) | 1)
            ky = max(3, int(round(h * structure_close_ratio_y)) | 1)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kx, ky))

        closed = cv2.morphologyEx(union, cv2.MORPH_CLOSE, kernel)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)

        if n <= 2:
            merged_mask = original.astype(bool)
            region = _build_region(members, merged_mask, image_area, next_id)
            if region is not None:
                out.append(region)
                next_id += 1
            continue

        for cid in range(1, n):
            comp = labels == cid
            # Recover only original pixels that belong to this closed component.
            piece = comp & (original > 0)
            if piece.sum() == 0:
                continue

            touched = []
            for r in members:
                if np.any(piece & (r.mask > 0)):
                    touched.append(r)

            region = _build_region(touched, piece, image_area, next_id)
            if region is not None:
                out.append(region)
                next_id += 1

    out.sort(key=lambda r: r.area, reverse=True)
    return out
