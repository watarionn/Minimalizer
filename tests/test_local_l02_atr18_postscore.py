import hashlib
import unittest

import numpy as np

from tools.research.local_l02_atr18_postscore import (
    ARM_CLASS_IDS,
    GARMENT_CLASS_IDS,
    MODEL_REVISION,
    MODEL_SHA256,
    PostscoreHold,
    decode_review_mask,
    score_case,
    topology_counts,
)


def receipt(case, encoded, rgba, ids):
    return {
        "case": case,
        "model_revision": MODEL_REVISION,
        "checkpoint_sha256": MODEL_SHA256,
        "postscore_not_yet_performed": True,
        "human_annotations_used": False,
        "review_labels_used_for_inference": False,
        "encoded_source_sha256": hashlib.sha256(encoded).hexdigest(),
        "source_rgba_sha256": hashlib.sha256(rgba.tobytes()).hexdigest(),
        "class_map_sha256_private": hashlib.sha256(ids.tobytes()).hexdigest(),
        "class_map_is_observer_output_not_owner_mask": True,
        "owner_modified": False,
        "unknown_not_treated_as_negative": True,
    }


class Atr18PostscoreTests(unittest.TestCase):
    def test_unknown_review_pixels_are_excluded(self):
        review = np.zeros((2, 2, 4), dtype=np.uint8)
        review[0, 0] = (0, 255, 0, 255)
        review[0, 1] = (255, 0, 0, 255)
        review[1, 0] = (127, 127, 0, 255)
        green, red, unknown = decode_review_mask(review)
        self.assertEqual(int(green.sum()), 1)
        self.assertEqual(int(red.sum()), 1)
        self.assertEqual(int(unknown.sum()), 2)

    def test_score_uses_known_labels_and_preserves_unknown(self):
        encoded = b"signed-source-fixture"
        rgba = np.full((2, 2, 4), 255, dtype=np.uint8)
        rgba[1, 1, 3] = 0
        mask = np.zeros((2, 2, 4), dtype=np.uint8)
        mask[0, 0] = (0, 255, 0, 255)
        mask[0, 1] = (255, 0, 0, 255)
        mask[1, 0] = (127, 127, 0, 255)
        ids = np.zeros((2, 2), dtype=np.uint8)
        ids[0, 0] = 4
        ids[0, 1] = 14
        got = score_case(case="H06", encoded_source=encoded, source_rgba=rgba,
                         review_mask_rgba=mask, class_ids=ids,
                         receipt=receipt("H06", encoded, rgba, ids),
                         review_mask_sha256="a" * 64)
        self.assertEqual(got["known_only_confusion"],
                         {"tp": 1, "fp": 0, "fn": 0, "tn": 1})
        self.assertEqual(got["unknown_source_pixels"], 1)
        self.assertEqual(got["human_positive_topology"]["components4"], 1)
        self.assertEqual(got["formal_quality"], "UNASSESSED")
        self.assertEqual(got["Phase4"], "FAIL")

    def test_alpha_zero_never_enters_known_negative_denominator(self):
        encoded = b"source"
        rgba = np.full((1, 2, 4), 255, dtype=np.uint8)
        rgba[0, 1, 3] = 0
        mask = np.zeros((1, 2, 4), dtype=np.uint8)
        mask[0, :] = (255, 0, 0, 255)
        ids = np.zeros((1, 2), dtype=np.uint8)
        got = score_case(case="H08", encoded_source=encoded, source_rgba=rgba,
                         review_mask_rgba=mask, class_ids=ids,
                         receipt=receipt("H08", encoded, rgba, ids),
                         review_mask_sha256="b" * 64)
        self.assertEqual(got["known_negative_pixels"], 1)
        self.assertEqual(got["known_only_confusion"]["tn"], 1)

    def test_labels_used_for_inference_fail_closed(self):
        encoded = b"source"
        rgba = np.full((1, 1, 4), 255, dtype=np.uint8)
        mask = np.zeros((1, 1, 4), dtype=np.uint8)
        ids = np.zeros((1, 1), dtype=np.uint8)
        bad = receipt("H04", encoded, rgba, ids)
        bad["human_annotations_used"] = True
        with self.assertRaisesRegex(PostscoreHold, "labels_not_used_for_inference"):
            score_case(case="H04", encoded_source=encoded, source_rgba=rgba,
                       review_mask_rgba=mask, class_ids=ids, receipt=bad,
                       review_mask_sha256="c" * 64)

    def test_modified_frozen_class_map_fails_receipt_binding(self):
        encoded = b"source"
        rgba = np.full((1, 1, 4), 255, dtype=np.uint8)
        mask = np.zeros((1, 1, 4), dtype=np.uint8)
        ids = np.zeros((1, 1), dtype=np.uint8)
        bad = receipt("H04", encoded, rgba, ids)
        ids[0, 0] = 4
        with self.assertRaisesRegex(PostscoreHold, "class_map_sha256"):
            score_case(case="H04", encoded_source=encoded, source_rgba=rgba,
                       review_mask_rgba=mask, class_ids=ids, receipt=bad,
                       review_mask_sha256="d" * 64)

    def test_topology_tracks_holes_without_count_subtraction(self):
        ring = np.ones((3, 3), dtype=bool)
        ring[1, 1] = False
        self.assertEqual(topology_counts(ring),
                         {"components4": 1, "components8": 1,
                          "holes4": 1, "holes8": 1})


if __name__ == "__main__":
    unittest.main()
