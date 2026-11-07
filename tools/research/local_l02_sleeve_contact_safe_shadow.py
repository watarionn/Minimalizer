"""Dormant L02 source-only sleeve recovery with frozen topology and contact guards.

Inputs must be authenticated by the existing signed-input adapter. The
independent AnimeSeg generic-clothes signal is NOT outerwear ground truth.
No human annotations, synthetic pixels or release authority enter inference.
"""
from __future__ import annotations
from collections import deque
import numpy as np
from scipy import ndimage
from local_l02_guarded_sleeve_geodesic_shadow import propose_guarded_sleeve
from local_l02_cross_owner_contact_gate import (
    prune_new_cross_owner_additions, verify_no_new_cross_owner_contacts,
)
from local_l02_frozen_owner_transition_audit import audit_frozen_owner_transition


class SleeveContactSafeHold(ValueError):
    pass


def _cut_collisions(frozen, current, owner_id, connectivity):
    st = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    original = frozen == owner_id
    orig_labels, orig_n = ndimage.label(original, structure=st)
    if orig_n <= 1:
        labels, _ = ndimage.label(current == owner_id, structure=st)
        seeded = np.unique(labels[original]); seeded = seeded[seeded > 0]
        orphan = (current == owner_id) & (frozen == 0) & ~np.isin(labels, seeded)
        current[orphan] = 0
        return int(orphan.sum())
    h, w = frozen.shape
    region = current == owner_id
    if np.any(original & ~region):
        raise SleeveContactSafeHold('FROZEN_OWNER_CHANGED')
    comp = np.zeros((h, w), dtype=np.int32)
    distance = np.full((h, w), -1, dtype=np.int32)
    comp[original] = orig_labels[original]
    distance[original] = 0
    q = deque(int(i) for i in np.flatnonzero(original))
    steps = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if connectivity == 8:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    while q:
        idx = q.popleft(); y, x = divmod(idx, w)
        for dy, dx in steps:
            yy, xx = y + dy, x + dx
            if yy < 0 or xx < 0 or yy >= h or xx >= w or not region[yy, xx]:
                continue
            if distance[yy, xx] == -1:
                distance[yy, xx] = distance[y, x] + 1
                comp[yy, xx] = comp[y, x]
                q.append(yy * w + xx)
    boundary = np.zeros((h, w), dtype=bool)
    for dy, dx in steps:
        ys = slice(max(0, -dy), min(h, h - dy))
        xs = slice(max(0, -dx), min(w, w - dx))
        yt = slice(max(0, dy), min(h, h + dy))
        xt = slice(max(0, dx), min(w, w + dx))
        a, b = comp[ys, xs], comp[yt, xt]
        conflict = (a > 0) & (b > 0) & (a != b)
        boundary[ys, xs] |= conflict
        boundary[yt, xt] |= conflict
    removed = boundary & (current == owner_id) & (frozen == 0)
    current[removed] = 0
    labels, _ = ndimage.label(current == owner_id, structure=st)
    seeded = np.unique(labels[original]); seeded = seeded[seeded > 0]
    orphan = (current == owner_id) & (frozen == 0) & ~np.isin(labels, seeded)
    current[orphan] = 0
    return int(removed.sum() + orphan.sum())


def propose_sleeve_contact_safe_shadow(*, class_ids, anime_classes,
        source_alpha, frozen_candidate, frozen_owner, connectivity=4):
    raw, upstream = propose_guarded_sleeve(
        class_ids=class_ids, anime_classes=anime_classes,
        source_alpha=source_alpha, frozen_candidate=frozen_candidate,
        frozen_owner=frozen_owner, connectivity=connectivity,
    )
    no_merge = raw.copy()
    removed = 0
    for conn in (4, 8):
        for owner_id in (1, 2):
            removed += _cut_collisions(frozen_owner, no_merge, owner_id, conn)
    out, contact = prune_new_cross_owner_additions(
        before=frozen_owner, proposed=no_merge,
    )
    verify_no_new_cross_owner_contacts(before=frozen_owner, after=out)
    transition = audit_frozen_owner_transition(before=frozen_owner, after=out)
    if transition['frozen_owner_pixels_modified']:
        raise SleeveContactSafeHold('FROZEN_OWNER_ERASURE')
    added = (frozen_owner == 0) & (out > 0)
    eligible = (frozen_candidate & (class_ids == 32)
                & (anime_classes == 10) & (source_alpha > 0))
    if np.any(added & ~eligible) or np.any((out > 0) & (source_alpha == 0)):
        raise SleeveContactSafeHold('SOURCE_OR_CLASS_ESCAPE')
    for owner_id in (1, 2):
        for conn in (1, 2):
            st = ndimage.generate_binary_structure(2, conn)
            old, n_old = ndimage.label(frozen_owner == owner_id, structure=st)
            new, n_new = ndimage.label(out == owner_id, structure=st)
            if n_old != n_new:
                raise SleeveContactSafeHold('FROZEN_COMPONENT_TOPOLOGY_CHANGED')
            if n_old:
                pairs = np.unique(np.stack((old[frozen_owner == owner_id],
                    new[frozen_owner == owner_id]), axis=1), axis=0)
                if (len(pairs) != n_old or len(np.unique(pairs[:, 0])) != n_old
                        or len(np.unique(pairs[:, 1])) != n_new):
                    raise SleeveContactSafeHold('FROZEN_COMPONENT_IDENTITY_CHANGED')
    return out, {
        'schema': 'minimalizer/local-l02/sleeve-contact-safe-shadow/v1',
        'raw_added_px': upstream['added_sleeve_pixels'],
        'no_merge_removed_px': removed,
        'cross_owner_4_edges_blocked': contact['new_cross_owner_4_edges_blocked'],
        'cross_owner_diagonal_edges_blocked': contact['new_cross_owner_diagonal_edges_blocked'],
        'cross_owner_new_pixels_removed': contact['newly_added_owner_pixels_removed'],
        'orphan_additions_removed': contact['detached_added_owner_pixels_removed'],
        'safe_added_px': int(np.count_nonzero(added)),
        'frozen_owner_modified_px': 0, 'source_pixels_generated': 0,
        'human_annotations_used_for_inference': False,
        'unseen_character_pass': False, 'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
