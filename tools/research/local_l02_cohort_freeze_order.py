"""L02 source-free cohort chronology gate; never a quality or holdout PASS."""
from datetime import datetime


class FreezeOrderHold(ValueError):
    pass


def _timestamp(value):
    if type(value) is not str:
        raise FreezeOrderHold('INVALID_TIMESTAMP')
    try:
        t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise FreezeOrderHold('INVALID_TIMESTAMP') from exc
    if t.tzinfo is None or t.utcoffset() is None:
        raise FreezeOrderHold('NAIVE_TIMESTAMP')
    return t


def audit_cohort_freeze_order(hypothesis_frozen_at, case_times):
    """Require ALL predictions frozen before ANY human annotation exists.

    Caller-provided times are not authenticated signatures. Human labels must
    remain postscore-only; no source, mask or private coordinates are accepted.
    """
    if type(case_times) not in (tuple, list) or not 2 <= len(case_times) <= 256:
        raise FreezeOrderHold('INVALID_COHORT')
    hypothesis = _timestamp(hypothesis_frozen_at)
    freezes, annotations = [], []
    for row in case_times:
        if type(row) is not dict or set(row) != {'prediction_frozen_at', 'annotation_created_at'}:
            raise FreezeOrderHold('INVALID_FIELDS')
        freeze = _timestamp(row['prediction_frozen_at'])
        annotation = _timestamp(row['annotation_created_at'])
        if not hypothesis < freeze < annotation:
            raise FreezeOrderHold('PER_CASE_FREEZE_ORDER')
        freezes.append(freeze)
        annotations.append(annotation)
    if max(freezes) >= min(annotations):
        raise FreezeOrderHold('CROSS_CASE_ANNOTATION_LEAKAGE_WINDOW')
    return {'schema': 'minimalizer/local-l02/cohort-freeze-order/v1',
            'cohort_size': len(case_times), 'chronology_preflight_pass': True,
            'timestamp_authority_verified': False,
            'annotation_used_for_inference': False,
            'unseen_generalization_proven': False, 'semantic_quality_pass': False,
            'L02': 'HOLD', 'Golden': 'HOLD', 'L03': 'NO_GO', 'production': 'NO_GO'}
