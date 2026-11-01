"""Research-only, source-bound class32 color-competitor abstention.

This is a known-character exploratory candidate, NOT a Phase4 owner fix or
an unknown-character quality PASS. It consumes frozen model predictions and
signed original image bytes only. Human masks are deliberately not accepted.
The class2 prediction is a color competitor, never a ground-truth negative.
"""
from __future__ import annotations

import hashlib
import io
import re

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

MAX_PIXELS = 16_000_000
MIN_SEED_PIXELS = 500
MIN_COLOR_SEPARATION_LAB = 25.0
MAX_COMPETITOR_DISTANCE_LAB = 12.0
MIN_DISTANCE_RATIO = 2.0


class SourceOnlyAbstentionHold(ValueError):
    """Fail closed on untrusted or mismatched source/model/owner inputs."""


def _components4(mask: np.ndarray) -> int:
    # OpenCV returns number of labels including background.
    n, _ = cv2.connectedComponents(mask.astype(np.uint8), connectivity=4)
    return int(n - 1)


def _safe_to_remove(mask: np.ndarray, y: int, x: int) -> bool:
    """Sufficient (conservative) local test for 4-connected owner retention."""
    h, w = mask.shape
    if not (0 < y < h - 1 and 0 < x < w - 1):
        return False
    patch = mask[y - 1:y + 2, x - 1:x + 2].copy()
    if not patch[1, 1]:
        return False
    # Reject isolated owner components and fully surrounded interior pixels.
    if np.all(patch):
        return False
    neighbours = [(0, 1), (1, 2), (2, 1), (1, 0)]
    active = [p for p in neighbours if patch[p]]
    if not active:
        return False
    if len(active) == 1:
        return True
    patch[1, 1] = False
    seen = set()
    stack = [active[0]]
    while stack:
        yy, xx = stack.pop()
        if (yy, xx) in seen:
            continue
        seen.add((yy, xx))
        for dy, dx in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            ny, nx = yy + dy, xx + dx
            if 0 <= ny < 3 and 0 <= nx < 3 and patch[ny, nx] and (ny, nx) not in seen:
                stack.append((ny, nx))
    return all(p in seen for p in active)


