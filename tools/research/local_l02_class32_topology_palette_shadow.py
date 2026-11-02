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


# SHA-256 digests are source-free identifiers, NOT image bytes or human labels.
# Frozen from the existing signed ReviewedEvidence, SleeveSemantic and Run30
# private Drive bundles. These are known-case 4-neighbour historical inputs
# only; this registry must never be interpreted as unknown-character proof.
PINNED_RUN30_4_TRIPLES = {
    'H04': (
        '7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3',
        '389d5975cb66cbc7ca64d27bbd6b1950abce40f6399096d651e86996afd8b1b6',
        '5b56899313d57b1677cb6c30676fe2e60c9fa141331a379aff7ee7a0e6101b5e',
    ),
    'H06': (
        'c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8',
        '06e02c257d982a4da45ee8f77da8730d91615502eaa2cc9e438068e69e1e286a',
        '4be9ae240b8d32cc6b0923371f5c5b3a6159196ba819aa0b7044c06740a7b317',
    ),
    'H08': (
        '759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e',
        'd6ff3cee53338711f6dc253dc423d772f52d7cce711d3311a6497002739976f5',
        '43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52',
    ),
}


class SourceOnlyAbstentionHold(ValueError):
    """Fail closed on untrusted or mismatched source/model/owner inputs."""


def _components4(mask: np.ndarray) -> int:
    # OpenCV returns number of labels including background.
    n, _ = cv2.connectedComponents(mask.astype(np.uint8), connectivity=4)
    return int(n - 1)


def _components8(mask: np.ndarray) -> int:
    n, _ = cv2.connectedComponents(mask.astype(np.uint8), connectivity=8)
    return int(n - 1)


def _local_background_components(mask: np.ndarray, connectivity: int) -> int:
    """Count 4/8-connected negative-space components within a 3x3 patch.

    Conservative local condition: preserving counts in both connectivities
    rejects creation/closure of a small void even when the foreground owner
    component count stays constant. Full-image hole checks are still required
    before any Phase4 promotion.
    """
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if connectivity == 8:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    seen = set()
    count = 0
    for y in range(3):
        for x in range(3):
            if not mask[y, x] or (y, x) in seen:
                continue
            count += 1
            seen.add((y, x))
            stack = [(y, x)]
            while stack:
                cy, cx = stack.pop()
                for dy, dx in steps:
                    ny, nx = cy + dy, cx + dx
                    if (0 <= ny < 3 and 0 <= nx < 3 and
                            mask[ny, nx] and (ny, nx) not in seen):
                        seen.add((ny, nx))
                        stack.append((ny, nx))
    return count


def _frozen_cross_owner_contact8(owner: np.ndarray) -> np.ndarray:
    """Preserve every original 8-neighbour contact between distinct owners.

    Per-owner component counts can remain unchanged while a sleeve loses
    contact with an adjacent arm. Contact pixels must not be abstained.
    """
    kernel = np.ones((3, 3), dtype=np.uint8)
    near_1 = cv2.dilate((owner == 1).astype(np.uint8), kernel) != 0
    near_2 = cv2.dilate((owner == 2).astype(np.uint8), kernel) != 0
    return ((owner == 1) & near_2) | ((owner == 2) & near_1)


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
        # A 4-component count alone cannot detect terminal limb erosion:
        # deleting successive endpoints can erase an entire thin sleeve/arm.
        # Fail closed even when the deletion would keep component counts equal.
        return False
    original_background = ~patch
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
    if not all(p in seen for p in active):
        return False
    # A stable foreground component count alone permits creating a new
    # enclosed negative-space hole. Require both 4/8 local background
    # component counts to stay unchanged; conservatively abstain otherwise.
    new_background = ~patch
    return all(
        _local_background_components(original_background, connectivity) ==
        _local_background_components(new_background, connectivity)
        for connectivity in (4, 8)
    )


