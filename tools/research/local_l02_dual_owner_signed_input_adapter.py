"""Fail-closed signed-source adapter for the dormant H08 LAB-reach shadow.

The expected digests MUST come from independently authenticated manifests.
This adapter never accepts human annotations, never approves semantic quality,
and does not connect the research shadow to production inference.
"""
from __future__ import annotations

import hashlib
import io

import numpy as np
from PIL import Image, UnidentifiedImageError

from local_l02_dual_owner_lab_reach_shadow import propose_dual_owner_lab_reach_shadow
from local_l02_signed_shadow_output_gate import (
    SignedShadowOutputHold, verify_signed_shadow_output,
)


class SignedDualOwnerInputHold(ValueError):
    """Unverified source, independent observation, or frozen owner."""


def _pin(value: str) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        c in '0123456789abcdef' for c in value)


def propose_signed_dual_owner_lab_reach_shadow(
    *, encoded_source: bytes, source_rgba: np.ndarray, class_ids: np.ndarray,
    composed_owner: np.ndarray, expected_encoded_source_sha256: str,
    expected_decoded_rgba_sha256: str, expected_class_ids_sha256: str,
    expected_composed_owner_sha256: str,
) -> tuple[np.ndarray, dict]:
    """Verify raw and decoded signed input before calling the A-only shadow.

    Source image bytes and frozen model-class bytes are not uploaded or logged.
    SHA pins are externally supplied and are NOT derived from these inputs.
    """
    if (type(encoded_source) is not bytes or not encoded_source or
            len(encoded_source) > 32 * 1024 * 1024 or
            type(source_rgba) is not np.ndarray or
            source_rgba.dtype != np.uint8 or source_rgba.ndim != 3 or
            source_rgba.shape[-1] != 4 or not source_rgba.size or
            source_rgba.shape[0] * source_rgba.shape[1] > 16_000_000 or
            type(class_ids) is not np.ndarray or
            class_ids.dtype != np.uint8 or class_ids.shape != source_rgba.shape[:2] or
            type(composed_owner) is not np.ndarray or
            composed_owner.dtype != np.uint8 or
            composed_owner.shape != source_rgba.shape[:2]):
        raise SignedDualOwnerInputHold('INVALID_SIGNED_INPUT_CONTRACT')
    if not all(_pin(p) for p in (
            expected_encoded_source_sha256, expected_decoded_rgba_sha256,
            expected_class_ids_sha256, expected_composed_owner_sha256)):
        raise SignedDualOwnerInputHold('MISSING_EXTERNAL_SHA256_PIN')
    if hashlib.sha256(encoded_source).hexdigest() != expected_encoded_source_sha256:
        raise SignedDualOwnerInputHold('ENCODED_SOURCE_SHA_MISMATCH')
    try:
        with Image.open(io.BytesIO(encoded_source)) as im:
            if getattr(im, 'n_frames', 1) != 1 or im.size != (
                    source_rgba.shape[1], source_rgba.shape[0]):
                raise SignedDualOwnerInputHold('DECODED_SOURCE_DIMENSION_OR_FRAME_MISMATCH')
            decoded = np.asarray(im.convert('RGBA'))
    except SignedDualOwnerInputHold:
        raise
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        raise SignedDualOwnerInputHold('SOURCE_DECODE_FAILED') from exc
    if (not np.array_equal(decoded, source_rgba) or
            hashlib.sha256(source_rgba.tobytes(order='C')).hexdigest()
            != expected_decoded_rgba_sha256):
        raise SignedDualOwnerInputHold('DECODED_RGBA_SHA_OR_BYTES_MISMATCH')
    if hashlib.sha256(class_ids.tobytes(order='C')).hexdigest() != expected_class_ids_sha256:
        raise SignedDualOwnerInputHold('INDEPENDENT_CLASS_SHA_MISMATCH')
    if hashlib.sha256(composed_owner.tobytes(order='C')).hexdigest() != expected_composed_owner_sha256:
        raise SignedDualOwnerInputHold('FROZEN_OWNER_SHA_MISMATCH')
    frozen_owner_before_shadow = composed_owner.copy()
    proposed, receipt = propose_dual_owner_lab_reach_shadow(
        source_rgba=source_rgba, class_ids=class_ids,
        composed_owner=composed_owner,
        expected_composed_owner_sha256=expected_composed_owner_sha256,
    )
    if (hashlib.sha256(composed_owner.tobytes(order='C')).hexdigest()
            != expected_composed_owner_sha256):
        raise SignedDualOwnerInputHold('SHADOW_MUTATED_FROZEN_OWNER')
    if (hashlib.sha256(class_ids.tobytes(order='C')).hexdigest()
            != expected_class_ids_sha256):
        raise SignedDualOwnerInputHold('SHADOW_MUTATED_INDEPENDENT_CLASS')
    if (hashlib.sha256(source_rgba.tobytes(order='C')).hexdigest()
            != expected_decoded_rgba_sha256):
        raise SignedDualOwnerInputHold('SHADOW_MUTATED_SIGNED_SOURCE')
    # A valid SHA pin does not prevent a shadow from returning a writable
    # alias of an authenticated input. Never hand that alias to callers.
    if type(proposed) is not np.ndarray:
        raise SignedDualOwnerInputHold('INVALID_SHADOW_OUTPUT_TYPE')
    if any(np.shares_memory(proposed, verified) for verified in
           (source_rgba, class_ids, composed_owner)):
        raise SignedDualOwnerInputHold('SHADOW_OUTPUT_ALIASES_SIGNED_INPUT')
    try:
        postcondition = verify_signed_shadow_output(
            source_rgba=source_rgba, class_ids=class_ids,
            before=frozen_owner_before_shadow, after=proposed, receipt=receipt,
        )
    except SignedShadowOutputHold as exc:
        raise SignedDualOwnerInputHold('SHADOW_POSTCONDITION_HOLD:' + str(exc)) from exc
    return proposed, {
        **receipt,
        'signed_shadow_postcondition_audit': postcondition,
        'signed_source_encoded_and_decoded_verified': True,
        'independent_class_bytes_verified': True,
        'frozen_owner_bytes_verified': True,
        'external_sha256_pins_required': True,
        'human_labels_used_for_inference': False,
        'semantic_owner_authorized': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
