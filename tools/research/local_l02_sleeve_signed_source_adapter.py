"""Authenticated, dormant Lane-A H08 sleeve candidate replay adapter.

All digests must be independently pinned before inference. Human labels and
manual polygons are not accepted. This is not a Phase4 or release approval.
"""
from __future__ import annotations

import hashlib
import io

import numpy as np
from PIL import Image, UnidentifiedImageError

from local_l02_sleeve_contact_safe_shadow import propose_sleeve_contact_safe_shadow


class SleeveSignedSourceHold(ValueError):
    pass


def _digest(a: np.ndarray) -> str:
    return hashlib.sha256(a.tobytes(order='C')).hexdigest()


def _valid_pin(s: str) -> bool:
    return isinstance(s, str) and len(s) == 64 and all(c in '0123456789abcdef' for c in s)


def propose_signed_sleeve_contact_safe_shadow(*, encoded_source: bytes,
        source_rgba: np.ndarray, class_ids: np.ndarray, anime_classes: np.ndarray,
        frozen_candidate: np.ndarray, frozen_owner: np.ndarray,
        expected_encoded_source_sha256: str, expected_rgba_sha256: str,
        expected_class_ids_sha256: str, expected_anime_classes_sha256: str,
        expected_candidate_sha256: str, expected_frozen_owner_sha256: str,
        connectivity: int = 4) -> tuple[np.ndarray, dict]:
    """Reject unsigned observations and mutated inputs before returning a shadow."""
    arrays = (source_rgba, class_ids, anime_classes, frozen_candidate, frozen_owner)
    pins = (expected_encoded_source_sha256, expected_rgba_sha256,
            expected_class_ids_sha256, expected_anime_classes_sha256,
            expected_candidate_sha256, expected_frozen_owner_sha256)
    if (type(encoded_source) is not bytes or not encoded_source or
            len(encoded_source) > 32 * 1024 * 1024 or
            not all(_valid_pin(p) for p in pins)):
        raise SleeveSignedSourceHold('INVALID_EXTERNAL_SOURCE_PINS')
    if (any(type(a) is not np.ndarray for a in arrays) or
            source_rgba.dtype != np.uint8 or source_rgba.ndim != 3 or
            source_rgba.shape[-1] != 4 or not source_rgba.size or
            source_rgba.shape[0] * source_rgba.shape[1] > 16_000_000 or
            any(a.shape != source_rgba.shape[:2] for a in arrays[1:]) or
            any(a.dtype != np.uint8 for a in (class_ids, anime_classes, frozen_owner)) or
            frozen_candidate.dtype != np.bool_ or connectivity not in (4, 8)):
        raise SleeveSignedSourceHold('INVALID_SIGNED_SLEEVE_INPUT')
    if hashlib.sha256(encoded_source).hexdigest() != pins[0]:
        raise SleeveSignedSourceHold('ENCODED_SOURCE_SHA_MISMATCH')
    try:
        with Image.open(io.BytesIO(encoded_source)) as im:
            if (getattr(im, 'n_frames', 1) != 1 or
                    im.size != (source_rgba.shape[1], source_rgba.shape[0])):
                raise SleeveSignedSourceHold('SOURCE_DIMENSION_OR_FRAME_MISMATCH')
            decoded = np.asarray(im.convert('RGBA'))
    except SleeveSignedSourceHold:
        raise
    except (OSError, UnidentifiedImageError, ValueError, Image.DecompressionBombError) as exc:
        raise SleeveSignedSourceHold('SOURCE_DECODE_FAILED') from exc
    if not np.array_equal(decoded, source_rgba):
        raise SleeveSignedSourceHold('SOURCE_DECODE_BYTES_MISMATCH')
    if any(_digest(a) != p for a, p in zip(arrays, pins[1:])):
        raise SleeveSignedSourceHold('SIGNED_OBSERVATION_SHA_MISMATCH')
    if np.any((frozen_owner > 0) & ~frozen_candidate):
        raise SleeveSignedSourceHold('CANDIDATE_EXCLUDES_FROZEN_OWNER')
    try:
        proposal, audit = propose_sleeve_contact_safe_shadow(
            class_ids=class_ids, anime_classes=anime_classes,
            source_alpha=source_rgba[..., 3], frozen_candidate=frozen_candidate,
            frozen_owner=frozen_owner, connectivity=connectivity)
    except (ValueError, TypeError, KeyError) as exc:
        raise SleeveSignedSourceHold('SHADOW_REJECTED:' + str(exc)) from exc
    if any(_digest(a) != p for a, p in zip(arrays, pins[1:])):
        raise SleeveSignedSourceHold('SHADOW_MUTATED_SIGNED_INPUT')
    if (type(proposal) is not np.ndarray or proposal.dtype != np.uint8 or
            proposal.shape != frozen_owner.shape or
            np.any((frozen_owner > 0) & (proposal != frozen_owner)) or
            np.any((proposal > 0) & (source_rgba[..., 3] == 0))):
        raise SleeveSignedSourceHold('INVALID_SHADOW_OUTPUT')
    return proposal, {
        **audit, 'schema': 'minimalizer/local-l02/signed-sleeve-contact-safe/v1',
        'proposal_owner_sha256': _digest(proposal),
        'external_encoded_and_decoded_source_verified': True,
        'external_class_anime_candidate_owner_pins_verified': True,
        'signed_inputs_immutable_after_shadow': True,
        'known_cases_exposed': True, 'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
