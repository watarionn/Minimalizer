"""Source-free contract negatives for direct seed contact protection."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_hue_seed_contact_shadow import propose_hue_conflict_seed_contact_guard
from local_l02_hue_conflict_abstain import propose_class32_hue_conflict_abstention


def scene():
    rgba=np.zeros((140,180,4),np.uint8)
    rgba[:,:,:3]=[175,135,80]
    rgba[:,:,3]=255
    cls=np.zeros((140,180),np.uint8)
    own=np.zeros_like(cls)
    cls[30:100,20:80]=10
    own[30:100,20:80]=2
    # Terminal underlayer is separated from the coat seed by a same-hue
    # class32 bridge. The source-only contact guard must not restore it.
    cls[60:90,80:90]=32
    own[60:90,80:90]=2
    cls[60:90,90:140]=32
    own[60:90,90:140]=2
    rgba[60:90,90:140,:3]=[238,239,235]
    # A second neutral class32 part touches the coat seed directly.
    cls[20:30,30:70]=32
    own[20:30,30:70]=2
    rgba[20:30,30:70,:3]=[238,239,235]
    return rgba,cls,own


class TestSeedContactGuard(unittest.TestCase):
    def test_direct_seed_contact_protected_but_distant_conflict_abstains(self):
        rgba,cls,own=scene()
        old,_=propose_class32_hue_conflict_abstention(rgba,cls,own)
        new,meta=propose_hue_conflict_seed_contact_guard(rgba,cls,own)
        self.assertEqual(old[24,50],0)
        self.assertEqual(new[24,50],2)
        self.assertEqual(new[70,115],0)
        self.assertGreater(meta['seed_contact_restored_pixels'],0)
        self.assertGreater(meta['final_abstained_pixels'],0)
        self.assertFalse(meta['semantic_quality_pass'])

    def test_no_owner_promotions_and_inputs_immutable(self):
        rgba,cls,own=scene()
        copies=[x.copy() for x in (rgba,cls,own)]
        new,_=propose_hue_conflict_seed_contact_guard(rgba,cls,own)
        self.assertFalse(np.any((own==0)&(new!=0)))
        self.assertFalse(np.any((new!=0)&(new!=own)))
        for before,after in zip(copies,(rgba,cls,own)):
            self.assertTrue(np.array_equal(before,after))

    def test_repeatable(self):
        rgba,cls,own=scene()
        a,am=propose_hue_conflict_seed_contact_guard(rgba,cls,own)
        b,bm=propose_hue_conflict_seed_contact_guard(rgba,cls,own)
        self.assertTrue(np.array_equal(a,b))
        self.assertEqual(am,bm)

if __name__=='__main__':unittest.main()
