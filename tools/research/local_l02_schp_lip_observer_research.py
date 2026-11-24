"""Offline, observer-only SCHP LIP20 research. Never assigns an L02 owner.

Requires an externally authenticated signed source and local ONNX checkpoint.
No network, annotations, owner changes, or production/Golden approval.
LIP training-data rights are noncommercial: research only pending clearance.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

SIZE = 473
MEAN = np.array([0.406, 0.456, 0.485], dtype=np.float32)
STD = np.array([0.225, 0.224, 0.229], dtype=np.float32)
RELEVANT = {2: 'hair', 3: 'glove', 5: 'upper_clothes', 7: 'coat',
            14: 'left_arm', 15: 'right_arm'}

# Immutable public HF/Xet LFS metadata, ONNX-int8 addition commit 3cc2b2d.
# These pins identify the actual checkpoint, not a caller-supplied arbitrary SHA.
SCHP_LIP20_INT8_REVISION = '3cc2b2d00b16840652c1b7845fd78466dae7f157'
SCHP_LIP20_INT8_SHA256 = '871c9e209dc67d6be61c73dcc79cb49e638fcf5bbc35a19b4c7429eba0bfc046'
SCHP_LIP20_INT8_SIZE = 68314352
SCHP_LIP20_INT8_FILENAME = 'schp-lip-20-int8-static.onnx'


class SCHPResearchHold(ValueError):
    """Missing provenance or invalid observer-only inference output."""


def _pin(s: str) -> bool:
    return type(s) is str and len(s) == 64 and all(c in '0123456789abcdef' for c in s)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _validate_signed_source(*, encoded_source: bytes, source_rgba: np.ndarray,
                            expected_encoded_sha256: str,
                            expected_rgba_sha256: str) -> np.ndarray:
    if (type(encoded_source) is not bytes or not encoded_source or
            len(encoded_source) > 32 * 1024 * 1024 or
            type(source_rgba) is not np.ndarray or
            source_rgba.dtype != np.uint8 or source_rgba.ndim != 3 or
            source_rgba.shape[-1] != 4 or not source_rgba.size or
            source_rgba.shape[0] * source_rgba.shape[1] > 16_000_000):
        raise SCHPResearchHold('INVALID_SIGNED_SOURCE')
    if not _pin(expected_encoded_sha256) or not _pin(expected_rgba_sha256):
        raise SCHPResearchHold('MISSING_EXTERNAL_SOURCE_PINS')
    # Freeze caller-owned mutable pixels before checking the external pins.
    # A concurrent caller mutation after validation must never affect inference.
    verified_rgba = np.array(source_rgba, copy=True, order='C')
    verified_rgba.setflags(write=False)
    if _sha(encoded_source) != expected_encoded_sha256 or _sha(verified_rgba.tobytes()) != expected_rgba_sha256:
        raise SCHPResearchHold('SIGNED_SOURCE_SHA_MISMATCH')
    try:
        with Image.open(io.BytesIO(encoded_source)) as img:
            if getattr(img, 'n_frames', 1) != 1 or img.size != (verified_rgba.shape[1], verified_rgba.shape[0]):
                raise SCHPResearchHold('SIGNED_SOURCE_FRAME_OR_DIMENSION_MISMATCH')
            decoded = np.asarray(img.convert('RGBA'))
    except SCHPResearchHold:
        raise
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        raise SCHPResearchHold('SIGNED_SOURCE_DECODE_FAILED') from exc
    if not np.array_equal(decoded, verified_rgba):
        raise SCHPResearchHold('SIGNED_SOURCE_RGBA_BYTES_MISMATCH')
    return verified_rgba


def _prepare(source_rgba: np.ndarray) -> np.ndarray:
    """Match upstream SCHP LIP processor: white RGBA composite, RGB, 473 bilinear.

    The white composite is a predeclared research choice for transparent art,
    not a proven training-domain equivalent. Never infer from review labels.
    """
    img = Image.fromarray(source_rgba, 'RGBA')
    white = Image.new('RGBA', img.size, (255, 255, 255, 255))
    rgb = Image.alpha_composite(white, img).convert('RGB')
    resized = np.asarray(rgb.resize((SIZE, SIZE), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
    normalized = (resized - MEAN) / STD
    return np.ascontiguousarray(normalized.transpose(2, 0, 1)[None, ...], dtype=np.float32)


def _decode_logits(logits: np.ndarray, source_alpha: np.ndarray) -> np.ndarray:
    if (type(logits) is not np.ndarray or logits.dtype not in (np.float32, np.float64) or
            logits.shape != (1, 20, SIZE, SIZE) or not np.isfinite(logits).all()):
        raise SCHPResearchHold('INVALID_SCHP_LIP20_LOGITS')
    labels = np.argmax(logits[0], axis=0).astype(np.uint8)
    # Label nearest-neighbour projection is a declared research choice, not a
    # learned or review-fitted resampler. Keep source-alpha eligibility separate.
    projected = np.asarray(Image.fromarray(labels).resize(
        (source_alpha.shape[1], source_alpha.shape[0]), Image.Resampling.NEAREST)).copy()
    projected[source_alpha == 0] = 0
    return projected


def run_offline_observer(*, encoded_source: bytes, source_rgba: np.ndarray,
                         expected_encoded_sha256: str, expected_rgba_sha256: str,
                         onnx_path: Path, expected_onnx_sha256: str,
                         expected_model_revision: str) -> tuple[np.ndarray, dict]:
    """Offline model-only observer. Caller must store class maps in private Drive.

    No human labels, source-specific thresholds, owner masks, or remote inference.
    Source pins and checkpoint pin must originate outside this function.
    """
    verified_rgba = _validate_signed_source(encoded_source=encoded_source, source_rgba=source_rgba,
                            expected_encoded_sha256=expected_encoded_sha256,
                            expected_rgba_sha256=expected_rgba_sha256)
    if (not _pin(expected_onnx_sha256) or not isinstance(onnx_path, Path) or
            not onnx_path.is_file() or type(expected_model_revision) is not str or
            len(expected_model_revision) != 40 or
            any(c not in '0123456789abcdef' for c in expected_model_revision)):
        raise SCHPResearchHold('MISSING_LOCAL_PINNED_ONNX')
    # A syntactically valid 40-hex revision and arbitrary caller hash do not
    # establish the official ONNX checkpoint. Fail before importing the model.
    if (expected_model_revision != SCHP_LIP20_INT8_REVISION or
            expected_onnx_sha256 != SCHP_LIP20_INT8_SHA256):
        raise SCHPResearchHold('UNVERIFIED_SCHP_CHECKPOINT_PIN')
    if (onnx_path.name != SCHP_LIP20_INT8_FILENAME or
            onnx_path.stat().st_size != SCHP_LIP20_INT8_SIZE):
        raise SCHPResearchHold('UNVERIFIED_SCHP_CHECKPOINT_FILE')
    # Authenticate the exact immutable bytes that ONNX Runtime will execute.
    # A path can be replaced after a streaming hash (TOCTOU). Reading one
    # bounded 68MB snapshot costs temporary RAM but prevents path re-open races.
    with onnx_path.open('rb') as f:
        model_bytes = f.read(SCHP_LIP20_INT8_SIZE + 1)
    if len(model_bytes) != SCHP_LIP20_INT8_SIZE:
        raise SCHPResearchHold('UNVERIFIED_SCHP_CHECKPOINT_FILE')
    if _sha(model_bytes) != expected_onnx_sha256:
        raise SCHPResearchHold('ONNX_SHA_MISMATCH')
    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise SCHPResearchHold('ONNXRUNTIME_NOT_INSTALLED') from exc
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    session = ort.InferenceSession(model_bytes, sess_options=opts,
                                   providers=['CPUExecutionProvider'])
    if (len(session.get_inputs()) != 1 or session.get_inputs()[0].name != 'pixel_values' or
            'logits' not in {o.name for o in session.get_outputs()} or
            session.get_providers() != ['CPUExecutionProvider']):
        raise SCHPResearchHold('UNEXPECTED_ONNX_INTERFACE_OR_PROVIDER')
    logits = session.run(['logits'], {'pixel_values': _prepare(verified_rgba)})[0]
    classes = _decode_logits(logits, verified_rgba[..., 3])
    opaque = verified_rgba[..., 3] > 0
    counts = {name: int(np.count_nonzero((classes == cid) & opaque))
              for cid, name in RELEVANT.items()}
    receipt = {
        'schema': 'minimalizer/local-l02/schp-lip20-offline-observer/v1',
        'model_repo': 'pirocheto/schp-lip-20',
        'model_revision': expected_model_revision,
        'checkpoint_sha256': expected_onnx_sha256,
        'class_map_sha256_private': _sha(classes.tobytes()),
        'source_rgba_sha256': expected_rgba_sha256,
        'relevant_class_counts_opaque_only': counts,
        'input_size': [SIZE, SIZE], 'white_alpha_composite': True,
        'unknown_not_treated_as_negative': True,
        'human_annotations_used': False, 'owner_modified': False,
        'noncommercial_research_only': True,
        'dataset_licence_production_cleared': False,
        'quality': 'UNASSESSED', 'Phase4': 'FAIL', 'L02': 'HOLD',
        'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
    }
    return classes, receipt
