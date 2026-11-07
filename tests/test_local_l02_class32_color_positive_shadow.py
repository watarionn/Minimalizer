"""Fail-closed source-only smoke checks. No private image or human label."""
import io
import unittest

import numpy as np
from PIL import Image

from tools.research.local_l02_class32_color_positive_shadow import (
    propose_pinned_run30_class32_positive, SourceOnlyAbstentionHold,
)


class TestPinnedColorPositive(unittest.TestCase):
    def test_rejects_unpinned_case(self):
        with self.assertRaisesRegex(SourceOnlyAbstentionHold, 'UNPINNED'):
            propose_pinned_run30_class32_positive(
                case_id='unknown', source_bytes=b'bad',
                class_ids=np.zeros((2, 2), np.uint8),
                frozen_owner=np.zeros((2, 2), np.uint8))

    def test_rejects_mixed_frozen_sources(self):
        b = io.BytesIO()
        Image.new('RGBA', (4, 4), (250, 100, 100, 255)).save(b, 'PNG')
        with self.assertRaisesRegex(SourceOnlyAbstentionHold, 'TRIPLE_MISMATCH'):
            propose_pinned_run30_class32_positive(
                case_id='H08', source_bytes=b.getvalue(),
                class_ids=np.full((4, 4), 32, np.uint8),
                frozen_owner=np.zeros((4, 4), np.uint8))

    def test_rejects_bad_class_dtype(self):
        with self.assertRaisesRegex(SourceOnlyAbstentionHold, 'INVALID'):
            propose_pinned_run30_class32_positive(
                case_id='H08', source_bytes=b'bad',
                class_ids=np.zeros((2, 2), np.int32),
                frozen_owner=np.zeros((2, 2), np.uint8))

    def test_rejects_bad_owner_taxonomy(self):
        with self.assertRaisesRegex(SourceOnlyAbstentionHold, 'INVALID'):
            propose_pinned_run30_class32_positive(
                case_id='H08', source_bytes=b'bad',
                class_ids=np.zeros((2, 2), np.uint8),
                frozen_owner=np.full((2, 2), 3, np.uint8))


if __name__ == '__main__':
    unittest.main()
