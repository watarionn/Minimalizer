import unittest

from minimalizer_zerobase.reviewed_sa10.source_svg_contour_proposals import ContourProposal
from minimalizer_zerobase.reviewed_sa10.source_svg_evidence import proposal_svg_evidence


class SvgEvidenceTests(unittest.TestCase):
    def test_svg_has_outline_only(self):
        p = ContourProposal("hair", ((1, 1), (8, 1), (8, 8)), 0.95, 3, 0.8, 0.9)
        svg = proposal_svg_evidence(p, width=16, height=16)
        self.assertIn('fill="none"', svg)
        self.assertIn('data-owner="hair"', svg)
        self.assertNotIn("<image", svg)

    def test_out_of_bounds_rejected(self):
        p = ContourProposal("face", ((1, 1), (18, 1), (8, 8)), 0.95, 3, 0.8, 0.9)
        with self.assertRaises(ValueError):
            proposal_svg_evidence(p, width=16, height=16)

    def test_unsupported_owner_rejected(self):
        p = ContourProposal("eye", ((1, 1), (8, 1), (8, 8)), 0.95, 3, 0.8, 0.9)
        with self.assertRaises(ValueError):
            proposal_svg_evidence(p, width=16, height=16)
