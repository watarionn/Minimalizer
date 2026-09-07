from __future__ import annotations

import cv2
import numpy as np

from ..models import Region


def _region_from_mask(parent: Region, mask: np.ndarray, new_id: int, image_area: int) -> Region | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None

    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    area = int(len(xs))

    return Region(
        id=new_id,
        palette_id=parent.palette_id,
        mask=(mask.astype(np.uint8) * 255),
        area=area,
        area_ratio=area / image_area,
        color_rgb=parent.color_rgb,
        color_lab=parent.color_lab,
        bbox=(x0, y0, x1 - x0 + 1, y1 - y0 + 1),
        centroid=(float(xs.mean()), float(ys.mean())),
        area_score=parent.area_score,
        contrast_score=parent.contrast_score,
        rarity_score=parent.rarity_score,
        structure_score=parent.structure_score,
        importance_score=parent.importance_score,
        is_accent=parent.is_accent,
        touches_edge=(
            x0 == 0 or y0 == 0
            or x1 >= mask.shape[1] - 1
            or y1 >= mask.shape[0] - 1
        ),
    )


def _propagate_labels(original: np.ndarray, seed_labels: np.ndarray) -> np.ndarray:
    """
    Reattach pixels removed by morphological opening to the nearest seed region.

    We expand all seeds one pixel at a time, but only inside the original mask.
    This converts a thin bridge into ownership by one neighboring mass instead
    of letting it reconnect the masses into one giant contour.
    """
    labels = seed_labels.astype(np.int32).copy()
    allowed = original > 0
    unlabeled = allowed & (labels == 0)

    if not np.any(unlabeled):
        return labels

    kernel = np.ones((3, 3), np.uint8)
    max_iter = original.shape[0] + original.shape[1]

    for _ in range(max_iter):
        if not np.any(unlabeled):
            break

        changed = False
        # Deterministic label order keeps same-input/same-config reproducibility.
        for label_id in range(1, int(labels.max()) + 1):
            current = (labels == label_id).astype(np.uint8)
            dilated = cv2.dilate(current, kernel, iterations=1).astype(bool)
            claim = dilated & unlabeled
            if np.any(claim):
                labels[claim] = label_id
                unlabeled[claim] = False
                changed = True

        if not changed:
            break

    # Rare isolated leftovers can occur after aggressive opening.
    # Attach them to the nearest already-labelled region by iterative dilation.
    if np.any(unlabeled):
        for _ in range(max_iter):
            if not np.any(unlabeled):
                break
            expanded = labels.copy()
            for label_id in range(1, int(labels.max()) + 1):
                current = (labels == label_id).astype(np.uint8)
                dilated = cv2.dilate(current, kernel, iterations=1).astype(bool)
                claim = dilated & unlabeled
                expanded[claim] = label_id
            if np.array_equal(expanded, labels):
                break
            labels = expanded
            unlabeled = allowed & (labels == 0)

    return labels


def split_large_regions(
    regions: list[Region],
    image_shape,
    area_ratio_threshold: float = 0.045,
    open_radius_ratio: float = 0.006,
    min_piece_ratio: float = 0.0015,
) -> list[Region]:
    """
    Break oversized, weakly-connected color masses into spatially coherent pieces.

    This is intentionally geometry-only. It does not need AI or semantic labels.
    Only regions that are both large and structurally suspicious are considered.
    """
    h, w = image_shape[:2]
    image_area = h * w
    short = min(h, w)
    out: list[Region] = []
    next_id = max((r.id for r in regions), default=-1) + 1

    for region in regions:
        if region.area_ratio < area_ratio_threshold or region.is_accent:
            out.append(region)
            continue

        x, y, bw, bh = region.bbox
        bbox_area = max(1, bw * bh)
        occupancy = region.area / bbox_area

        contours, _ = cv2.findContours(region.mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            out.append(region)
            continue

        contour = max(contours, key=cv2.contourArea)
        hull = cv2.convexHull(contour)
        hull_area = max(float(cv2.contourArea(hull)), 1.0)
        solidity = min(1.0, float(cv2.contourArea(contour)) / hull_area)

        # Compact solid masses are already good silhouettes.
        suspicious = (
            occupancy < 0.70
            or solidity < 0.62
            or (bw / w > 0.52 and bh / h > 0.28)
        )
        if not suspicious:
            out.append(region)
            continue

        radius = max(1, int(round(short * open_radius_ratio)))
        # Try from modest to stronger opening. Stop at first useful split.
        chosen_labels = None
        for factor in (1.0, 1.5, 2.0):
            r = max(1, int(round(radius * factor)))
            k = r * 2 + 1
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
            opened = cv2.morphologyEx(region.mask, cv2.MORPH_OPEN, kernel)

            n, labels, stats, _ = cv2.connectedComponentsWithStats(
                (opened > 0).astype(np.uint8), connectivity=8
            )
            if n <= 2:
                continue

            meaningful = [
                cid for cid in range(1, n)
                if stats[cid, cv2.CC_STAT_AREA] / image_area >= min_piece_ratio
            ]
            if len(meaningful) < 2:
                continue

            remapped = np.zeros_like(labels, dtype=np.int32)
            for new_label, cid in enumerate(meaningful, start=1):
                remapped[labels == cid] = new_label

            propagated = _propagate_labels(region.mask, remapped)
            if int(propagated.max()) >= 2:
                chosen_labels = propagated
                break

        if chosen_labels is None:
            out.append(region)
            continue

        pieces = []
        for lid in range(1, int(chosen_labels.max()) + 1):
            piece_mask = (chosen_labels == lid).astype(np.uint8)
            piece_area = int(piece_mask.sum())
            if piece_area / image_area < min_piece_ratio:
                continue
            piece = _region_from_mask(region, piece_mask, next_id, image_area)
            if piece is not None:
                # Larger pieces retain more of the parent's salience.
                share = piece.area / max(region.area, 1)
                piece.importance_score = min(
                    1.0, region.importance_score * (0.70 + 0.30 * min(1.0, share * 4.0))
                )
                pieces.append(piece)
                next_id += 1

        if len(pieces) >= 2:
            out.extend(pieces)
        else:
            out.append(region)

    return out
