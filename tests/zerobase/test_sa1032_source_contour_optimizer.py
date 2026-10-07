import unittest
import cv2
import numpy as np
from minimalizer_zerobase.reviewed_sa10.source_contour_optimizer import optimize_existing_owner_contour

class ExistingContourOptimizerTests(unittest.TestCase):
    def masks(self):
        source = np.zeros((80, 80), np.uint8)
        cv2.rectangle(source, (12, 12), (65, 65), 1, -1)
        existing = np.zeros_like(source)
        cv2.rectangle(existing, (14, 14), (63, 63), 1, -1)
        return existing, source
    def decide(self, **overrides):
        a,b = self.masks()
        kwargs = dict(owner="face",existing_mask=a,source_mask=b,existing_primitive_count=1,proposed_primitive_count=1,existing_material="#fff",proposed_material="#fff",minimum_existing_iou=0.80)
        kwargs.update(overrides)
        return optimize_existing_owner_contour(**kwargs)
    def test_only_research_candidate(self):
        d=self.decide()
        self.assertEqual(d.status,"RESEARCH_CANDIDATE_ONLY")
        self.assertGreater(d.proposal.source_iou,d.proposal.existing_source_iou)
    def test_material_immutable(self):
        self.assertEqual(self.decide(proposed_material="#000").reason,"material_changed")
    def test_budget_immutable(self):
        self.assertEqual(self.decide(proposed_primitive_count=2).reason,"primitive_budget_changed")
    def test_arm_not_eligible(self):
        self.assertEqual(self.decide(owner="left_arm").reason,"owner_not_eligible")
    def test_holes_rejected(self):
        a,b=self.masks()
        b[30:40,30:40]=0
        self.assertEqual(self.decide(source_mask=b).status,"HOLD")
    def test_no_op_rejected(self):
        a,b=self.masks()
        self.assertEqual(self.decide(existing_mask=b).reason,"no_safe_improving_contour")
