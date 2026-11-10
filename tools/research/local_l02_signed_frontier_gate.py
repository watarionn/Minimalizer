"""Post-inference, known-label P0 frontier. Not inference or a release gate.

Inputs are source-free aggregate counts from independently authenticated signed
replays. Human annotations may be used only by the upstream postscore, after
candidate owner arrays have been frozen. Unknown pixels are never negatives.
This module cannot promote a known-character candidate to Phase4 or Golden.
"""
from __future__ import annotations

from collections.abc import Mapping
import re


class SignedFrontierHold(ValueError):
    pass


COUNTS = ('TP', 'known_FP', 'known_FN', 'known_arm_FP', 'known_underlayer_FP')
SHA_FIELDS = ('source_sha256', 'review_sha256', 'owner_sha256')
SHA256_RE = re.compile(r'[0-9a-f]{64}\Z')


def validate_record(record: Mapping) -> None:
    if not isinstance(record, Mapping):
        raise SignedFrontierHold('INVALID_RECORD')
    if (type(record.get('case')) is not str or not record['case'] or
            type(record.get('candidate')) is not str or not record['candidate']):
        raise SignedFrontierHold('INVALID_CASE_OR_CANDIDATE')
    for key in SHA_FIELDS:
        value = record.get(key)
        if type(value) is not str or SHA256_RE.fullmatch(value) is None:
            raise SignedFrontierHold('MISSING_OR_INVALID_SIGNED_SHA:' + key)
    if record.get('known_exposed_case_only') is not True:
        raise SignedFrontierHold('KNOWN_CASE_PROVENANCE_REQUIRED')
    if (record.get('source_sha_verified') is not True or
            record.get('topology_verified') is not True or
            record.get('labels_used_only_for_postscore') is not True):
        raise SignedFrontierHold('SIGNED_SOURCE_TOPOLOGY_OR_POSTSCORE_UNVERIFIED')
    if (record.get('quality') != 'FAIL' or
            record.get('unseen_character_pass') is not False):
        raise SignedFrontierHold('QUALITY_OR_UNSEEN_PASS_FORBIDDEN')
    for key in COUNTS + ('known_positive_total',):
        value = record.get(key)
        if type(value) is not int or value < 0:
            raise SignedFrontierHold('INVALID_KNOWN_COUNT:' + key)
    if record['known_positive_total'] != record['TP'] + record['known_FN']:
        raise SignedFrontierHold('KNOWN_POSITIVE_DENOMINATOR_CHANGED')
    if (record['known_arm_FP'] > record['known_FP'] or
            record['known_underlayer_FP'] > record['known_FP']):
        raise SignedFrontierHold('SUBSET_COUNT_EXCEEDS_KNOWN_FP')


def dominates(a: Mapping, b: Mapping) -> bool:
    """Pareto dominance among the same exposed signed character only."""
    validate_record(a)
    validate_record(b)
    if (a['case'] != b['case'] or
            a['source_sha256'] != b['source_sha256'] or
            a['review_sha256'] != b['review_sha256'] or
            a['known_positive_total'] != b['known_positive_total']):
        raise SignedFrontierHold('INCOMPARABLE_SIGNED_CASE')
    better_or_equal = (a['TP'] >= b['TP'] and
                       a['known_FP'] <= b['known_FP'] and
                       a['known_arm_FP'] <= b['known_arm_FP'] and
                       a['known_underlayer_FP'] <= b['known_underlayer_FP'])
    strictly_better = (a['TP'] > b['TP'] or
                       a['known_FP'] < b['known_FP'] or
                       a['known_arm_FP'] < b['known_arm_FP'] or
                       a['known_underlayer_FP'] < b['known_underlayer_FP'])
    return bool(better_or_equal and strictly_better)


def evaluate_frontier(records: list[Mapping]) -> dict:
    if not isinstance(records, list) or not records:
        raise SignedFrontierHold('EMPTY_RECORDS')
    for record in records:
        validate_record(record)
    names = [record['candidate'] for record in records]
    if len(names) != len(set(names)):
        raise SignedFrontierHold('DUPLICATE_CANDIDATE')
    cases = {record['case'] for record in records}
    totals = {record['known_positive_total'] for record in records}
    source_shas = {record['source_sha256'] for record in records}
    review_shas = {record['review_sha256'] for record in records}
    if (len(cases) != 1 or len(totals) != 1 or
            len(source_shas) != 1 or len(review_shas) != 1):
        raise SignedFrontierHold('INCOMPARABLE_SIGNED_CASE')
    result = []
    for target in records:
        dominators = [record['candidate'] for record in records
                      if record is not target and dominates(record, target)]
        result.append({
            'candidate': target['candidate'],
            'dominated_by': dominators,
            'pareto_known_case': not bool(dominators),
            'known_TP': target['TP'],
            'known_FP': target['known_FP'],
            'known_arm_FP': target['known_arm_FP'],
            'known_underlayer_FP': target['known_underlayer_FP'],
        })
    return {
        'schema': 'minimalizer/local-l02/signed-known-p0-frontier/v2',
        'source_sha256': next(iter(source_shas)),
        'review_sha256': next(iter(review_shas)),
        'case': next(iter(cases)),
        'frontier': result,
        'unlabelled_pixels_treated_as_negative': False,
        'human_labels_in_inference': False,
        'known_case_not_unseen': True,
        'candidate_auto_promoted': False,
        'semantic_quality': 'FAIL',
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
