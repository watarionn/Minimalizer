"""Existing observer source-mask and eyewear hypothesis location regression."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
import eyewear_existing_observer_audit as m

def test_historic_eye_detections_outside_real_head_goggles_window():
    assert m.bbox_overlap((137,119,18,13),m.TOP_ROI)==0
    assert m.bbox_overlap((185,120,24,12),m.TOP_ROI)==0
    assert m.bbox_overlap((104,33,116,61),m.TOP_ROI)>0

def test_accessory_label_cannot_become_verified_goggles():
    src=Image.fromarray(np.full((340,340,3),[240,123,54],np.uint8))
    cls=np.zeros((340,340,3),np.uint8)
    cls[48:67,121:150]=m.CLASS_ACCESSORY
    _,top,report=m.audit(src,Image.fromarray(cls))
    assert report["accessory_in_goggle_window"]==19*29
    assert report["verified_goggle_mask"] is False
    assert report["production_render_authority"] is False
    assert top.sum()==19*29

def test_no_inferred_geometry_or_production_edits():
    s=Path(m.__file__).read_text(encoding="utf-8")
    assert "from diffusers" not in s and "import torch" not in s
    assert '"verified_goggle_mask":False' in s
