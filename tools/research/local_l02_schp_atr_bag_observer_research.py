"""Pinned offline SCHP-ATR18 bag/arm observer, research only, no owner promotion.

This module intentionally reuses the independently verified signed-source gate
from the isolated LIP observer PR. No private images or masks leave the caller.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
from PIL import Image
from local_l02_schp_lip_observer_research import (
    _validate_signed_source, _sha, SCHPResearchHold, MEAN, STD,
)

SIZE = 512
REVISION = 'a54fa65e7e4f27f21011f652ffc0053ebb24b292'
MODEL_SHA256 = '4420d8db8c1f266967c89485786b01209f6d405f320fc0f87e8ced49392cefb5'
MODEL_BYTES = 69141996
MODEL_FILENAME = 'schp-atr-18-int8-static.onnx'
RELEVANT = {2: 'hair', 4: 'upper_clothes', 6: 'pants',
            14: 'left_arm', 15: 'right_arm', 16: 'bag'}


def _prepare(rgba: np.ndarray) -> np.ndarray:
    image = Image.fromarray(rgba, 'RGBA')
    rgb = Image.alpha_composite(
        Image.new('RGBA', image.size, (255, 255, 255, 255)), image,
    ).convert('RGB')
    arr = np.asarray(rgb.resize((SIZE, SIZE), Image.Resampling.BILINEAR),
                     dtype=np.float32) / 255.0
    return np.ascontiguousarray(((arr - MEAN) / STD).transpose(2, 0, 1)[None],
                                dtype=np.float32)


def _decode(logits: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    if (type(logits) is not np.ndarray or logits.dtype not in (np.float32, np.float64)
            or logits.shape != (1, 18, SIZE, SIZE) or not np.isfinite(logits).all()):
        raise SCHPResearchHold('INVALID_SCHP_ATR18_LOGITS')
    ids = np.argmax(logits[0], axis=0).astype(np.uint8)
    projected = np.asarray(Image.fromarray(ids).resize(
        (alpha.shape[1], alpha.shape[0]), Image.Resampling.NEAREST)).copy()
    projected[alpha == 0] = 0
    return projected


def run_offline_atr_bag_observer(*, encoded_source: bytes, source_rgba: np.ndarray,
                                 expected_encoded_sha256: str, expected_rgba_sha256: str,
                                 onnx_path: Path, expected_onnx_sha256: str,
                                 expected_model_revision: str) -> tuple[np.ndarray, dict]:
    """Return only private class IDs and source-free receipt; never an owner map.

    Model bytes are never downloaded or inferred remotely. The exact upstream
    ONNX checkpoint is required. Human labels and frozen owner are not inputs.
    """
    rgba = _validate_signed_source(
        encoded_source=encoded_source, source_rgba=source_rgba,
        expected_encoded_sha256=expected_encoded_sha256,
        expected_rgba_sha256=expected_rgba_sha256)
    if (type(expected_onnx_sha256) is not str or
            expected_onnx_sha256 != MODEL_SHA256 or
            type(expected_model_revision) is not str or
            expected_model_revision != REVISION):
        raise SCHPResearchHold('UNVERIFIED_SCHP_ATR_CHECKPOINT_PIN')
    if (not isinstance(onnx_path, Path) or not onnx_path.is_file() or
            onnx_path.name != MODEL_FILENAME or
            onnx_path.stat().st_size != MODEL_BYTES):
        raise SCHPResearchHold('UNVERIFIED_SCHP_ATR_CHECKPOINT_FILE')
    # Immutable authenticated snapshot prevents path replacement during load.
    with onnx_path.open('rb') as handle:
        model = handle.read(MODEL_BYTES + 1)
    if len(model) != MODEL_BYTES or _sha(model) != MODEL_SHA256:
        raise SCHPResearchHold('SCHP_ATR_ONNX_SHA_MISMATCH')
    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise SCHPResearchHold('ONNXRUNTIME_NOT_INSTALLED') from exc
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    session = ort.InferenceSession(model, sess_options=opts,
                                   providers=['CPUExecutionProvider'])
    if (len(session.get_inputs()) != 1 or
            session.get_inputs()[0].name != 'pixel_values' or
            'logits' not in {v.name for v in session.get_outputs()} or
            session.get_providers() != ['CPUExecutionProvider']):
        raise SCHPResearchHold('UNEXPECTED_SCHP_ATR_INTERFACE_OR_PROVIDER')
    ids = _decode(session.run(['logits'], {'pixel_values': _prepare(rgba)})[0],
                  rgba[..., 3])
    opaque = rgba[..., 3] > 0
    receipt = {
        'schema': 'minimalizer/local-l02/schp-atr18-bag-observer/v1',
        'model_repo': 'pirocheto/schp-atr-18',
        'model_revision': REVISION,
        'checkpoint_sha256': MODEL_SHA256,
        'class_map_sha256_private': _sha(ids.tobytes()),
        'source_rgba_sha256': expected_rgba_sha256,
        'relevant_class_counts_opaque_only': {
            name: int(np.count_nonzero((ids == cid) & opaque))
            for cid, name in RELEVANT.items()},
        'human_annotations_used': False, 'owner_modified': False,
        'unknown_not_treated_as_negative': True,
        'model_licence_metadata': 'MIT',
        'atr_training_data_rights_verified': False,
        'research_only': True, 'quality': 'UNASSESSED',
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
    return ids, receipt