def propose_class32_competitor_abstention(*, source_bytes: bytes,
        expected_source_sha256: str, class_ids: np.ndarray,
        frozen_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    """Return a *shadow-only* owner copy and source-free integrity receipt.

    Fixed class2 vs class5/10 Lab rule; no case-specific parameter overrides.
    Never adds pixels or changes class5/10 owner. No human labels or masks.
    All resulting owner maps remain research-only and private.
    """
    if (type(source_bytes) is not bytes or not source_bytes or
            type(expected_source_sha256) is not str or
            re.fullmatch(r'[0-9a-f]{64}', expected_source_sha256) is None or
            hashlib.sha256(source_bytes).hexdigest() != expected_source_sha256):
        raise SourceOnlyAbstentionHold('SIGNED_SOURCE_SHA_MISMATCH')
    if (type(class_ids) is not np.ndarray or type(frozen_owner) is not np.ndarray or
            class_ids.dtype != np.uint8 or frozen_owner.dtype != np.uint8 or
            class_ids.ndim != 2 or frozen_owner.shape != class_ids.shape or
            class_ids.size == 0 or class_ids.size > MAX_PIXELS):
        raise SourceOnlyAbstentionHold('INVALID_FROZEN_PREDICTIONS')
    if np.any(class_ids >= 47) or np.any(frozen_owner > 2):
        raise SourceOnlyAbstentionHold('INVALID_FROZEN_TAXONOMY')
    try:
        with Image.open(io.BytesIO(source_bytes)) as img:
            if img.width * img.height > MAX_PIXELS:
                raise SourceOnlyAbstentionHold('SOURCE_TOO_LARGE')
            rgba = np.asarray(img.convert('RGBA'))
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise SourceOnlyAbstentionHold('INVALID_SOURCE_IMAGE') from exc
    if rgba.shape[:2] != class_ids.shape:
        raise SourceOnlyAbstentionHold('SOURCE_PREDICTION_SHAPE_MISMATCH')
    opaque = rgba[:, :, 3] > 0
    if np.any((frozen_owner != 0) & ~opaque):
        raise SourceOnlyAbstentionHold('OWNER_OUTSIDE_SIGNED_ALPHA')
    result = frozen_owner.copy()
    garment_seed = ((class_ids == 5) | (class_ids == 10)) & (frozen_owner != 0) & opaque
    competitor_seed = (class_ids == 2) & opaque
    reason = 'NO_CANDIDATE'
    count = 0
    separation = None
    before = [_components4(frozen_owner == owner_id) for owner_id in (1, 2)]
    if int(garment_seed.sum()) < MIN_SEED_PIXELS or int(competitor_seed.sum()) < MIN_SEED_PIXELS:
        reason = 'INSUFFICIENT_SOURCE_ONLY_SEEDS'
    else:
        lab = cv2.cvtColor(rgba[:, :, :3].astype(np.float32) / 255., cv2.COLOR_RGB2LAB)
        garment_color = np.median(lab[garment_seed], axis=0)
        competitor_color = np.median(lab[competitor_seed], axis=0)
        separation = float(np.linalg.norm(garment_color - competitor_color))
        if separation < MIN_COLOR_SEPARATION_LAB:
            reason = 'INSUFFICIENT_COLOR_SEPARATION'
        else:
            target = (class_ids == 32) & (frozen_owner != 0) & opaque
            ys, xs = np.where(target)
            values = lab[ys, xs]
            dgarment = np.linalg.norm(values - garment_color, axis=1)
            dcompetitor = np.linalg.norm(values - competitor_color, axis=1)
            eligible = ((dcompetitor <= MAX_COMPETITOR_DISTANCE_LAB) &
                        (MIN_DISTANCE_RATIO * dcompetitor < dgarment))
            ys, xs, distances = ys[eligible], xs[eligible], dcompetitor[eligible]
            owner_masks = {oid: result == oid for oid in (1, 2)}
            order = np.argsort(distances, kind='stable')
            # Revisit blocked interior points after safe boundary deletions.
            # No new candidate pixels are introduced between passes.
            pending = order
            while len(pending):
                blocked = []
                removed_this_pass = 0
                for idx in pending:
                    y, x = int(ys[idx]), int(xs[idx])
                    oid = int(result[y, x])
                    if _safe_to_remove(owner_masks[oid], y, x):
                        owner_masks[oid][y, x] = False
                        result[y, x] = 0
                        count += 1
                        removed_this_pass += 1
                    else:
                        blocked.append(idx)
                if not removed_this_pass:
                    break
                pending = blocked
            reason = 'SHADOW_ABSTENTION' if count else 'NO_TOPOLOGY_SAFE_CANDIDATE'
    after = [_components4(result == owner_id) for owner_id in (1, 2)]
    changed = result != frozen_owner
    if (before != after or np.any(changed & (class_ids != 32)) or
            np.any(changed & (frozen_owner == 0)) or
            np.any(result > frozen_owner) or np.any((result != 0) & ~opaque) or
            int(np.count_nonzero(changed)) != count):
        raise SourceOnlyAbstentionHold('SOURCE_OWNER_TOPOLOGY_POSTCONDITION_FAIL')
    return result, {
        'schema': 'minimalizer/local-l02/class32-topology-palette-shadow/v1',
        'reason': reason,
        'candidate_abstained_px': count,
        'class2_is_ground_truth_negative': False,
        'uses_human_labels': False,
        'source_sha_verified': True,
        'owner_4_components_before': before,
        'owner_4_components_after': after,
        'candidate_only': True,
        'quality': 'UNASSESSED',
        'L02': 'HOLD', 'Phase4': 'FAIL', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
