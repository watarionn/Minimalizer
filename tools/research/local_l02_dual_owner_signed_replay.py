"""Run the dormant Lane-A dual-owner shadow on independently pinned private inputs.

No manual labels or coordinates are accepted. No candidate owner or source pixels
are written. The JSON stdout is a source-free research receipt, not a quality
approval or a production integration. Never compute a manifest pin from the
untrusted manifest supplied to this invocation.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from local_l02_replay_lineage_gate import ReplayLineageHold, verify_pr_replay_lineage


class SignedReplayHold(ValueError):
    """Source, model observation, owner or manifest provenance is not verified."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bounded(path: Path, limit: int) -> bytes:
    if not path.is_file() or path.stat().st_size > limit:
        raise SignedReplayHold('MISSING_OR_OVERSIZE_PRIVATE_INPUT')
    data = path.read_bytes()
    if not data or len(data) > limit:
        raise SignedReplayHold('EMPTY_OR_OVERSIZE_PRIVATE_INPUT')
    return data


def _read_npz_array(path: Path, key: str) -> np.ndarray:
    raw = _read_bounded(path, 32 * 1024 * 1024)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
            member = zipped.getinfo(key + '.npy')
            if member.file_size > 16_000_256:
                raise SignedReplayHold('OVERSIZE_UNCOMPRESSED_NPZ_ARRAY')
        with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
            if key not in archive.files:
                raise SignedReplayHold('MISSING_PINNED_NPZ_ARRAY')
            array = archive[key]
    except SignedReplayHold:
        raise
    except (OSError, ValueError, KeyError, EOFError, zipfile.BadZipFile) as exc:
        raise SignedReplayHold('INVALID_PINNED_NPZ') from exc
    if (type(array) is not np.ndarray or array.dtype != np.uint8 or
            array.ndim != 2 or not array.size or array.size > 16_000_000):
        raise SignedReplayHold('INVALID_PINNED_NPZ_ARRAY')
    return array


def run_pinned_replay(*, source_path: Path, class_npz_path: Path,
                      owner_npz_path: Path, manifest_path: Path,
                      expected_manifest_sha256: str) -> dict:
    """Return only source-free receipt; never return or persist owner pixels."""
    if (not isinstance(expected_manifest_sha256, str) or
            len(expected_manifest_sha256) != 64 or
            any(c not in '0123456789abcdef' for c in expected_manifest_sha256)):
        raise SignedReplayHold('MISSING_EXTERNAL_MANIFEST_SHA256')
    # Source-only code provenance first: reject stale/partial PR dependencies
    # before opening the signed manifest, source image, or private NPZ files.
    try:
        lineage = verify_pr_replay_lineage()
    except ReplayLineageHold as exc:
        raise SignedReplayHold('PR_DEPENDENCY_LINEAGE_HOLD:' + str(exc)) from exc
    # Import the pinned adapter only after its Git blob and transitive imports
    # are checked. A top-level import would execute unverified code first.
    from local_l02_dual_owner_signed_input_adapter import (
        SignedDualOwnerInputHold, propose_signed_dual_owner_lab_reach_shadow,
    )
    manifest_bytes = _read_bounded(manifest_path, 64 * 1024)
    if _sha256(manifest_bytes) != expected_manifest_sha256:
        raise SignedReplayHold('MANIFEST_SHA256_MISMATCH')
    try:
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SignedReplayHold('INVALID_MANIFEST_JSON') from exc
    required = ('schema', 'case', 'stage', 'encoded_source_sha256',
                'decoded_rgba_sha256', 'class_ids_sha256',
                'composed_owner_sha256')
    if (not isinstance(manifest, dict) or
            manifest.get('schema') != 'minimalizer/local-l02/signed-run30-replay-pin/v1' or
            manifest.get('case') not in ('H06', 'H08') or
            manifest.get('stage') != 'RUN30_HISTORICAL' or
            any(not isinstance(manifest.get(k), str) for k in required)):
        raise SignedReplayHold('UNSUPPORTED_OR_INCOMPLETE_REPLAY_STAGE')
    source = _read_bounded(source_path, 32 * 1024 * 1024)
    if _sha256(source) != manifest['encoded_source_sha256']:
        raise SignedReplayHold('ENCODED_SOURCE_SHA_MISMATCH')
    try:
        with Image.open(io.BytesIO(source)) as im:
            if getattr(im, 'n_frames', 1) != 1 or im.width * im.height > 16_000_000:
                raise SignedReplayHold('UNSUPPORTED_SOURCE_FRAME_OR_SIZE')
            rgba = np.asarray(im.convert('RGBA'))
    except SignedReplayHold:
        raise
    except (OSError, UnidentifiedImageError, ValueError, Image.DecompressionBombError) as exc:
        raise SignedReplayHold('SOURCE_DECODE_FAILED') from exc
    classes = _read_npz_array(class_npz_path, 'classids')
    owner = _read_npz_array(owner_npz_path, 'owner')
    if (classes.shape != rgba.shape[:2] or owner.shape != rgba.shape[:2]):
        raise SignedReplayHold('SOURCE_CLASS_OWNER_SHAPE_MISMATCH')
    try:
        proposal, receipt = propose_signed_dual_owner_lab_reach_shadow(
            encoded_source=source, source_rgba=rgba,
            class_ids=classes, composed_owner=owner,
            expected_encoded_source_sha256=manifest['encoded_source_sha256'],
            expected_decoded_rgba_sha256=manifest['decoded_rgba_sha256'],
            expected_class_ids_sha256=manifest['class_ids_sha256'],
            expected_composed_owner_sha256=manifest['composed_owner_sha256'],
        )
    except SignedDualOwnerInputHold as exc:
        raise SignedReplayHold('SIGNED_ADAPTER_HOLD:' + str(exc)) from exc
    return {
        'schema': 'minimalizer/local-l02/signed-replay-sourcefree-receipt/v1',
        'case': manifest['case'],
        'stage': 'RUN30_HISTORICAL',
        'manifest_sha256': expected_manifest_sha256,
        'pr_dependency_lineage': lineage,
        'proposal_owner_sha256': _sha256(proposal.tobytes(order='C')),
        'new_source_pixels_unscored': receipt['new_source_pixels'],
        'signed_source_encoded_and_decoded_verified': receipt['signed_source_encoded_and_decoded_verified'],
        'independent_class_bytes_verified': receipt['independent_class_bytes_verified'],
        'frozen_owner_bytes_verified': receipt['frozen_owner_bytes_verified'],
        'frozen_owner_transition_audit': receipt.get('frozen_owner_transition_audit'),
        'cross_owner_contact_audit': receipt.get('cross_owner_contact_audit'),
        'known_cases_exposed': True,
        'semantic_owner_authorized': False,
        'new_unseen_signed_blind': 'PENDING',
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--classes', type=Path, required=True)
    parser.add_argument('--owner', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    try:
        receipt = run_pinned_replay(
            source_path=args.source, class_npz_path=args.classes,
            owner_npz_path=args.owner, manifest_path=args.manifest,
            expected_manifest_sha256=args.manifest_sha256,
        )
    except (SignedReplayHold, ValueError) as exc:
        print(json.dumps({'status': 'HOLD', 'reason': str(exc),
                          'Phase4': 'FAIL', 'L02': 'HOLD',
                          'production': 'NO_GO'}, sort_keys=True))
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
