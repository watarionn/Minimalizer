"""Lane A source-only protection of frozen owner component identities.

Research-only. Never accepts human masks, coordinates, or quality labels.
Conservatively prunes *new* owner pixels that join previously distinct
frozen components, under both 4- and 8-neighbour connectivity.
"""
from __future__ import annotations

from collections import deque
import numpy as np
from scipy import ndimage


class FrozenComponentHold(ValueError):
    pass


def _cut_collisions(frozen: np.ndarray, current: np.ndarray,
                    owner_id: int, connectivity: int) -> int:
    structure = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    original = frozen == owner_id
    orig_labels, n_orig = ndimage.label(original, structure=structure)
    if n_orig <= 1:
        labels, _ = ndimage.label(current == owner_id, structure=structure)
        seeds = np.unique(labels[original])
        seeds = seeds[seeds > 0]
        orphan = (current == owner_id) & (frozen == 0) & ~np.isin(labels, seeds)
        current[orphan] = 0
        return int(np.count_nonzero(orphan))
    h, w = frozen.shape
    region = current == owner_id
    if np.any(original & ~region):
        raise FrozenComponentHold('FROZEN_OWNER_CHANGED')
    comp = np.zeros((h, w), dtype=np.int32)
    distance = np.full((h, w), -1, dtype=np.int32)
    comp[original] = orig_labels[original]
    distance[original] = 0
    queue = deque(int(i) for i in np.flatnonzero(original))
    steps = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if connectivity == 8:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    while queue:
        idx = queue.popleft()
        y, x = divmod(idx, w)
        for dy, dx in steps:
            yy, xx = y + dy, x + dx
            if yy < 0 or xx < 0 or yy >= h or xx >= w or not region[yy, xx]:
                continue
            if distance[yy, xx] == -1:
                distance[yy, xx] = distance[y, x] + 1
                comp[yy, xx] = comp[y, x]
                queue.append(yy * w + xx)
    boundary = np.zeros((h, w), dtype=bool)
    for dy, dx in steps:
        sy = slice(max(0, -dy), min(h, h - dy))
        sx = slice(max(0, -dx), min(w, w - dx))
        ty = slice(max(0, dy), min(h, h + dy))
        tx = slice(max(0, dx), min(w, w + dx))
        a, b = comp[sy, sx], comp[ty, tx]
        collision = (a > 0) & (b > 0) & (a != b)
        boundary[sy, sx] |= collision
        boundary[ty, tx] |= collision
    removed = boundary & (current == owner_id) & (frozen == 0)
    current[removed] = 0
    labels, _ = ndimage.label(current == owner_id, structure=structure)
    seeded = np.unique(labels[original])
    seeded = seeded[seeded > 0]
    orphan = (current == owner_id) & (frozen == 0) & ~np.isin(labels, seeded)
    current[orphan] = 0
    return int(np.count_nonzero(removed)) + int(np.count_nonzero(orphan))


def prune_frozen_component_joins(*, frozen_owner: np.ndarray,
                                 proposed_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    """Remove only additions causing frozen component merges/splits/islands."""
    if (type(frozen_owner) is not np.ndarray or
            type(proposed_owner) is not np.ndarray or
            frozen_owner.dtype != np.uint8 or proposed_owner.dtype != np.uint8 or
            frozen_owner.ndim != 2 or proposed_owner.shape != frozen_owner.shape or
            not frozen_owner.size or np.any(frozen_owner > 2) or
            np.any(proposed_owner > 2)):
        raise FrozenComponentHold('INVALID_OWNER_ARRAYS')
    if np.any((frozen_owner > 0) & (proposed_owner != frozen_owner)):
        raise FrozenComponentHold('FROZEN_OWNER_CHANGED')
    out = proposed_owner.copy()
    for connectivity in (4, 8):
        for owner_id in (1, 2):
            _cut_collisions(frozen_owner, out, owner_id, connectivity)
    for connectivity in (4, 8):
        structure = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
        for owner_id in (1, 2):
            old, old_n = ndimage.label(frozen_owner == owner_id, structure=structure)
            new, new_n = ndimage.label(out == owner_id, structure=structure)
            if old_n != new_n:
                raise FrozenComponentHold('FROZEN_COMPONENT_COUNT_CHANGED')
            # Frozen pixels must retain a bijection of old and new component IDs.
            pairs = np.unique(np.stack((old[frozen_owner == owner_id],
                                        new[frozen_owner == owner_id]), axis=1), axis=0)
            if (len(pairs) != old_n or
                    len(np.unique(pairs[:, 0])) != old_n or
                    len(np.unique(pairs[:, 1])) != new_n):
                raise FrozenComponentHold('FROZEN_COMPONENT_IDENTITY_CHANGED')
    if np.any((frozen_owner > 0) & (out != frozen_owner)):
        raise FrozenComponentHold('FROZEN_OWNER_CHANGED')
    original_add = (frozen_owner == 0) & (proposed_owner > 0)
    final_add = (frozen_owner == 0) & (out > 0)
    if np.any(final_add & ~original_add):
        raise FrozenComponentHold('NEW_OWNER_ADDITION_CREATED')
    return out, {
        'schema': 'minimalizer/local-l02/frozen-component-identity-gate/v1',
        'proposed_additions_px': int(np.count_nonzero(original_add)),
        'retained_additions_px': int(np.count_nonzero(final_add)),
        'pruned_additions_px': int(np.count_nonzero(original_add)) - int(np.count_nonzero(final_add)),
        'frozen_component_identity_4_and_8': 'PRESERVED',
        'human_annotations_used_for_inference': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
    }
