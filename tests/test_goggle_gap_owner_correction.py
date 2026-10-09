"""The inter-eye verified bang cannot be assigned to high forehead goggle gaps."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import goggle_gap_owner_correction as mod

def test_source_mask_owner_is_not_semantically_verified():
    rgb=np.full((340,340,3),[244,109,31],np.uint8)
    mask=np.zeros((340,340),dtype=np.uint8)
    mask[45:50,110:115]=255
    mask[45:50,130:135]=255
    hair=np.zeros((340,340),bool);hair[40:90,:]=True
    masks={"hair":hair,"face":np.zeros_like(hair),"accessory_or_held_object":np.zeros_like(hair),"subject":hair.copy()}
    certified=np.zeros_like(hair);certified[115:130,150:173]=True
    rows=mod.check(Image.fromarray(rgb),Image.fromarray(mask),masks,certified)
    assert len(rows)==1
    assert rows[0]["certified_inter_eye_fringe_count"]==0
    assert rows[0]["source_orange_sample_count"]>0
    assert rows[0]["occlusion_direction_verified"] is False
    assert rows[0]["can_bridge"] is False

def test_fail_closed_on_non_source_occlusion():
    code=Path(mod.__file__).read_text(encoding="utf-8")
    assert '"all_occlusion_directions_verified":False' in code
    assert '"goggle_bridge_authorized":False' in code
    assert '"filled_goggle_svg_generated":False' in code
    assert "from diffusers" not in code
