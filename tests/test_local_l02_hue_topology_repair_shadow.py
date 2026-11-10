"""Source-free unit checks of the frozen-owner minimal 4-connected bridge."""
import sys,unittest
from pathlib import Path
import numpy as np
from scipy import ndimage
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_hue_topology_repair_shadow import _bridge_one_component,TopologyRepairHold

class TestMinimalFrozenOwnerBridge(unittest.TestCase):
    def test_shortest_bridge_uses_original_owner_only(self):
        old=np.zeros((15,30),bool)
        old[4:11,3:11]=True
        old[4:11,19:27]=True
        old[7,11:19]=True
        cur=old.copy();cur[7,11:19]=False
        restored=_bridge_one_component(old,cur,2)
        self.assertEqual(restored,8)
        self.assertEqual(ndimage.label(cur,ndimage.generate_binary_structure(2,1))[1],1)
        self.assertTrue(np.all(cur<=old))

    def test_disjoint_original_components_not_connected(self):
        old=np.zeros((15,30),bool)
        old[4:11,3:11]=True
        old[4:11,19:27]=True
        cur=old.copy()
        with self.assertRaisesRegex(TopologyRepairHold,"NO_FROZEN_OWNER_PATH"):
            _bridge_one_component(old,cur,2)
        self.assertTrue(np.array_equal(cur,old))

    def test_original_unowned_gap_never_filled(self):
        old=np.zeros((10,20),bool)
        old[3:7,2:7]=True
        old[3:7,13:18]=True
        cur=old.copy()
        with self.assertRaisesRegex(TopologyRepairHold,"NO_FROZEN_OWNER_PATH"):
            _bridge_one_component(old,cur,1)
        self.assertFalse(np.any(cur[:,7:13]))

if __name__=='__main__':unittest.main()