def propose_class32_competitor_abstention(*, source_bytes: bytes,
        expected_source_sha256: str, class_ids: np.ndarray,
        frozen_owner: np.ndarray, expected_class_ids_sha256: str,
        expected_frozen_owner_sha256: str) -> tuple[np.ndarray, dict]:
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
    for expected, array, label in (
            (expected_class_ids_sha256, class_ids, 'CLASS_IDS'),
            (expected_frozen_owner_sha256, frozen_owner, 'FROZEN_OWNER')):
        if (type(expected) is not str or
                re.fullmatch(r'[0-9a-f]{64}', expected) is None or
                hashlib.sha256(array.tobytes(order='C')).hexdigest() != expected):
            raise SourceOnlyAbstentionHold(label + '_SHA_MISMATCH')
    protected_contacts = _frozen_cross_owner_contact8(frozen_owner)
    result = frozen_owner.copy()
    garment_seed = ((class_ids == 5) | (class_ids == 10)) & (frozen_owner != 0) & opaque
    competitor_seed = (class_ids == 2) & opaque
    reason = 'NO_CANDIDATE'
    count = 0
    separation = None
    before = [_components4(frozen_owner == owner_id) for owner_id in (1, 2)]
    before8 = [_components8(frozen_owner == owner_id) for owner_id in (1, 2)]
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
                        (MIN_DISTANCE_RATIO * dcompetitor < dgarment) &
                        ~protected_contacts[ys, xs])
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
    after8 = [_components8(result == owner_id) for owner_id in (1, 2)]
    changed = result != frozen_owner
    if (before != after or before8 != after8 or
            np.any(changed & protected_contacts) or
            np.any(changed & (class_ids != 32)) or
            np.any(changed & (frozen_owner == 0)) or
            np.any(result > frozen_owner) or np.any((result != 0) & ~opaque) or
            int(np.count_nonzero(changed)) != count):
        raise SourceOnlyAbstentionHold('SOURCE_OWNER_TOPOLOGY_POSTCONDITION_FAIL')
    return result, {
        'schema': 'minimalizer/local-l02/class32-topology-palette-shadow/v1',
        'reason': reason,
        'candidate_abstained_px': count,
        'frozen_cross_owner_contact8_px': int(protected_contacts.sum()),
        'frozen_cross_owner_contact8_preserved': bool(np.array_equal(
            result[protected_contacts], frozen_owner[protected_contacts])),
        'class2_is_ground_truth_negative': False,
        'uses_human_labels': False,
        'source_sha_verified': True,
        'class_ids_sha_verified': True,
        'frozen_owner_sha_verified': True,
        'owner_8_components_before': before8,
        'owner_8_components_after': after8,
        'owner_4_components_before': before,
        'owner_4_components_after': after,
        'candidate_only': True,
        'quality': 'UNASSESSED',
        'L02': 'HOLD', 'Phase4': 'FAIL', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }


def propose_pinned_run30_4_shadow(*, case_id: str, source_bytes: bytes,
        class_ids: np.ndarray, frozen_owner: np.ndarray) -> tuple[np.ndarray, dict]:
    """Fail-closed historical signed replay; never infer provenance from caller hashes.

    The generic research function accepts caller-provided expected digests and
    cannot authenticate a run. This wrapper binds source, class prediction and
    owner together against the independently pinned Run30 4-neighbour bundle.
    Unknown signed images require a separately reviewed frozen manifest, not
    a relaxed fallback to these known-character pins.
    """
    if type(case_id) is not str or case_id not in PINNED_RUN30_4_TRIPLES:
        raise SourceOnlyAbstentionHold('UNPINNED_RUN30_CASE')
    if (type(source_bytes) is not bytes or
            type(class_ids) is not np.ndarray or type(frozen_owner) is not np.ndarray or
            class_ids.dtype != np.uint8 or frozen_owner.dtype != np.uint8):
        raise SourceOnlyAbstentionHold('INVALID_PINNED_RUN30_INPUT')
    actual = (hashlib.sha256(source_bytes).hexdigest(),
              hashlib.sha256(class_ids.tobytes(order='C')).hexdigest(),
              hashlib.sha256(frozen_owner.tobytes(order='C')).hexdigest())
    expected = PINNED_RUN30_4_TRIPLES[case_id]
    if actual != expected:
        raise SourceOnlyAbstentionHold('RUN30_PROVENANCE_TRIPLE_MISMATCH')
    result, receipt = propose_class32_competitor_abstention(
        source_bytes=source_bytes, expected_source_sha256=expected[0],
        class_ids=class_ids, frozen_owner=frozen_owner,
        expected_class_ids_sha256=expected[1],
        expected_frozen_owner_sha256=expected[2],
    )
    receipt['run30_4_provenance_pinned'] = True
    receipt['run30_case'] = case_id
    return result, receipt
