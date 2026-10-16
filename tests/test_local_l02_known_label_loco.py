"""Public synthetic, source-free regression for explicit-negative LOCO control."""
import inspect
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from benchmark_known_label_loco import (
    CASES,
    LabelAuthorityError,
    evaluate_known_label_loco,
    validate_known_labels,
)
from benchmark_leave_character_out import predict, sample_train


def synthetic(case):
    h, w = 50, 60
    alpha = np.ones((h, w), dtype=bool)
    positive = np.zeros((h, w), dtype=bool)
    negative = np.zeros((h, w), dtype=bool)
    positive[5:30, 5:30] = True
    negative[33:48, 8:48] = True
    # Unknown is neither a training negative nor an evaluated false positive.
    features = np.zeros((h, w, 18), dtype=np.float32)
    features[..., 0] = 99  # Unknown source color is deliberately misleading.
    features[positive, 0] = 5
    features[negative, 0] = -5
    features[..., 1] = np.arange(h)[:, None] / h
    features[..., 2] = np.arange(w)[None, :] / w
    return {
        'case': case, 'alpha': alpha, 'positive': positive, 'negative': negative,
        'known': positive | negative, 'features': features,
    }


class KnownOnlyTrainingControl(unittest.TestCase):
    def test_unknown_never_enters_training_class(self):
        a, b = synthetic('H04'), synthetic('H06')
        X, y, counts = sample_train([a, b], limit=150, negative_method='known')
        self.assertTrue(np.all(X[y == 0, 0] == -5))
        self.assertTrue(np.all(X[y == 1, 0] == 5))
        self.assertEqual(len(y), 600)
        self.assertEqual(counts['H04']['negative_training_px'], 150)

    def test_strict_positive_negative_unknown_partition(self):
        v = validate_known_labels('H04', synthetic('H04'))
        self.assertEqual(v['positive_px'], 625)
        self.assertEqual(v['explicit_negative_px'], 600)
        self.assertEqual(v['unknown_px'], 1775)
        self.assertLess(v['labelled_alpha_fraction'], 1)

    def test_untraced_opaque_pixels_not_promoted_to_known(self):
        t = synthetic('H04')
        t['known'] = t['alpha']
        with self.assertRaisesRegex(LabelAuthorityError, 'known must equal'):
            validate_known_labels('H04', t)

    def test_conflicting_human_labels_fail_closed(self):
        t = synthetic('H04')
        t['negative'][10, 10] = True
        t['known'] = t['positive'] | t['negative']
        with self.assertRaisesRegex(LabelAuthorityError, 'conflicting'):
            validate_known_labels('H04', t)

    def test_outside_signed_alpha_fails_closed(self):
        t = synthetic('H04')
        t['alpha'][12, 12] = False
        with self.assertRaisesRegex(LabelAuthorityError, 'past signed source alpha'):
            validate_known_labels('H04', t)

    def test_tiny_verified_negative_abstains(self):
        t = synthetic('H04')
        t['negative'][:] = False
        t['negative'][35:39, 10:14] = True
        t['known'] = t['positive'] | t['negative']
        with self.assertRaisesRegex(LabelAuthorityError, 'ABSTAIN'):
            validate_known_labels('H04', t)

    def test_nonfinite_features_abstain(self):
        t = synthetic('H04')
        t['features'][0, 0, 0] = np.nan
        with self.assertRaisesRegex(LabelAuthorityError, 'nonfinite'):
            validate_known_labels('H04', t)

    def test_cannot_train_on_partial_or_duplicate_cases(self):
        with self.assertRaises(LabelAuthorityError):
            evaluate_known_label_loco({'H04': synthetic('H04'), 'H06': synthetic('H06')})

    def test_inference_api_has_no_human_mask_argument(self):
        self.assertEqual(list(inspect.signature(predict).parameters), ['test', 'model'])

    def test_loco_has_independent_training_and_stable_replay(self):
        data = {case: synthetic(case) for case in CASES}
        r1, p1 = evaluate_known_label_loco(data, train_cap=150)
        r2, p2 = evaluate_known_label_loco(data, train_cap=150)
        self.assertEqual(r1, r2)
        self.assertEqual(set(r1['folds']), set(CASES))
        self.assertTrue(all(np.array_equal(p1[k], p2[k]) for k in CASES))
        self.assertTrue(all(np.count_nonzero(p1[k] & ~data[k]['alpha']) == 0 for k in CASES))
        self.assertEqual(r1['production_release'], 'NO_GO')
        self.assertFalse(r1['unknown_used_in_training'])
        for heldout, report in r1['folds'].items():
            self.assertNotIn(heldout, report['train_cases'])
            self.assertEqual(len(report['train_cases']), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
