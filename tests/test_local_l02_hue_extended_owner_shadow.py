"""Source-free structural regressions for frozen extension owner retention."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_hue_extended_owner_shadow import propose_hue_extended_owner_shadow,ExtendedOwnerHold


def scene():
    rgba=np.zeros((9,11,4),dtype=np.uint8)
    rgba[...,3]=255
    cls=np.zeros((9,11),dtype=np.uint8)
    own=np.zeros_like(cls)
    cls[4,1]=10;own[4,1]=2
    cls[4,2:8]=32;own[4,2:8]=2
    cls[4,8]=30;own[4,8]=2
    cls[3,5]=32;own[3,5]=2
    return rgba,cls,own

class TestExtendedOwner(unittest.TestCase):
    def test_class32_abstention_preserves_extension_and_identity(self):
        rgba,cls,own=scene()
        def fake(_,__,core):
            o=core.copy();o[3,5]=0
            return o,{'semantic_quality_pass':False}
        with patch('local_l02_hue_extended_owner_shadow.propose_hue_topology_repair_shadow',side_effect=fake):
            result,meta=propose_hue_extended_owner_shadow(source_rgba=rgba,class_ids=cls,frozen_owner=own)
        self.assertEqual(result[4,8],2)
        self.assertEqual(result[3,5],0)
        self.assertEqual(meta['removed_class32_owner_pixels'],1)
        self.assertEqual(meta['component_identity_4_8_preserved']['owner2_4'],1)
        self.assertFalse(meta['semantic_quality_pass'])

    def test_split_fails_closed(self):
        rgba,cls,own=scene()
        def fake(_,__,core):
            o=core.copy();o[4,4]=0
            return o,{}
        with patch('local_l02_hue_extended_owner_shadow.propose_hue_topology_repair_shadow',side_effect=fake):
            with self.assertRaisesRegex(ExtendedOwnerHold,'OWNER_COMPONENT_COUNT_CHANGED'):
                propose_hue_extended_owner_shadow(source_rgba=rgba,class_ids=cls,frozen_owner=own)

    def test_nonclass32_erasure_fails_closed(self):
        rgba,cls,own=scene()
        def fake(_,__,core):
            o=core.copy();o[4,1]=0
            return o,{}
        with patch('local_l02_hue_extended_owner_shadow.propose_hue_topology_repair_shadow',side_effect=fake):
            with self.assertRaisesRegex(ExtendedOwnerHold,'FROZEN_SOURCE_OR_EXTENSION_VIOLATION'):
                propose_hue_extended_owner_shadow(source_rgba=rgba,class_ids=cls,frozen_owner=own)

    def test_source_alpha_and_class_domain(self):
        rgba,cls,own=scene()
        rgba[4,8,3]=0
        with self.assertRaisesRegex(ExtendedOwnerHold,'OWNER_OUTSIDE_SOURCE'):
            propose_hue_extended_owner_shadow(source_rgba=rgba,class_ids=cls,frozen_owner=own)
        rgba[4,8,3]=255;cls[4,8]=15
        with self.assertRaisesRegex(ExtendedOwnerHold,'OWNER_CLASS_CONFLICT'):
            propose_hue_extended_owner_shadow(source_rgba=rgba,class_ids=cls,frozen_owner=own)

if __name__=='__main__':unittest.main()
