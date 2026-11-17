"""Source-only ATR18 raw/refined head disagreement, research-only ABSTAIN.

No human labels, owner maps, original RGB, coordinates or private masks enter
this function. Its aggregate cannot authorize owner promotion or Golden.
"""
from __future__ import annotations

import numpy as np


class ATRHeadAuditHold(ValueError):
    """Invalid model/head provenance must not yield a PASS-like receipt."""


PARTS = {4: 'upper_clothes', 14: 'left_arm', 15: 'right_arm', 16: 'bag'}


def audit_atr_head_disagreement(*, raw_ids: np.ndarray,
                                refined_ids: np.ndarray,
                                source_alpha: np.ndarray) -> dict:
    """Audit *frozen* raw `logits` vs refined `parsing_logits` class maps.

    Both class maps must already be alpha-clipped at original source resolution.
    The alpha is an immutable signed-source domain, not a human annotation.
    """
    if (type(raw_ids) is not np.ndarray or raw_ids.dtype != np.uint8 or
            raw_ids.ndim != 2 or not 0 < raw_ids.size <= 16_000_000 or
            type(refined_ids) is not np.ndarray or
            refined_ids.dtype != np.uint8 or refined_ids.shape != raw_ids.shape or
            type(source_alpha) is not np.ndarray or
            source_alpha.shape != raw_ids.shape or
            source_alpha.dtype != np.uint8):
        raise ATRHeadAuditHold('INVALID_ATR_HEAD_OR_SIGNED_ALPHA')
    if np.any(raw_ids > 17) or np.any(refined_ids > 17):
        raise ATRHeadAuditHold('INVALID_ATR18_TAXONOMY')
    visible = source_alpha > 0
    if np.any((raw_ids != 0) & ~visible) or np.any((refined_ids != 0) & ~visible):
        raise ATRHeadAuditHold('HEAD_PREDICTION_OUTSIDE_SOURCE_ALPHA')
    diff = (raw_ids != refined_ids) & visible
    counts = {
        'opaque_px': int(np.count_nonzero(visible)),
        'head_disagreement_px': int(np.count_nonzero(diff)),
    }
    for cls, name in PARTS.items():
        a = (raw_ids == cls) & visible
        b = (refined_ids == cls) & visible
        counts[name + '_raw_px'] = int(np.count_nonzero(a))
        counts[name + '_refined_px'] = int(np.count_nonzero(b))
        counts[name + '_raw_only_px'] = int(np.count_nonzero(a & ~b))
        counts[name + '_refined_only_px'] = int(np.count_nonzero(b & ~a))
    if counts['head_disagreement_px'] > counts['opaque_px']:
        raise ATRHeadAuditHold('HEAD_PARTITION_INVARIANT')
    return {
        'schema': 'minimalizer/local-l02/atr18-head-disagreement/v1',
        'raw_output': 'logits', 'refined_output': 'parsing_logits',
        'head_selection_authorized': False,
        'owner_modified': False, 'human_labels_used': False,
        'unknown_treated_as_negative': False,
        'quality': 'UNASSESSED', 'Phase4': 'FAIL', 'L02': 'HOLD',
        'L03': 'NO_GO', 'Golden': 'HOLD', 'production': 'NO_GO',
        'counts': counts,
    }
