"""Negative controls for L02 exclusive owner research candidate. No private user originals."""
import io,sys,unittest
from pathlib import Path
import cv2,numpy as np
from PIL import Image
import hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_owner_topology_candidate import PARTS,PROTECTED,LEAVES,Hold,validate_shapes,connected_core,prune_detached_to_unknown,resolve_owners,count_components,verify_signed_source

class CandidateTest(unittest.TestCase):
    def setUp(self):
        h,w=100,100; self.src=np.zeros((h,w,4),np.uint8)
        self.src[10:90,10:90,3]=255
        self.src[10:90,10:90,:3]=[40,80,90]
        self.owners={k:np.zeros((h,w),bool) for k in PARTS}
        self.owners['head'][10:37,30:70]=True
        self.owners['hair'][10:34,30:60]=True
        self.owners['face'][16:28,60:68]=True
        self.owners['neck'][34:40,45:54]=True
        self.owners['torso'][40:84,20:76]=True
        self.owners['major_clothing'][48:65,20:30]=True
        self.owners['torso'] &= ~self.owners['major_clothing']
        self.owners['left_arm'][50:78,10:19]=True
        self.owners['right_arm'][50:78,80:88]=True
        self.owners['lower_body'][84:90,30:67]=True
        self.owners['unknown'][36:42,20:30]=True
        self.owners['torso'] &= ~self.owners['neck']
        self.owners['torso'] &= ~self.owners['unknown']
        self.evidence=np.zeros((h,w),bool);self.evidence[43:83,30:63]=True
        bio=io.BytesIO();Image.fromarray(self.src,'RGBA').save(bio,format='PNG')
        self.source_bytes=bio.getvalue()
        self.sha256=hashlib.sha256(self.source_bytes).hexdigest()
    def run_repair(self,source,owners,evidence):
        return resolve_owners(source,owners,evidence,source_bytes=self.source_bytes,expected_sha256=self.sha256)
    def test_base_accepts(self):self.assertEqual(validate_shapes(self.src,self.owners,self.evidence).shape,(100,100))
    def test_source_opaque_reject(self):
        x=self.evidence.copy();x[0,0]=True
        with self.assertRaises(Hold):self.run_repair(self.src,self.owners,x)
    def test_missing_owner_reject(self):
        x=dict(self.owners);x.pop('head')
        with self.assertRaises(Hold):self.run_repair(self.src,x,self.evidence)
    def test_nonbinary_owner_reject(self):
        x=dict(self.owners);x['hair']=x['hair'].astype(np.uint8)
        with self.assertRaises(Hold):self.run_repair(self.src,x,self.evidence)
    def test_bad_rgba_reject(self):
        with self.assertRaises(Hold):self.run_repair(self.src[:,:,:3],self.owners,self.evidence)
    def test_protected_reject(self):
        x=self.evidence.copy();x[20,62]=True
        with self.assertRaises(Hold):self.run_repair(self.src,self.owners,x)
    def test_beyond_signed_union_reject(self):
        x=self.evidence.copy();x[20,20]=True
        with self.assertRaises(Hold):self.run_repair(self.src,self.owners,x)
    def test_nonsensical_tiny_evidence_reject(self):
        x=np.zeros(self.evidence.shape,bool);x[55:60,40:45]=True
        with self.assertRaises(Hold):self.run_repair(self.src,self.owners,x)
    def test_source_already_signed_overlap_reject(self):
        x={k:v.copy() for k,v in self.owners.items()};x['hair'][60,45]=True
        with self.assertRaises(Hold):self.run_repair(self.src,x,self.evidence)
    def test_evidence_format_reject(self):
        with self.assertRaises(Hold):self.run_repair(self.src,self.owners,self.evidence.astype(np.uint8))
    def test_output_protected_unchanged(self):
        n,core,rep=self.run_repair(self.src,self.owners,self.evidence)
        self.assertEqual(rep.protected_xor_pixels,0)
        for key in PROTECTED:self.assertTrue(np.array_equal(n[key],self.owners[key]))
    def test_output_head_parent_unchanged(self):
        n,core,rep=self.run_repair(self.src,self.owners,self.evidence)
        self.assertTrue(np.array_equal(n['head'],self.owners['head']))
    def test_output_source_union_exact(self):
        n,core,rep=self.run_repair(self.src,self.owners,self.evidence)
        old=np.logical_or.reduce(list(self.owners.values()))
        new=np.logical_or.reduce(list(n.values()))
        self.assertTrue(np.array_equal(old,new));self.assertEqual(rep.signed_union_xor_pixels,0)
    def test_no_leaf_overlap(self):
        n,core,rep=self.run_repair(self.src,self.owners,self.evidence)
        self.assertFalse((sum(n[k].astype('uint8') for k in LEAVES)>1).any());self.assertEqual(rep.leaf_overlap_pixels,0)
    def test_research_never_gold(self):
        n,core,rep=self.run_repair(self.src,self.owners,self.evidence)
        self.assertEqual(rep.status,'RESEARCH_CANDIDATE_NOT_GOLDEN')
    def test_detached_hair_abstains(self):
        h=np.zeros((30,50),bool);h[4:25,7:43]=True
        cut=h.copy();cut[:,25:27]=False
        ret,unk=prune_detached_to_unknown(cut,h)
        self.assertEqual(count_components(ret),1);self.assertTrue(unk.any());self.assertFalse((ret&unk).any())
    def test_loss_of_original_component_abstains(self):
        h=np.zeros((30,50),bool);h[4:25,7:43]=True;h[2,2]=True
        cut=h.copy();cut[2,2]=False
        with self.assertRaises(Hold):prune_detached_to_unknown(cut,h)
    def test_reject_bad_min_area(self):
        with self.assertRaises(Hold):connected_core(self.evidence,self.evidence,absolute_min_area=0)
    def test_reject_unknown_change_to_original(self):
        n,core,rep=self.run_repair(self.src,self.owners,self.evidence)
        self.assertEqual(int(self.owners['unknown'].sum()),60)
    def test_neck_bridge_restores_relation_without_painting(self):
        evidence=np.zeros(self.evidence.shape,bool)
        evidence[40:78,20:76]=True
        evidence &= ~self.owners['neck']
        evidence &= ~self.owners['face']
        # Source evidence may overlap old major clothing but not any protected original class.
        n,core,rep=self.run_repair(self.src,self.owners,evidence)
        self.assertGreater(rep.reserved_original_torso_bridge_pixels,0)
        self.assertLessEqual(rep.neck_torso_gap_new,6.0)
        self.assertEqual(rep.signed_union_xor_pixels,0)
        self.assertEqual(rep.protected_xor_pixels,0)
        self.assertEqual(rep.repaired_components['torso'],rep.inherited_components['torso'])
    def test_missing_neck_bridge_rejected(self):
        x={k:v.copy() for k,v in self.owners.items()};x['neck'][:]=False
        with self.assertRaises(Hold):self.run_repair(self.src,x,self.evidence)
    def test_signed_bytes_tampering_refused(self):
        with self.assertRaises(Hold):resolve_owners(self.src,self.owners,self.evidence,source_bytes=b'tampered',expected_sha256=self.sha256)
    def test_original_raw_with_changed_rgba_refused(self):
        changed=self.src.copy();changed[55,50,0]=250
        with self.assertRaises(Hold):self.run_repair(changed,self.owners,self.evidence)
    def test_missing_source_hash_refused(self):
        with self.assertRaises(Hold):resolve_owners(self.src,self.owners,self.evidence,source_bytes=self.source_bytes,expected_sha256='')
    def test_independent_no_manual_reference_in_api(self):
        self.assertNotIn('manual',resolve_owners.__code__.co_varnames[:resolve_owners.__code__.co_argcount])

if __name__=='__main__':unittest.main(verbosity=2)
