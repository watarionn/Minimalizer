"""Synthetic-only contracts; no private pixels or human annotation coordinates."""
import sys
import unittest
from pathlib import Path
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_hue_conflict_abstain import (
    propose_class32_hue_conflict_abstention, ColorConflictHold)


def scene():
    rgba=np.zeros((120,120,4),dtype=np.uint8)
    rgba[:,:,:3]=[175,135,80]
    rgba[:,:,3]=255
    cls=np.zeros((120,120),dtype=np.uint8)
    owner=np.zeros_like(cls)
    cls[25:85,20:75]=10
    owner[25:85,20:75]=2
    # White terminal underlayer spur with no trusted class10 seed.
    cls[50:80,75:110]=32
    owner[50:80,75:110]=2
    rgba[50:80,75:110,:3]=[238,239,235]
    # Correct class32 coat fragment in the same seed hue.
    cls[35:45,75:95]=32
    owner[35:45,75:95]=2
    return rgba,cls,owner


class TestSourceOnlyColorConflict(unittest.TestCase):
    def test_neutral_underlayer_abstains_without_erasing_coat_seed(self):
        rgba,cls,owner=scene()
        out,meta=propose_class32_hue_conflict_abstention(rgba,cls,owner)
        self.assertGreater(meta['abstained_pixels'],64)
        self.assertEqual(out[60,90],0)
        self.assertEqual(out[40,85],2)
        self.assertTrue(np.array_equal(out[cls==10],owner[cls==10]))
        self.assertFalse(meta['semantic_quality_pass'])
        self.assertFalse(meta['release_authorized'])

    def test_unknown_never_promoted(self):
        rgba,cls,owner=scene()
        out,_=propose_class32_hue_conflict_abstention(rgba,cls,owner)
        self.assertFalse(np.any((owner==0)&(out>0)))
        self.assertFalse(np.any(out>owner))

    def test_source_alpha_not_extended(self):
        rgba,cls,owner=scene()
        rgba[0,0,3]=0
        out,_=propose_class32_hue_conflict_abstention(rgba,cls,owner)
        self.assertEqual(out[0,0],0)
        rgba[30,30,3]=0
        with self.assertRaisesRegex(ColorConflictHold,'SOURCE_ALPHA'):
            propose_class32_hue_conflict_abstention(rgba,cls,owner)

    def test_no_color_conflict_keeps_owner_exact(self):
        rgba,cls,owner=scene()
        rgba[50:80,75:110,:3]=[175,135,80]
        out,meta=propose_class32_hue_conflict_abstention(rgba,cls,owner)
        self.assertTrue(np.array_equal(out,owner))
        self.assertEqual(meta['abstained_pixels'],0)

    def test_fail_closed_on_untrusted_seed(self):
        rgba,cls,owner=scene()
        cls[cls==10]=32
        with self.assertRaisesRegex(ColorConflictHold,'NO_SATURATED_SEED'):
            propose_class32_hue_conflict_abstention(rgba,cls,owner)

    def test_invalid_contracts(self):
        rgba,cls,owner=scene()
        for x,y,z,kw in [
            (rgba.astype(np.int16),cls,owner,{}),
            (rgba[:,:,:3],cls,owner,{}),
            (rgba,cls[:50],owner,{}),
            (rgba,cls.astype(np.int16),owner,{}),
            (rgba,cls,owner.astype(np.int16),{}),
            (rgba,cls,owner,{'min_region':1}),
        ]:
            with self.subTest(shape=x.shape,kwargs=kw),self.assertRaises(ColorConflictHold):
                propose_class32_hue_conflict_abstention(x,y,z,**kw)

    def test_unexpected_owner_and_class_fail_closed(self):
        rgba,cls,owner=scene()
        owner[40,40]=3
        with self.assertRaisesRegex(ColorConflictHold,'OWNER_DOMAIN'):
            propose_class32_hue_conflict_abstention(rgba,cls,owner)
        rgba,cls,owner=scene()
        cls[40,40]=4
        with self.assertRaisesRegex(ColorConflictHold,'OWNER_CLASS_CONFLICT'):
            propose_class32_hue_conflict_abstention(rgba,cls,owner)

    def test_preserves_connected_components(self):
        rgba,cls,owner=scene()
        out,_=propose_class32_hue_conflict_abstention(rgba,cls,owner)
        st=np.ones((3,3),np.uint8)
        self.assertLessEqual(ndimage.label(out==2,structure=st)[1],
                             ndimage.label(owner==2,structure=st)[1])

    def test_bridge_between_two_seed_islands_must_not_be_cut(self):
        rgba=np.zeros((110,130,4),dtype=np.uint8)
        rgba[:,:,:3]=[175,135,80]
        rgba[:,:,3]=255
        cls=np.zeros((110,130),dtype=np.uint8)
        owner=np.zeros_like(cls)
        for left,right in [(10,35),(90,115)]:
            cls[35:75,left:right]=10
            owner[35:75,left:right]=2
        cls[45:65,35:90]=32
        owner[45:65,35:90]=2
        rgba[45:65,35:90,:3]=[240,240,239]
        out,meta=propose_class32_hue_conflict_abstention(rgba,cls,owner)
        self.assertTrue(np.array_equal(out,owner))
        self.assertGreater(meta['skipped_regions'],0)

    def test_seedless_owner_region_not_auto_deleted(self):
        rgba,cls,owner=scene()
        cls[95:115,90:115]=32
        owner[95:115,90:115]=2
        rgba[95:115,90:115,:3]=[240,240,239]
        out,meta=propose_class32_hue_conflict_abstention(rgba,cls,owner)
        self.assertTrue(np.all(out[95:115,90:115]==2))
        self.assertGreater(meta['skipped_regions'],0)

    def test_replay_is_deterministic_and_input_immutable(self):
        rgba,cls,owner=scene()
        frozen=(rgba.copy(),cls.copy(),owner.copy())
        a,am=propose_class32_hue_conflict_abstention(rgba,cls,owner)
        b,bm=propose_class32_hue_conflict_abstention(rgba,cls,owner)
        self.assertTrue(np.array_equal(a,b))
        self.assertEqual(am,bm)
        for old,new in zip(frozen,(rgba,cls,owner)):
            self.assertTrue(np.array_equal(old,new))

if __name__=='__main__':unittest.main()
