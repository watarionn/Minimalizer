"""Source-only external-image *diagnostic*, never a Phase4 candidate.

A classifier trained on H04 is probed on different images using only original
RGBA source pixels. No anatomical/part masks are available for new images.
Consequently results cannot become signed semantic owners, Golden PASS or L02
release approval. Opaque-backdrop images are rejected fail-closed.
"""
from __future__ import annotations
import dataclasses
import hashlib
import math
from typing import Protocol
import numpy as np

from local_l02_manual_supervised_shadow import source_features, AuthorityHold


class Predictor(Protocol):
    def predict_proba(self, x: np.ndarray) -> np.ndarray: ...


@dataclasses.dataclass(frozen=True)
class SourceProbe:
    case_id: str
    status: str
    reason: str
    original_sha256: str
    original_size: tuple[int, int]
    sample_shape: tuple[int, int] | None
    sample_stride: int | None
    foreground_fraction: float
    border_foreground_fraction: float
    source_foreground_samples: int
    high_confidence_pixels: int | None
    positive_pixels: int | None
    positive_ratio: float | None
    top_quarter_positive_ratio: float | None
    semantic_iou: None = None
    semantic_pass: bool = False
    production_candidate: bool = False
    original_masks_available: bool = False

    def to_dict(self) -> dict:
        out = dataclasses.asdict(self)
        out['original_size'] = list(self.original_size)
        if self.sample_shape is not None:
            out['sample_shape'] = list(self.sample_shape)
        return out


def verify_exact_bytes(raw: bytes, expected_hex: str) -> str:
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_hex:
        raise AuthorityHold('signed original source bytes differ from manifest')
    return actual


def assess_transparency(src: np.ndarray) -> tuple[float, float]:
    if src.ndim != 3 or src.shape[2] != 4 or src.dtype != np.uint8:
        raise AuthorityHold('source must be RGBA uint8')
    alpha = src[:, :, 3] > 0
    foreground = float(alpha.mean())
    border = np.concatenate((alpha[0, :], alpha[-1, :], alpha[1:-1, 0], alpha[1:-1, -1]))
    return foreground, float(border.mean())


def raw_probe(case_id: str, src: np.ndarray, source_digest: str, model: Predictor, *, max_dimension: int = 800,
              predict_chunk: int = 18000) -> tuple[SourceProbe, np.ndarray | None, np.ndarray | None]:
    """No mask ownership or morphology. Return raw diagnostics only.

    Subsample *existing* source pixel values by integer stride. This changes
    neighborhood scale, so visual overlays are only diagnostic thumbnails.
    """
    fg, border = assess_transparency(src)
    h, w = src.shape[:2]
    if not isinstance(source_digest, str) or len(source_digest) != 64:
        raise AuthorityHold('missing authenticated source hash')
    reason = ''
    if border > .20 or fg > .92:
        reason = 'OPAQUE_OR_COMPLEX_BACKGROUND_UNSUPPORTED'
    elif fg < .008:
        reason = 'SOURCE_FOREGROUND_TOO_SMALL'
    if reason:
        return SourceProbe(case_id, 'ABSTAIN', reason, source_digest, (w,h), None, None, fg, border, 0,
                           None, None, None, None), None, None
    if max_dimension < 100 or predict_chunk < 100:
        raise AuthorityHold('invalid probe resource guard')
    stride = max(1, math.ceil(max(h, w) / max_dimension))
    source_sample = np.ascontiguousarray(src[::stride, ::stride, :])
    alpha = source_sample[:, :, 3] > 0
    indices = np.flatnonzero(alpha.ravel())
    if len(indices) < 30:
        raise AuthorityHold('insufficient source samples')
    features = source_features(source_sample).reshape(-1, 18)
    predicted = np.zeros(alpha.size, np.uint8)
    confident = np.zeros(alpha.size, np.uint8)
    for start in range(0, len(indices), predict_chunk):
        ids = indices[start:start+predict_chunk]
        probs = np.asarray(model.predict_proba(features[ids]))
        if probs.shape != (len(ids), 2) or not np.isfinite(probs).all():
            raise AuthorityHold('nonfinite or incorrectly shaped probability')
        if np.any(probs < 0) or np.any(probs > 1):
            raise AuthorityHold('untrusted probability distribution')
        predicted[ids] = probs[:, 1] >= .5
        confident[ids] = probs[:, 1] >= .8
    predicted = predicted.reshape(alpha.shape).astype(bool)
    confident = confident.reshape(alpha.shape).astype(bool)
    if np.any(predicted & ~alpha):
        raise AuthorityHold('source-unsupported response')
    q = max(1, round(source_sample.shape[0]*.25))
    top_area = alpha[:q]
    top_ratio = float(predicted[:q].sum()) / max(1, int(top_area.sum()))
    record = SourceProbe(case_id, 'RAW_PROBE_ONLY', 'NO_INDEPENDENT_OWNER_OR_JACKET_LABELS', source_digest,
        (w,h), (source_sample.shape[1],source_sample.shape[0]), stride, fg, border,
        int(indices.size), int(confident.sum()), int(predicted.sum()),
        round(float(predicted.sum()) / len(indices), 6), round(top_ratio, 6))
    return record, predicted, source_sample


def release_gate(results: list[SourceProbe], independently_authenticated_jacket_labels: int) -> dict:
    """Never infer quality PASS from unlabeled soft evidence or internal consistency."""
    if any(r.semantic_pass or r.production_candidate or r.original_masks_available for r in results):
        raise AuthorityHold('diagnostic attempt pretends to be authoritative')
    if independently_authenticated_jacket_labels != 0:
        raise AuthorityHold('this transfer probe cannot consume signed ground truth')
    return {'status': 'HOLD', 'labelled_unseen_cases': 0, 'observed_unseen_cases': len(results),
            'probed': sum(r.status == 'RAW_PROBE_ONLY' for r in results),
            'abstained': sum(r.status == 'ABSTAIN' for r in results),
            'semantic_precision': None, 'semantic_recall': None, 'semantic_iou': None,
            'phase4_candidate_created': False, 'production_release': 'NO_GO'}
