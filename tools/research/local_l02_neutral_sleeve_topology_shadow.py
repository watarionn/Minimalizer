"""Source-only neutral sleeve abstention with frozen-owner topology restoration.

Research shadow only. Never use human masks, annotation coordinates, or a
case identifier as inference inputs. A returned map is not a Phase4 owner PASS.
"""
from collections import deque

import cv2
import numpy as np
from scipy import ndimage as ndi


class NeutralSleeveHold(ValueError):
    pass


def _restore_four_connected(original, removed, budget):
    keep = original & ~removed
    restored = np.zeros_like(keep)
    structure = ndi.generate_binary_structure(2, 1)
    source_groups, source_count = ndi.label(original, structure)
    height, width = keep.shape
    for source_id in range(1, source_count + 1):
        domain = source_groups == source_id
        if not np.any(domain & removed):
            continue
        for _ in range(64):
            parts, part_count = ndi.label(keep & domain, structure)
            if part_count <= 1:
                break
            counts = np.bincount(parts.ravel())
            counts[0] = 0
            root = int(np.argmax(counts))
            frontier = np.flatnonzero((ndi.binary_dilation(parts == root, structure=structure) & removed & domain).ravel())
            if not frontier.size:
                raise NeutralSleeveHold('TOPOLOGY_UNREACHABLE')
            parent = {int(i): -1 for i in frontier}
            queue = deque(int(i) for i in frontier)
            flat_parts, flat_removed = parts.ravel(), removed.ravel()
            endpoint = None
            while queue:
                idx = queue.popleft()
                y, x = divmod(idx, width)
                for adj in (idx - width if y else -1,
                            idx + width if y + 1 < height else -1,
                            idx - 1 if x else -1,
                            idx + 1 if x + 1 < width else -1):
                    if adj < 0:
                        continue
                    if flat_parts[adj] and flat_parts[adj] != root:
                        endpoint = idx
                        break
                    if flat_removed[adj] and adj not in parent:
                        parent[adj] = idx
                        queue.append(adj)
                if endpoint is not None:
                    break
            if endpoint is None:
                raise NeutralSleeveHold('TOPOLOGY_NO_PATH')
            path = []
            while endpoint != -1:
                path.append(endpoint)
                endpoint = parent[endpoint]
            if int(restored.sum()) + len(path) > budget:
                raise NeutralSleeveHold('TOPOLOGY_RESTORE_BUDGET')
            pixels = np.asarray(path, dtype=np.intp)
            keep.ravel()[pixels] = True
            removed.ravel()[pixels] = False
            restored.ravel()[pixels] = True
        else:
            raise NeutralSleeveHold('TOPOLOGY_ITERATION_BUDGET')
    return keep, restored


def propose_neutral_sleeve_abstention(*, rgba, class_ids, frozen_owner,
                                      max_owner_pixels=600_000,
                                      max_restore_pixels=1024):
    """Return a research-only owner *reduction*, preserving source-only topology.

    Neutral-white hypothesis: HSV saturation <= 0.16 and value >= 0.74;
    contiguous candidate groups >= 32 pixels. These exposed-case thresholds
    are NOT validated for unseen characters. Mixed jacket/coat, neutral coat
    seed >5%, malformed inputs, or topology uncertainty abstain/fail closed.
    """
    if (type(rgba) is not np.ndarray or rgba.dtype != np.uint8 or
            rgba.ndim != 3 or rgba.shape[2] != 4 or not rgba.size):
        raise NeutralSleeveHold('INVALID_RGBA')
    shape = rgba.shape[:2]
    if (type(class_ids) is not np.ndarray or class_ids.dtype != np.uint8 or
            class_ids.shape != shape or np.any(class_ids >= 47)):
        raise NeutralSleeveHold('INVALID_CLASS_IDS')
    if (type(frozen_owner) is not np.ndarray or frozen_owner.dtype != np.uint8 or
            frozen_owner.shape != shape or np.any(frozen_owner > 2)):
        raise NeutralSleeveHold('INVALID_FROZEN_OWNER')
    selected = frozen_owner > 0
    if (np.any(selected & (rgba[:, :, 3] == 0)) or
            np.any((frozen_owner == 1) & ~np.isin(class_ids, (5, 32))) or
            np.any((frozen_owner == 2) & ~np.isin(class_ids, (10, 32)))):
        raise NeutralSleeveHold('SOURCE_ALPHA_OR_OWNER_CLASS_CONFLICT')
    if int(selected.sum()) > max_owner_pixels or max_restore_pixels < 1:
        raise NeutralSleeveHold('OWNER_OR_RESTORE_BUDGET')
    info = {'schema': 'minimalizer/local-l02/neutral-sleeve-topology-shadow/v1',
            'owner_promotion_authorized': False, 'Phase4': 'FAIL',
            'unseen_character_quality': 'NOT_VERIFIED', 'removed': 0,
            'restored_bridges': 0}
    if np.any(frozen_owner == 1) or not np.any((frozen_owner == 2) & (class_ids == 10)):
        return frozen_owner.copy(), {**info, 'decision': 'ABSTAIN_MIXED_OR_NO_COAT_SEED'}
    rgb = rgba[:, :, :3]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    neutral = (hsv[:, :, 1] <= 41) & (hsv[:, :, 2] >= 189)
    seed = (frozen_owner == 2) & (class_ids == 10)
    if np.count_nonzero(neutral & seed) / np.count_nonzero(seed) > 0.05:
        return frozen_owner.copy(), {**info, 'decision': 'ABSTAIN_NEUTRAL_COAT_SEED'}
    candidate = neutral & (frozen_owner == 2) & (class_ids == 32)
    groups, _ = ndi.label(candidate, ndi.generate_binary_structure(2, 1))
    sizes = np.bincount(groups.ravel())
    remove = (groups > 0) & (sizes[groups] >= 32)
    if not np.any(remove):
        return frozen_owner.copy(), {**info, 'decision': 'ABSTAIN_NO_NEUTRAL_SLEEVE'}
    if np.count_nonzero(remove) > 0.05 * np.count_nonzero(selected):
        raise NeutralSleeveHold('REMOVAL_FRACTION_BUDGET')
    before4 = ndi.label(selected, ndi.generate_binary_structure(2, 1))[1]
    before8 = ndi.label(selected, ndi.generate_binary_structure(2, 2))[1]
    keep, restored = _restore_four_connected(selected, remove.copy(), max_restore_pixels)
    if (ndi.label(keep, ndi.generate_binary_structure(2, 1))[1] != before4 or
            ndi.label(keep, ndi.generate_binary_structure(2, 2))[1] != before8 or
            np.any(keep & ~selected) or np.any((selected & ~keep) & (class_ids != 32))):
        raise NeutralSleeveHold('FROZEN_TOPOLOGY_OR_CLASS_REGRESSION')
    result = frozen_owner.copy()
    result[selected & ~keep] = 0
    return result, {**info, 'decision': 'SOURCE_ONLY_CANDIDATE_NOT_OWNER_PASS',
                    'removed': int(np.count_nonzero(selected & ~keep)),
                    'restored_bridges': int(restored.sum()),
                    'components_4': before4, 'components_8': before8}
