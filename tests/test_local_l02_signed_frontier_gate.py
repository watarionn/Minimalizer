"""Fail-closed postscore frontier contracts, without private pixels."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_signed_frontier_gate import (
    SignedFrontierHold, dominates, evaluate_frontier, validate_record,
)


def row(name, tp=90, fp=10, arm=1, under=9, fn=None):
    if fn is None:
        fn = 100 - tp
    return dict(candidate=name, case='H06', known_exposed_case_only=True,
                source_sha_verified=True, topology_verified=True,
                labels_used_only_for_postscore=True,
                quality='FAIL', unseen_character_pass=False,
                TP=tp, known_FP=fp, known_FN=fn,
                known_arm_FP=arm, known_underlayer_FP=under,
                known_positive_total=100)


class KnownFrontierContract(unittest.TestCase):
    def test_known_dominance_not_quality_pass(self):
        base = row('base')
        better = row('better', fp=2, arm=0, under=2)
        self.assertTrue(dominates(better, base))
        result = evaluate_frontier([base, better])
        self.assertEqual(result['frontier'][0]['dominated_by'], ['better'])
        self.assertFalse(result['candidate_auto_promoted'])
        self.assertEqual(result['Phase4'], 'FAIL')

    def test_tradeoff_is_not_automatic_win(self):
        a = row('a')
        b = row('b', tp=89, fp=0, arm=0, under=0, fn=11)
        self.assertFalse(dominates(a, b))
        self.assertFalse(dominates(b, a))
        self.assertEqual(sum(x['pareto_known_case'] for x in
                             evaluate_frontier([a, b])['frontier']), 2)

    def test_unknown_is_not_negative(self):
        r = row('one')
        r['unknown_predicted_px'] = 90000
        self.assertFalse(evaluate_frontier([r])['unlabelled_pixels_treated_as_negative'])

    def test_provenance_and_release_fail_closed(self):
        for key, value in (
            ('source_sha_verified', False), ('topology_verified', False),
            ('labels_used_only_for_postscore', False),
            ('quality', 'PASS'), ('unseen_character_pass', True),
            ('known_exposed_case_only', False),
        ):
            with self.subTest(key=key):
                r = row('one')
                r[key] = value
                with self.assertRaises(SignedFrontierHold):
                    validate_record(r)

    def test_known_counts_and_denominator_fail_closed(self):
        for key, value in (
            ('TP', -1), ('known_FP', 3.5),
            ('known_positive_total', 101), ('known_arm_FP', 11),
            ('known_underlayer_FP', True),
        ):
            with self.subTest(key=key):
                r = row('one')
                r[key] = value
                with self.assertRaises(SignedFrontierHold):
                    validate_record(r)

    def test_no_cross_case_duplicate_or_missing_identity(self):
        a = row('a')
        b = row('b')
        b['case'] = 'H08'
        with self.assertRaises(SignedFrontierHold):
            evaluate_frontier([a, b])
        with self.assertRaises(SignedFrontierHold):
            evaluate_frontier([a, row('a')])
        for key in ('case', 'candidate'):
            c = row('c')
            c[key] = ''
            with self.assertRaises(SignedFrontierHold):
                validate_record(c)


if __name__ == '__main__':
    unittest.main()
