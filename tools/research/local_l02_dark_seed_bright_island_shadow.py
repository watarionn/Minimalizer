"""Dormant Lane-A source-only dark-garment bright-island abstention.

Research only. No human annotations, coordinates, masks, or production imports.
Thresholds were explored on exposed H04/H06/H08; NOT blind generalization.
"""
from __future__ import annotations

import heapq

import cv2
import numpy as np
from scipy.ndimage import binary_dilation, generate_binary_structure, label, uniform_filter

_FOUR = generate_binary_structure(2, 1)
_EIGHT = generate_binary_structure(2, 2)


def _connect_without_new_pixels(original: np.ndarray, kept: np.ndarray) -> np.ndarray:
    """Restore the cheapest original-owner 4-neighbour paths after abstention."""
    components, count = label(original, _FOUR)
    result = kept.copy()
    for component_id in range(1, count + 1):
        component = components == component_id
        if not np.any(component & ~result):
            continue
        ys, xs = np.where(component)
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        region = component[y0:y1, x0:x1]
        active = result[y0:y1, x0:x1].copy() & region
        if not np.any(active):
            result[y0:y1, x0:x1][region] = True
            continue
        for _ in range(128):
            fragments, nfragments = label(active, _FOUR)
            if nfragments <= 1:
                break
            sizes = np.bincount(fragments.ravel())[1:]
            main = int(np.argmax(sizes)) + 1
            frontier = binary_dilation(fragments == main, structure=_FOUR) & region & ~active
            starts = np.argwhere(frontier)
            if not len(starts):
                active[:] = region
                break
            h, w = active.shape
            dist = np.full((h, w), np.iinfo(np.int32).max, dtype=np.int32)
            parent = np.full((h, w), -1, dtype=np.int64)
            queue = []
            for y, x in starts:
                y, x = int(y), int(x)
                dist[y, x] = 1
                heapq.heappush(queue, (1, y, x))
            target = None
            while queue:
                cost, y, x = heapq.heappop(queue)
                if cost != dist[y, x]:
                    continue
                if fragments[y, x] not in (0, main):
                    target = (y, x)
                    break
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if not (0 <= ny < h and 0 <= nx < w and region[ny, nx]):
                        continue
                    new_cost = cost + (0 if active[ny, nx] else 1)
                    if new_cost < dist[ny, nx]:
                        dist[ny, nx] = new_cost
                        parent[ny, nx] = y * w + x
                        heapq.heappush(queue, (new_cost, ny, nx))
            if target is None:
                active[:] = region
                break
            y, x = target
            while True:
                active[y, x] = True
                previous = int(parent[y, x])
                if previous < 0:
                    break
                y, x = divmod(previous, w)
        else:
            active[:] = region
        if label(active, _FOUR)[1] != 1:
            active[:] = region
        view = result[y0:y1, x0:x1]
        view[region] = active[region]
    return result


def propose_dark_seed_abstention(
    source_rgba: np.ndarray,
    class_ids: np.ndarray,
    frozen_owner: np.ndarray,
) -> np.ndarray:
    """Only drop suspect class5/10 bright islands, preserving owner topology.

    Bright-island veto is restricted to connected DARK garment seeds. The
    non-dark garment case abstains. Owner IDs and original alpha are immutable;
    a removed pixel becomes 0 (unknown), never another garment owner.
    """
    if (source_rgba.ndim != 3 or source_rgba.shape[2] != 4 or
            source_rgba.dtype != np.uint8 or class_ids.dtype != np.uint8 or
            frozen_owner.dtype != np.uint8 or
            class_ids.shape != frozen_owner.shape or
            source_rgba.shape[:2] != frozen_owner.shape):
        raise ValueError("source RGBA, uint8 classes, and uint8 owner shapes required")
    # The input is an exclusive outerwear map, not a full-body owner map.
    # A foreign owner (skin, hair, underlayer) must never be abstained here.
    if np.any(frozen_owner > 2):
        raise ValueError("UNSUPPORTED_OWNER_IDS: expected unknown=0, jacket=1, coat=2")
    # A valid numeric owner ID is insufficient: preserve the source-model
    # jacket/coat provenance before any subtractive bright-island operation.
    if (np.any((frozen_owner == 1) &
               ~np.isin(class_ids, (5, 29, 30, 31, 32))) or
        np.any((frozen_owner == 2) &
               ~np.isin(class_ids, (10, 29, 30, 31, 32)))):
        raise ValueError("OWNER_CLASS_PROVENANCE_MISMATCH")
    if np.any((frozen_owner != 0) & (source_rgba[:, :, 3] == 0)):
        raise ValueError("frozen owner contains pixels outside source alpha")
    lum = cv2.cvtColor(source_rgba[:, :, :3], cv2.COLOR_RGB2LAB)[:, :, 0].astype(np.int16)
    output = frozen_owner.copy()
    for owner_id in np.unique(frozen_owner):
        if owner_id == 0:
            continue
        original = frozen_owner == owner_id
        seeds = original & np.isin(class_ids, (5, 10))
        components, n = label(seeds, _FOUR)
        delete = np.zeros(original.shape, dtype=bool)
        for component_id in range(1, n + 1):
            component = components == component_id
            if np.count_nonzero(component) < 512:
                continue
            median_lum = float(np.median(lum[component]))
            if median_lum >= 64:
                continue
            bright = component & (lum >= median_lum + 25)
            consensus = uniform_filter(bright.astype(np.float32), size=3, mode="constant") >= 0.7
            islands, ni = label(consensus, _FOUR)
            for island_id in range(1, ni + 1):
                island = islands == island_id
                if np.count_nonzero(island) >= 128:
                    delete |= island
        if not np.any(delete):
            continue
        kept = _connect_without_new_pixels(original, original & ~delete)
        if label(kept, _FOUR)[1] != label(original, _FOUR)[1] or \
                label(kept, _EIGHT)[1] != label(original, _EIGHT)[1]:
            continue  # fail closed: do not erode a connected garment
        output[original & ~kept] = 0
    assert np.all((output == 0) | (output == frozen_owner))
    return output
