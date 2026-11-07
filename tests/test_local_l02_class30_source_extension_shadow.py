"""Source-free owner/alpha/ambiguity negatives, never an unseen-quality test."""
import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_class30_source_extension_shadow import propose_class30_extension_shadow, Class30Hold


def scene():
    cls = np.zeros((7, 12), dtype=np.uint8)
    anime = np.zeros_like(cls)
    owner = np.zeros_like(cls)
    owner[3,1] = 2; cls[3,1] = 10
    cls[3,2:7] = 30; anime[3,2:7] = 10
    rgba = np.zeros((*cls.shape, 4), dtype=np.uint8)
    rgba[...,3] = 255
    return dict(source_rgba=rgba, class_ids=cls, anime_classes=anime,
                frozen_owner=owner, safe_baseline=owner.copy())

class TestClass30SourceExtension(unittest.TestCase):
    def test_single_owner_source_only_connected(self):
        x=scene();out,m=propose_class30_extension_shadow(**x)
        self.assertEqual(m['source_only_added_px'],5)
        self.assertEqual(m['coat_added_px'],5)
        self.assertTrue(np.array_equal(out[x['frozen_owner']>0],x['frozen_owner'][x['frozen_owner']>0]))
        self.assertFalse(m['unseen_character_pass'])
        self.assertEqual(m['quality'],'FAIL')
    def test_ambiguous_whole_fragment_abstains(self):
        x=scene();x['frozen_owner'][3,7]=1;x['safe_baseline'][3,7]=1;x['class_ids'][3,7]=5
        out,m=propose_class30_extension_shadow(**x)
        self.assertEqual(m['source_only_added_px'],0)
        self.assertEqual(m['ambiguous_class30_abstained_px'],5)
        self.assertTrue(np.array_equal(out,x['safe_baseline']))
    def test_diagonal_only_cannot_attach(self):
        x=scene();x['class_ids'][3,2:7]=0;x['anime_classes'][3,2:7]=0
        x['class_ids'][2,2]=30;x['anime_classes'][2,2]=10
        out,m=propose_class30_extension_shadow(**x)
        self.assertEqual(m['source_only_added_px'],0)
    def test_alpha_zero_never_promoted(self):
        x=scene();x['source_rgba'][3,2,3]=0
        out,m=propose_class30_extension_shadow(**x)
        self.assertEqual(out[3,2],0)
        self.assertEqual(m['source_pixels_generated'],0)
    def test_generic_clothes_required(self):
        x=scene();x['anime_classes'][:]=11
        out,m=propose_class30_extension_shadow(**x)
        self.assertTrue(np.array_equal(out,x['safe_baseline']))
    def test_non_class30_not_promoted(self):
        x=scene();x['class_ids'][3,2:7]=32
        out,m=propose_class30_extension_shadow(**x)
        self.assertEqual(m['source_only_added_px'],0)
    def test_existing_owner_immutable(self):
        x=scene();x['safe_baseline'][3,1]=0
        with self.assertRaises(Class30Hold):propose_class30_extension_shadow(**x)
    def test_invalid_domain_fails(self):
        x=scene();x['class_ids'][1,1]=255
        with self.assertRaises(Class30Hold):propose_class30_extension_shadow(**x)
    def test_invalid_alpha_fails(self):
        x=scene();x['source_rgba'][3,1,3]=0
        with self.assertRaises(Class30Hold):propose_class30_extension_shadow(**x)
    def test_invalid_shape_fails(self):
        x=scene();x['anime_classes']=np.zeros((3,3),dtype=np.uint8)
        with self.assertRaises(Class30Hold):propose_class30_extension_shadow(**x)
    def test_invalid_owner_fails(self):
        x=scene();x['frozen_owner'][0,0]=3
        with self.assertRaises(Class30Hold):propose_class30_extension_shadow(**x)
    def test_invalid_baseline_class_fails(self):
        x=scene();x['safe_baseline'][2,1]=1;x['frozen_owner'][2,1]=1
        with self.assertRaises(Class30Hold):propose_class30_extension_shadow(**x)
    def test_no_human_annotations_accepted(self):
        x=scene();x['human_mask']=np.zeros((7,12),bool)
        with self.assertRaises(TypeError):propose_class30_extension_shadow(**x)

if __name__=='__main__':unittest.main()
