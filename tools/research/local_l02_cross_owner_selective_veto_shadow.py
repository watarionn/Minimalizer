"""Experimental A-only cross-owner conflict repair preserving more source pixels.

The established conservative repair deletes *both* newly added endpoints of
an illegal jacket/coat edge.  This research candidate first removes additions
that touch an immutable opposite owner, then removes one owner-side of each
remaining connected conflict graph.  It never promotes, repaints, reassigns,
or changes any original owner except an explicit preapproved abstention.

This is a source-only topology candidate, NOT a semantic/Phase4 quality pass.
It must be replayed against authenticated private signed sources before use.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

from local_l02_cross_owner_contact_gate import (
    CrossOwnerContactHold, verify_no_new_cross_owner_contacts,
    prune_new_cross_owner_additions,
)


class SelectiveVetoHold(ValueError):
    pass


def _same_components(before: np.ndarray, after: np.ndarray, owner: int, conn: int) -> bool:
    st = ndimage.generate_binary_structure(2, 1 if conn == 4 else 2)
    old, n_old = ndimage.label(before == owner, structure=st)
    new, n_new = ndimage.label(after == owner, structure=st)
    if n_old != n_new:
        return False
    if not n_old:
        return True
    surviving = (before == owner) & (after == owner)
    if not np.any(surviving):
        return False
    pairs = np.unique(np.stack((old[surviving], new[surviving]), axis=1), axis=0)
    return (len(pairs) == n_old and not np.any(pairs == 0) and
            len(np.unique(pairs[:, 0])) == n_old and
            len(np.unique(pairs[:, 1])) == n_new)


def _edges(before: np.ndarray, proposed: np.ndarray):
    """Yield new undirected 4/8 cross-owner contact pairs as flat indices."""
    h, w = before.shape
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        sy = slice(max(0, -dy), h - max(0, dy))
        ty = slice(max(0, dy), h - max(0, -dy))
        sx = slice(max(0, -dx), w - max(0, dx))
        tx = slice(max(0, dx), w - max(0, -dx))
        b1, b2 = before[sy, sx], before[ty, tx]
        a1, a2 = proposed[sy, sx], proposed[ty, tx]
        old = ((b1 == 1) & (b2 == 2)) | ((b1 == 2) & (b2 == 1))
        new = ((a1 == 1) & (a2 == 2)) | ((a1 == 2) & (a2 == 1))
        yy, xx = np.nonzero(new & ~old)
        if yy.size:
            yield ((yy + max(0, -dy)) * w + xx + max(0, -dx),
                   (yy + max(0, dy)) * w + xx + max(0, dx))


def propose_selective_cross_owner_veto(*, before: np.ndarray,
                                       proposed: np.ndarray,
                                       source_alpha: np.ndarray,
                                       class_ids: np.ndarray,
                                       allowed_abstentions: np.ndarray | None = None,
                                       max_conflict_edges: int = 250_000):
    """Keep one safe side of each conflicting added-owner graph component.

    The returned owner map remains research-only even when its topology passes.
    A conservative baseline is also computed for a *pixel-retention* comparison,
    not a quality claim.  This operation does not use labels or case IDs.
    """
    if (type(before) is not np.ndarray or type(proposed) is not np.ndarray or
            before.dtype != np.uint8 or proposed.dtype != np.uint8 or
            before.ndim != 2 or proposed.shape != before.shape or not before.size or
            np.any(before > 2) or np.any(proposed > 2)):
        raise SelectiveVetoHold('INVALID_OWNER_ARRAYS')
    if (type(source_alpha) is not np.ndarray or source_alpha.dtype != np.uint8 or
            source_alpha.shape != before.shape or
            type(class_ids) is not np.ndarray or class_ids.dtype != np.uint8 or
            class_ids.shape != before.shape or np.any(class_ids >= 47)):
        raise SelectiveVetoHold('INVALID_SIGNED_SOURCE_OR_CLASS_INPUT')
    if np.any((proposed > 0) & (source_alpha == 0)) or np.any(
            (before > 0) & (source_alpha == 0)):
        raise SelectiveVetoHold('OWNER_OUTSIDE_SIGNED_SOURCE')
    if (np.any((before == 1) & ~np.isin(class_ids, (5, 29, 30, 31, 32))) or
            np.any((before == 2) & ~np.isin(class_ids, (10, 29, 30, 31, 32))) or
            np.any((before == 0) & (proposed > 0) &
                   ~np.isin(class_ids, (30, 32)))):
        raise SelectiveVetoHold('OWNER_CLASS_CONFLICT')
    if allowed_abstentions is None:
        allowed_abstentions = np.zeros(before.shape, dtype=bool)
    if (type(allowed_abstentions) is not np.ndarray or
            allowed_abstentions.dtype != np.bool_ or
            allowed_abstentions.shape != before.shape or
            np.any(allowed_abstentions & (before == 0))):
        raise SelectiveVetoHold('INVALID_ABSTENTION_AUTHORITY')
    if np.any((before > 0) & (proposed > 0) & (before != proposed)):
        raise SelectiveVetoHold('FROZEN_OWNER_REASSIGNMENT')
    erased = (before > 0) & (proposed == 0)
    if np.any(erased & ~allowed_abstentions):
        raise SelectiveVetoHold('UNAUTHORIZED_FROZEN_OWNER_ERASURE')

    flat_before, flat_prop = before.ravel(), proposed.ravel()
    pairs = []
    forced = set()
    n_edges = 0
    for first, second in _edges(before, proposed):
        n_edges += len(first)
        if n_edges > max_conflict_edges:
            raise SelectiveVetoHold('CONFLICT_GRAPH_BUDGET_EXCEEDED')
        for i, j in zip(first.tolist(), second.tolist()):
            ia = flat_before[i] == 0 and flat_prop[i] > 0
            ja = flat_before[j] == 0 and flat_prop[j] > 0
            if not ia and not ja:
                raise SelectiveVetoHold('FROZEN_TO_FROZEN_CONTACT')
            if not ia:
                forced.add(j)
            elif not ja:
                forced.add(i)
            else:
                pairs.append((i, j))

    # Build connected components only among added-vs-added conflicts not
    # already resolved by mandatory removal adjacent to frozen owners.
    parent = {}
    size = {}

    def root(x):
        if x not in parent:
            parent[x] = x
            size[x] = 1
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def join(x, y):
        a, b = root(x), root(y)
        if a == b:
            return
        if size[a] < size[b] or (size[a] == size[b] and a > b):
            a, b = b, a
        parent[b] = a
        size[a] += size[b]

    for i, j in pairs:
        if i not in forced and j not in forced:
            join(i, j)

    sides = {}
    for node in parent:
        group = sides.setdefault(root(node), {1: [], 2: []})
        group[int(flat_prop[node])].append(node)

    to_remove = set(forced)
    for group in sides.values():
        # Both sides cover every edge. Choose the smaller side. On ties
        # deterministically remove owner2 additions and keep owner1.
        owner = 1 if len(group[1]) < len(group[2]) else 2
        to_remove.update(group[owner])

    out = proposed.copy()
    if to_remove:
        out.ravel()[np.fromiter(sorted(to_remove), dtype=np.int64)] = 0

    # Discard detached newly-added islands, never immutable frozen pixels.
    orphan_removed = 0
    if to_remove:
        st4 = ndimage.generate_binary_structure(2, 1)
        for owner in (1, 2):
            seeds = (before == owner) & (out == owner)
            connected = ndimage.binary_propagation(
                seeds, structure=st4, mask=(out == owner))
            orphan = (out == owner) & ~connected & (before == 0)
            orphan_removed += int(np.count_nonzero(orphan))
            out[orphan] = 0

    try:
        verify_no_new_cross_owner_contacts(before=before, after=out)
    except CrossOwnerContactHold as exc:
        raise SelectiveVetoHold('CONTACT_REPAIR_INCOMPLETE') from exc
    if np.any((out > 0) & (out != proposed)):
        raise SelectiveVetoHold('UNEXPECTED_OWNER_CHANGE')
    for owner in (1, 2):
        for conn in (4, 8):
            if not _same_components(before, out, owner, conn):
                raise SelectiveVetoHold('FROZEN_COMPONENT_IDENTITY_CHANGED')

    baseline, _ = prune_new_cross_owner_additions(
        before=before, proposed=proposed,
        allowed_abstentions=allowed_abstentions)
    baseline_add = int(np.count_nonzero((before == 0) & (baseline > 0)))
    selected_add = int(np.count_nonzero((before == 0) & (out > 0)))
    # A new hypothesis must not keep *fewer* pixels than the conservative
    # result. That would be a source-only regression with no semantic benefit.
    if selected_add < baseline_add:
        raise SelectiveVetoHold('ADDITION_RETENTION_REGRESSION')
    return out, {
        'schema': 'minimalizer/local-l02/selective-cross-owner-veto-shadow/v1',
        'new_conflict_edges_seen': n_edges,
        'mandatory_added_pixels_removed': len(forced),
        'conflict_graph_components': len(sides),
        'selected_added_pixels_removed': len(to_remove),
        'detached_added_pixels_removed': orphan_removed,
        'conservative_added_pixels_retained': baseline_add,
        'selective_added_pixels_retained': selected_add,
        'source_only_retained_gain_vs_conservative': selected_add - baseline_add,
        'original_owner_reassignments': 0,
        'human_annotations_used_for_inference': False,
        'unknown_pixels_not_treated_as_negative': True,
        'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
