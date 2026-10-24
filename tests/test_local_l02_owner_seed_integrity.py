import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_owner_seed_integrity import verify_owner_seed_integrity,OwnerSeedIntegrityHold

class TestOwnerSeedIntegrity(unittest.TestCase):
    def scene(self):
        cls=np.zeros((5,12),np.uint8);cls[2,1]=10;cls[2,2:10]=32
        own=np.zeros_like(cls);own[2,1:10]=2
        return dict(before=own,after=own.copy(),class_ids=cls,source_alpha=np.full_like(cls,255))
    def test_identity_is_structural_only(self):
        x=self.scene();meta=verify_owner_seed_integrity(**x)
        self.assertFalse(meta['semantic_quality_pass'])
    def test_last_seed_erasure_rejected(self):
        x=self.scene();x['after'][2,1]=0
        with self.assertRaisesRegex(OwnerSeedIntegrityHold,'SEED_ERASURE'):
            verify_owner_seed_integrity(**x)
    def test_bridge_split_rejected(self):
        x=self.scene();x['after'][2,5]=0
        with self.assertRaisesRegex(OwnerSeedIntegrityHold,'COMPONENT_LOSS_OR_SPLIT'):
            verify_owner_seed_integrity(**x)
    def test_promote_unknown_rejected(self):
        x=self.scene();x['after'][1,1]=2
        with self.assertRaisesRegex(OwnerSeedIntegrityHold,'PROMOTION'):
            verify_owner_seed_integrity(**x)
    def test_alpha_and_owner_class_fail_closed(self):
        x=self.scene();x['source_alpha'][2,1]=0
        with self.assertRaisesRegex(OwnerSeedIntegrityHold,'OWNER_OUTSIDE_SOURCE'):
            verify_owner_seed_integrity(**x)
        x=self.scene();x['class_ids'][2,1]=3
        with self.assertRaisesRegex(OwnerSeedIntegrityHold,'OWNER_CLASS_CONFLICT'):
            verify_owner_seed_integrity(**x)
    def test_noop_unknown_not_negative(self):
        x=self.scene();x['after'][0,0]=0
        verify_owner_seed_integrity(**x)
    def test_safe_terminal_abstain(self):
        x=self.scene();x['after'][2,9]=0
        verify_owner_seed_integrity(**x)
if __name__=='__main__':unittest.main()
